# Skill Evaluation Report: adk-cross-session-knowledge-bank

**Date:** 2026-09-11
**Evaluator:** evaluator
**Iteration:** 1 of 3

## Summary

Ship. The 20-case routing suite scored 100% precision and recall with no
false positives. Offline seed and scoped recall integrations passed; real
persistent writes now require an explicit `--confirm-write` after dry-run.

## Metrics

| Metric | Target | Result | Status |
|---|---|---|---|
| Trigger Precision | > 90% | 100% (10/10) | PASS |
| Trigger Recall | > 85% | 100% (10/10) | PASS |
| False Positive Rate | < 5% | 0% (0/10) | PASS |
| Task Completion Rate | > 80% | 100% (3/3 paths) | PASS |
| Step Error Rate | baseline | 0% | Baseline |
| Reference Hit Rate | baseline | 100% | Baseline |

## Security

**High risk.** Real-mode scripts call the Vertex AI API and can persist or
retrieve Confidential user memory. They have no credentials embedded; writes
are guarded by dry-run guidance and `--confirm-write`. Scanner path matches
are documentation URL ellipses, not reachable traversal behavior.

## Fixes

- Added `--confirm-write` enforcement for real persistent writes.
- Added JSON-object validation for both scope inputs.
- Added a 20-case balanced routing suite and offline seed/recall fixture.

## Evidence

- `preload_memory.py --dry-run` validated two facts without importing Vertex AI.
- `load_memory.py --dry-run --as-prompt` rendered only the matching scoped fact.
- Invalid array scope input fails with exit-2 validation behavior.
- Python compilation and schema JSON validation passed.

External ADK/Vertex SME review remains recommended before production handling
of sensitive user data.
