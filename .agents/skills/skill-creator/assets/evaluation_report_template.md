# Skill Evaluation Report: {{skill_name}}

**Date:** {{date}}
**Evaluator:** {{evaluator}}
**Iteration:** {{iteration_number}} (of {{max_iterations}})

## Summary
{{one-paragraph verdict: ship / iterate / deprecate, and why}}

## Risk Tier
**{{Low | Medium | High | Critical}}**

{{one-sentence justification citing the specific indicators found}}

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---|---|---|
| Trigger Precision | > 90% | {{}} | {{}} | {{PASS/FAIL}} |
| Trigger Recall | > 85% | {{}} | {{}} | {{PASS/FAIL}} |
| False Positive Rate | < 5% | {{}} | {{}} | {{PASS/FAIL}} |
| Task Completion Rate | > 80% | {{}} | {{}} | {{PASS/FAIL}} |
| Token Usage | < 5,000 | {{}} | {{}} | {{PASS/FAIL}} |
| Step Error Rate | baseline | {{}} | {{}} | — |
| Reference Hit Rate | baseline | {{}} | {{}} | — |
| Time to Completion | baseline | {{}} | {{}} | — |

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---|---|
| Output Quality — Accuracy | {{}} | |
| Output Quality — Completeness | {{}} | |
| Output Quality — Clarity | {{}} | |
| Output Quality — Formatting | {{}} | |
| Instruction Fidelity | {{}} | |
| Edge Case Handling | {{}} | |
| Coexistence | {{}} | |
| User Trust | {{}} | |

## Production Checklist Status
{{paste unchecked items from references/production_checklist.md here}}

## Findings & Fixes Applied
| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | {{}} | {{}} | {{}} |

## Remaining Gaps
{{list anything still failing after this iteration, with a recommendation:
continue iterating, accept as baseline, or deprecate}}

## Security Review
- Order-of-operations checklist completed: {{yes/no}}
- `scripts/security_scan.sh` findings requiring manual follow-up: {{list or "none"}}
- Blast radius (all bash/kubectl/CLI calls the skill can issue): {{list}}
