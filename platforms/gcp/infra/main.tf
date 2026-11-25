# PegWatch on Google Cloud: core infrastructure.
# Everything here is chosen to stay inside the always-free tier.

locals {
  labels = {
    project = "pegwatch"
    managed = "terraform"
  }
}

# Bucket names are global, so add a short random suffix.
resource "random_id" "suffix" {
  byte_length = 3
}

# ---------------------------------------------------------------------------
# Bronze storage: raw files exactly as received from each source
# ---------------------------------------------------------------------------
resource "google_storage_bucket" "bronze" {
  name                        = "${var.project_id}-bronze-${random_id.suffix.hex}"
  location                    = upper(var.region) # regional = free-tier eligible
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true # portfolio project: allow terraform destroy
  labels                      = local.labels

  lifecycle_rule {
    condition {
      age = var.bronze_retention_days
    }
    action {
      type = "Delete"
    }
  }
}

# ---------------------------------------------------------------------------
# BigQuery: one dataset per medallion layer
# ---------------------------------------------------------------------------
resource "google_bigquery_dataset" "layers" {
  for_each = {
    bronze = "Raw data loaded from the bronze bucket"
    silver = "Cleaned, deduplicated, converted to USD and SEK"
    gold   = "Risk metrics, MiCA status and model scores. Must match shared/ gold schema contract."
  }

  dataset_id                 = "pegwatch_${each.key}"
  description                = each.value
  location                   = var.region
  delete_contents_on_destroy = true
  labels                     = local.labels
}

# ---------------------------------------------------------------------------
# Service accounts: one per workload, least privilege
# ---------------------------------------------------------------------------
resource "google_service_account" "collector" {
  account_id   = "pegwatch-collector"
  display_name = "PegWatch live collector (VM)"
}

resource "google_service_account" "jobs" {
  account_id   = "pegwatch-jobs"
  display_name = "PegWatch batch jobs (Cloud Run)"
}

# Collector may only write new files to bronze
resource "google_storage_bucket_iam_member" "collector_writes_bronze" {
  bucket = google_storage_bucket.bronze.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.collector.email}"
}

# Batch jobs read/write bronze, load into BigQuery and read secrets
resource "google_storage_bucket_iam_member" "jobs_use_bronze" {
  bucket = google_storage_bucket.bronze.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.jobs.email}"
}

resource "google_bigquery_dataset_iam_member" "jobs_edit_layers" {
  for_each   = google_bigquery_dataset.layers
  dataset_id = each.value.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.jobs.email}"
}

resource "google_project_iam_member" "jobs_run_queries" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.jobs.email}"
}

# ---------------------------------------------------------------------------
# Secrets: containers only. Add the values with gcloud, never in code.
# ---------------------------------------------------------------------------
resource "google_secret_manager_secret" "api_keys" {
  for_each  = toset(["coingecko-api-key", "riksbank-api-key"])
  secret_id = each.value
  labels    = local.labels

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "jobs_read_secrets" {
  for_each  = google_secret_manager_secret.api_keys
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.jobs.email}"
}

# ---------------------------------------------------------------------------
# Always-free e2-micro VM for the live Coinbase WebSocket collector
# Free tier: 1 e2-micro in us-central1/us-west1/us-east1, 30 GB standard disk,
# external IP not charged on the free tier.
# ---------------------------------------------------------------------------
resource "google_compute_instance" "collector" {
  count = var.create_collector_vm ? 1 : 0

  name                      = "pegwatch-collector"
  machine_type              = "e2-micro"
  zone                      = var.zone
  labels                    = local.labels
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 30
      type  = "pd-standard" # pd-balanced is NOT free
    }
  }

  network_interface {
    network = "default"
    access_config {} # ephemeral external IP, needed to reach Coinbase
  }

  service_account {
    email  = google_service_account.collector.email
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot = true
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  # Installs Python only. The collector service itself is deployed in a later step.
  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -e
    if [ ! -f /opt/pegwatch/.installed ]; then
      apt-get update
      apt-get install -y python3 python3-venv python3-pip git
      mkdir -p /opt/pegwatch
      python3 -m venv /opt/pegwatch/venv
      touch /opt/pegwatch/.installed
    fi
  EOT
}
