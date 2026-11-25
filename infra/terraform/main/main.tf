resource "google_compute_network" "todo" {
  name                    = "todo-vpc"
  auto_create_subnetworks = false
}
resource "google_compute_subnetwork" "todo" {
  name                     = "todo-subnet"
  network                  = google_compute_network.todo.id
  ip_cidr_range            = "10.42.0.0/24"
  region                   = var.region
  private_ip_google_access = true
}
resource "google_compute_firewall" "web" {
  name          = "todo-web"
  network       = google_compute_network.todo.name
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["todo-app"]
  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
}
resource "google_compute_firewall" "iap" {
  name          = "todo-iap-ssh"
  network       = google_compute_network.todo.name
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["todo-app", "todo-db"]
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}
resource "google_compute_firewall" "mongo" {
  name          = "todo-private-mongo"
  network       = google_compute_network.todo.name
  source_ranges = ["10.42.0.10/32"]
  target_tags   = ["todo-db"]
  allow {
    protocol = "tcp"
    ports    = ["27017"]
  }
}
resource "google_compute_firewall" "packages" {
  name          = "todo-private-packages"
  network       = google_compute_network.todo.name
  source_ranges = ["10.42.0.20/32"]
  target_tags   = ["todo-app"]
  allow {
    protocol = "tcp"
    ports    = ["3128"]
  }
}
resource "google_compute_disk" "data" {
  name   = "todo-mongo-data"
  type   = "pd-standard"
  size   = 10
  zone   = var.zone
  labels = { application = "todo", purpose = "persistent-data" }
}
resource "google_compute_instance" "vm" {
  for_each                  = { app = "10.42.0.10", db = "10.42.0.20" }
  name                      = "todo-${each.key}"
  machine_type              = "e2-micro"
  zone                      = var.zone
  tags                      = ["todo-${each.key}"]
  labels                    = { application = "todo", managed_by = "terraform" }
  allow_stopping_for_update = true
  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 10
      type  = "pd-standard"
    }
  }
  dynamic "attached_disk" {
    for_each = each.key == "db" ? [1] : []
    content {
      source      = google_compute_disk.data.id
      device_name = "todo-mongo-data"
      mode        = "READ_WRITE"
    }
  }
  network_interface {
    subnetwork = google_compute_subnetwork.todo.id
    network_ip = each.value
    dynamic "access_config" {
      for_each = each.key == "app" ? [1] : []
      content { network_tier = "STANDARD" }
    }
  }
  metadata = { enable-oslogin = "TRUE", block-project-ssh-keys = "TRUE" }
  service_account {
    email  = "todo-${each.key}@${var.project_id}.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }
  scheduling {
    automatic_restart           = false
    on_host_maintenance         = "MIGRATE"
    provisioning_model          = "STANDARD"
    instance_termination_action = "STOP"
    max_run_duration { seconds = var.max_run_seconds }
  }
  lifecycle { ignore_changes = [desired_status] }
}
