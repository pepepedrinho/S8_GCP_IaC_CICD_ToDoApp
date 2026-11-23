variable "project_id" {
  type    = string
  default = "triodelicia-mensal4-2026"
  validation {
    condition     = var.project_id == "triodelicia-mensal4-2026"
    error_message = "This academic deployment is restricted to the new project."
  }
}
variable "region" {
  type    = string
  default = "us-central1"
  validation {
    condition     = var.region == "us-central1"
    error_message = "Only us-central1 is approved."
  }
}
variable "zone" {
  type    = string
  default = "us-central1-a"
  validation {
    condition     = startswith(var.zone, "us-central1-")
    error_message = "Choose a zone in us-central1."
  }
}
variable "max_run_seconds" {
  type    = number
  default = 21600
  validation {
    condition     = var.max_run_seconds >= 30 && var.max_run_seconds <= 21600
    error_message = "Runtime must be between 30 seconds and the approved 6 hour maximum."
  }
}
