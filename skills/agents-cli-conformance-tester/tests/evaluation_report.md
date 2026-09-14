# Skill Evaluation Report: agents-cli-conformance-tester

**Date:** 2026-09-14
**Evaluator:** evaluator
**Iteration:** 1 (of 3)

## Summary

Ship. The dependency-free, loopback-only UCP/A2A pre-flight suite passed its
UCP and A2A mock integrations and every routing test. This pass tightened
loopback validation to require HTTP(S) and exclusively loopback DNS answers,
and corrected references that overstated the available CLI options and checks.

## Risk Tier

**Medium**

The only executable is a standard-library HTTP client/server constrained to
loopback targets; it has no credentials, privileged CLI operations, or
non-loopback network path.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---|---|---|
| Trigger Precision | > 90% | 100% | 100% | PASS |
| Trigger Recall | > 85% | 100% | 100% | PASS |
| False Positive Rate | < 5% | 0% | 0% | PASS |
| Task Completion Rate | > 80% | 100% | 100% | PASS |
| Token Usage | < 5,000 | ~2,200 | ~2,200 | PASS |
| Step Error Rate | baseline | 0% | 0% | baseline |
| Reference Hit Rate | baseline | 100% | 100% | baseline |
| Time to Completion | baseline | < 1 second mock run | < 1 second mock run | baseline |

The routing metrics were computed by `score_eval_suite.py` from 20 balanced
cases (10 should-trigger and 10 should-not-trigger); all 20 observable
assertions passed.

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---:|---|
| Output Quality - Accuracy | 4 | Clearly distinguishes pre-flight results from certification. |
| Output Quality - Completeness | 4 | Covers UCP and A2A HTTP+JSON; intentionally excludes full upstream scope. |
| Output Quality - Clarity | 5 | Exit codes, severity, and handoff conditions are explicit. |
| Output Quality - Formatting | 5 | JSON/JUnit and a report template are defined. |
| Instruction Fidelity | 5 | Prerequisites, ordered steps, decisions, and errors are actionable. |
| Edge Case Handling | 5 | Invalid schemes, remote hosts, inaccessible targets, and auto-detection failures are handled. |
| Coexistence | 5 | Explicitly routes authoring and official certification to dedicated skills/tools. |
| User Trust | 4 | Limits and the non-certification boundary are prominent; no independent user study ran. |

## Production Checklist Status

All applicable description, body, reference, validation, and security items
pass. The 20-case routing suite and integration checks are included under
`tests/`. An A/B no-skill study and independent SME review were not available;
they are non-blocking evidence gaps rather than self-asserted completions.

## Findings & Fixes Applied

| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | `localhost` was accepted without checking its resolved addresses; non-HTTP URLs could reach the HTTP client. | Require HTTP(S), resolve host addresses, and accept only an all-loopback answer set. | `scripts/run_conformance_suite.py` |
| 2 | Sandbox reference promised an unsupported `--mock-timeout` option. | Documented the actual per-request timeout and daemon-thread behavior. | `references/local_mock_sandbox.md` |
| 3 | UCP idempotency and A2A AgentCard descriptions did not match their actual assertions. | Aligned reference wording with suite behavior. | `references/conformance_test_standards.md` |
| 4 | The suite JSON declared itself to be a JSON Schema while containing suite data. | Removed the misleading `$schema` declaration. | `assets/mock_conformance_payload.json` |

## Remaining Gaps

The bundled suite is intentionally a local smoke test, not UCP or A2A
certification. It does not cover UCP's full lifecycle or A2A gRPC, streaming,
and authenticated extended cards; users targeting staging or production must
run the named official upstream suite.

## Security Review

- Order-of-operations checklist completed: yes.
- `security_scan.sh` findings requiring manual follow-up: `urllib`/HTTP hits
  are reachable only through loopback-validated HTTP(S) targets; no privileged
  CLI, traversal, or credential findings.
- Blast radius: runs Python's local mock HTTP server and sends HTTP(S) requests
  only to addresses that resolve entirely to loopback; optionally writes the
  requested JSON or JUnit report path. No irreversible operations exist.

## Integration Evidence

- `--serve-mock ucp --format junit`: 7 must passes, 1 should pass, 1 expected
  signature-check skip, exit 0.
- `--serve-mock a2a --format json`: 3 must passes, 2 should passes, exit 0.
- Remote HTTPS and `file://` target inputs were rejected with exit 2.
- Python syntax compilation and suite JSON validation passed.
