---
name: agents-cli-conformance-tester
description: "Spins up a local, dependency-free mock sandbox to run a MUST/SHOULD/MAY-leveled conformance suite against a loopback-bound UCP merchant server or A2A host/remote agent, printing a JSON or JUnit compliance summary. TRIGGER for \"run UCP conformance tests\", \"verify A2A compliance of my local server\", \"agents-cli test-compliance\", \"check protocol compatibility\", or a mock sandbox to smoke-test a local merchant server or agent. DO NOT TRIGGER for standard PyTest/Vitest unit-testing or generic linting; DO NOT TRIGGER for a remote/staging/production (non-loopback) endpoint -- use the official Universal-Commerce-Protocol/conformance or a2aproject/a2a-tck suites for those; DO NOT TRIGGER for authoring a new UCP server or A2A agent from scratch (use ucp-merchant-servers or a2a-workflows first)."
version: 1.0.0
author: Actual Agentic Solutions
tags: [ucp, a2a, conformance, testing, protocol, cli, mock-sandbox]
license: Apache-2.0
compatibility: "Python 3.9+ standard library only (argparse, http.server, urllib) -- no pip install required; tests a running local UCP merchant server or A2A host/remote agent over HTTP"
metadata: {}
---

- Protocol Conformance Scanner

- Overview
This skill answers "does my local UCP merchant server or A2A agent even
look right, before I install the real, heavyweight conformance suite and
wire up test databases and secrets?" It bundles a small, curated,
RFC 2119-leveled (`must`/`should`/`may`) subset of the checks the *official*
upstream suites perform, and runs them with nothing but the Python standard
library against a strictly loopback-bound target. It can also spin up its
own minimal, reference-correct HTTP server -- a local mock sandbox standing
in for a real merchant/agent -- to self-test the harness or to show what a
passing response looks like.

This is a fast pre-flight gate, not a certification. A clean run here means
"safe to move on to the real suite," not "officially conformant." The two
official suites this skill complements are `Universal-Commerce-Protocol/
conformance` (UCP, pytest-based, needs seeded test data and a
`SIMULATION_SECRET`) and `a2aproject/a2a-tck` (A2A, multi-transport, needs a
cloned repo and `uv`) -- see `references/conformance_test_standards.md` for
exactly how the bundled subset maps onto each, and when the gap matters
enough to justify running the real thing.

- Prerequisites
- Python 3.9+ available to run `scripts/run_conformance_suite.py` (standard
  library only).
- Either a UCP merchant server or A2A host/remote agent already running
  locally and reachable at a `127.0.0.1`/`::1`/`localhost` URL, **or** no
  target at all if only exercising the bundled `--serve-mock` sandbox.
- **Tool boundary:** this script only ever talks to loopback addresses. It
  refuses any `--target-url` whose host does not resolve to `127.0.0.1`,
  `::1`, or `localhost` before sending a single request -- see
  `references/local_mock_sandbox.md` §4 for the full network boundary
  policy. Never pass real production credentials, signing keys, or payment
  tokens as part of a run; nothing in this suite has a secret-handling
  story beyond what the target's own local dev configuration provides.
- **Data classification:** Public/Local-test-only. All fixtures in
  `assets/mock_conformance_payload.json` are synthetic and safe to reuse
  across runs and CI.

- Workflow

- Step 1: Decide what you're testing
Ask (or infer from context) which protocol and which mode:
- **A real local target:** confirm the base URL (e.g.
  `http://127.0.0.1:8182` for a UCP server, `http://127.0.0.1:9999` for an
  A2A agent) and that it is actually running before Step 2 -- a target
  that isn't listening yet will just produce "connection error" failures
  for every test, which is correctly reported but not useful.
- **No real target yet, or first time using this skill:** use
  `--serve-mock ucp` or `--serve-mock a2a` instead. This is the "local mock
  sandbox" the routing description refers to: a minimal, reference-correct
  stand-in server this skill starts, tests against, and tears down in one
  process, with no setup required.

- Step 2: Run the suite
```
scripts/run_conformance_suite.py --target-url http://127.0.0.1:8182 --protocol ucp
scripts/run_conformance_suite.py --target-url http://127.0.0.1:9999 --protocol a2a
scripts/run_conformance_suite.py --serve-mock ucp
scripts/run_conformance_suite.py --serve-mock a2a
```
Omit `--protocol` (default `auto`) to let the script probe
`/.well-known/ucp` then `/.well-known/agent-card.json` and pick whichever
responds `200` -- pass it explicitly if the target exposes both or neither
convincingly. Add `--level must` to see only blocking requirements, or
`--format junit --out reports/junit.xml` for CI integration matching the
official suites' own JUnit output convention.

- Step 3: Read the exit code before the JSON
`0` = every `must`-level test passed. `1` = at least one `must`-level
failure -- read the `results` array for the specific `id`s and `reason`s.
`2` = usage error, unreadable suite file, or a rejected (non-loopback)
target -- **never** treat exit `2` as "0 findings"; fix the invocation and
re-run rather than reporting a clean bill of health.

- Step 4: Triage by level, not just pass/fail count
- Every `must` failure blocks the recommendation (`BLOCK` in the report).
  Fix the target and re-run before doing anything else with it.
