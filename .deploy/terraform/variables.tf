variable "environment" {
  type        = string
  description = "environment to deploy to"
}

variable "region" {
  type        = string
  description = "GCP region to use"
  default     = "europe-west4"
}

variable "project_id" {
  type        = string
  description = "project id for deploy artifacts"
}
