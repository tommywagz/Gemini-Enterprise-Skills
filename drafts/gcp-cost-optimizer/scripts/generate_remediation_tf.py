#!/usr/bin/env python3
"""generate_remediation_tf.py

Reads the JSON findings produced by `audit_gcp_costs.py --json` and writes
one reviewable Terraform HCL snippet per finding to an output directory.

Like the security-scanner sibling skill's remediation script, this NEVER
edits the user's real .tf files and NEVER runs `terraform apply` or
`terraform destroy` -- every snippet is written as a `.tf.snippet` file (an
extension Terraform does not load) for a human to review, adapt to the real
resource address, and merge into their own configuration. This matters even
more here than in a pure security scan: several of these changes are
capacity/availability tradeoffs (stopping an instance, releasing an IP,
lowering Cloud Run min_instances) that must be confirmed against actual
traffic/usage patterns before being applied, not just against a point-in-time
inventory snapshot.

Destructive actions (deleting a disk, releasing a static IP) always get a
snippet that performs the SAFE precursor step (snapshot, or an explicit
manual-confirmation comment) rather than a direct delete -- see the
per-rule templates below.

Usage:
    audit_gcp_costs.py --inventory inventory.json --json > findings.json
    generate_remediation_tf.py findings.json [output-dir]

    [output-dir]  default: ./gcp_cost_remediation_snippets

Exit codes: 0 = wrote snippets (or found nothing to remediate), 2 = findings
file missing or unparseable.
"""
import json
import os
import re
import sys

TEMPLATES = {
    "GCP-COST-COMPUTE-001": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Option A -- workload does not need to run continuously: stop it and add an
# instance schedule instead of leaving it running 24/7.
resource "google_compute_resource_policy" "REPLACE_ME_schedule" {{
  name   = "REPLACE_WITH_SCHEDULE_NAME"
  region = "REPLACE_WITH_REGION"
  instance_schedule_policy {{
    vm_start_schedule {{ schedule = "0 8 * * MON-FRI" }}
    vm_stop_schedule  {{ schedule = "0 18 * * MON-FRI" }}
    time_zone = "REPLACE_WITH_TZ"
  }}
}}
# Then attach REPLACE_ME_schedule to the instance via
# google_compute_instance.resource_policies.
#
# Option B -- workload must run continuously but is genuinely over-sized:
# run `gcloud recommender recommendations list
# --recommender=google.compute.instance.MachineTypeRecommender` for a
# data-driven machine_type suggestion before editing machine_type by hand.
''',
    "GCP-COST-COMPUTE-002": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Confirm the workload is actually restartable before applying this.
resource "google_compute_instance" "REPLACE_ME" {{
  # ... existing config ...
  scheduling {{
    provisioning_model  = "SPOT"
    preemptible         = true
    automatic_restart   = false
    instance_termination_action = "STOP"
  }}
}}
''',
    "GCP-COST-DISK-001": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Snapshot before deleting -- never delete an unattached disk directly
# unless it is confirmed scratch/ephemeral data.
resource "google_compute_snapshot" "REPLACE_ME_final_snapshot" {{
  name        = "REPLACE_WITH_SNAPSHOT_NAME"
  source_disk = "REPLACE_WITH_DISK_SELF_LINK_OR_NAME"
  zone        = "REPLACE_WITH_ZONE"
}}
# After confirming the snapshot succeeded, remove the google_compute_disk
# resource for this disk from your configuration (and `terraform apply` /
# `terraform state rm` as appropriate for how it's currently managed).
''',
    "GCP-COST-DISK-002": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# ADVISORY ONLY -- verify actual IOPS/throughput needs before changing an
# existing disk's type (this is a destructive resize on most disk types).
resource "google_compute_disk" "REPLACE_ME" {{
  # ... existing config ...
  type = "pd-balanced" # was pd-ssd -- confirm workload does not need pd-ssd/pd-extreme IOPS first
}}
''',
    "GCP-COST-IP-001": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Confirm no external DNS record or firewall allow-list references this IP
# before releasing it.
# To release: remove the google_compute_address resource for this IP from
# your configuration and apply. There is no "keep the address, stop billing"
# state for a reserved-but-unattached static IP -- release or attach it.
''',
    "GCP-COST-BQ-001": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Reduce the reservation size to better match trailing-30-day utilization
# (verify against INFORMATION_SCHEMA.JOBS slot usage first):
resource "google_bigquery_reservation" "REPLACE_ME" {{
  # ... existing config ...
  slot_capacity = REPLACE_WITH_RIGHT_SIZED_SLOT_COUNT
}}
''',
    "GCP-COST-BQ-002": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Confirm no compliance/audit retention requirement first.
resource "google_bigquery_dataset" "REPLACE_ME" {{
  # ... existing config ...
  default_table_expiration_ms = REPLACE_WITH_MS # e.g. 7776000000 for 90 days
}}
''',
    "GCP-COST-RUN-001": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Confirm there is no latency SLA requiring warm instances before lowering.
resource "google_cloud_run_v2_service" "REPLACE_ME" {{
  # ... existing config ...
  template {{
    scaling {{
      min_instance_count = 0 # was set higher than observed traffic supports
    }}
  }}
}}
''',
    "GCP-COST-RUN-002": '''# {rule_id}: {title}
# Resource: {resource}
# Detail: {detail}
#
# Only raise concurrency if the request handler is thread-/async-safe.
resource "google_cloud_run_v2_service" "REPLACE_ME" {{
  # ... existing config ...
  template {{
    max_instance_request_concurrency = 80 # was 1 -- verify handler safety first
  }}
}}
''',
}


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_remediation_tf.py <findings.json> [output-dir]", file=sys.stderr)
        sys.exit(2)
    findings_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "./gcp_cost_remediation_snippets"

    try:
        with open(findings_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"error: findings file not found: {findings_path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"error: {findings_path} is not valid JSON: {e} -- run "
              "'audit_gcp_costs.py --json' first", file=sys.stderr)
        sys.exit(2)

    os.makedirs(out_dir, exist_ok=True)
    findings = data.get("findings", [])
    count = 0
    for f in findings:
        rule_id = f["rule_id"]
        safe_resource = re.sub(r"[^A-Za-z0-9_.-]", "_", f["resource"])
        out_file = os.path.join(out_dir, f"{rule_id}__{safe_resource}.tf.snippet")
        template = TEMPLATES.get(rule_id)
        if template is None:
            body = (f"# {rule_id}: {f['title']}\n"
                     f"# Resource: {f['resource']}\n"
                     f"# Detail: {f['detail']}\n"
                     "# No canned template for this rule yet -- see "
                     "assets/finops_checklist.json for its recommendation "
                     "and apply manually.\n")
        else:
            body = template.format(
                rule_id=rule_id, title=f["title"], resource=f["resource"], detail=f["detail"]
            )
        with open(out_file, "w") as out:
            out.write(body)
        print(f"wrote {out_file}")
        count += 1

    if count == 0:
        print(f"No findings in {findings_path} -- nothing to remediate.")
    else:
        print(f"\n{count} remediation snippet(s) written to {out_dir}/")
        print("None of your original .tf files were modified, and nothing was "
              "applied or destroyed. Review each snippet, replace the "
              "REPLACE_ME/REPLACE_WITH_* placeholders, confirm the tradeoff "
              "against real traffic/usage data, then merge it into your "
              "configuration yourself.")
    sys.exit(0)


if __name__ == "__main__":
    main()
