---
name: gcp-cost-optimizer
description: "Analyzes a normalized Google Cloud resource inventory (idle Compute Engine instances, unattached persistent disks/static IPs, under-utilized BigQuery flat-rate slots, unexpiring BigQuery datasets, over-provisioned Cloud Run min_instances/concurrency) and generates prescriptive recommendations plus reviewable Terraform remediation snippets to cut spend. TRIGGER when the user asks to \"reduce GCP costs\", \"find idle Google Cloud resources\", \"optimize BigQuery slot utilization\", \"run a GCP spend/FinOps audit\", or provides a GCP billing/inventory export. DO NOT TRIGGER for general Terraform authoring unrelated to cost, AWS/Azure cost optimization, or security/compliance scanning of GCP resources (use the gcp-terraform-security-policy skill for that)."
version: 1.0.0
author: Actual Agentic Solutions
tags: [gcp, finops, cost-optimization, terraform, bigquery, cloud-run]
license: Apache-2.0
compatibility: "Python 3.9+ for scripts/; Google Cloud SDK (gcloud, bq) and/or a Cloud Billing export recommended for sourcing real inventory data"
metadata: {}
---

- Google Cloud FinOps Auditor

- Overview
This skill turns raw GCP resource usage signals into a ranked, actionable
spend-reduction report: idle Compute Engine instances, unattached disks and
static IPs, under-utilized BigQuery slot reservations, BigQuery datasets
with no storage expiration, and over-provisioned Cloud Run scaling
settings. Every rule maps to a documented waste pattern in
`assets/finops_checklist.json` (the single source of truth for severity and
recommendation text — the audit script only implements the check logic).

This is an **advisory** audit, not a security gate: unlike a compliance
scanner, there is no universally correct cost/performance tradeoff. Every
finding needs the resource owner to confirm the workload can tolerate the
change (a cold start, a preemption, a warm-instance latency hit) before
anything is applied — this skill never runs `terraform apply` or deletes
anything itself.

Success looks like: a findings list ranked by severity with an estimated
dollar savings *only* where the input data actually supports one (never a
fabricated price), reviewable HCL remediation snippets, and an explicit list
of patterns that need trend data or context beyond a single inventory
snapshot.

