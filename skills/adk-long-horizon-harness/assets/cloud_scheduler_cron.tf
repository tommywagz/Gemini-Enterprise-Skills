# Review-only Cloud Scheduler -> authenticated HTTP endpoint template.
resource "google_cloud_scheduler_job" "adk_ambient_worker" {
  name        = "REPLACE_JOB_NAME"
  description = "Triggers a durable ADK ambient worker"
  schedule    = "0 2 * * *"
  time_zone   = "Etc/UTC"
  http_target {
    uri         = "https://REPLACE_HOST/ambient/events"
    http_method = "POST"
    oidc_token { service_account_email = "REPLACE_SCHEDULER_SERVICE_ACCOUNT" }
    headers = { "Content-Type" = "application/json" }
    body = base64encode(jsonencode({ id = "scheduled-reconcile", schema_version = "1" }))
  }
  retry_config { retry_count = 3, min_backoff_duration = "30s", max_backoff_duration = "300s" }
}
