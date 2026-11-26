# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze ingestion
# MAGIC Runs the shared jobs in `shared/pegwatch_shared/ingest.py`, the same code Google Cloud runs,
# MAGIC and writes raw files to the volume `/Volumes/workspace/pegwatch_bronze/raw` using the same folder layout as the GCS bucket.
# MAGIC
# MAGIC Started by the scheduled jobs created in `00_setup`. Can also be run by hand.

# COMMAND ----------

dbutils.widgets.dropdown("job", "market_hourly", ["market_hourly", "fx_daily", "mica_weekly"], "Job")
dbutils.widgets.text("sink", "/Volumes/workspace/pegwatch_bronze/raw", "Sink")

job = dbutils.widgets.get("job")
sink = dbutils.widgets.get("sink")

# COMMAND ----------

import importlib
import os
import sys

# Use the shared package straight from the Git folder (requests and pyyaml are preinstalled)
repo_root = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
shared_path = os.path.join(repo_root, "shared")
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# Key comes from the Databricks secret scope, never from code
os.environ["COINGECKO_DEMO_API_KEY"] = dbutils.secrets.get("pegwatch", "coingecko-api-key")

from pegwatch_shared import ingest  # noqa: E402

importlib.reload(ingest)

# COMMAND ----------

exit_code = ingest.main(["--job", job, "--sink", sink])
if exit_code != 0:
    raise RuntimeError(f"Ingestion job '{job}' had failing steps; see the step_failed lines above")
