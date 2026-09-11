---
name: gcp-terraform-security-policy
description: "Audits Google Cloud Terraform configuration (raw .tf files or a `terraform show -json` plan) against CIS Google Cloud Platform Foundation Benchmark controls, private-by-default storage/network defaults, and least-privilege IAM, then proposes remediation HCL before `terraform apply`. TRIGGER when the user asks to \"audit Terraform for GCP security\", \"scan for public GCS buckets/IAM/firewall rules\", \"check CIS GCP benchmark compliance\", \"review least-privilege IAM in Terraform\", or provides a `terraform plan`/`terraform show -json` output for GCP. DO NOT TRIGGER for general Terraform authoring/module design unrelated to security, AWS/Azure/other-cloud IaC scanning, or actually running `terraform apply` (this skill only audits and proposes; it never applies infrastructure changes)."
version: 1.0.0
author: Actual Agentic Solutions
tags: [gcp, terraform, iac, security, cis-benchmark, iam, compliance]
license: Apache-2.0
compatibility: "Google Terraform provider (hashicorp/google or hashicorp/google-beta); Terraform CLI 1.x for --plan-json generation; Python 3.9+ for scripts/audit_tf_gcp.py"
metadata: {}
---

- GCP IaC Compliance Reviewer

- Overview
This skill scans a Google Cloud Terraform configuration for security and
compliance violations *before* `terraform apply` runs, so a misconfigured
public bucket, an open SSH rule, or a `roles/editor` grant never reaches a
real project. It is not a generic Terraform linter: every rule it checks
maps to a specific CIS Google Cloud Platform Foundation Benchmark control,
a private-by-default storage/network default, or a least-privilege IAM
guideline, documented in `references/` and encoded once as the canonical
rule metadata in `assets/gcp_compliance_checklist.json`.

Success looks like: a findings list ranked by severity, each with the exact
resource address and a concrete fix (not just "this is insecure"), plus a
set of reviewable — never auto-applied — HCL remediation snippets, and an
explicit list of controls that need human/org-level judgment this scan
cannot make on its own.

- Prerequisites
- The Terraform module/root directory to audit, or (preferred) a
  `terraform show -json` plan export from it.
- Python 3.9+ available to run `scripts/audit_tf_gcp.py` (standard library
  only — no pip install required).
- Bash available to run `scripts/remediate_tf_compliance.sh` (uses `python3`
  for JSON parsing internally, not `jq` — do not assume `jq` is installed on
  the target machine).

- Workflow

- Step 1: Get the most authoritative view of the configuration you can
Ask whether the user can run Terraform against the target module. If yes,
have them (or run yourself, if you have the credentials and this is safe to
do in the target environment):
```
terraform init
terraform plan -out=tf.plan
terraform show -json tf.plan > plan.json
```
This is the **preferred** path: Terraform has already resolved every
variable, local, module input, and `count`/`for_each` expansion, so the scan
in Step 2 has no blind spots from unresolved HCL expressions.
- If `terraform` isn't available (no credentials, CI-only environment, or
  the user just wants a quick look), fall back to scanning the raw `.tf`
  directory directly in Step 2 — but see the heuristic-mode caveat below
  before reporting any result as a clean pass.

- Step 2: Run the audit
Preferred:
```
scripts/audit_tf_gcp.py --plan-json plan.json --json > findings.json
```
Fallback (heuristic — see the script's own docstring for exactly what it
cannot see: variables, locals, module outputs, `for_each`, `dynamic`
blocks):
```
scripts/audit_tf_gcp.py --tf-dir path/to/module --json > findings.json
```
Read the `mode` field in the JSON output before drawing any conclusion. If
`mode` is `"tf-dir"` and `findings` is empty, tell the user this is
**inconclusive, not a clean bill of health** — recommend generating a
`--plan-json` export instead of trusting the heuristic scan's silence.

- Step 3: Generate reviewable remediation snippets
For every CRITICAL/HIGH finding, run:
```
scripts/remediate_tf_compliance.sh findings.json ./tf_remediation_snippets
```
This writes one `.tf.snippet` file per finding — never edits the user's
actual `.tf` files, and never runs `terraform apply`. Present each snippet
next to its finding; tell the user to replace the `REPLACE_ME`/
`REPLACE_WITH_*` placeholders with their real resource names before merging
it into their configuration themselves.

- Step 4: Deepen IAM-specific findings
If any finding has `rule_id` starting `GCP-IAM-`, or the user is asking
specifically about role scoping, read
`references/iam_least_privilege_guidelines.md` and recommend a *specific*
predefined role (not just "use a narrower role") based on what the flagged
principal actually needs to do — the reference file's role-mapping table
covers the common cases (bucket access, BigQuery queries, Cloud SQL
connections, CI/CD deploys).

