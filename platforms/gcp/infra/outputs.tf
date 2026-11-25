output "bronze_bucket" {
  description = "Put this in .env as GCS_BRONZE_BUCKET"
  value       = google_storage_bucket.bronze.name
}

output "bigquery_datasets" {
  value = [for d in google_bigquery_dataset.layers : d.dataset_id]
}

output "collector_service_account" {
  value = google_service_account.collector.email
}

output "jobs_service_account" {
  value = google_service_account.jobs.email
}

output "collector_vm" {
  value = var.create_collector_vm ? google_compute_instance.collector[0].name : "not created"
}
