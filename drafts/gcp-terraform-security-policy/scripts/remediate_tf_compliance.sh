#!/usr/bin/env bash
# remediate_tf_compliance.sh
#
# Reads the JSON findings produced by `audit_tf_gcp.py --json` and, for each
# HIGH/CRITICAL finding, writes a ready-to-review Terraform HCL remediation
# snippet to an output directory -- one file per finding.
#
# This script NEVER edits the scanned .tf files and NEVER runs `terraform
# apply`. Terraform changes (removing a firewall rule, tightening an IAM
# binding, disabling a public IP) can break a running workload, so every
# snippet is written next to -- not into -- the user's configuration for a
# human to review, adapt to their exact resource address, and apply through
# their own change-management process.
#
# Usage:
#   audit_tf_gcp.py --plan-json plan.json --json > findings.json
#   remediate_tf_compliance.sh findings.json [output-dir]
#
#   [output-dir]  default: ./tf_remediation_snippets
#
# Exit codes: 0 = wrote snippets (or found nothing to remediate), 1 = usage
# error, 2 = findings.json missing or unparseable.

set -euo pipefail

FINDINGS_FILE="${1:?Usage: remediate_tf_compliance.sh <findings.json> [output-dir]}"
OUT_DIR="${2:-./tf_remediation_snippets}"

if [[ ! -f "$FINDINGS_FILE" ]]; then
  echo "error: findings file not found: $FINDINGS_FILE" >&2
  exit 2
fi

if ! python3 -c "import json; json.load(open('$FINDINGS_FILE'))" 2>/dev/null; then
  echo "error: $FINDINGS_FILE is not valid JSON -- run with 'audit_tf_gcp.py --json' first" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"

# Template lookup: rule_id -> HCL snippet. Uses a bash associative array so
# this stays dependency-light (stdlib bash + python3 for JSON only, no jq
# assumed present on the target machine). Keep in sync with the checklist's
# `remediation` field in assets/gcp_compliance_checklist.json -- this map
# only supplies the pasteable HCL; the checklist remains the source of truth
# for *why* each control matters.
declare -A TEMPLATES=(
  [GCP-STORAGE-001]='# Remove the offending member below, then enforce it going forward:
resource "google_storage_bucket" "REPLACE_ME" {
  # ... existing config ...
  public_access_prevention = "enforced"
}'
  [GCP-STORAGE-002]='resource "google_storage_bucket" "REPLACE_ME" {
  # ... existing config ...
  uniform_bucket_level_access = true
}'
  [GCP-NET-001]='# Prefer IAP TCP forwarding over a public SSH/RDP rule:
resource "google_compute_firewall" "REPLACE_ME_iap_ssh" {
  name      = "allow-iap-ssh"
  network   = "REPLACE_WITH_NETWORK"
  direction = "INGRESS"
  source_ranges = ["35.235.240.0/20"]  # IAP TCP forwarding range only
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}
# Then delete (or narrow source_ranges on) the flagged public rule.'
  [GCP-NET-002]='resource "google_compute_firewall" "REPLACE_ME" {
  # ... existing config ...
  source_ranges = ["REPLACE_WITH_NARROW_CIDR"]
  allow {
    protocol = "tcp"      # never leave protocol/ports unset with a public source range
    ports    = ["REPLACE_WITH_PORT"]
  }
}'
  [GCP-NET-003]='resource "google_compute_subnetwork" "REPLACE_ME" {
  # ... existing config ...
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}'
  [GCP-IAM-001]='# Replace the primitive role member below with a predefined role scoped
# to the actual need (see references/iam_least_privilege_guidelines.md):
resource "google_project_iam_member" "REPLACE_ME" {
  project = "REPLACE_WITH_PROJECT_ID"
  role    = "roles/REPLACE_WITH_NARROWEST_PREDEFINED_ROLE"
  member  = "REPLACE_WITH_SAME_MEMBER"
}
# Then remove the roles/owner or roles/editor binding/member entirely.'
  [GCP-IAM-002]='# Delete the google_service_account_key resource. If the workload runs on
