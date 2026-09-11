# Skill Evaluation Report: gcp-cost-optimizer

**Date:** 2026-09-11
**Evaluator:** evaluator
**Iteration:** 1 (of 3)

## Summary

Ship. The skill meets the default routing thresholds with 20 balanced cases
and passes clean and wasteful-inventory integration tests. It produces local,
review-only Terraform snippets and requires owner confirmation for every
availability or deletion tradeoff.

## Risk Tier

**Medium**

The bundle contains local Python scripts that read confidential billing and
inventory data and write a selected local output directory. It has no
reachable network call, credential, destructive command, or auto-apply path.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---|---|---|
| Trigger Precision | > 90% | Not measured | 100% (10/10) | PASS |
| Trigger Recall | > 85% | Not measured | 100% (10/10) | PASS |
| False Positive Rate | < 5% | Not measured | 0% (0/10) | PASS |
| Task Completion Rate | > 80% | Not measured | 100% (3/3 paths) | PASS |
| Token Usage | < 5,000 | Not measured | Approx. 2,000 | PASS |
| Step Error Rate | baseline | Not measured | 0% (0/3) | Baseline |
| Reference Hit Rate | baseline | Not measured | 100% | Baseline |

## Findings & Fixes Applied

| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | Inventory category values could be malformed and cause a traceback. | Validated regular file inputs, category lists, and object entries with exit 2 errors. | `scripts/audit_gcp_costs.py` |
| 2 | Data handling and execution limits were implicit. | Declared Confidential classification, local-only input boundary, no cloud CLI/Terraform execution, and unavailable-reference fallback. | `SKILL.md` |

## Checklist And Security

- [x] Specific triggers, common anti-triggers, 20-case routing tests, ordered workflow, error handling, output format, references, and asset documentation.
- [x] Scripts compiled and were integration-tested with clean and wasteful inventory fixtures; adversarial non-trigger cases pass.
- [x] Medium risk tier, input validation, no credentials, confidential data classification, and owner approval for availability/destructive changes.
- [ ] Independent FinOps SME review and blind user-trust study remain recommended governance follow-ups.

The scanner's URL and AWS-test prompt matches are non-executable false
positives. The skill never runs `terraform apply`, destroys resources, or
executes cloud-provider commands; bundled scripts only read local JSON and
write reviewable `.tf.snippet` files.

## Test Evidence

- The evaluator scoring utility reported TP=10, TN=10, FP=0, FN=0.
- `tests/inventory.json` produced six documented findings and six remediation snippets without modifying source fixtures.
- `tests/inventory_clean.json` returned no automated findings and retained two manual-review controls.
- Python compilation and checklist JSON validation passed.
