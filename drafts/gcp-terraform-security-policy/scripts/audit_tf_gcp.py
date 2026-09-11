#!/usr/bin/env python3
"""audit_tf_gcp.py

Scans Google Cloud Terraform configuration for security and compliance
violations against the curated rule set in
`../assets/gcp_compliance_checklist.json` (CIS Google Cloud Platform
Foundation Benchmark controls, private-by-default storage/network rules,
and least-privilege IAM). Every `automated: true` entry in that checklist
has a matching check() function in this script, keyed by rule id -- the
checklist file is the single source of truth for severity, CIS control
number, rationale, and remediation text; this script only ever prints them,
never re-defines them.

Two input modes, in order of reliability:

1. --plan-json PATH   (preferred, authoritative)
   The output of `terraform show -json <planfile>`, e.g.:
       terraform plan -out=tf.plan
       terraform show -json tf.plan > plan.json
   Terraform has already resolved every variable, local, module input, and
   count/for_each expansion by the time it writes this file, so this mode
   has no false negatives caused by unresolved HCL expressions.

2. --tf-dir PATH      (fallback, heuristic)
   A directory of raw `.tf` files, scanned with brace-depth-aware regex
   matching. This CANNOT resolve variables, locals, module inputs, `for_each`,
   or `dynamic` blocks -- it only sees literal values written directly in the
   scanned files. Treat findings from this mode as a lower bound and a clean
   run as INCONCLUSIVE, never as a pass. Prefer --plan-json whenever the
   `terraform` binary and provider credentials are available to produce one.

Exit codes:
  0  ran to completion, no CRITICAL/HIGH finding
  1  ran to completion, at least one CRITICAL/HIGH finding
  2  usage error or unparseable input (never treat this as "0 findings")

Usage:
    audit_tf_gcp.py --plan-json plan.json [--min-severity MEDIUM] [--json]
    audit_tf_gcp.py --tf-dir ./envs/prod [--json]
"""
import argparse
import json
import os
import re
import sys

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
PUBLIC_MEMBERS = ("allUsers", "allAuthenticatedUsers")
PRIMITIVE_ROLES = ("roles/owner", "roles/editor")


# --------------------------------------------------------------------------
# Checklist loading (single source of truth: assets/gcp_compliance_checklist.json)
# --------------------------------------------------------------------------
def load_checklist():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "..", "assets", "gcp_compliance_checklist.json")
    path = os.path.normpath(path)
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"error: checklist not found at {path} -- this script must stay "
              "next to the skill's assets/ directory", file=sys.stderr)
        sys.exit(2)
    return {c["id"]: c for c in data["controls"]}


# --------------------------------------------------------------------------
# --plan-json mode: walk `terraform show -json` output
# --------------------------------------------------------------------------
def resources_from_plan_json(path):
    with open(path) as f:
        plan = json.load(f)
    resources = []

    def walk(module):
        for r in module.get("resources", []):
            if r.get("mode") != "managed":
                continue
            resources.append({
                "address": r.get("address"),
                "type": r.get("type"),
                "values": r.get("values") or {},
            })
        for child in module.get("child_modules", []):
            walk(child)

    root = plan.get("planned_values", {}).get("root_module")
    if root is None:
        print("error: plan JSON has no planned_values.root_module -- is this "
              "really `terraform show -json` output? (found top-level keys: "
              f"{list(plan.keys())})", file=sys.stderr)
        sys.exit(2)
    walk(root)
    return resources


# --------------------------------------------------------------------------
# --tf-dir mode: heuristic brace-depth-aware scan of raw .tf files
# --------------------------------------------------------------------------
_RESOURCE_HEADER_RE = re.compile(
    r'resource\s+"([a-zA-Z0-9_]+)"\s+"([a-zA-Z0-9_\-]+)"\s*\{'
)


def _matching_brace(text, open_pos):
    depth = 0
    i = open_pos
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _extract_blocks(body, block_name):
    """Best-effort extraction of every `block_name { ... }` body at the top
    level of `body`. Returns a list of raw body strings (not parsed further)."""
    out = []
    for m in re.finditer(rf'{re.escape(block_name)}\s*\{{', body):
        close = _matching_brace(body, m.end() - 1)
        if close != -1:
            out.append(body[m.end():close])
    return out


def _scalar(body, key):
    m = re.search(rf'\b{re.escape(key)}\s*=\s*"([^"]*)"', body)
    if m:
        return m.group(1)
    m = re.search(rf'\b{re.escape(key)}\s*=\s*(true|false)\b', body)
    if m:
        return m.group(1) == "true"
    return None


