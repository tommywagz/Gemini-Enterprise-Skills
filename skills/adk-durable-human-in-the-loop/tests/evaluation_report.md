# Skill Evaluation Report: adk-durable-human-in-the-loop

**Date:** 2026-09-14
**Evaluator:** evaluator
**Iteration:** 1 (of 3)

## Summary

Ship after one refinement. The skill cleanly routes durable ADK approval and
resume work while excluding synchronous input and memory tasks. The resume
handler was corrected so a failed downstream `/run_sse` request does not mark
the approval resolved and prevent a retry.

## Risk Tier

**High**

The bundle contains webhook and ADK API-server network calls. It contains no
path traversal, hardcoded credentials, or adversarial instructions; inbound
decisions require schema validation, HMAC verification, record matching, and
expiry checks before a resume request is sent.

**Data classification:** Confidential, because the workflow handles a shared
HMAC secret supplied through an environment variable.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---|---|---|
| Trigger Precision | > 90% | 1.00 | 1.00 | PASS |
| Trigger Recall | > 85% | 1.00 | 1.00 | PASS |
| False Positive Rate | < 5% | 0.00 | 0.00 | PASS |
| Task Completion Rate | > 80% | 1.00 | 1.00 | PASS |
| Token Usage | < 5,000 | 2,238 | 2,238 | PASS |
| Step Error Rate | baseline | 0.00 | 0.00 | baseline |
| Reference Hit Rate | baseline | 1.00 | 1.00 | baseline |
| Time to Completion | baseline | local | local | baseline |

The 20-case routing suite has 10 trigger and 10 anti-trigger cases. It scored
TP=10, FP=0, TN=10, FN=0 using `score_eval_suite.py`.

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---|---|
| Output Quality - Accuracy | 4 | Resume payload, signature, and matching requirements are explicit. |
| Output Quality - Completeness | 4 | Covers generation, resume, replay, expiry, and retry behavior. |
| Output Quality - Clarity | 5 | Ordered workflow and exact commands are provided. |
| Output Quality - Formatting | 5 | Standard frontmatter, headings, and reference links are present. |
| Instruction Fidelity | 5 | Generated files, validation, and resume flow match the documented process. |
| Edge Case Handling | 5 | Invalid signatures, unknown or expired tickets, replay, and downstream failure are handled. |
| Coexistence | 5 | Explicitly defers same-turn input and cross-session memory work. |
| User Trust | 4 | Strong safeguards; production ingress rate limiting remains deployment work. |

## Production Checklist Status

Passed: specific trigger and anti-trigger wording; 20-case routing suite;
documented prerequisites, branches, errors, outputs, asset formats, and
fallbacks; independent script checks; integration and adversarial tests;
High-risk assessment; minimal declared tool set; input validation; no embedded
credentials; Confidential data classification; signed approval workflow.

Remaining non-blocking validation gaps: no independent domain-expert review
or A/B study against a no-skill baseline was available in this local run.

## Findings & Fixes Applied

| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | A failed downstream resume marked the ticket resolved before delivery, blocking a safe retry. | Mark the ticket resolved only after `/run_sse` returns successfully in the CLI resume path and HTTP receiver. | `scripts/resume_workflow.py` |

## Security Review

- Order-of-operations checklist completed: yes.
- `security_scan.sh` findings requiring manual follow-up: external webhook and local/remote ADK API calls. They are intentional, signed for inbound decisions, and documented with production ingress requirements.
- Blast radius: generator writes only to a user-selected empty directory; `resume` and `serve` can POST only after valid signed input; generated projects can POST signed outbound approval webhooks. No destructive cloud or repository command is included.

## Test Evidence

- `python3 -m py_compile` passed for both bundled scripts and all generated Python files.
- Generator dry-run and real generation succeeded.
- Both JSON schemas parsed successfully.
- Signed dry-run resume produced the expected `/run_sse` body.
- An invalid HMAC was rejected.
- A deliberately unavailable local ADK server returned an error while preserving the pending ticket for retry.