- A `should` failure is worth a look but is not blocking on its own --
  check whether it's a stated local exception (e.g. "I run signature
  enforcement off in dev") before treating it as a real gap. A `should`
  test with outcome `SKIPPED` (not `FAIL`) usually means the target didn't
  advertise the relevant capability at all (see
  `UCP-SIG-001`'s `skip_if_json_path_absent` behavior in
  `references/conformance_test_standards.md` §1.2) -- that is expected,
  not a finding to chase.
- `may`-level tests are skipped automatically when the target doesn't
  advertise the optional capability; don't report a `may` skip as a gap.

- Step 5: Compile the report
Copy `assets/conformance_report_template.md` and fill it in from the JSON
output's `summary` and `results`. If the run used `--serve-mock`, say so
explicitly in the report header -- a clean mock-sandbox run says nothing
about the user's real implementation.

- Step 6: Point at the real suite when it matters
If the target is headed for a staging or production audience, or the user
explicitly wants official certification, don't stop at this skill's
report. Read `references/conformance_test_standards.md` §1.1 (UCP) or §2.1
(A2A) and hand off to the matching official suite with its exact
invocation and required inputs (`conformance_input.json`/
`test_fixtures.json` for UCP; `./run_tck.py --sut-host ...` for A2A).

- Examples

- Example 1: First-time user, no server running yet
Input: "I just want to see this conformance tool work before I point it at
anything."
Expected output / behavior: run
`scripts/run_conformance_suite.py --serve-mock ucp` (or `a2a`), get a
`PROCEED` recommendation with all `must`-level tests passing against the
built-in reference mock, and explain that this validates the harness, not
any real server.

- Example 2: Smoke-testing a local UCP merchant server mid-development
Input: "Here's my UCP server on localhost:8182, is it in decent shape?"
Expected output / behavior: run
`scripts/run_conformance_suite.py --target-url http://127.0.0.1:8182 --protocol ucp`,
report any `must`-level failures with the exact endpoint and expected vs.
observed status, note any `should`-level signature/idempotency gaps, and
recommend running the official `Universal-Commerce-Protocol/conformance`
suite next if the target is close to shippable.

- Example 3: A remote/staging URL is offered
Input: "Can you run this against https://staging.example.com?"
Expected output / behavior: refuse -- `--target-url` only accepts loopback
hosts -- and explain that staging/production endpoints belong to the
official upstream suites (`references/conformance_test_standards.md`
§1.1/§2.1), which are designed for exactly that and handle auth/secrets
this bundled suite deliberately does not.

- Error Handling
- `run_conformance_suite.py` exits `2`: usage error, an unreadable/invalid
  `--suite` file, a target URL that failed the loopback check, or a
  `--protocol auto` probe that got no `200` from either well-known path.
  Show the stderr message; do not retry with a broadened scan (e.g. never
  fall back to testing a non-loopback host).
- Every test fails with `"connection error: ..."`: the target isn't
  listening on that host/port yet, or is listening on a different
  interface. Confirm the server is up before concluding it's
  non-conformant.
- A `should`-level test unexpectedly fails against a target that *does*
  advertise the relevant capability (e.g. `keys` is non-null but no
  signature enforcement is observed): this is a legitimate finding, not a
  harness bug -- report it as a `should` gap, not a `must` failure.
- The bundled suite passes but the target still misbehaves in ways the
  official suite catches (e.g. incorrect discount math, stored-address
  handling): that's expected -- see
  `references/conformance_test_standards.md` for the explicit list of
  what the bundled MUST-level subset does *not* cover.

- Reference Files
- **scripts/run_conformance_suite.py**: the whole tool -- loopback
  enforcement, suite execution against a real target or the built-in mock
  sandbox, JSON/JUnit report rendering. Run in Step 2.
- **references/conformance_test_standards.md**: what each bundled test
  checks and why, how it maps to the official
  `Universal-Commerce-Protocol/conformance` and `a2aproject/a2a-tck`
  suites, and the shared `must`/`should`/`may` vocabulary -- read before
  triaging results in Step 4, or before handing off to the official suite
  in Step 6.
- **references/local_mock_sandbox.md**: the two run modes, the mock
  server's lifecycle (ephemeral loopback port, daemon thread, guaranteed
  teardown), and the full network boundary policy -- read before running
  `--serve-mock`, or if asked why a given host was rejected.
- **assets/mock_conformance_payload.json**: the canonical, versioned test
  assertions and fixtures the script loads at runtime -- the single source
  of truth if a test's expectation ever needs to change. Never hardcode a
  new check directly in the script instead of adding it here.
- **assets/conformance_report_template.md**: fill-in-the-blanks report
  structure -- copy it in Step 5 rather than inventing a report format ad
  hoc.
- If a referenced script or asset is missing, stop and report the skill as
  incomplete; do not re-derive test assertions from memory or silently
  skip the loopback check.

- Output Format
Return, in order: (1) which mode was used (real target vs. `--serve-mock`)
and the exit code, (2) the `must`-level results with any failures listed
first, (3) the `should`/`may`-level results with skip reasons where
relevant, (4) the overall `BLOCK`/`PROCEED` recommendation, and (5) an
explicit note if official upstream certification is still outstanding.
Never state or imply "conformant" from a bundled-suite pass alone, and
never report a `--serve-mock` run as evidence about a real implementation.
