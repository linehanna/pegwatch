"""Generate gold-layer DDL for BigQuery and Databricks from gold_contract.yaml.

Usage (from the repo root):
    python shared/schema/generate_ddl.py

Writes:
    shared/schema/generated/bigquery_gold.sql
    shared/schema/generated/databricks_gold.sql

Never edit the generated files by hand: change the contract and regenerate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
CONTRACT = HERE / "gold_contract.yaml"
OUT_DIR = HERE / "generated"

BQ_DATASET = "pegwatch.pegwatch_gold"
DBX_SCHEMA = "workspace.pegwatch_gold"

TYPE_MAP = {
    #  contract     BigQuery     Databricks
    "STRING":    ("STRING",    "STRING"),
    "INT64":     ("INT64",     "BIGINT"),
    "FLOAT64":   ("FLOAT64",   "DOUBLE"),
    "NUMERIC":   ("NUMERIC",   "DECIMAL(38,9)"),
    "BOOL":      ("BOOL",      "BOOLEAN"),
    "DATE":      ("DATE",      "DATE"),
    "TIMESTAMP": ("TIMESTAMP", "TIMESTAMP"),
}

def sql_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'")


def load_contract() -> dict:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    validate(contract)
    return contract


def validate(contract: dict) -> None:
    errors: list[str] = []
    for table, spec in contract["tables"].items():
        names = [c["name"] for c in spec["columns"]]
        if len(names) != len(set(names)):
            errors.append(f"{table}: duplicate column names")
        if "platform" not in names:
            errors.append(f"{table}: missing required column 'platform'")
        for col in spec["columns"]:
            if col["type"] not in TYPE_MAP:
                errors.append(f"{table}.{col['name']}: unknown type {col['type']}")
        part = spec.get("partition_by")
        if part and part not in names:
            errors.append(f"{table}: partition_by '{part}' is not a column")
        for c in spec.get("cluster_by", []):
            if c not in names:
                errors.append(f"{table}: cluster_by '{c}' is not a column")
    if errors:
        sys.exit("Contract errors:\n  " + "\n  ".join(errors))


def column_lines(spec: dict, dialect: int) -> list[str]:
    lines = []
    for col in spec["columns"]:
        sql_type = TYPE_MAP[col["type"]][dialect]
        not_null = " NOT NULL" if not col.get("nullable", True) else ""
        desc = col.get("description")
        if dialect == 0:  # BigQuery
            opts = f" OPTIONS(description='{sql_string(desc)}')" if desc else ""
        else:  # Databricks
            opts = f" COMMENT '{sql_string(desc)}'" if desc else ""
        lines.append(f"  {col['name']} {sql_type}{not_null}{opts}")
    return lines


def bigquery_ddl(name: str, spec: dict) -> str:
    cols = ",\n".join(column_lines(spec, 0))
    parts = [f"CREATE TABLE IF NOT EXISTS `{BQ_DATASET}.{name}` (\n{cols}\n)"]
    part = spec.get("partition_by")
    if part:
        col_type = next(c["type"] for c in spec["columns"] if c["name"] == part)
        parts.append(f"PARTITION BY {part}" if col_type == "DATE" else f"PARTITION BY DATE({part})")
    if spec.get("cluster_by"):
        parts.append("CLUSTER BY " + ", ".join(spec["cluster_by"]))
    parts.append(f"OPTIONS(description='{sql_string(spec['description'])}')")
    return "\n".join(parts) + ";\n"


def databricks_ddl(name: str, spec: dict) -> str:
    cols = ",\n".join(column_lines(spec, 1))
    parts = [f"CREATE TABLE IF NOT EXISTS {DBX_SCHEMA}.{name} (\n{cols}\n)"]
    parts.append("USING DELTA")
    # Liquid clustering replaces partitioning on Databricks; include the time column.
    cluster = list(spec.get("cluster_by", []))
    if spec.get("partition_by") and spec["partition_by"] not in cluster:
        cluster.append(spec["partition_by"])
    if cluster:
        parts.append("CLUSTER BY (" + ", ".join(cluster) + ")")
    parts.append(f"COMMENT '{sql_string(spec['description'])}'")
    return "\n".join(parts) + ";\n"


def main() -> None:
    contract = load_contract()
    OUT_DIR.mkdir(exist_ok=True)
    header = (
        "-- GENERATED from shared/schema/gold_contract.yaml "
        f"(contract v{contract['version']}). Do not edit by hand.\n\n"
    )

    bq = [header, "-- Dataset pegwatch_gold is created by Terraform (platforms/gcp/infra).\n\n"]
    dbx = [header, f"CREATE SCHEMA IF NOT EXISTS {DBX_SCHEMA};\n\n"]
    for name, spec in contract["tables"].items():
        bq.append(bigquery_ddl(name, spec) + "\n")
        dbx.append(databricks_ddl(name, spec) + "\n")

    (OUT_DIR / "bigquery_gold.sql").write_text("".join(bq), encoding="utf-8")
    (OUT_DIR / "databricks_gold.sql").write_text("".join(dbx), encoding="utf-8")
    print(f"Generated {len(contract['tables'])} tables for BigQuery and Databricks in {OUT_DIR}")


if __name__ == "__main__":
    main()
