variable "gcp_project_id" {
  type        = string
  description = "project id for deploy artifacts"
}

variable "environment" {
  type        = string
  description = "environment to deploy to"
}

variable "region" {
  type        = string
  description = "GCP region to use"
  default     = "europe-west4"
}

variable "github_owner" {
  type        = string
  description = "Github Organisations name"
  default     = "kolonialno"
}