def _list_of_strings(body, key):
    m = re.search(rf'\b{re.escape(key)}\s*=\s*\[([^\]]*)\]', body)
    if not m:
        return None
    return [s.strip().strip('"') for s in m.group(1).split(",") if s.strip()]


def resources_from_tf_dir(dir_path):
    """Heuristic scan. Normalizes each resource into the same
    {address, type, values} shape used by resources_from_plan_json, using
    per-resource-type extraction tuned to the attributes the rule set below
    actually reads. This is NOT a general HCL parser: it will miss anything
    expressed via a variable, local, module output, `for_each`, or `dynamic`
    block."""
    resources = []
    for root, _dirs, files in os.walk(dir_path):
        for fname in files:
            if not fname.endswith(".tf"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, errors="replace") as f:
                text = f.read()
            for m in _RESOURCE_HEADER_RE.finditer(text):
                rtype, rname = m.group(1), m.group(2)
                close = _matching_brace(text, m.end() - 1)
                if close == -1:
                    continue
                body = text[m.end():close]
                values = _extract_values_heuristic(rtype, body)
                resources.append({
                    "address": f"{rtype}.{rname}",
                    "type": rtype,
                    "values": values,
                    "_source_file": fpath,
                })
    return resources


def _extract_values_heuristic(rtype, body):
    v = {}
    if rtype == "google_storage_bucket":
        v["uniform_bucket_level_access"] = _scalar(body, "uniform_bucket_level_access")
        v["public_access_prevention"] = _scalar(body, "public_access_prevention")
    elif rtype in ("google_storage_bucket_iam_binding", "google_bigquery_dataset_iam_binding",
                   "google_project_iam_binding"):
        v["role"] = _scalar(body, "role")
        v["members"] = _list_of_strings(body, "members") or []
    elif rtype in ("google_storage_bucket_iam_member", "google_project_iam_member"):
        v["role"] = _scalar(body, "role")
        member = _scalar(body, "member")
        v["member"] = member
    elif rtype == "google_compute_firewall":
        v["direction"] = _scalar(body, "direction") or "INGRESS"
        v["source_ranges"] = _list_of_strings(body, "source_ranges") or []
        allow_blocks = _extract_blocks(body, "allow")
        v["allow"] = []
        for ab in allow_blocks:
            v["allow"].append({
                "protocol": _scalar(ab, "protocol"),
                "ports": _list_of_strings(ab, "ports") or [],
            })
    elif rtype == "google_service_account_key":
        v["_present"] = True
    elif rtype == "google_sql_database_instance":
        settings_blocks = _extract_blocks(body, "settings")
        v["settings"] = []
        for sb in settings_blocks:
            ip_blocks = _extract_blocks(sb, "ip_configuration")
            backup_blocks = _extract_blocks(sb, "backup_configuration")
            v["settings"].append({
                "ip_configuration": [
                    {"ipv4_enabled": _scalar(ib, "ipv4_enabled"),
                     "require_ssl": _scalar(ib, "require_ssl")}
                    for ib in ip_blocks
                ],
                "backup_configuration": [
                    {"enabled": _scalar(bb, "enabled")} for bb in backup_blocks
                ],
            })
    elif rtype == "google_container_cluster":
        v["enable_legacy_abac"] = _scalar(body, "enable_legacy_abac")
        v["private_cluster_config"] = [
            {"enable_private_nodes": _scalar(pb, "enable_private_nodes")}
            for pb in _extract_blocks(body, "private_cluster_config")
        ]
        v["network_policy"] = [
            {"enabled": _scalar(nb, "enabled")}
            for nb in _extract_blocks(body, "network_policy")
        ]
    elif rtype == "google_kms_crypto_key":
        v["rotation_period"] = _scalar(body, "rotation_period")
    elif rtype == "google_bigquery_dataset":
        access_blocks = _extract_blocks(body, "access")
        v["access"] = []
        for ab in access_blocks:
            v["access"].append({
                "special_group": _scalar(ab, "special_group"),
                "iam_member": _scalar(ab, "iam_member"),
            })
    elif rtype in ("google_compute_instance", "google_compute_instance_template"):
        meta_blocks = _extract_blocks(body, "metadata")
        merged = {}
        for mb in meta_blocks:
            for m in re.finditer(r'"([^"]+)"\s*=\s*"([^"]*)"', mb):
                merged[m.group(1)] = m.group(2)
        v["metadata"] = merged
    elif rtype == "google_compute_subnetwork":
        v["log_config"] = _extract_blocks(body, "log_config")
    return v


