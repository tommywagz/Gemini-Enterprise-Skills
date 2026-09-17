# Review-only templates. Replace placeholders after evidence and owner approval.
resource "google_storage_bucket_iam_member" "app_object_admin" {
  bucket = "REPLACE_BUCKET"
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:REPLACE_SERVICE_ACCOUNT"
}

resource "google_artifact_registry_repository_iam_member" "ci_reader" {
  project    = "REPLACE_IMAGE_PROJECT"
  location   = "REPLACE_LOCATION"
  repository = "REPLACE_REPOSITORY"
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:REPLACE_NODE_SERVICE_ACCOUNT"
}

# Bind only approved external identity attributes to impersonate this account.
resource "google_service_account_iam_member" "federated_ci" {
  service_account_id = "projects/REPLACE_PROJECT/serviceAccounts/REPLACE_SERVICE_ACCOUNT"
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/REPLACE_NUMBER/locations/global/workloadIdentityPools/REPLACE_POOL/attribute.repository/REPLACE_REPOSITORY"
}
