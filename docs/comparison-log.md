# Platform comparison log

Write a line every time you notice something about either platform. The final comparison is built from this log.

## Criteria

| # | Criterion | How it is measured |
|---|---|---|
| 1 | Cost | Actual spend (kr) + estimated cost at production scale |
| 2 | Development time | Hours per layer, logged honestly |
| 3 | Data freshness | Seconds/minutes from trade to gold table |
| 4 | ML workflow | Tracking, retraining, explainability |
| 5 | Governance | Lineage, access control, audit |
| 6 | CI/CD and IaC | Effort to deploy from GitHub |
| 7 | Free-tier limits | Limits hit, and workarounds |
| 8 | Fit for a bank on Google Cloud | Qualitative discussion |

## Time log

| Date | Platform | Layer | Hours | Notes |
|---|---|---|---|---|
| 2026-11-25 | GCP | Setup | ~3.5 | Signup, project, budget alert, APIs, Terraform install + apply (18 resources). Elapsed time incl. troubleshooting |
| 2026-11-25 | Databricks | Setup | ~0.5 | Free Edition signup, GitHub link, Git folder, connectivity test |
| 2026-11-26 | Both | Gold schema | ~0.5 | Contract + generated DDL applied on both platforms |
| 2026-11-26 | Shared | Clients + ingest jobs | ~1.5 | 4 source clients, smoke test, 3 jobs; all sources OK locally |
| 2026-11-26 | GCP | Bronze ingestion | ~1 | Docker image, Cloud Build, 3 Cloud Run jobs, 3 Cloud Scheduler jobs via Terraform |
| 2026-11-26 | Databricks | Bronze ingestion | ~0.3 | Secret scope, volume, 3 scheduled jobs via SDK notebook; same ingest.py as GCP |

## Observations

| Date | Platform | Criterion | Observation |
|---|---|---|---|
| 2026-11-25 | GCP | 2 Dev time | API activation was slow (Compute Engine took several minutes; `--async` helped) |
| 2026-11-25 | GCP | 6 CI/CD and IaC | Terraform not preinstalled in Cloud Shell; installed manually in `~/bin` |
| 2026-11-25 | GCP | 6 CI/CD and IaC | Terraform needed IAM and Cloud Resource Manager APIs enabled first. Errors were clear and linked to the fix |
| 2026-11-25 | GCP | 6 CI/CD and IaC | Partial apply was safe: Terraform resumed where it stopped, nothing created twice |
| 2026-11-25 | GCP | 1 Cost | Budget alerts only notify; they do not stop spending. New option "spend cap enforcement" exists but covers limited services |
| 2026-11-25 | Databricks | 2 Dev time | Setup much faster than GCP: no infrastructure to provision, serverless notebook ready in ~1 s |
| 2026-11-25 | Databricks | 7 Free-tier limits | No "Verify identity" button shown, but outbound access to CoinGecko, Coinbase, Riksbank, ESMA and GCS all worked |
| 2026-11-25 | Databricks | 5 Governance | Free Edition does not commit notebook outputs to Git, only code (good for keeping data out of a public repo) |
| 2026-11-26 | Databricks | 2 Dev time | Two compute types (serverless notebook vs SQL warehouse) are easy to mix up: Python cell failed on SQL warehouse |
| 2026-11-26 | Databricks | 2 Dev time | Serverless session ends after inactivity; must reattach notebook to Serverless when returning |
| 2026-11-26 | GCP | 2 Dev time | Cloud Shell resets to the default project after a restart; select the project in the console first |
| 2026-11-26 | GCP | 6 CI/CD and IaC | Gold tables created with `bq query` from generated SQL in ~3 s |
| 2026-11-26 | Databricks | 6 CI/CD and IaC | Gold tables created by a notebook reading the same generated SQL from the Git folder in ~2 s |
| 2026-11-26 | Shared | 8 Fit for a bank | Tether is not in ESMA's EMT register; Circle (USDC, EURC) is. Real MiCA compliance signal for the game |
| 2026-11-26 | GCP | 6 CI/CD and IaC | Deploy needs 3 steps (registry, image build, jobs) because Cloud Run jobs need the image to exist first |
| 2026-11-26 | GCP | 6 CI/CD and IaC | Cloud Run pins the image at deploy: a new build needs `gcloud run jobs update` to take effect |
| 2026-11-26 | GCP | 2 Dev time | First run failed on a missing Python dependency; Cloud Logging showed the full traceback in seconds |
| 2026-11-26 | GCP | 2 Dev time | Image build ~37 s; job cold start 20-60 s; runs complete well within free tier |
| 2026-11-26 | GCP | 1 Cost | Uses exactly the 3 free Cloud Scheduler jobs per billing account; a 4th schedule would cost ~$0.10/month |
| 2026-11-26 | Both | 2 Dev time | Same `ingest.py` runs unchanged on both; only the sink differs (gs:// vs /Volumes/...) |
| 2026-11-26 | Databricks | 2 Dev time | No container or image build needed: notebook imports the shared code straight from the Git folder |
| 2026-11-26 | Databricks | 3 Data freshness | market_hourly run took 7.4 s end to end (serverless); GCP Cloud Run job needed 20-60 s cold start |
| 2026-11-26 | Databricks | 5 Governance | Secrets stored via SDK in a secret scope; key passed through a notebook parameter, never in code |
| 2026-11-26 | Databricks | 6 CI/CD and IaC | Jobs created from code (SDK in a notebook), not yet Asset Bundles; GCP uses Terraform |
| 2026-11-26 | Databricks | 2 Dev time | New notebook UI moved widgets to a side panel, easy to miss |

## Limits hit

| Date | Platform | Limit | Workaround |
|---|---|---|---|
| 2026-11-25 | Databricks | Restricted outbound internet (no LinkedIn verification offered) | None needed: all five data sources reachable |
| 2026-11-25 | GCP | 24/7 WebSocket on Cloud Run would exceed free compute | Use always-free e2-micro VM instead |
| 2026-11-25 | GCP | BigQuery streaming inserts are not free | Write files to Cloud Storage, batch-load into BigQuery |
| 2026-11-26 | Shared | CoinGecko Demo history limited to 365 days (2023 USDC depeg out of reach) | Use Coinbase candles for older history |
| 2026-11-26 | Shared | Riksbank keyless limit 5 calls/min | Client waits 13 s between calls; daily job needs only 2 calls |
