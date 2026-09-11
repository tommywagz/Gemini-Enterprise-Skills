# Google Cloud FinOps Audit Report

**Scope:** `[project(s)/inventory source described]`
**Inventory captured:** `[UTC timestamp of the inventory snapshot]`
**Checklist version:** `[checklist_version from assets/finops_checklist.json]`

## Summary

| Severity | Count |
|---|---|
| HIGH | `[n]` |
| MEDIUM | `[n]` |
| LOW | `[n]` |

**Total estimated monthly savings:** `~$[total_estimated_monthly_savings_usd]`
_(documented estimate from findings where the inventory supplied
`monthly_cost_usd` — not a live Cloud Billing quote; see each finding's
estimate note.)_

**Findings without a cost estimate:** `[n]` _(no `monthly_cost_usd` was
available for these resources — cross-reference the Cloud Billing export to
size these before prioritizing.)_

## Findings

> One entry per finding from `audit_gcp_costs.py`'s JSON output, ordered by
> severity (already sorted in the tool's output -- preserve that order).

### `[SEVERITY]` `[rule_id]` -- `[title]`

- **Resource:** `[resource_category]/[resource]`
- **Detail:** `[detail]`
- **Recommendation:** `[recommendation text from the finding]`
- **Estimated monthly savings:** `~$[estimated_monthly_savings_usd]` (or "not
  estimated -- no monthly_cost_usd supplied")
- **Snippet:** `[path to the matching file in
  gcp_cost_remediation_snippets/, if scripts/generate_remediation_tf.py was
  run]`
- **Confirmed with workload owner:** `[ ] yes  [ ] no -- do not apply until confirmed`

_(repeat per finding)_

## Manual Review Required

> From the JSON output's `manual_review_required` list -- patterns that need
> trend data or a resource inventory this point-in-time scan doesn't cover
> (Committed Use Discount sizing, snapshot/image lifecycle).

- `[id]`: `[title]` -- `[why it needs manual review, from the checklist's recommendation field]`

_(repeat per manual-review item)_

## Next Steps

1. For each HIGH finding, confirm the tradeoff with the resource's owner
   (traffic pattern, latency requirement, restart tolerance) before applying
   anything from `gcp_cost_remediation_snippets/`.
2. Re-run `scripts/audit_gcp_costs.py` against a fresh inventory after
   changes to confirm the finding actually cleared.
3. Escalate Manual Review items to whoever owns billing/commitment strategy
   -- this scan cannot size a Committed Use Discount or audit snapshot
   lifecycle on its own.
4. Track total estimated savings against the next billing cycle's actual
   invoice to validate the estimates were directionally correct.
