# Skill Evaluation Report: agents-cli-benchmark-eval

**Date:** 2026-09-17  
**Evaluator:** evaluator  
**Iteration:** 2 (of 3)

## Summary

Ship. The standard-library runner now rejects malformed datasets before executing a configured command. The command-mode fixture passed 4/4 cases, routing passed 20/20 cases, and the bundle supplies ordered safety, metric, and reporting guidance.

## Risk Tier

**Medium**

The bundle contains local scripts that run a supplied local command with `shell=False`; no network client, credentials, high-privilege CLI, or path traversal is present.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---:|---:|---|
| Trigger Precision | > 90% | 100% | 100% | PASS |
| Trigger Recall | > 85% | 100% | 100% | PASS |
| False Positive Rate | < 5% | 0% | 0% | PASS |
| Task Completion Rate | > 80% | 100% | 100% | PASS |
| Token Usage | < 5,000 | 936 words | 961 words | PASS |
| Step Error Rate | baseline | 0% | 0% | baseline |
| Reference Hit Rate | baseline | 100% (4/4) | 100% (4/4) | baseline |

Routing scorer: 20 graded, TP=10, FP=0, TN=10, FN=0, assertion pass rate=100%.

## Findings & Fixes Applied

| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | JSON parsing alone allowed malformed cases to fail after execution began. | Added preflight validation for required fields, types, assertion types, route flags, and risk labels. | `scripts/run_eval_and_score.py` |
| 2 | Dataset content can be sensitive and required an explicit classification. | Added Confidential data handling and a missing-reference fallback. | `SKILL.md` |

## Security Review

- Order-of-operations checklist completed: yes.
- Scanner finding: schema URI only; it is declarative, not a network call.
- Blast radius: `run_eval_and_score.py` runs a user-supplied local argv via `subprocess.run(shell=False)`, with a per-case timeout. The skill explicitly prohibits production endpoints, credentials, shell pipelines, and mutation-capable commands.

## Remaining Gaps

An independent SME review and an A/B comparison against a no-skill baseline are not recorded. Use sandbox commands for all high-side-effect cases.
