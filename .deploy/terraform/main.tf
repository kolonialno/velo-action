resource "google_service_account" "velo_action" {
  account_id   = "velo-action"
  display_name = "velo-action"
  description  = "Used by Github Action Velo-Action"
  project      = var.project_id
}

resource "google_project_iam_member" "velo_action_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.velo_action.email}"
}

resource "google_project_iam_member" "velo_action_secrets_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.velo_action.email}"
}

// allow velo_action gsa to push traces to tempo by finding the password in the secrets
resource "google_project_iam_member" "velo_action_secrets_accessor_observability_project" {
  project = "nube-observability-prod"
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.velo_action.email}"
}

// allow velo_action gsa to push and pull images to nube-hub registry
resource "google_storage_bucket_iam_member" "velo_action_storage_admin_nube_hub" {
  bucket = "eu.artifacts.nube-hub.appspot.com"
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.velo_action.email}"
}

// allow velo_action gsa to push and pull images to nube-hub artifacts registry
resource "google_artifact_registry_repository_iam_member" "docker_public_registry_writer_access" {
  provider   = google-beta
  project    = "nube-hub"
  location   = "europe"
  repository = "docker-public"
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.velo_action.email}"
}

// allow velo_action gsa to push and pull images to nube-hub artifacts registry
resource "google_artifact_registry_repository_iam_member" "docker_registry_writer_access" {
  provider   = google-beta
  project    = "nube-hub"
  location   = "europe"
  repository = "docker"
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.velo_action.email}"
}

resource "google_storage_bucket_iam_member" "velo_action_cloudbuild_bucket_admin" {
  bucket = "nube-hub_cloudbuild"
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.velo_action.email}"
}

resource "google_project_iam_member" "velo_action_nube_hub_storage_admin" {
  project = "nube-hub"
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.velo_action.email}"
}

resource "google_project_iam_member" "velo_action_cloudbuild_editor" {
  project = "nube-hub"
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${google_service_account.velo_action.email}"
}

resource "google_service_account_key" "velo_action_gsa_key" {
  service_account_id = google_service_account.velo_action.name
}

module "velo_action_gsa_key_secret" {
  source      = "git@github.com:kolonialno/nube.git//terraform/modules/service_secret?ref=1f399a1125d177aec7167fa32745303924509202"
  project_id  = var.project_id
  secret_data = base64decode(google_service_account_key.velo_action_gsa_key.private_key)
  secret_id   = "velo_action_gsa_key"
  service_account_emails = [
    google_service_account.velo_action.email
  ]
}

// Used by act when running github actions locally
module "velo_action_gsa_key_secret_encoded" {
  source      = "git@github.com:kolonialno/nube.git//terraform/modules/service_secret?ref=1f399a1125d177aec7167fa32745303924509202"
  secret_id   = "velo_action_gsa_key_encoded"
  secret_data = google_service_account_key.velo_action_gsa_key.private_key
  project_id  = var.project_id
  service_account_emails = [
    google_service_account.velo_action.email
  ]
}

data "google_secret_manager_secret_version" "velo_action_gsa_key_secret_encoded_version" {
  secret = module.velo_action_gsa_key_secret_encoded.secret_id
}

# Using the 'velo_action_gsa_key' resource directly wont work since this resource does not output the key if it already exists.
resource "github_actions_organization_secret" "velo_action_gsa_key" {
  secret_name     = "VELO_ACTION_GSA_KEY_${upper(var.environment)}"
  visibility      = "private"
  plaintext_value = data.google_secret_manager_secret_version.velo_action_gsa_key_secret_encoded_version.secret_data
}

data "google_secret_manager_secret_version" "velo_action_gsa_key_secret_json_version" {
  secret = module.velo_action_gsa_key_secret.secret_id
}

resource "github_actions_organization_secret" "velo_action_gsa_key_decoded" {
  secret_name     = "VELO_ACTION_GSA_KEY_JSON_${upper(var.environment)}"
  visibility      = "private"
  plaintext_value = data.google_secret_manager_secret_version.velo_action_gsa_key_secret_json_version.secret_data
}

# The secrets below are used by the velo-action
module "deploy_artifacts_bucket_name" {
  source    = "git@github.com:kolonialno/nube.git//terraform/modules/service_secret?ref=1f399a1125d177aec7167fa32745303924509202"
  secret_id = "velo_action_artifacts_bucket_name"
  # Currently there is no dev env for the artifacts bucket.
  # Use prod
  # "${var.project_id}-deploy-artifacts"
  secret_data = "nube-velo-prod-deploy-artifacts"
  project_id  = var.project_id
  service_account_emails = [
    google_service_account.velo_action.email
  ]
}

// TODO: remove after https://github.com/kolonialno/velo-action/blob/2e8d17b72390d632ae209d4634594bacbe61174c/action.yml#L71
// is update to use https://console.cloud.google.com/security/secret-manager/secret/octopus-deploy-api-key/versions?project=nube-velo-prod
module "velo_action_octopus_api_key" {
  source          = "git@github.com:kolonialno/nube.git//terraform/modules/service_secret?ref=1f399a1125d177aec7167fa32745303924509202"
  secret_id       = "velo_action_octopus_api_key"
  manage_external = true
  project_id      = var.project_id
  service_account_emails = [
    google_service_account.velo_action.email
  ]
}

// TODO: remove after https://github.com/kolonialno/velo-action/blob/2e8d17b72390d632ae209d4634594bacbe61174c/action.yml#L66
// is update to use https://console.cloud.google.com/security/secret-manager/secret/octopus-deploy-server-url/versions?project=nube-velo-prod
module "velo_action_octopus_serverapi_key" {
  source      = "git@github.com:kolonialno/nube.git//terraform/modules/service_secret?ref=1f399a1125d177aec7167fa32745303924509202"
  secret_id   = "velo_action_octopus_server"
  secret_data = "https://octopusdeploy.prod.nube.tech"
  project_id  = var.project_id
  service_account_emails = [
    google_service_account.velo_action.email
  ]
}

# Push velo-action image to dockerhub.
# Dockerhub is used since it is publicly available.
resource "github_actions_organization_secret" "velo_action_gsa_key_github_org_secret" {
  secret_name     = "VELO_ACTION_GSA_KEY_${upper(var.environment)}"
  visibility      = "private"
  plaintext_value = google_service_account_key.velo_action_gsa_key.private_key
}


# This secret is used by the Github Action in the velo-action repo to push
# the velo-action image to the nube-docker-public repo.
resource "github_actions_secret" "velo_action_gsa_key" {
  repository      = "velo-action"
  secret_name     = "VELO_ACTION_GSA_KEY_${upper(var.environment)}_PUBLIC"
  plaintext_value = data.google_secret_manager_secret_version.velo_action_gsa_key_secret_json_version.secret_data
}

# Give velo-action GSA permission to upload files to Centro bucket
# This is a hack to get around the fact that the "CENTRO_DOCS_UPLOADER_GSA_KEY_PROD" Github Org secret is
# not available for this repo since it is public.
# The repo is public since private Github Actions is not supported.
resource "google_storage_bucket_iam_member" "upload_centro_docs_prod" {
  bucket = "centro-docs-prod"
  member = "serviceAccount:${google_service_account.velo_action.email}"
  role   = "roles/storage.objectCreator"
}

resource "google_storage_bucket_iam_member" "upload_centro_docs_staging" {
  bucket = "centro-docs-staging"
  member = "serviceAccount:${google_service_account.velo_action.email}"
  role   = "roles/storage.objectCreator"
}
