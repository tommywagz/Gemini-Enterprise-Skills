# Skill Evaluation Report: agents-cli-plugin-moderator

**Date:** 2026-09-17
**Evaluator:** evaluator
**Iteration:** 3 (of 3)

## Summary

Ship. The complete bundle was reviewed, the local Model Armor decision harness passed all seven cases, and the 20-case routing suite met the default targets. One wording correction now accurately scopes outbound exfiltration scanning to configured outbound tools rather than all tools.

## Risk Tier

**High**

The bundle contains a local loopback HTTP mock and documents live regional Model Armor REST endpoints; it has no credential, real external call, high-privilege CLI, or reachable path-traversal behavior.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---:|---:|---|
| Trigger Precision | > 90% | 100% | 100% | PASS |
| Trigger Recall | > 85% | 100% | 100% | PASS |
| False Positive Rate | < 5% | 0% | 0% | PASS |
| Task Completion Rate | > 80% | 100% | 100% | PASS |
| Token Usage | < 5,000 | 1,746 words | 1,746 words | PASS |
| Step Error Rate | baseline | 0% | 0% | baseline |
| Reference Hit Rate | baseline | 100% (4/4) | 100% (4/4) | baseline |
| Time to Completion | baseline | 1 local pass | 1 local pass | baseline |

`score_eval_suite.py` result: 20 graded; TP=10, FP=0, TN=10, FN=0; assertion pass rate=100%.

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---:|---|
| Output Quality - Accuracy | 4 | Separates Model Armor verdicts from availability failures and documents regional endpoints. |
| Output Quality - Completeness | 5 | Covers prompt, response, tool, and session-state gates with config and validation. |
| Output Quality - Clarity | 5 | Ordered steps, explicit branches, and concrete snippets. |
| Output Quality - Formatting | 5 | Standard frontmatter, headings, and reference links. |
| Instruction Fidelity | 5 | The documented selftest and independent ad hoc prompt/response checks passed. |
| Edge Case Handling | 5 | Handles inspect-only, fail modes, bad callback return values, duplicate templates, and wrong endpoints. |
| Coexistence | 4 | Anti-triggers distinguish GCP IaC, local callbacks, and generic moderation; routing was checked against adjacent skills. |
| User Trust | 4 | Clear guardrails and explicit no-live-call boundary; production rollout still needs traffic baselining. |

## Production Checklist Status

- [x] Level 1 description is specific, anti-triggered, under 150 words, and tested with 20 cases.
- [x] Level 2 body is within budget and defines prerequisites, ordered decisions, errors, output, and sources.
- [x] Level 3 script was independently tested; references over 100 lines have contents lists; asset and fallback boundaries are documented.
- [x] Validation includes routing, simulator integration, and adversarial prompts.
- [ ] A/B comparison with and without the skill is not practical in this static evaluation.
- [ ] Independent ADK/Model Armor SME review is not recorded.
- [x] Security risk tier, declared minimal tool boundary, input validation, credential absence, Confidential data classification, and approval boundary are addressed. The skill does not perform irreversible actions.

## Findings & Fixes Applied

| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | The description implied exfiltration scanning at every tool call, while the workflow correctly scopes scanning to configured outbound tools. | Scoped the description and overview to model boundaries and configured outbound tools. | `SKILL.md` |
| 2 | The skill handles PII and credential-shaped data but did not declare the required data classification. | Declared Confidential handling and prohibited logging raw matched values. | `SKILL.md` |
| 3 | The body referred to its bundled references but lacked an explicit unavailable-reference fallback. | Added a stop-and-obtain-versioned-documentation fallback. | `SKILL.md` |

## Remaining Gaps

Run an A/B routing comparison and obtain ADK/Model Armor SME review before a production rollout. Start live deployments in `inspect_only` and measure false positives before enabling blocking.

## Security Review

- Order-of-operations checklist completed: yes.
- `security_scan.sh` findings requiring manual follow-up: documentation URLs and `urllib` were reviewed. The simulator binds only to `127.0.0.1`; path-traversal hits are API wildcard notation, not filesystem paths.
- Blast radius: `python3 scripts/simulate_moderation_violation.py` starts a loopback-only mock HTTP server and makes loopback HTTP requests. The skill instructs local code/config edits only; it does not provision cloud resources, call live APIs, or execute destructive commands.
