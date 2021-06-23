terraform {
  backend "gcs" {
    bucket = "nube-global-tfstate"
    prefix = "infra-it/velo-action/{{ environment }}"
  }

  required_version = "1.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 3.72"
    }
    github = {
      source  = "integrations/github"
      version = "~> 4.11"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.region
}

data "google_secret_manager_secret_version" "app_id" {
  project = "nube-velo-prod"
  secret  = "velo_github_app_id"
}

data "google_secret_manager_secret_version" "app_installation_id" {
  project = "nube-velo-prod"
  secret  = "velo_github_app_installation_id"
}

data "google_secret_manager_secret_version" "app_pem_file" {
  project = "nube-velo-prod"
  secret  = "velo_github_app_private_key"
}

provider "github" {
  owner = var.github_owner
  app_auth {
    id              = data.google_secret_manager_secret_version.app_id.secret_data
    installation_id = data.google_secret_manager_secret_version.app_installation_id.secret_data
    pem_file        = data.google_secret_manager_secret_version.app_pem_file.secret_data
  }
}