- Prerequisites
- A normalized inventory JSON matching the schema documented in
  `scripts/audit_gcp_costs.py`'s docstring — build it from `gcloud compute
  instances/disks/addresses list --format=json`, BigQuery reservation
  utilization data, `bq show --format=json`, and Cloud Run's
  `avg_requests_per_min` (Cloud Monitoring). See
  `references/gcp_finops_practices.md`'s source-mapping table for exactly
  which command/metric feeds which field.
- Optionally, a Cloud Billing export (or per-resource cost figures) to
  populate each resource's `monthly_cost_usd` — without it, findings are
  still reported, just without a dollar estimate attached.
- Python 3.9+ (standard library only) to run the scripts; no `jq` assumed.
- **Data classification:** Confidential. Inventory and billing exports can
  disclose project names, service usage, labels, and spend; keep them local to
  authorized storage and redact sensitive fields before sharing reports.
- **Tool boundary:** Use only the bundled local scripts on a local regular JSON
  inventory file. Do not run `gcloud`, `bq`, Terraform, cloud deletion, or
  billing API commands yourself; ask the user to supply authorized exports.

- Workflow

- Step 1: Build the normalized inventory
Help the user assemble the inventory JSON from their actual GCP project(s)
— do not invent utilization numbers or costs. If they only have raw
`gcloud ... list` output, map each field per
`references/gcp_finops_practices.md`'s source table rather than guessing
field names. Any resource category can be omitted if there's no data for
it; the script skips categories that aren't present.
- If `monthly_cost_usd` isn't available for a resource, proceed anyway —
  the finding still fires, just without a dollar estimate. Do not block the
  audit on having complete billing data.

- Step 2: Run the cost audit
```
scripts/audit_gcp_costs.py --inventory inventory.json --json > findings.json
```
Adjust `--idle-cpu-threshold`, `--bq-reservation-underutil-pct`,
`--bq-long-term-storage-gb-threshold`, or `--run-low-traffic-rpm` if the
defaults don't match the user's stated tolerance (e.g. a user who says "only
flag instances under 2% CPU" should get `--idle-cpu-threshold 2.0`, not a
manually filtered version of the default output). Read the `manual_review_required`
list in the output — these (Committed Use Discount sizing, snapshot/image
lifecycle) need trend data or a broader resource listing this single-pass
scan does not have; say so rather than guessing an answer for them.

- Step 3: Generate reviewable remediation snippets
```
scripts/generate_remediation_tf.py findings.json ./gcp_cost_remediation_snippets
```
This writes one `.tf.snippet` file per finding — never edits the user's
actual `.tf` files, never runs `terraform apply`, and never deletes a
resource directly (e.g. the unattached-disk snippet creates a
`google_compute_snapshot` first, with instructions to remove the disk only
after confirming the snapshot succeeded). Present each snippet next to its
finding.

- Step 4: Confirm before recommending anything irreversible or availability-affecting
For every HIGH finding involving stopping/scheduling a running instance,
migrating to Spot VMs, releasing a static IP, or lowering Cloud Run
`min_instances`: explicitly ask the user (or note in the report) that this
needs the resource owner's confirmation the workload tolerates the change.
Never present these as safe to auto-apply — see the Error Handling
anti-patterns below.

- Step 5: Compile the report
Copy `assets/cost_savings_report_template.md` and fill in the Summary
counts, per-finding sections (from `findings.json`), the total estimated
savings, and the Manual Review Required section. Read
`references/gcp_pricing_and_quotas.md` if the user needs the pricing
*mechanics* explained (why a Committed Use Discount vs. Spot VM, why
long-term BigQuery storage isn't the real lever) — never quote a specific
current $/unit rate from memory; point to the Cloud Pricing Calculator or
the user's own Cloud Billing export instead.

- Examples

- Example 1: Full inventory with billing data
Input: "Here's our GCP inventory with billing export data, find us savings."
Expected output / behavior: run `audit_gcp_costs.py --inventory ... --json`,
surface e.g. an idle dev instance (`GCP-COST-COMPUTE-001`, HIGH, ~$120/mo
estimated) and an unattached disk (`GCP-COST-DISK-001`, HIGH, ~$85/mo
estimated) with real dollar figures since `monthly_cost_usd` was supplied;
generate snippets via Step 3; total estimated savings computed only from
findings that had a cost figure, stated as an estimate, not a quote.

- Example 2: Inventory with no cost data
Input: "I just have gcloud list output, no billing export."
Expected output / behavior: still run the audit and report every finding
(e.g. a low-utilization BigQuery reservation), but omit dollar estimates
entirely rather than guessing a price — tell the user to cross-reference
Cloud Billing or the Pricing Calculator to size the actual opportunity
before prioritizing.

- Error Handling
- `audit_gcp_costs.py` exits 2: this is a parse/usage error (missing or
  malformed inventory JSON) — never treat exit 2 as "no findings"; show the
  stderr message and fix the input.
- A resource category has no matching checklist rule (e.g. Cloud SQL,
  GKE node pools, Cloud Storage lifecycle): say so explicitly — this
  checklist covers Compute Engine, disks, static IPs, BigQuery, and Cloud
  Run only, not every billable GCP resource. Do not imply completeness the
  scan doesn't have.
- `generate_remediation_tf.py` finds a `rule_id` with no canned template: it
  prints a generic fallback pointing at `assets/finops_checklist.json`'s
  recommendation field instead of silently skipping it.
- **Never** recommend applying a stop/delete/resize/Spot-migration snippet
  without the workload owner's explicit confirmation the tradeoff is
  acceptable — a single idle-looking snapshot can be misleading for
  workloads with legitimate periodic-but-sparse usage (e.g. a
  monthly-batch-only instance that happens to be mid-idle-period when
  the inventory was captured). Recommend a longer lookback window if the
  user's inventory only reflects a very short capture period.
- A `monthly_cost_usd`-derived savings estimate looks suspiciously large or
  small: it is a documented `waste_fraction` multiplied against a
  user-supplied cost, not a live pricing calculation — flag it as an
  estimate needing verification against the actual Cloud Billing invoice,
   don't present it as exact.
- A referenced script, asset, or reference file is missing: stop and report
  the skill as incomplete rather than substituting an unreviewed command or
  inventing pricing/control information.

- Reference Files
- **scripts/audit_gcp_costs.py**: runs the automated checklist against a
  normalized inventory JSON, prints/JSON-dumps ranked findings, estimated
  savings (only where cost data was supplied), and the manual-review list —
  run in Step 2.
- **scripts/generate_remediation_tf.py**: converts `findings.json` into
  reviewable `.tf.snippet` files — run in Step 3. Never modifies the user's
  own `.tf` files or applies/destroys anything.
- **references/gcp_finops_practices.md**: where each inventory field
  typically comes from (gcloud/bq commands, Cloud Monitoring metrics), the
  rationale behind each waste pattern, and explicit anti-patterns to avoid
  recommending — read in Step 1 and Step 4.
- **references/gcp_pricing_and_quotas.md**: machine type family overview,
  discount mechanism comparison (sustained use, CUDs, Spot), disk type
  tradeoffs, BigQuery and Cloud Run billing mechanics — deliberately has no
  hardcoded $/unit figures; read in Step 5 when explaining *why* a
  recommendation saves money.
- **assets/finops_checklist.json**: the canonical rule metadata (severity,
  rationale, recommendation, documented `waste_fraction`) that both the
  script and this SKILL.md draw from.
- **assets/cost_savings_report_template.md**: fill-in-the-blanks report
  structure, including an explicit "confirmed with workload owner"
  checkbox per finding — copy it in Step 5.

- Output Format
Return, in order: (1) the findings ranked by severity with resource,
detail, and recommendation for each, (2) the estimated monthly savings per
finding and the total (both explicitly labeled as documented estimates, not
live quotes, and omitted where no cost data was supplied), (3) the path to
the generated remediation snippets, (4) the manual-review list, and (5) an
explicit reminder that every HIGH finding needs the resource owner's
confirmation before anything is applied. Never state a specific current GCP
price from memory, and never imply a recommendation is safe to auto-apply.
