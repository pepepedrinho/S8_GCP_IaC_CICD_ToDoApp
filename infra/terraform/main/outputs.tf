output "project_id" { value = var.project_id }
output "zone" { value = var.zone }
output "app_name" { value = google_compute_instance.vm["app"].name }
output "db_name" { value = google_compute_instance.vm["db"].name }
output "app_private_ip" { value = google_compute_instance.vm["app"].network_interface[0].network_ip }
output "db_private_ip" { value = google_compute_instance.vm["db"].network_interface[0].network_ip }
output "backup_bucket" { value = "${var.project_id}-todo-backups" }
