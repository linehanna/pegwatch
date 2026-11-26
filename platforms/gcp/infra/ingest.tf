# PegWatch on Google Cloud: scheduled bronze ingestion.
#
# Deploy order (first time): see platforms/gcp/ingest/README.md
#   1. terraform apply -target=google_artifact_registry_repository.pegwatch -target=google_project_iam_member.build
#   2. gcloud builds submit (from repo root, see cloudbuild.yaml)
#   3. terraform apply
#
# Free-tier notes: Cloud Run jobs only use compute while running (~30 s/run),
# Cloud Scheduler gives 3 free jobs per billing account, Artifact Registry 0.5 GB.

locals {
  ingest_jobs = {
    market_hourly = {
      schedule    = "5 * * * *"   # every hour at :05
      description = "CoinGecko snapshot, USDC history, Coinbase 1-minute candles"
    }
    fx_daily = {
      schedule    = "30 16 * * 1-5" # weekdays 16:30, after Riksbank publishes at 16:15
      description = "Riksbank USD/SEK and EUR/SEK"
    }
    mica_weekly = {
      schedule    = "0 7 * * 1"   # Mondays 07:00
      description = "ESMA interim MiCA register"
    }
  }
}

variable "ingest_image" {
  description = "Container image for the ingestion jobs"
  type        = string
  default     = "us-central1-docker.pkg.dev/pegwatch/pegwatch/ingest:latest"
}

# ---------------------------------------------------------------------------
# Artifact Registry: where the container image lives
# ---------------------------------------------------------------------------
resource "google_artifact_registry_repository" "pegwatch" {
  repository_id = "pegwatch"
  location      = var.region
  format        = "DOCKER"
  description   = "PegWatch container images"
  labels        = local.labels

  # Keep storage under the 0.5 GB free tier
  cleanup_policies {
    id     = "keep-latest-3"
    action = "KEEP"
    most_recent_versions {
      keep_count = 3
    }
  }
  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      older_than = "1209600s" # 14 days
    }
  }
}

# ---------------------------------------------------------------------------
# Build service account: Cloud Build runs as this, with only what it needs
# ---------------------------------------------------------------------------
resource "google_service_account" "build" {
  account_id   = "pegwatch-build"
  display_name = "PegWatch Cloud Build"
}

resource "google_project_iam_member" "build" {
  for_each = toset([
    "roles/artifactregistry.writer", # push images
    "roles/logging.logWriter",       # write build logs
    "roles/storage.objectViewer",    # read the uploaded source
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.build.email}"
}

# ---------------------------------------------------------------------------
# Cloud Run jobs: one per ingestion job, all using the same image
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_job" "ingest" {
  for_each = local.ingest_jobs

  name                = "pegwatch-${replace(each.key, "_", "-")}"
  location            = var.region
  deletion_protection = false
  labels              = local.labels

  template {
    task_count = 1
    template {
      service_account = google_service_account.jobs.email
      timeout         = "600s"
      max_retries     = 1

      containers {
        image = var.ingest_image
        args  = ["--job", each.key, "--sink", "gs://${google_storage_bucket.bronze.name}"]

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        env {
          name = "COINGECKO_DEMO_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.api_keys["coingecko-api-key"].secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.jobs_read_secrets]
}

# ---------------------------------------------------------------------------
# Cloud Scheduler: triggers each job on its schedule (Stockholm time)
# ---------------------------------------------------------------------------
resource "google_service_account" "scheduler" {
  account_id   = "pegwatch-scheduler"
  display_name = "PegWatch scheduler (starts Cloud Run jobs)"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_runs_jobs" {
  for_each = google_cloud_run_v2_job.ingest

  name     = each.value.name
  location = each.value.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "ingest" {
  for_each = google_cloud_run_v2_job.ingest

  name        = each.value.name
  region      = var.region
  description = local.ingest_jobs[each.key].description
  schedule    = local.ingest_jobs[each.key].schedule
  time_zone   = "Europe/Stockholm"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${each.value.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_cloud_run_v2_job_iam_member.scheduler_runs_jobs]
}

output "ingest_jobs" {
  value = [for j in google_cloud_run_v2_job.ingest : j.name]
}
