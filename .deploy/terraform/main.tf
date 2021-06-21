resource "google_service_account" "velo_action" {
  account_id   = "velo-action"
  display_name = "velo-action"
  description  = "Velo Github ACtion service account"
  project      = var.gcp_project_id
}
