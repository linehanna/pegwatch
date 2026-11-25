variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
  default     = "pegwatch"
}

variable "region" {
  description = "Region. us-central1 is covered by the always-free tier."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zone for the free e2-micro VM"
  type        = string
  default     = "us-central1-a"
}

variable "bronze_retention_days" {
  description = "Delete raw files in the bronze bucket after this many days, to stay under the 5 GB free storage"
  type        = number
  default     = 90
}

variable "create_collector_vm" {
  description = "Create the always-free e2-micro VM for the live WebSocket collector"
  type        = bool
  default     = true
}
