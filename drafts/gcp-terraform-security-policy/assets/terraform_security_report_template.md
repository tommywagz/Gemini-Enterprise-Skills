# GCP Terraform Security Audit Report

**Target:** `[module/directory path or repo name]`
**Scan mode:** `[plan-json (authoritative) | tf-dir (heuristic -- treat a clean
result as inconclusive, not a pass)]`
**Scanned:** `[UTC timestamp]`
**Checklist version:** `[checklist_version from assets/gcp_compliance_checklist.json]`

## Summary

| Severity | Count |
|---|---|
| CRITICAL | `[n]` |
| HIGH | `[n]` |
| MEDIUM | `[n]` |
| LOW | `[n]` |
| **Blocking (CRITICAL+HIGH)** | `[n]` |

**Recommendation:** `[BLOCK apply until CRITICAL/HIGH findings are resolved |
PROCEED -- no CRITICAL/HIGH findings, review MEDIUM/LOW at next iteration]`

## Findings

> One entry per finding from `audit_tf_gcp.py`'s JSON output, ordered by
> severity (already sorted in the tool's output -- preserve that order).

### `[SEVERITY]` `[rule_id]` -- `[title]` (CIS `[cis_id]`)

- **Resource:** `[resource_address]`
- **Detail:** `[detail]`
- **Remediation:** `[remediation text from the finding]`
- **Snippet:** `[path to the matching file in tf_remediation_snippets/, if
  scripts/remediate_tf_compliance.sh was run]`

_(repeat per finding)_

## Manual Review Required

> From the JSON output's `manual_review_required` list -- controls that need
> organization- or folder-level context this scan cannot see from a single
> module's plan.

- `[id]`: `[title]` -- `[why it needs manual review, from the checklist's
  remediation field]`

_(repeat per manual-review item)_

## Next Steps

1. Resolve every CRITICAL and HIGH finding above before running
   `terraform apply`, using the snippets in `tf_remediation_snippets/` as a
   starting point -- adapt each `REPLACE_ME`/`REPLACE_WITH_*` placeholder to
   the real resource, then merge it into your own configuration.
2. Re-run `scripts/audit_tf_gcp.py` against a fresh plan after edits to
   confirm the finding is actually gone, not just visually addressed.
3. Escalate any Manual Review item to whoever owns organization/folder-level
   policy -- this scan cannot confirm or deny those controls on its own.
