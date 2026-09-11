#!/usr/bin/env python3
"""audit_gcp_costs.py

Scans a normalized Google Cloud resource inventory for cost-waste patterns
defined in the skill's `assets/finops_checklist.json` (idle Compute Engine instances,
unattached persistent disks, unattached static IPs, under-utilized BigQuery
slot reservations, unexpiring BigQuery datasets, over-provisioned Cloud Run
scaling). The checklist file is the single source of truth for severity,
rationale, and recommendation text; this script only implements the check()
predicate for each `automated: true` entry, keyed by rule id.

This is an ADVISORY audit, not a security gate: unlike a compliance scanner,
there is no universally "correct" cost/performance tradeoff -- every finding
needs a human to confirm the workload can actually tolerate the change
(stopping an instance, releasing an IP, lowering min_instances). Exit code
therefore reflects run success, not a pass/fail policy gate.

Input: a normalized JSON inventory (NOT any single `gcloud ... list` output
verbatim -- map your source data into this shape first; see
references/gcp_pricing_and_quotas.md for where each field typically comes
from). Top-level keys are resource category names; each maps to a list of
resource objects. Any category may be omitted if you have no data for it.

    {
      "compute_instances": [
        {"name": "...", "zone": "...", "machine_type": "...",
         "status": "RUNNING", "cpu_utilization_pct_p95": 2.1,
         "is_preemptible_or_spot": false, "labels": {"workload": "batch"},
         "monthly_cost_usd": 48.50}
      ],
      "persistent_disks": [
        {"name": "...", "zone": "...", "size_gb": 500, "type": "pd-ssd",
         "attached_instances": [], "monthly_cost_usd": 85.0}
      ],
      "static_ips": [
        {"name": "...", "region": "...", "status": "RESERVED", "users": [],
         "monthly_cost_usd": 7.30}
      ],
      "bigquery_reservations": [
        {"name": "...", "slots": 500, "avg_utilization_pct": 12.0,
         "monthly_cost_usd": 10000.0}
      ],
      "bigquery_datasets": [
        {"dataset_id": "...", "active_storage_gb": 50, "long_term_storage_gb": 4000,
         "default_table_expiration_days": null, "monthly_cost_usd": 82.0}
      ],
      "cloud_run_services": [
        {"name": "...", "region": "...", "min_instances": 3, "max_instances": 10,
         "cpu": 2, "concurrency": 1, "avg_requests_per_min": 1.5,
         "monthly_cost_usd": 210.0}
      ]
    }

Every `monthly_cost_usd` field is OPTIONAL. When present, an estimated
savings figure is computed as `monthly_cost_usd * waste_fraction` using the
checklist's documented (not live-priced) waste_fraction -- always printed
labeled as an ESTIMATE. When absent, the finding is still reported, just
without a dollar figure; the script never invents a price.

Usage:
    audit_gcp_costs.py --inventory inventory.json [--min-severity MEDIUM] [--json]
    audit_gcp_costs.py --inventory inventory.json --idle-cpu-threshold 5.0

Exit codes:
  0  ran to completion (regardless of how many findings -- this is advisory)
  2  usage error or unparseable/malformed inventory input
"""
import argparse
import json
import os
import sys

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def load_checklist():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(script_dir, "..", "assets", "finops_checklist.json"))
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"error: checklist not found at {path} -- this script must stay "
              "next to the skill's assets/ directory", file=sys.stderr)
        sys.exit(2)
    return {c["id"]: c for c in data["controls"]}


