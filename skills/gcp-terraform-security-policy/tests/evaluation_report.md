# Skill Evaluation Report: gcp-terraform-security-policy

**Date:** 2026-09-11
**Evaluator:** evaluator
**Iteration:** 1 (of 3)

## Summary

Ship. The skill passed the default routing thresholds on a balanced 20-case
suite and all three integration paths. A critical filename-to-Python-source
injection defect in the remediation script was removed before final testing;
the final bundle uses only local read-only audit operations and produces
review-only snippets.

## Risk Tier

**Medium**

The bundle contains local Python and Bash scripts that read Terraform inputs
and write user-selected remediation directories, but has no network calls,
hardcoded credentials, destructive Terraform commands, or reachable path
traversal/exfiltration behavior. Its data classification is Confidential
because Terraform plans may contain sensitive provider values.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---|---|---|
| Trigger Precision | > 90% | Not measured | 100% (10/10) | PASS |
| Trigger Recall | > 85% | Not measured | 100% (10/10) | PASS |
| False Positive Rate | < 5% | Not measured | 0% (0/10) | PASS |
| Task Completion Rate | > 80% | Not measured | 100% (3/3 integration paths) | PASS |
| Token Usage | < 5,000 | Not measured | Approx. 2,100 tokens for SKILL.md | PASS |
| Step Error Rate | baseline | Not measured | 0% (0/3) | Baseline |
| Reference Hit Rate | baseline | Not measured | 100% (audit, remediation, checklist) | Baseline |
| Time to Completion | baseline | Not measured | Local fixture runs completed in under 1 second each | Baseline |

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---|---|
| Output Quality - Accuracy | 5 | Findings carry checklist-grounded IDs, severities, resources, and remediation text. |
| Output Quality - Completeness | 5 | Includes manual org-policy review items and tf-dir limitations. |
| Output Quality - Clarity | 5 | Ordered workflow and explicit report format distinguish findings from review-only snippets. |
| Output Quality - Formatting | 5 | Structured JSON and Markdown templates are directly usable. |
| Instruction Fidelity | 5 | Fixtures verified plan audit, no-findings output, heuristic behavior, and non-mutating remediation. |
| Edge Case Handling | 5 | Missing plans now exit with a validation error; heuristic clean results remain inconclusive. |
| Coexistence | 5 | Description excludes generic Terraform, non-GCP IaC, execution, and cost work. |
| User Trust | 4 | Clear caveats and no-apply boundary support review; independent user study remains outside this evaluation. |

## Production Checklist Status

- [x] Specific domain trigger conditions and common anti-triggers; 20-case routing suite passes.
- [x] Body is below 5,000 tokens with prerequisites, atomic branches, error handling, output format, and cited domain references.
- [x] Scripts independently compiled/syntax-checked and tested; long references include contents lists; asset formats and unavailable-reference fallback are documented.
- [x] Integration, edge-case, and adversarial inputs were tested. The skill-specific audit workflow provides a material delta over unstructured Terraform review.
- [ ] External SME review and blind user-trust study were not performed; these are governance follow-ups, not blockers for the automated release gate.
- [x] Medium risk tier, minimal local tool boundary, input validation, confidential data classification, no credentials, and no irreversible action path.

## Findings & Fixes Applied

| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | A quoted findings-file path was interpolated into Python source, allowing code injection through a crafted filename. | Passed the path as `sys.argv[1]` to a quoted heredoc Python program. | `scripts/remediate_tf_compliance.sh` |
| 2 | Raw-HCL fallback did not parse Terraform's `metadata = { ... }` form, missing serial-port findings. | Added brace-aware metadata-object parsing and a regression fixture. | `scripts/audit_tf_gcp.py`, `tests/raw_compute.tf` |
| 3 | Unsupported IAM policy resources were listed as automated but could not be decoded. | Limited the primitive-role control to binding/member resource types the script can inspect. | `assets/gcp_compliance_checklist.json` |
| 4 | Tool boundary, plan confidentiality, and missing-reference behavior were implicit. | Added explicit local-only, no-apply, data-classification, input-validation, and fallback instructions. | `SKILL.md` |

## Remaining Gaps

Independent GCP security SME review and a blind user-trust study remain recommended. They do not affect the measured automated gate; revisit them before making compliance certification claims.

## Security Review

- Order-of-operations checklist completed: yes.
- `scripts/security_scan.sh` findings requiring manual follow-up: the `$schema` URL and an AWS identity example are non-executable false positives. No network call, credential, or reachable traversal behavior exists.
- Blast radius: `terraform init`, `terraform plan`, and `terraform show` are instructions for the user only; the skill explicitly prohibits the agent from running them. Bundled scripts locally read plan/HCL/JSON inputs and write only the selected review-snippet directory. They never execute `terraform apply`, cloud CLIs, or network calls.

## Test Evidence

- `python3 scripts/audit_tf_gcp.py --plan-json tests/plan_with_findings.json --json` identified two CRITICAL findings.
- `bash scripts/remediate_tf_compliance.sh tests/findings.json tests/remediation_output` generated two `.tf.snippet` files without modifying fixtures.
- `python3 scripts/audit_tf_gcp.py --plan-json tests/plan_clean.json --json` returned no findings and two manual-review items.
- `python3 scripts/audit_tf_gcp.py --tf-dir tests --json` detected `GCP-COMPUTE-001` in `raw_compute.tf` and marked heuristic mode inconclusive.
- The evaluator's `score_eval_suite.py` reported TP=10, TN=10, FP=0, FN=0 for `tests/eval_suite.json`.
