# Databricks notebook source
# MAGIC %md
# MAGIC # Create gold tables
# MAGIC Creates the PegWatch gold layer from the shared contract.
# MAGIC Source: `shared/schema/generated/databricks_gold.sql` (generated from `gold_contract.yaml`). Safe to re-run.

# COMMAND ----------

import os
from pathlib import Path

sql_path = (Path(os.getcwd()) / "../../shared/schema/generated/databricks_gold.sql").resolve()
print(f"Reading {sql_path}")

statements = [
    s.strip()
    for s in sql_path.read_text(encoding="utf-8").split(";\n")
    if s.strip() and not all(line.startswith("--") for line in s.strip().splitlines())
]

for stmt in statements:
    sql = "\n".join(line for line in stmt.splitlines() if not line.startswith("--")).strip()
    first_line = sql.splitlines()[0]
    spark.sql(sql)
    print(f"OK  {first_line}")

# COMMAND ----------

display(spark.sql("SHOW TABLES IN workspace.pegwatch_gold"))
