# Databricks notebook source
# MAGIC %md
# MAGIC # PegWatch Databricks setup (run once, safe to re-run)
# MAGIC 1. Stores the CoinGecko key in the secret scope `pegwatch`
# MAGIC 2. Creates the bronze schema and volume
# MAGIC 3. Creates or updates the three scheduled ingestion jobs
# MAGIC
# MAGIC **Paste the key in the widget at the top, run all, then clear the widget.**
# MAGIC Widget values are not saved to Git, but never type the key into a cell.

# COMMAND ----------

dbutils.widgets.text("coingecko_api_key", "", "CoinGecko key (empty = keep existing)")

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

w = WorkspaceClient()
SCOPE = "pegwatch"

if SCOPE not in {s.name for s in w.secrets.list_scopes()}:
    w.secrets.create_scope(scope=SCOPE)
    print(f"Created secret scope '{SCOPE}'")

key = dbutils.widgets.get("coingecko_api_key").strip()
if key:
    w.secrets.put_secret(scope=SCOPE, key="coingecko-api-key", string_value=key)
    print("Stored coingecko-api-key. Now clear the widget at the top.")
else:
    print("No key entered, keeping the existing secret.")

print("Secrets in scope:", [s.key for s in w.secrets.list_secrets(scope=SCOPE)])

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.pegwatch_bronze")
spark.sql(
    "CREATE VOLUME IF NOT EXISTS workspace.pegwatch_bronze.raw "
    "COMMENT 'Raw bronze files, same layout as the GCS bucket'"
)
print("Volume ready: /Volumes/workspace/pegwatch_bronze/raw")

# COMMAND ----------

import os

# Path of the ingestion notebook in this Git folder (workspace path, without /Workspace prefix)
notebook_path = os.path.join(os.getcwd(), "01_ingest_bronze").removeprefix("/Workspace")

# Quartz cron, Stockholm time. Same schedules as GCP, offset 5 minutes so the two don't overlap.
SCHEDULES = {
    "market_hourly": "0 10 * * * ?",       # every hour at :10
    "fx_daily": "0 35 16 ? * MON-FRI",     # weekdays 16:35
    "mica_weekly": "0 5 7 ? * MON",        # Mondays 07:05
}

existing = {j.settings.name: j.job_id for j in w.jobs.list() if j.settings and j.settings.name}

for job, cron in SCHEDULES.items():
    name = f"pegwatch-{job.replace('_', '-')}"
    settings = jobs.JobSettings(
        name=name,
        tags={"project": "pegwatch", "layer": "bronze"},
        max_concurrent_runs=1,
        schedule=jobs.CronSchedule(
            quartz_cron_expression=cron,
            timezone_id="Europe/Stockholm",
            pause_status=jobs.PauseStatus.UNPAUSED,
        ),
        tasks=[
            jobs.Task(
                task_key="ingest",
                notebook_task=jobs.NotebookTask(notebook_path=notebook_path, base_parameters={"job": job}),
                max_retries=1,
                timeout_seconds=900,
            )
        ],
    )
    if name in existing:
        w.jobs.reset(job_id=existing[name], new_settings=settings)
        print(f"Updated {name} (job {existing[name]})")
    else:
        created = w.jobs.create(
            name=settings.name,
            tags=settings.tags,
            max_concurrent_runs=settings.max_concurrent_runs,
            schedule=settings.schedule,
            tasks=settings.tasks,
        )
        print(f"Created {name} (job {created.job_id})")
