resource "google_compute_instance" "serial_enabled" {
  name = "test"
  metadata = {
    "serial-port-enable" = "true"
  }
}
