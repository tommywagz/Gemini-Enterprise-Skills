# Skill Evaluation Report: ucp-consumer-surface

**Date:** 2026-09-16
**Evaluator:** evaluator
**Iteration:** 1 (of 3)

## Summary

Ship after one refinement pass. The description passed the default 20-case
routing evaluation, and the self-contained client lifecycle test passed all
21 checks. The pass corrected missing safeguards at the irreversible order
boundary, inbound signed-webhook boundary, and retry idempotency boundary.

## Risk Tier

**High**

The helper intentionally issues HTTPS requests to a caller-selected UCP
business endpoint and can complete an order; it has no hardcoded credentials,
path traversal, privileged CLI operations, or data-exfiltration behavior.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---:|---:|---|
| Trigger Precision | > 90% | 100% | 100% | PASS |
| Trigger Recall | > 85% | 100% | 100% | PASS |
| False Positive Rate | < 5% | 0% | 0% | PASS |
| Task Completion Rate | > 80% | 100% | 100% | PASS |
| Token Usage | < 5,000 | 1,676 words | 1,768 words | PASS |
| Step Error Rate | baseline | 0/21 checks | 0/21 checks | Baseline |
| Reference Hit Rate | baseline | 3/3 integration paths | 3/3 integration paths | Baseline |
| Time to Completion | baseline | Not measured | Not measured | Baseline |

Routing results were generated with `score_eval_suite.py`: 10 TP, 10 TN, 0 FP,
and 0 FN. Integration coverage was the in-process discovery-to-order lifecycle,
confirmation rejection, authority validation, idempotency-key preservation, and
webhook verification/replay/tamper rejection.

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---:|---|
| Output Quality - Accuracy | 4 | Bound to cited UCP sources; live merchant compatibility remains untested. |
| Output Quality - Completeness | 5 | Covers discovery, catalog guidance, cart, checkout, order tracking, and webhooks. |
| Output Quality - Clarity | 5 | Ordered workflow and explicit state/error branches. |
| Output Quality - Formatting | 5 | Standard frontmatter and scannable references. |
| Instruction Fidelity | 5 | Tests cover the prescribed lifecycle and refusal branches. |
| Edge Case Handling | 5 | Covers absent capabilities, business errors, retries, untrusted schemas, and bad webhooks. |
| Coexistence | 5 | Explicitly defers merchant-server, extension, and AP2 mandate work. |
| User Trust | Not independently measured | Requires external user study. |

## Production Checklist Status

Passed: specific trigger and anti-trigger language; under-150-word description;
20-case trigger evaluation; under-5,000-token body; prerequisites, ordered
decision branches, error handling, anti-patterns, output contract, and cited
domain material; independently tested script; tables of contents for long
references; asset and reference fallback documentation; integration and red-team
coverage; assessed risk tier; minimal Python stdlib tool set; input validation;
no hardcoded credentials; Confidential data classification; and explicit buyer
confirmation before irreversible checkout completion.

Open validation items: no A/B comparison against a no-skill control and no
independent SME review were available. These are recorded as release follow-up,
not fabricated as completed evidence.

## Findings & Fixes Applied

| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | Signed webhooks were only parsed, not cryptographically verified. | Require a caller-supplied verifier for any signature and reject missing required signatures/verifiers. | `scripts/ucp_client_helper.py`, `SKILL.md` |
| 2 | Completion could issue an irreversible order without a confirmation gate or handler allow-list. | Require current-profile handler IDs and explicit buyer confirmation; add rejection test. | `scripts/ucp_client_helper.py`, `SKILL.md` |
| 3 | Caller could not reuse an idempotency key for a retry. | Thread optional `idempotency_key` through state-changing methods and regression-test preservation. | `scripts/ucp_client_helper.py`, `SKILL.md` |

## Remaining Gaps

Use a production cryptographic verifier callback backed by a validated business
profile and run an interoperability test against a real sandbox merchant before
deployment. Obtain independent UCP SME review and an A/B routing study.

## Security Review

- Order-of-operations checklist completed: yes.
- `scripts/security_scan.sh` findings requiring manual follow-up: expected
  `urllib` external UCP calls only; no credentials, traversal, or privileged
  command findings.
- Blast radius: `discover` sends a GET to the explicit business base URL;
  state-changing helper methods send POST/PUT requests to the resolved endpoint;
  `complete_checkout` can place an order only after explicit confirmation and
  current-profile handler validation. The self-test uses a loopback in-process
  mock server only.
