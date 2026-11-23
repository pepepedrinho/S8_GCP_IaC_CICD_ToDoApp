terraform {
  required_version = ">= 1.14, < 2.0"
  required_providers { google = { source = "hashicorp/google", version = "~> 7.0" } }
}
provider "google" {
  project               = var.project_id
  billing_project       = var.project_id
  user_project_override = true
}
variable "project_id" {
  type = string
  validation {
    condition     = var.project_id == "triodelicia-mensal4-2026"
    error_message = "Bootstrap is restricted to the new academic project."
  }
}
variable "repository_id" { type = string }
variable "repository_owner_id" { type = string }
variable "billing_account_id" {
  type      = string
  sensitive = true
}
variable "repository" {
  type    = string
  default = "pepepedrinho/S8_GCP_IaC_CICD_ToDoApp"
}
locals {
  services = toset(["compute.googleapis.com", "storage.googleapis.com", "iam.googleapis.com", "iamcredentials.googleapis.com", "cloudresourcemanager.googleapis.com", "sts.googleapis.com", "iap.googleapis.com", "oslogin.googleapis.com", "billingbudgets.googleapis.com", "serviceusage.googleapis.com", "cloudbilling.googleapis.com"])
}
resource "google_billing_budget" "initial_tests" {
  billing_account = var.billing_account_id
  display_name    = "ToDo academic initial tests - BRL5 alert"
  budget_filter { projects = ["projects/271680307280"] }
  amount {
    specified_amount {
      currency_code = "BRL"
      units         = "5"
    }
  }
  threshold_rules { threshold_percent = 0.5 }
  threshold_rules { threshold_percent = 0.9 }
  threshold_rules { threshold_percent = 1.0 }
  depends_on = [google_project_service.required]
}
resource "google_project_service" "required" {
  for_each           = local.services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
resource "google_storage_bucket" "protected" {
  for_each                    = toset(["state", "backups"])
  name                        = "${var.project_id}-todo-${each.key}"
  location                    = "US-CENTRAL1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  versioning { enabled = each.key == "state" }
  soft_delete_policy { retention_duration_seconds = 0 }
  dynamic "retention_policy" {
    for_each = each.key == "backups" ? [1] : []
    content { retention_period = 604800 }
  }
  lifecycle_rule {
    condition {
      age        = each.key == "backups" ? 7 : 30
      with_state = each.key == "state" ? "ARCHIVED" : "ANY"
    }
    action { type = "Delete" }
  }
  lifecycle { prevent_destroy = true }
  depends_on = [google_project_service.required]
}
resource "google_service_account" "runtime" {
  for_each     = toset(["app", "db"])
  account_id   = "todo-${each.key}"
  display_name = "ToDo ${each.key} runtime"
  depends_on   = [google_project_service.required]
}
resource "google_storage_bucket_iam_member" "backup" {
  bucket = google_storage_bucket.protected["backups"].name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.runtime["db"].email}"
}
resource "google_service_account" "automation" {
  account_id   = "todo-automation"
  display_name = "ToDo trusted GitHub workflows"
  depends_on   = [google_project_service.required]
}
resource "google_project_iam_custom_role" "automation" {
  project     = var.project_id
  role_id     = "todoInfrastructure"
  title       = "ToDo approved infrastructure lifecycle"
  description = "Only Compute resources used by this repository; no IAM, billing, APIs or bucket administration."
  permissions = [
    "compute.projects.get", "compute.zones.get", "compute.zones.list", "compute.regions.get",
    "compute.machineTypes.get", "compute.images.get", "compute.images.useReadOnly",
    "compute.networks.create", "compute.networks.get", "compute.networks.list", "compute.networks.delete", "compute.networks.updatePolicy",
    "compute.subnetworks.create", "compute.subnetworks.get", "compute.subnetworks.list", "compute.subnetworks.delete", "compute.subnetworks.use", "compute.subnetworks.useExternalIp",
    "compute.firewalls.create", "compute.firewalls.get", "compute.firewalls.list", "compute.firewalls.update", "compute.firewalls.delete",
    "compute.disks.create", "compute.disks.get", "compute.disks.list", "compute.disks.use", "compute.disks.delete", "compute.disks.setLabels",
    "compute.instances.create", "compute.instances.get", "compute.instances.list", "compute.instances.delete", "compute.instances.start", "compute.instances.stop",
    "compute.instances.setMetadata", "compute.instances.setServiceAccount", "compute.instances.setTags", "compute.instances.setLabels", "compute.instances.setScheduling",
    "compute.instances.attachDisk", "compute.instances.detachDisk", "compute.instances.update", "compute.instances.osLogin", "compute.instances.osAdminLogin",
    "compute.globalOperations.get", "compute.regionOperations.get", "compute.zoneOperations.get", "serviceusage.services.use"
  ]
  depends_on = [google_project_service.required]
}
resource "google_project_iam_member" "automation" {
  project = var.project_id
  role    = google_project_iam_custom_role.automation.name
  member  = "serviceAccount:${google_service_account.automation.email}"
}
resource "google_project_iam_member" "iap" {
  project = var.project_id
  role    = "roles/iap.tunnelResourceAccessor"
  member  = "serviceAccount:${google_service_account.automation.email}"
  condition {
    title      = "only-todo-private-ssh"
    expression = "destination.port == 22 && (destination.ip == '10.42.0.10' || destination.ip == '10.42.0.20')"
  }
}
resource "google_service_account_iam_member" "attach_runtime" {
  for_each           = google_service_account.runtime
  service_account_id = each.value.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.automation.email}"
}
resource "google_storage_bucket_iam_member" "state" {
  bucket = google_storage_bucket.protected["state"].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.automation.email}"
  condition {
    title      = "only-main-state-and-locks"
    expression = "resource.type == 'storage.googleapis.com/Bucket' || resource.name.startsWith('projects/_/buckets/${google_storage_bucket.protected["state"].name}/objects/todo/main/')"
  }
}
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "todo-github"
  display_name              = "ToDo trusted GitHub"
  depends_on                = [google_project_service.required]
}
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  attribute_mapping = {
    "google.subject"                = "assertion.sub"
    "attribute.repository_id"       = "assertion.repository_id"
    "attribute.repository_owner_id" = "assertion.repository_owner_id"
  }
  attribute_condition = "assertion.repository_id == '${var.repository_id}' && assertion.repository_owner_id == '${var.repository_owner_id}' && (assertion.ref == 'refs/heads/main' || assertion.ref == 'refs/heads/feat/infra-terraform-ansible-actions')"
  oidc { issuer_uri = "https://token.actions.githubusercontent.com" }
}
resource "google_service_account_iam_member" "federation" {
  service_account_id = google_service_account.automation.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository_id/${var.repository_id}"
}
output "state_bucket" { value = google_storage_bucket.protected["state"].name }
output "backup_bucket" { value = google_storage_bucket.protected["backups"].name }
output "wif_provider" { value = google_iam_workload_identity_pool_provider.github.name }
output "automation_service_account" { value = google_service_account.automation.email }