# --------------------------------------------------------------------------
# Rule check functions -- one per "automated": true entry in the checklist.
# Each takes a normalized resource dict and returns a list of finding
# detail strings (empty list = no finding on this resource).
# --------------------------------------------------------------------------
def _nested(values, *path):
    """Walk plan-json's list-of-one nested-block convention:
    values['settings'][0]['ip_configuration'][0][...] . Tolerates the
    tf-dir heuristic shape, which is built the same way on purpose."""
    cur = values
    for key in path:
        if isinstance(cur, list):
            if not cur:
                return None
            cur = cur[0]
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def check_storage_public(r):
    v = r["values"]
    members = list(v.get("members") or [])
    if v.get("member"):
        members.append(v["member"])
    findings = []
    for m in members:
        if any(pub in (m or "") for pub in PUBLIC_MEMBERS):
            findings.append(f"role={v.get('role')} member={m}")
    return findings


def check_uniform_bucket_level_access(r):
    v = r["values"]
    if v.get("uniform_bucket_level_access") is False:
        return ["uniform_bucket_level_access = false"]
    if v.get("uniform_bucket_level_access") is None:
        return ["uniform_bucket_level_access not set (defaults to false)"]
    return []


def _firewall_findings(r, want_ssh_rdp):
    v = r["values"]
    if (v.get("direction") or "INGRESS") != "INGRESS":
        return []
    ranges = v.get("source_ranges") or []
    if "0.0.0.0/0" not in ranges:
        return []
    findings = []
    for allow in v.get("allow") or []:
        ports = allow.get("ports") or []
        protocol = (allow.get("protocol") or "").lower()
        no_ports_restriction = protocol in ("all", "") or not ports
        if want_ssh_rdp:
            if any(p in ("22", "3389") for p in ports) or (protocol == "all" and not ports):
                findings.append(f"protocol={allow.get('protocol')} ports={ports} source=0.0.0.0/0")
        else:
            if no_ports_restriction:
                findings.append(f"protocol={allow.get('protocol') or 'all'} ports={ports or ['*']} source=0.0.0.0/0")
    return findings


def check_firewall_ssh_rdp_open(r):
    return _firewall_findings(r, want_ssh_rdp=True)


def check_firewall_all_open(r):
    return _firewall_findings(r, want_ssh_rdp=False)


def check_subnet_flow_logs(r):
    v = r["values"]
    if not v.get("log_config"):
        return ["log_config block absent -- VPC Flow Logs disabled"]
    return []


def check_primitive_role(r):
    v = r["values"]
    role = v.get("role")
    members = list(v.get("members") or [])
    if v.get("member"):
        members.append(v["member"])
    if role in PRIMITIVE_ROLES:
        return [f"role={role} members={members or ['(policy binding)']}"]
    return []


def check_service_account_key(r):
    return ["user-managed service_account_key resource present"]


def check_sql_public_ip(r):
    ipv4 = _nested(r["values"], "settings", "ip_configuration", "ipv4_enabled")
    if ipv4 is True:
        return ["ip_configuration.ipv4_enabled = true"]
    return []


def check_sql_require_ssl(r):
    ssl = _nested(r["values"], "settings", "ip_configuration", "require_ssl")
    if ssl is False or ssl is None:
        return [f"ip_configuration.require_ssl = {ssl}"]
    return []


def check_sql_backups(r):
    enabled = _nested(r["values"], "settings", "backup_configuration", "enabled")
    if enabled is not True:
        return [f"backup_configuration.enabled = {enabled}"]
    return []


def check_gke_legacy_abac(r):
    if r["values"].get("enable_legacy_abac") is True:
        return ["enable_legacy_abac = true"]
    return []


def check_gke_private_cluster(r):
    enabled = _nested(r["values"], "private_cluster_config", "enable_private_nodes")
    if enabled is not True:
        return ["private_cluster_config.enable_private_nodes is not true (or block absent)"]
    return []


def check_gke_network_policy(r):
    enabled = _nested(r["values"], "network_policy", "enabled")
    if enabled is not True:
        return ["network_policy.enabled is not true (or block absent)"]
    return []


def check_kms_rotation(r):
    period = r["values"].get("rotation_period")
    if not period:
        return ["rotation_period not set"]
    m = re.match(r"^(\d+)s$", str(period))
    if not m or int(m.group(1)) > 7776000:
        return [f"rotation_period={period} (> 90 days)"]
    return []


def check_bigquery_public(r):
    findings = []
    for entry in r["values"].get("access") or []:
        sg = entry.get("special_group")
        im = entry.get("iam_member") or ""
        if sg in PUBLIC_MEMBERS or any(pub in im for pub in PUBLIC_MEMBERS):
            findings.append(f"special_group={sg} iam_member={im}")
    return findings


