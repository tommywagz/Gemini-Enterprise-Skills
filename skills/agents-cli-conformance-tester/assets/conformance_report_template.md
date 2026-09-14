# Protocol Conformance Report (Bundled Local Suite)

**Protocol:** `[ucp | a2a]`
**Target:** `[--target-url value, or "local mock sandbox (--serve-mock <protocol>)"]`
**Suite version:** `[suite_version from assets/mock_conformance_payload.json]`
**Run at:** `[UTC timestamp]`
**Exit code:** `[0 = all must-level tests passed | 1 = at least one must-level failure | 2 = usage/connection error]`

> This report certifies the bundled MUST-level subset only. It is **not**
> equivalent to official certification — see
> `references/conformance_test_standards.md` for the gap between this suite
> and the official upstream suites (`Universal-Commerce-Protocol/conformance`
> for UCP, `a2aproject/a2a-tck` for A2A), and run those before certifying a
> deployed endpoint.

## Summary

| Level | Passed | Failed | Skipped |
|---|---|---|---|
| must | `[n]` | `[n]` | `[n]` |
| should | `[n]` | `[n]` | `[n]` |
| may | `[n]` | `[n]` | `[n]` |

**Recommendation:** `[BLOCK -- one or more must-level failures below must be fixed before this target can be considered baseline-conformant | PROCEED -- no must-level failures; review should-level findings before wider integration testing]`

## must-Level Results

> One entry per `must` test. List failures first, then passes, so the
> reader sees what's blocking before what's fine.

### `[FAIL|PASS]` `[test id]` — `[description]`
- **Request:** `[method] [path]`
- **Expected:** `[summary of the expect block]`
- **Observed:** `[actual status code and relevant JSON excerpt]`
- **Why it matters:** `[one line, from conformance_test_standards.md if not obvious]`

_(repeat per must-level test)_

## should-Level Results

> Failures here do not block the recommendation above, but call out any
> local exception the target owner has stated (e.g. "signatures
> intentionally off in dev") rather than silently downgrading the finding.

### `[FAIL|PASS|SKIPPED]` `[test id]` — `[description]`
- **Observed:** `[...]`
- **Stated local exception (if any):** `[...]`

_(repeat per should-level test)_

## may-Level Results

> Only tests whose declared capability the target actually advertised are
> listed here; capability-absent tests are silently skipped, not failed.

- `[test id]`: `[PASS|FAIL|SKIPPED — capability not advertised]`

## Next Steps

1. Fix every `must`-level failure above and re-run
   `scripts/run_conformance_suite.py` against the same target to confirm.
2. For any `should`-level failure without a stated local exception, decide
   and record whether it's an intentional deviation or a real gap.
3. Before treating this target as conformant for a staging/production
   audience, run the official upstream suite that matches the protocol —
   see `references/conformance_test_standards.md` §1.1 (UCP) or §2.1 (A2A)
   for exact invocation.
4. If this run used `--serve-mock` (the reference sandbox, not a real
   target), re-run against the real implementation with `--target-url`
   before drawing any conclusion about it.