def load_inventory(path):
    if not os.path.isfile(path):
        print(f"error: inventory is not a readable regular file: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path) as f:
            inv = json.load(f)
    except FileNotFoundError:
        print(f"error: inventory file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(inv, dict):
        print("error: inventory JSON must be an object keyed by resource "
              "category (compute_instances, persistent_disks, ...)", file=sys.stderr)
        sys.exit(2)
    for category in CHECKS.values():
        name = category[0]
        if name in inv and not isinstance(inv[name], list):
            print(f"error: inventory category {name} must be a list", file=sys.stderr)
            sys.exit(2)
        if name in inv and not all(isinstance(item, dict) for item in inv[name]):
            print(f"error: every {name} entry must be an object", file=sys.stderr)
            sys.exit(2)
    return inv


# --------------------------------------------------------------------------
# Rule check functions -- one per "automated": true checklist entry.
# Each takes (resource_dict, thresholds_dict) and returns a list of finding
# detail strings (empty list = no finding on this resource).
# --------------------------------------------------------------------------
def check_idle_compute(r, t):
    if r.get("status") != "RUNNING":
        return []
    util = r.get("cpu_utilization_pct_p95")
    if util is None:
        return []
    if util < t["idle_cpu_threshold"]:
        return [f"status=RUNNING cpu_utilization_pct_p95={util} (< {t['idle_cpu_threshold']}%)"]
    return []


def check_spot_eligible(r, t):
    if r.get("is_preemptible_or_spot"):
        return []
    labels = {str(k).lower(): str(v).lower() for k, v in (r.get("labels") or {}).items()}
    fault_tolerant_signal = any(
        v in ("batch", "true", "fault-tolerant", "fault_tolerant")
        for v in labels.values()
    ) or any(k in ("batch", "fault-tolerant", "fault_tolerant") for k in labels)
    if fault_tolerant_signal:
        return [f"labels={r.get('labels')} suggest a restartable workload not using Spot/Preemptible"]
    return []


def check_unattached_disk(r, t):
    if not r.get("attached_instances"):
        return [f"size_gb={r.get('size_gb')} type={r.get('type')} attached_instances=[]"]
    return []


def check_ssd_no_iops_evidence(r, t):
    if r.get("type") == "pd-ssd" and not r.get("attached_instances"):
        return []  # already covered by GCP-COST-DISK-001, don't double-count
    if r.get("type") == "pd-ssd":
        return [f"type=pd-ssd size_gb={r.get('size_gb')} -- verify IOPS requirement before downgrading"]
    return []


def check_idle_static_ip(r, t):
    if r.get("status") == "RESERVED" and not r.get("users"):
        return ["status=RESERVED users=[] (billed at the idle static-IP rate)"]
    return []


def check_bq_reservation_underutilized(r, t):
    util = r.get("avg_utilization_pct")
    if util is not None and util < t["bq_reservation_underutil_pct"]:
        return [f"slots={r.get('slots')} avg_utilization_pct={util} (< {t['bq_reservation_underutil_pct']}%)"]
    return []


def check_bq_dataset_no_expiration(r, t):
    exp = r.get("default_table_expiration_days")
    long_term = r.get("long_term_storage_gb") or 0
    if not exp and long_term >= t["bq_long_term_storage_gb_threshold"]:
        return [f"default_table_expiration_days={exp} long_term_storage_gb={long_term}"]
    return []


def check_run_warm_low_traffic(r, t):
    min_i = r.get("min_instances") or 0
    rpm = r.get("avg_requests_per_min")
    if min_i > 0 and rpm is not None and rpm < t["run_low_traffic_rpm"]:
        return [f"min_instances={min_i} avg_requests_per_min={rpm} (< {t['run_low_traffic_rpm']} rpm)"]
    return []


def check_run_concurrency_one_multi_cpu(r, t):
    cpu = r.get("cpu") or 1
    concurrency = r.get("concurrency")
    if cpu and float(cpu) >= 2 and concurrency == 1:
        return [f"cpu={cpu} concurrency=1"]
    return []


CHECKS = {
    "GCP-COST-COMPUTE-001": ("compute_instances", check_idle_compute),
    "GCP-COST-COMPUTE-002": ("compute_instances", check_spot_eligible),
    "GCP-COST-DISK-001": ("persistent_disks", check_unattached_disk),
    "GCP-COST-DISK-002": ("persistent_disks", check_ssd_no_iops_evidence),
    "GCP-COST-IP-001": ("static_ips", check_idle_static_ip),
    "GCP-COST-BQ-001": ("bigquery_reservations", check_bq_reservation_underutilized),
    "GCP-COST-BQ-002": ("bigquery_datasets", check_bq_dataset_no_expiration),
    "GCP-COST-RUN-001": ("cloud_run_services", check_run_warm_low_traffic),
    "GCP-COST-RUN-002": ("cloud_run_services", check_run_concurrency_one_multi_cpu),
}


def resource_label(category, r):
    for key in ("name", "dataset_id"):
        if key in r:
            return r[key]
    return "<unnamed>"


def run_audit(inventory, checklist, thresholds):
    findings = []
    for rule_id, (category, check_fn) in CHECKS.items():
        control = checklist.get(rule_id)
        if control is None or not control.get("automated"):
            continue
        for r in inventory.get(category, []):
            for detail in check_fn(r, thresholds):
                waste_fraction = control.get("waste_fraction")
                monthly_cost = r.get("monthly_cost_usd")
                estimate = None
                if waste_fraction is not None and monthly_cost is not None:
                    estimate = round(monthly_cost * waste_fraction, 2)
                findings.append({
                    "rule_id": rule_id,
                    "category": control["category"],
                    "severity": control["severity"],
                    "title": control["title"],
                    "resource_category": category,
                    "resource": resource_label(category, r),
                    "detail": detail,
                    "recommendation": control["recommendation"],
                    "estimated_monthly_savings_usd": estimate,
                    "estimate_is_documented_not_live_priced": estimate is not None,
                })
    return findings


def manual_review_items(checklist):
    return [c for c in checklist.values() if not c.get("automated")]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", required=True, help="path to the normalized inventory JSON")
    ap.add_argument("--min-severity", choices=list(SEVERITY_ORDER), default="LOW",
                     help="omit findings below this severity (default: LOW, i.e. all)")
    ap.add_argument("--idle-cpu-threshold", type=float, default=5.0,
                     help="p95 CPU %% below which a RUNNING instance is flagged idle (default: 5.0)")
    ap.add_argument("--bq-reservation-underutil-pct", type=float, default=30.0,
                     help="reservation avg utilization %% below which it is flagged (default: 30.0)")
    ap.add_argument("--bq-long-term-storage-gb-threshold", type=float, default=100.0,
                     help="long_term_storage_gb above which a missing expiration is flagged (default: 100.0)")
    ap.add_argument("--run-low-traffic-rpm", type=float, default=5.0,
                     help="avg_requests_per_min below which warm min_instances is flagged (default: 5.0)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    checklist = load_checklist()
    inventory = load_inventory(args.inventory)

    thresholds = {
        "idle_cpu_threshold": args.idle_cpu_threshold,
        "bq_reservation_underutil_pct": args.bq_reservation_underutil_pct,
        "bq_long_term_storage_gb_threshold": args.bq_long_term_storage_gb_threshold,
        "run_low_traffic_rpm": args.run_low_traffic_rpm,
    }

    findings = run_audit(inventory, checklist, thresholds)
    threshold = SEVERITY_ORDER[args.min_severity]
    findings = [f for f in findings if SEVERITY_ORDER[f["severity"]] >= threshold]
    findings.sort(key=lambda f: -SEVERITY_ORDER[f["severity"]])

    total_estimated_savings = round(sum(
        f["estimated_monthly_savings_usd"] for f in findings
        if f["estimated_monthly_savings_usd"] is not None
    ), 2)
    manual = manual_review_items(checklist)

    if args.json:
        print(json.dumps({
            "findings": findings,
            "total_estimated_monthly_savings_usd": total_estimated_savings,
            "manual_review_required": manual,
        }, indent=2))
    else:
        print(f"Findings: {len(findings)}\n")
        for f in findings:
            print(f"[{f['severity']}] {f['rule_id']} - {f['title']}")
            print(f"    resource: {f['resource_category']}/{f['resource']}")
            print(f"    detail:   {f['detail']}")
            print(f"    fix:      {f['recommendation']}")
            if f["estimated_monthly_savings_usd"] is not None:
                print(f"    est. savings: ~${f['estimated_monthly_savings_usd']}/mo "
                      "(documented estimate, not a live price -- verify in Cloud Billing)")
            print()
        print(f"Total estimated monthly savings (documented estimate, only for "
              f"findings with monthly_cost_usd supplied): ~${total_estimated_savings}")
        if manual:
            print(f"\nManual-review items (need reservation/query-history context this "
                  f"script cannot see from a point-in-time inventory): {len(manual)}")
            for c in manual:
                print(f"  - {c['id']}: {c['title']}")

    sys.exit(0)


if __name__ == "__main__":
    main()