def check_serial_port(r):
    meta = r["values"].get("metadata") or {}
    if str(meta.get("serial-port-enable", "")).lower() in ("true", "1"):
        return ["metadata['serial-port-enable'] = true"]
    return []


CHECKS = {
    "GCP-STORAGE-001": check_storage_public,
    "GCP-STORAGE-002": check_uniform_bucket_level_access,
    "GCP-NET-001": check_firewall_ssh_rdp_open,
    "GCP-NET-002": check_firewall_all_open,
    "GCP-NET-003": check_subnet_flow_logs,
    "GCP-IAM-001": check_primitive_role,
    "GCP-IAM-002": check_service_account_key,
    "GCP-SQL-001": check_sql_public_ip,
    "GCP-SQL-002": check_sql_require_ssl,
    "GCP-SQL-003": check_sql_backups,
    "GCP-GKE-001": check_gke_legacy_abac,
    "GCP-GKE-002": check_gke_private_cluster,
    "GCP-GKE-003": check_gke_network_policy,
    "GCP-KMS-001": check_kms_rotation,
    "GCP-BQ-001": check_bigquery_public,
    "GCP-COMPUTE-001": check_serial_port,
}


def run_audit(resources, checklist):
    findings = []
    for rule_id, control in checklist.items():
        if not control.get("automated"):
            continue
        check_fn = CHECKS.get(rule_id)
        if check_fn is None:
            print(f"warning: {rule_id} is marked automated in the checklist "
                  "but has no check() implementation -- skipping", file=sys.stderr)
            continue
        for r in resources:
            if r["type"] not in control["resource_types"]:
                continue
            for detail in check_fn(r):
                findings.append({
                    "rule_id": rule_id,
                    "cis_id": control["cis_id"],
                    "severity": control["severity"],
                    "title": control["title"],
                    "resource_address": r["address"],
                    "resource_type": r["type"],
                    "detail": detail,
                    "remediation": control["remediation"],
                })
    return findings


def manual_review_items(checklist):
    return [c for c in checklist.values() if not c.get("automated")]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--plan-json", help="path to `terraform show -json` output")
    src.add_argument("--tf-dir", help="directory of raw .tf files (heuristic fallback)")
    ap.add_argument("--min-severity", choices=list(SEVERITY_ORDER), default="LOW",
                     help="omit findings below this severity from the report (default: LOW, i.e. all)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    checklist = load_checklist()

    if args.plan_json:
        mode = "plan-json"
        resources = resources_from_plan_json(args.plan_json)
    else:
        mode = "tf-dir"
        if not os.path.isdir(args.tf_dir):
            print(f"error: {args.tf_dir} is not a directory", file=sys.stderr)
            sys.exit(2)
        resources = resources_from_tf_dir(args.tf_dir)

    findings = run_audit(resources, checklist)
    threshold = SEVERITY_ORDER[args.min_severity]
    findings = [f for f in findings if SEVERITY_ORDER[f["severity"]] >= threshold]
    findings.sort(key=lambda f: -SEVERITY_ORDER[f["severity"]])

    manual = manual_review_items(checklist)

    if args.json:
        print(json.dumps({
            "mode": mode,
            "resource_count": len(resources),
            "findings": findings,
            "manual_review_required": manual,
        }, indent=2))
    else:
        print(f"Mode: {mode} ({'heuristic -- lower bound only' if mode == 'tf-dir' else 'authoritative'})")
        print(f"Resources scanned: {len(resources)}")
        print(f"Automated findings: {len(findings)}\n")
        for f in findings:
            print(f"[{f['severity']}] {f['rule_id']} (CIS {f['cis_id']}) - {f['title']}")
            print(f"    resource: {f['resource_address']}")
            print(f"    detail:   {f['detail']}")
            print(f"    fix:      {f['remediation']}\n")
        if manual:
            print(f"Manual-review items (not verifiable from Terraform config alone): {len(manual)}")
            for c in manual:
                print(f"  - {c['id']}: {c['title']}")

    if mode == "tf-dir":
        print("\nNOTE: tf-dir mode is heuristic. A clean result here is "
              "INCONCLUSIVE, not a pass -- re-run with --plan-json when "
              "possible.", file=sys.stderr)

    has_blocking = any(SEVERITY_ORDER[f["severity"]] >= SEVERITY_ORDER["HIGH"] for f in findings)
    sys.exit(1 if has_blocking else 0)


if __name__ == "__main__":
    main()