# GKE, use Workload Identity instead:
resource "google_service_account_iam_member" "REPLACE_ME_workload_identity" {
  service_account_id = "REPLACE_WITH_SA_ID"
  role                = "roles/iam.workloadIdentityUser"
  member              = "serviceAccount:REPLACE_WITH_PROJECT.svc.id.goog[REPLACE_WITH_NAMESPACE/REPLACE_WITH_KSA]"
}'
  [GCP-SQL-001]='resource "google_sql_database_instance" "REPLACE_ME" {
  # ... existing config ...
  settings {
    ip_configuration {
      ipv4_enabled    = false
      private_network = "REPLACE_WITH_VPC_SELF_LINK"
    }
  }
}'
  [GCP-SQL-002]='resource "google_sql_database_instance" "REPLACE_ME" {
  # ... existing config ...
  settings {
    ip_configuration {
      require_ssl = true
    }
  }
}'
  [GCP-SQL-003]='resource "google_sql_database_instance" "REPLACE_ME" {
  # ... existing config ...
  settings {
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }
}'
  [GCP-GKE-001]='resource "google_container_cluster" "REPLACE_ME" {
  # ... existing config ...
  enable_legacy_abac = false
}'
  [GCP-GKE-002]='resource "google_container_cluster" "REPLACE_ME" {
  # ... existing config ...
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "REPLACE_WITH_/28_CIDR"
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "REPLACE_WITH_ADMIN_CIDR"
      display_name = "admin-access"
    }
  }
}'
  [GCP-GKE-003]='resource "google_container_cluster" "REPLACE_ME" {
  # ... existing config ...
  network_policy {
    enabled  = true
    provider = "CALICO"
  }
}'
  [GCP-KMS-001]='resource "google_kms_crypto_key" "REPLACE_ME" {
  # ... existing config ...
  rotation_period = "7776000s" # 90 days
}'
  [GCP-BQ-001]='# Remove the allUsers/allAuthenticatedUsers access block entirely, then
# grant only named principals the narrowest role needed:
resource "google_bigquery_dataset_access" "REPLACE_ME" {
  dataset_id    = "REPLACE_WITH_DATASET_ID"
  role          = "roles/bigquery.dataViewer"
  user_by_email = "REPLACE_WITH_PRINCIPAL_EMAIL"
}'
  [GCP-COMPUTE-001]='resource "google_compute_instance" "REPLACE_ME" {
  # ... existing config ...
  metadata = {
    serial-port-enable = "false"
  }
}'
)

count=0
python3 - "$FINDINGS_FILE" <<'PY' > "$OUT_DIR/.findings_index.tsv"
import json, sys
data = json.load(open(sys.argv[1]))
for f in data.get("findings", []):
    if f["severity"] in ("HIGH", "CRITICAL"):
        print(f"{f['rule_id']}\t{f['resource_address']}\t{f['severity']}\t{f['detail']}")
PY

while IFS=$'\t' read -r rule_id address severity detail; do
  [[ -z "$rule_id" ]] && continue
  safe_addr="$(echo "$address" | tr -c 'A-Za-z0-9_.-' '_')"
  out_file="$OUT_DIR/${rule_id}__${safe_addr}.tf.snippet"
  {
    echo "# Finding: $rule_id  severity=$severity"
    echo "# Resource: $address"
    echo "# Detail:   $detail"
    echo "# Review and adapt before merging into your actual configuration."
    echo "# This file is NOT loaded by terraform (.snippet extension) and was"
    echo "# never applied automatically."
    echo
    if [[ -n "${TEMPLATES[$rule_id]:-}" ]]; then
      echo "${TEMPLATES[$rule_id]}"
    else
      echo "# No canned template for $rule_id yet."
      echo "# See assets/gcp_compliance_checklist.json for this rule's"
      echo "# remediation guidance and apply it manually."
    fi
  } > "$out_file"
  echo "wrote $out_file"
  count=$((count + 1))
done < "$OUT_DIR/.findings_index.tsv"

rm -f "$OUT_DIR/.findings_index.tsv"

if [[ "$count" -eq 0 ]]; then
  echo "No HIGH/CRITICAL findings in $FINDINGS_FILE -- nothing to remediate."
else
  echo
  echo "$count remediation snippet(s) written to $OUT_DIR/"
  echo "None of your original .tf files were modified. Review each snippet," \
       "replace the REPLACE_ME/REPLACE_WITH_* placeholders with your real" \
       "resource names and values, then merge it into your configuration" \
       "yourself and run terraform plan again."
fi