- Step 5: Compile the report
Copy `assets/terraform_security_report_template.md` and fill in the Summary
counts, the per-finding sections (from `findings.json`), and the Manual
Review Required section from the JSON output's `manual_review_required`
list — these are checklist controls marked `automated: false` because they
need organization- or folder-level context (audit log sinks, org policy
constraints) a single module's plan cannot confirm on its own. Read
`references/gcp_security_benchmarks.md` if you need to explain *why* a
control matters, beyond the one-line rationale in the JSON output.

- Examples

- Example 1: Plan-json audit with a blocking finding
Input: "Here's our GCP Terraform module, can you check it's safe to apply?"
Expected output / behavior: generate `plan.json` per Step 1, run
`audit_tf_gcp.py --plan-json plan.json --json`, find e.g. a
`google_compute_firewall` allowing `0.0.0.0/0` on port 22 (`GCP-NET-001`,
CRITICAL) and a `roles/editor` project IAM member (`GCP-IAM-001`,
CRITICAL). Run `remediate_tf_compliance.sh` to produce the two snippets,
recommend `roles/storage.objectAdmin` (or whatever the member's actual job
is) in place of `roles/editor` per `references/iam_least_privilege_guidelines.md`,
and state clearly: **do not run `terraform apply` until these are
resolved.**

- Example 2: No Terraform binary available
Input: "I don't have terraform installed, just look at these .tf files."
Expected output / behavior: run `audit_tf_gcp.py --tf-dir <path> --json`,
note in the report header that this is heuristic mode, and if a `for_each`
or module-sourced value is visible in the raw files, explicitly flag that
those resources could not be fully evaluated rather than silently reporting
them as clean.

- Error Handling
- `audit_tf_gcp.py` exits 2: this is a parse/usage error (e.g. a plan JSON
  missing `planned_values.root_module`, likely from a `terraform show -json`
  run against an unsupported/very old Terraform version) — never treat exit
  2 as "0 findings"; show the stderr message and ask the user to
  regenerate the plan JSON.
- A resource type is absent from `assets/gcp_compliance_checklist.json`
  entirely (e.g. Cloud Run, Pub/Sub, Artifact Registry): say so explicitly —
  this checklist covers the controls in
  `references/gcp_security_benchmarks.md`'s CIS sections 1–7, not every GCP
  resource type. Do not imply a clean scan covers resources it never looked
  at.
- `remediate_tf_compliance.sh` finds a `rule_id` with no canned template: it
  prints a generic fallback pointing at the checklist's `remediation` field
  instead of silently skipping the finding — surface that fallback file to
  the user rather than treating the finding as handled.
- A finding looks like it might already be neutralized by an org-level
  policy the scan can't see (e.g. an inherited `publicAccessPrevention`
  constraint): report the finding anyway and note the possibility — see
  "Known limitations of scanning a single Terraform plan" in
  `references/gcp_security_benchmarks.md`. Never suppress a finding based on
  an assumption you can't verify from the plan.
- Do not run `terraform apply` yourself, and do not instruct the user to
  auto-apply the generated snippets without review — Terraform changes here
  (removing a firewall rule, disabling a public IP) can break a running
  workload; every snippet is a starting point for manual integration, not a
  patch to merge blind.

- Reference Files
- **scripts/audit_tf_gcp.py**: runs the automated checklist against a
  `--plan-json` export (authoritative) or a `--tf-dir` (heuristic) and
  prints/JSON-dumps ranked findings plus the manual-review list — run in
  Step 2.
- **scripts/remediate_tf_compliance.sh**: converts `findings.json` into
  reviewable `.tf.snippet` files, one per CRITICAL/HIGH finding — run in
  Step 3. Never modifies the user's own `.tf` files.
- **references/gcp_security_benchmarks.md**: CIS GCP Foundation Benchmark
  structure, the private-by-default rationale for storage/network/compute/
  GKE/Cloud SQL controls, the org-policy constraints that make a fix
  durable, and the limitations of scanning a single Terraform plan — read
  in Step 5, or whenever "why does this matter" needs a real answer.
- **references/iam_least_privilege_guidelines.md**: primitive vs. predefined
  vs. custom role guidance, a role-mapping table for common job functions,
  service account and Workload Identity best practices — read in Step 4 for
  any `GCP-IAM-*` finding.
- **assets/gcp_compliance_checklist.json**: the canonical rule metadata
  (severity, CIS control ID, rationale, remediation text) that both the
  script and this SKILL.md draw from — the single source of truth if a
  rule's wording or severity ever needs updating.
- **assets/terraform_security_report_template.md**: fill-in-the-blanks
  report structure — copy it in Step 5 rather than inventing a report
  format ad hoc.

- Output Format
Return, in order: (1) the scan mode used (plan-json vs. tf-dir) and an
explicit inconclusive-vs-clean caveat if tf-dir was used, (2) the findings
ranked by severity with resource address and fix for each, (3) the path to
the generated remediation snippets, (4) the manual-review list, and (5) a
one-line go/no-go recommendation on running `terraform apply` given the
current CRITICAL/HIGH count. Never state or imply "compliant" based on a
tf-dir scan with zero findings.
