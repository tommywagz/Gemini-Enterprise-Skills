# Protocol Conformance Standards: UCP and A2A

This reference distills the checks that matter for **local, pre-flight**
conformance testing of a UCP merchant server or an A2A host/remote agent. It
covers two layers for each protocol:

1. The **official, heavyweight conformance suite** maintained by the
   protocol's own project — the authoritative source of truth, but it
   requires cloning a separate repository, installing dependencies with
   `uv`, and (for UCP) seeding a real database and a `SIMULATION_SECRET`.
2. The **bundled local suite** in `assets/mock_conformance_payload.json`,
   which this skill's `scripts/run_conformance_suite.py` executes directly
   with the Python standard library — a fast MUST-level smoke test you can
   run before touching the official suite, or in a pre-commit/CI gate where
   installing the full suite is impractical.

Passing the bundled suite is **not** equivalent to official certification.
Treat it as "safe to proceed to the real suite," not "conformant."

## Table of Contents
- [1. UCP Conformance](#1-ucp-conformance)
  - [1.1 Official Suite](#11-official-suite)
  - [1.2 Bundled MUST-Level Subset](#12-bundled-must-level-subset)
- [2. A2A Conformance](#2-a2a-conformance)
  - [2.1 Official Suite (TCK)](#21-official-suite-tck)
  - [2.2 Bundled MUST-Level Subset](#22-bundled-must-level-subset)
- [3. Shared Result Vocabulary](#3-shared-result-vocabulary)

---

## 1. UCP Conformance

### 1.1 Official Suite

Source: `github.com/Universal-Commerce-Protocol/conformance` — a pytest suite
of language-agnostic integration tests that runs HTTP requests against a
**live, running** UCP Merchant Server. Relevant facts to give a user
considering the jump from this skill to the official suite:

- **Test files** (each a pytest module, run individually or together):
  `protocol_test.py` (discovery manifest, RFC 9421 signatures),
  `binding_test.py` (REST binding shape), `checkout_lifecycle_test.py`
  (cart → checkout → complete state machine), `discount_test.py`,
  `fulfillment_test.py` / `fulfillment_structure_test.py`,
  `idempotency_test.py`, `invalid_input_test.py`, `order_test.py`,
  `totals_test.py`, `validation_test.py`, `webhook_test.py` /
  `webhook_structure_test.py`, `card_credential_test.py`, `ap2_test.py`
  (AP2 mandate bridging), `simulation_url_security_test.py`.
- **Inputs the server owner must supply:**
  - `conformance_input.json` — `ucp_version`, `required_capabilities`,
    `items` (catalog fixtures), `out_of_stock_item`, `non_existent_item`.
  - `test_fixtures.json` — exact prices, discount codes and their expected
    percentages/fixed reductions, known-customer records with stored
    addresses, free-shipping thresholds, and destination/shipping-option
    pairs for dynamic fulfillment tests. Most fields beyond the basic item
    price are **optional** and the corresponding test is skipped (not
    failed) if omitted.
  - Environment variables `SERVER_URL` and `SIMULATION_SECRET` (a shared
    secret the test suite uses to trigger deterministic simulated failure
    paths on the server, e.g. forcing an out-of-stock or payment-decline
    response).
- **Invocation:** `uv sync` once, then either
  `uv run pytest --conformance_input=... --fixture_config=...` for the full
  suite, or `uv run <file>_test.py --server_url=... --simulation_secret=...
  --conformance_input=... --fixture_config=...` for a single module.
- This is an external, network-touching, dependency-installing process —
  **do not attempt to run it from inside this skill.** If the user wants
  full official certification, point them at the repository directly (or,
  once available, the dedicated `ucp-conformance` skill that automates this
  exact handoff and turns failures into actionable fixes).

### 1.2 Bundled MUST-Level Subset

`assets/mock_conformance_payload.json`'s `"ucp"` block encodes a small,
dependency-free translation of the highest-value checks above, grouped by
the same RFC 2119 vocabulary the A2A TCK uses (see §3) so pass/fail severity
reads the same across both protocols:

- **Discovery (`must`):** `/.well-known/ucp` returns `200` with valid JSON
  and `ucp.version`, `ucp.services`, `ucp.capabilities` present; at least
  one capability's `spec` names `checkout`.
- **Cart lifecycle (`must`):** `POST /carts` with one valid line item
  returns `200`/`201` with an `id`; a nonexistent `item_id` does not crash
  the server with a `5xx`.
- **Checkout lifecycle (`must`):** `POST /checkout-sessions` with a valid
  cart returns an `id` and a `status` field; completing checkout for a
  `non_existent_item` returns a structured UCP error envelope
  (`messages[]`) with a `4xx`, never a bare `5xx` or an empty body.
- **Error envelope shape (`must`):** every `4xx` response body parses as
  JSON and contains a `messages` array with `type`, `code`, and `content`
  per §2.2 of `references/ucp-spec.md` (bundled with the
  `ucp-merchant-servers` skill) — a malformed or missing envelope is a
  `must` failure even if the status code itself is correct.
- **Signature enforcement (`should`):** a state-changing request
  (`POST /checkout-sessions`) sent *without* `Signature`/`Signature-Input`
  headers is rejected with `401`/`400` when the server advertises
  `--require_signatures`; this is `should`, not `must`, because some local
  dev servers intentionally run with signature enforcement off.
- **Idempotency (`should`):** repeating `POST
  /checkout-sessions/{id}/complete` with the same `Idempotency-Key` returns
  the same result rather than a second side effect — the bundled test can
  only check for a non-`5xx`, consistent status code on the retry; it
  cannot verify no duplicate order was created without database access,
  which is exactly the gap the official `idempotency_test.py` closes.

## 2. A2A Conformance

### 2.1 Official Suite (TCK)

Source: `github.com/a2aproject/a2a-tck` — the A2A Protocol Technology
Compatibility Kit. It validates a live "System Under Test" (SUT) across
three transports and reports results using the same RFC 2119 levels this
skill borrows:

- **Transports:** `grpc`, `jsonrpc`, `http_json` — selected automatically
  from the `supportedInterfaces` declared in the SUT's own AgentCard, or
  filtered explicitly with `--transport`.
- **Levels:** `must` (hard failure if unmet), `should` (recorded as
  `xfail`, does not block compatibility), `may` (skipped unless the agent
  declares the optional capability).
- **Invocation:** `./run_tck.py --sut-host http://localhost:9999` after
  `uv pip install -e .` in a clone of the repo; `--level must` narrows to
  blocking requirements only.
- **Reports:** written to `reports/` every run —
  `compatibility.json` (machine-readable, per-requirement/per-transport),
  `compatibility.html`, `tck_report.html` (pytest-html), and
  `reports/junitreport.xml` for CI integration.
- Like the UCP suite, this is an external, dependency-installing process.
  Do not attempt to shell out to a cloned TCK checkout from inside this
  skill's script — point the user at the repository, or at the SUT code
  generator (`make codegen-a2a-python-sut`, etc.) if they are also
  authoring the agent itself.

### 2.2 Bundled MUST-Level Subset

`assets/mock_conformance_payload.json`'s `"a2a"` block covers the
HTTP+JSON transport only (the one this skill's stdlib-only script can speak
without a gRPC stub or JSON-RPC client library):

- **AgentCard (`must`):** `GET /.well-known/agent-card.json` returns `200`
  with `name`, `description`, and `version` present, and at least one
  entry under the interfaces/capabilities structure described in
  `references/a2a-spec.md` §2.1 (bundled with the `a2a-workflows` skill).
- **SendMessage RPC (`must`):** a `message/send` JSON-RPC call returns a
  `200` with a top-level `result` object — either a `Task` or a `Message`
  — never a bare transport-level error for a well-formed request.
- **Unknown task handling (`must`):** `GetTask` for a fabricated task `id`
  returns a structured JSON-RPC error object (`error.code`,
  `error.message`), not an unhandled `500` with a stack trace leaked into
  the response body.
- **TaskState enum discipline (`should`):** whenever a response includes
  `result.status.state`, its value is one of the eight documented
  `TaskState` values (`submitted`, `working`, `completed`, `failed`,
  `canceled`, `rejected`, `input-required`, `auth-required`) — an
  unrecognized state string is flagged as a `should` failure since it is
  the single most common source of A2A host/sub-agent interop breakage.

Multi-transport (gRPC), streaming (`SendStreamingMessage`/SSE), and
extended-card-after-auth checks are explicitly **out of scope** for the
bundled suite — they require client capabilities beyond
`urllib.request`. Route those to the official TCK.

## 3. Shared Result Vocabulary

Both bundled blocks label each test with the same RFC 2119-derived `level`
the A2A TCK uses, so a combined report reads consistently:

| Level | Meaning | Script behavior |
| --- | --- | --- |
| `must` | Absolute requirement | A failure makes the overall run exit non-zero |
| `should`| Expected, but a documented local exception is plausible | A failure is reported but does not flip the run's exit code |
| `may` | Optional; only relevant if the target advertises the capability | Skipped automatically when the target's discovery document doesn't mention it |

Never upgrade a `should`/`may` finding to a blocking failure in a report
without saying so explicitly — that miscommunicates the bundled suite's own
declared severity.
