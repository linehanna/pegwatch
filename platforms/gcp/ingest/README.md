# PegWatch on Google Cloud: bronze ingestion

Runs the shared jobs in `shared/pegwatch_shared/ingest.py` as **Cloud Run jobs**, started by **Cloud Scheduler**, writing to the bronze bucket.

| Cloud Run job | Schedule (Stockholm time) | Fetches |
|---|---|---|
| `pegwatch-market-hourly` | Every hour at :05 | CoinGecko snapshot + USDC history, Coinbase 1-minute candles |
| `pegwatch-fx-daily` | Weekdays 16:30 | Riksbank USD/SEK, EUR/SEK |
| `pegwatch-mica-weekly` | Mondays 07:00 | ESMA MiCA register |

## First deploy (Cloud Shell)

```bash
# 0. Once: enable Cloud Build and store the CoinGecko key
gcloud services enable cloudbuild.googleapis.com
printf '%s' 'YOUR_COINGECKO_KEY' | gcloud secrets versions add coingecko-api-key --data-file=-

# 1. Create the image registry and the build service account
cd ~/pegwatch && git pull
cd platforms/gcp/infra
terraform apply -target=google_artifact_registry_repository.pegwatch -target=google_project_iam_member.build

# 2. Build and push the image (from the repo root)
cd ~/pegwatch
gcloud builds submit . --config platforms/gcp/ingest/cloudbuild.yaml \
  --service-account=projects/pegwatch/serviceAccounts/pegwatch-build@pegwatch.iam.gserviceaccount.com

# 3. Create the jobs and schedules
cd platforms/gcp/infra
terraform apply
```

## Test a job by hand

```bash
gcloud run jobs execute pegwatch-market-hourly --region us-central1 --wait
gcloud storage ls -r gs://pegwatch-bronze-9aa513/ | head -20
```

## After changing the shared code

```bash
cd ~/pegwatch && git pull
gcloud builds submit . --config platforms/gcp/ingest/cloudbuild.yaml \
  --service-account=projects/pegwatch/serviceAccounts/pegwatch-build@pegwatch.iam.gserviceaccount.com
gcloud run jobs update pegwatch-market-hourly --image us-central1-docker.pkg.dev/pegwatch/pegwatch/ingest:latest --region us-central1
```

Cloud Run pins the image when a job is updated, so a new build only takes effect after `jobs update` (or `terraform apply` with a new image tag).

## Logs

Each step logs one JSON line (`step_ok` / `step_failed`). In the console: **Cloud Run → Jobs → pegwatch-market-hourly → Logs**.
