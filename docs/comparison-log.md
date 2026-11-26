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

## Limits hit

| Date | Platform | Limit | Workaround |
|---|---|---|---|
| 2026-11-25 | Databricks | Restricted outbound internet (no LinkedIn verification offered) | None needed: all five data sources reachable |
| 2026-11-25 | GCP | 24/7 WebSocket on Cloud Run would exceed free compute | Use always-free e2-micro VM instead |
| 2026-11-25 | GCP | BigQuery streaming inserts are not free | Write files to Cloud Storage, batch-load into BigQuery |
