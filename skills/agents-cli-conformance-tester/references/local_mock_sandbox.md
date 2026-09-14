# Local Mock Sandbox: Design, Lifecycle, and Network Boundary Policy

`scripts/run_conformance_suite.py` can operate in two modes. Both are local
by construction; neither ever makes an outbound call past the loopback
interface.

## Table of Contents
- [1. Mode A: Test a Real Local Target](#1-mode-a-test-a-real-local-target)
- [2. Mode B: Serve a Reference Mock and Self-Test](#2-mode-b-serve-a-reference-mock-and-self-test)
- [3. Sandbox Lifecycle](#3-sandbox-lifecycle)
- [4. Network Boundary Policy](#4-network-boundary-policy)
- [5. Why a Mock Sandbox at All](#5-why-a-mock-sandbox-at-all)

---

## 1. Mode A: Test a Real Local Target

`--target-url http://127.0.0.1:<port>` — the script acts purely as a client:
it sends the requests defined in `assets/mock_conformance_payload.json` to
the user's own running UCP merchant server or A2A host agent, and scores
the responses. Nothing is "spun up" in this mode except the requests
themselves; the process the user is testing is theirs, already running,
before the script is invoked.

## 2. Mode B: Serve a Reference Mock and Self-Test

`--serve-mock ucp` or `--serve-mock a2a` — the script starts a minimal,
**reference-correct** HTTP server on an OS-assigned ephemeral loopback port
using only `http.server.HTTPServer` and `threading.Thread(daemon=True)`,
then runs the exact same suite against it. This is the literal "local mock
sandbox": a stand-in counterparty (the role a real buyer platform plays
against a UCP merchant server, or a real remote caller plays against an A2A
agent) good enough to exercise the assertions end-to-end without requiring
any real implementation to already exist.

Use this mode for two things:
1. **Baseline sanity check.** Run it once after installing this skill to
   confirm the harness itself is not the source of a failure — a clean
   `--serve-mock` run proves the suite and scorer work; a subsequent
   failure against `--target-url` is then attributable to the real target.
2. **Learning the expected shape.** Read the mock's handler code
   (`_MockUcpHandler` / `_MockA2aHandler` in the script) as a minimal,
   correct reference implementation of the endpoints this suite checks —
   useful when a real target's failure isn't obviously wrong and a
   side-by-side comparison of "what did the mock return here" clarifies it.

The mock server is intentionally minimal: it hardcodes exactly the fields
the bundled suite checks (see `references/conformance_test_standards.md`)
and nothing more. It is not a usable starting point for a real merchant
server or agent — for that, use the `ucp-merchant-servers` or
`a2a-workflows` skills.

## 3. Sandbox Lifecycle

1. Bind `HTTPServer(("127.0.0.1", 0), handler_cls)` — port `0` asks the OS
   for any free ephemeral port, so the sandbox never collides with a
   real server the user may also have running, and never claims a
   well-known port that could be mistaken for a production listener.
2. Start the server in a daemon thread so an uncaught exception in the
   parent process cannot leave an orphaned listener behind.
3. Run the full suite against `http://127.0.0.1:<assigned-port>`.
4. Call `server.shutdown()` and `server.server_close()` in a `finally`
   block — the sandbox is torn down whether the suite passed, failed, or
   raised, and before the script exits or prints its report.
5. The server uses the request client's 10-second per-request timeout, and
   the daemon thread ensures process exit is never blocked if a request
   cannot complete.

## 4. Network Boundary Policy

- **Loopback only, both directions.** `--target-url` is validated before
  any request is sent: it must use HTTP(S), and every resolved address must
  be a loopback address (`127.0.0.0/8` or `::1`). Any other host — a LAN IP,
  a public domain, a cloud staging URL, or a hostname with mixed loopback
  and non-loopback answers — is rejected with a clear error before a single
  byte is sent. This skill is a local dev-loop and CI pre-flight tool, not a
  general-purpose HTTP conformance client; testing a deployed/staging/
  production endpoint is explicitly out of scope (use the official suites
  in `references/conformance_test_standards.md` §1.1/§2.1 for that, which
  are designed for exactly this and document their own auth/secret handling).
- **No third-party calls.** The mock server in Mode B never makes an
  outbound request of its own — it only answers the inbound requests this
  script sends it. Neither mode resolves DNS for anything other than the
  loopback aliases above.
- **No real credentials.** The mock's stand-in signatures, tokens, and
  simulation secrets are fixed test strings living in
  `assets/mock_conformance_payload.json`. Never point `--target-url` at a
  target while passing it real production API keys, signing keys, or
  payment credentials — this suite has no secret-handling story beyond
  what a local dev server already does for itself.
- **No file writes outside the report path.** The script writes only to
  the `--out` path the caller specifies (default: stdout). It does not
  create databases, temp directories, or log files elsewhere.

## 5. Why a Mock Sandbox at All

Without Mode B, a first-time user has no way to distinguish "the suite is
broken" from "my server is broken" the first time they see a failure. A
sandbox that is provably correct (because this skill's own author wrote and
tested it against the same assertions) gives a fast, zero-dependency
reference point — and it means the suite itself can be exercised in this
skill's own validation/CI without standing up a real UCP or A2A
implementation at all.
