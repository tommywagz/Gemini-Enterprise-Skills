---
name: adk-durable-human-in-the-loop
description: "Scaffolds and explains a durable, asynchronous Human-in-the-Loop (HITL) approval gate for ADK agent workflows: pauses a node via LongRunningFunctionTool, publishes a signed state-holding webhook to an external dashboard, and resumes the exact paused invocation via ADK's /run_sse resume contract once a signed decision arrives. TRIGGER when the user asks to \"add a workflow approval gate in ADK\", \"suspend/pause ADK graph execution for human input\", \"implement human sign-off\" or \"durable human-in-the-loop\" for an ADK agent, \"resume a paused ADK invocation\", \"integrate ADK asynchronous resume\", or needs ResumabilityConfig / LongRunningFunctionTool / a signed approval webhook. DO NOT TRIGGER for synchronous same-turn clarification via request_input or a graph RequestInput node with no cross-process durability need, ADK Tool Confirmation used purely in-memory, or cross-session agent memory (use adk-cross-session-knowledge-bank)."
version: 1.0.0
author: Actual Agentic Solutions
tags: [adk, human-in-the-loop, hitl, approval-gate, durable-workflow, webhook, resumability]
license: Apache-2.0
compatibility: "google-adk >= 2.0.0 for LongRunningFunctionTool/App; >= 1.16.0 for ResumabilityConfig. Generated projects additionally need `requests`. scripts/ themselves (generate_hitl_workflow.py, resume_workflow.py) require only the Python standard library -- jsonschema is optional, for stricter validation."
metadata: {}
---

- ADK Durable Human-in-the-Loop Approval Gates

- Overview
This skill scaffolds a Human-in-the-Loop approval gate for ADK agents that
must survive more than one process's lifetime: the agent pauses mid-task,
an external system (a dashboard, Slack app, ticketing tool) is durably
notified via a signed webhook, and — possibly hours or days later, possibly
from a different process or machine entirely — a signed decision resumes
the exact paused invocation. This is deliberately narrower than "ask the
user a question": ADK's built-in `request_input` tool and graph
`RequestInput` nodes already handle same-turn, same-process clarification
well and this skill is not needed for that (see Do Not Trigger above).

Grounded directly in `adk.dev`'s Resume, Tool Confirmation, and Long
Running Function Tool docs (fetched while building this skill — re-verify
against the current `google-adk` release before depending on this for a
production pipeline, since this surface is still evolving). The single
most important, non-obvious finding from that research: ADK's more
ergonomic-looking Tool Confirmation feature is **explicitly documented as
unsupported** with `DatabaseSessionService` or `VertexAiSessionService` —
the only two session services that survive a process restart. This skill
therefore builds the durable gate on `LongRunningFunctionTool` instead,
which carries no such documented restriction. See
`references/adk_graph_hitl_api.md` §1 and §6 before reaching for Tool
Confirmation on a "durable" requirement.

- Prerequisites
- `pip install google-adk` (>= 2.0.0) for the generated project to actually
  run; none of this skill's own `scripts/` require it.
- A persistent `SessionService` target for production use
  (`DatabaseSessionService` DSN or `VertexAiSessionService` config) — the
  generator defaults to local SQLite, which is durable across restarts but
  not across machines.
- A shared HMAC secret between this service and the external
  dashboard/reviewer, delivered via an environment variable — never a CLI
  flag or a committed file (see `references/durable_hitl_patterns.md` §3).
- Decide, before scaffolding, whether the approval is genuinely
  cross-process/cross-restart durable (this skill) or same-turn
  clarification (point the user at `request_input` / graph `RequestInput`
  instead, per `references/adk_graph_hitl_api.md` §1's comparison table).

- Workflow

- Step 1: Confirm the durability requirement, then pick the primitive
Ask (or infer from context) whether the pause must survive a process
restart. If yes — the common case for "approval gate," "sign-off," "review
before proceeding" — proceed with `LongRunningFunctionTool` per this
skill. If the user only needs a same-turn question answered before the
turn continues, redirect to ADK's plain `request_input` tool or a graph
`RequestInput` node (§1 and §5 of `references/adk_graph_hitl_api.md`) —
building the full webhook + signed-resume machinery for that case is
unnecessary complexity.

- Step 2: Generate the project skeleton
```
scripts/generate_hitl_workflow.py --output-dir ./my_approval_agent --dry-run
```
Review the file list, then re-run without `--dry-run` (add `--app-name`,
`--tool-name`, `--agent-name`, `--model`, `--webhook-url`, and
`--secret-env-var` to match the target system — defaults are reasonable for
a first pass). This produces `agent.py` (the `LlmAgent` +
`LongRunningFunctionTool` + resumable `App`), `hitl_support.py` (ticket
recording + signed webhook dispatch), `service.py` (a `DatabaseSessionService`
run loop that detects the pause), `README.md`, and `requirements.txt`. Never
hand-write this scaffold from scratch — the exact field names in the
generated ticket record must match `scripts/resume_workflow.py`'s
`PendingStore` (Step 4 reuses that script unmodified).

- Step 3: Customize the approval tool for the real use case
Edit the generated `agent.py`'s tool function to carry whatever domain
fields the approval actually needs (amount, requester, links, risk level)
in its `payload` argument to `record_ticket_and_notify` — do not remove the
call to `record_ticket_and_notify` itself or change the ticket record's
field names, since `resume_workflow.py` depends on them verbatim (see that
script's own docstring and `references/durable_hitl_patterns.md` §2 and
§5).

- Step 4: Wire the resume side — reuse, don't reimplement
Do not write a new signature-verification/resume handler per project.
Point this skill's own `scripts/resume_workflow.py` at the generated
project's `pending_approvals.json`:
```
scripts/resume_workflow.py serve --pending-store ./my_approval_agent/pending_approvals.json \
    --secret-env-var HITL_WEBHOOK_SECRET --adk-server-url http://localhost:8000 --port 8787
```
or, for a one-shot resume from a decision file the dashboard produced:
```
scripts/resume_workflow.py resume --input-file decision.json \
    --pending-store ./my_approval_agent/pending_approvals.json \
    --secret-env-var HITL_WEBHOOK_SECRET --dry-run   # review before sending
```
Every inbound decision must validate against
`assets/approval_response_schema.json` and its HMAC signature before this
script will touch the runner — a rejection is not a bug to work around by
hand-crafting a bypass.

- Step 5: Verify before calling it durable
Run the dry-run chain end-to-end once with no real ADK server or dashboard:
(a) call the generated tool with a stub `tool_context` and confirm a ticket
lands in `pending_approvals.json`; (b) hand-build a signed decision payload
and run `resume_workflow.py resume --dry-run` against it, confirming the
printed `/run_sse` body has the right `invocation_id`,
`function_response.id`, and `session_id`; (c) confirm a bad signature, an
unknown `ticket_id`, and a resolved-ticket replay are each rejected or
no-op'd, not silently accepted. Only after this passes should the user
point `--adk-server-url` at a real running `adk api_server`.

- Examples

- Example 1: New expense-approval agent
Input: "I need my ADK reimbursement agent to pause and wait for finance
approval before finalizing anything over $500, even if the service
restarts overnight."
Expected output / behavior: run Step 2 with `--tool-name ask_for_approval
--webhook-url <finance dashboard ingest URL>`, customize the tool per Step
3 to include `amount` and `requester` in the payload, wire
`resume_workflow.py serve` per Step 4 behind the finance dashboard's
outbound integration, and walk through the Step 5 dry-run chain before
connecting a real dashboard.

- Example 2: User only wants a same-turn confirmation
Input: "Before the agent deletes the file, just ask the user yes or no in
the same conversation."
Expected output / behavior: redirect to ADK's tool-level
`require_confirmation=True` (in-memory, same-session) or a graph
`RequestInput` node per `references/adk_graph_hitl_api.md` §1's comparison
table — do not scaffold the full durable webhook pipeline for a need that
does not cross a process boundary.

- Error Handling
- User wants "durable" HITL built on Tool Confirmation
  (`require_confirmation=`/`request_confirmation`): explain the documented
  `DatabaseSessionService`/`VertexAiSessionService` restriction
  (`references/adk_graph_hitl_api.md` §6) before proceeding — steer to
  `LongRunningFunctionTool` instead rather than building on a primitive
  that silently loses durability.
- `resume_workflow.py resume`/`serve` rejects with "signature verification
  failed": the shared secret differs between the sender and
  `--secret-env-var`, or the payload was mutated after signing (the
  signature covers the canonical JSON of every other field) — never add a
  bypass flag; fix the signing side.
- Rejects with "unknown ticket_id": the pending-approvals store path is
  wrong, the ticket was recorded against a different store file, or this
  is a replay/spoofed `ticket_id` — investigate before assuming it's a
  path typo.
- Resuming twice for the same ticket: this is handled as an idempotent
  no-op (see `references/durable_hitl_patterns.md` §4) and is not an
  error — do not "fix" this by making the second call resend to the
  runner.
- `generate_hitl_workflow.py` refuses to write: `--output-dir` already
  exists and is non-empty — confirm with the user before ever removing an
  existing directory to make room.
- A resumed invocation doesn't continue where expected: check that
  `invocation_id` was included and matches the original invocation exactly
  (`references/adk_graph_hitl_api.md` §4) — omitting it or supplying a
  stale value starts a **new** invocation instead of resuming, which ADK
  does silently rather than erroring.

- Reference Files
- **references/adk_graph_hitl_api.md**: the three ADK pause mechanisms
  compared, the exact `/run_sse` resume payload contract, the
  session-service durability matrix, and the graph `RequestInput`
  alternative for same-process pauses — read in Step 1 and whenever the
  exact resume wire format is needed.
- **references/durable_hitl_patterns.md**: the application-layer design
  this skill's scripts implement — why `LongRunningFunctionTool` over Tool
  Confirmation, webhook payload design, signature verification, at-least-once
  tool execution and idempotency, ticket matching, expiry, and the resume
  endpoint's threat model — read in Steps 3-5 and whenever a security or
  durability "why" question comes up.
- **scripts/generate_hitl_workflow.py**: scaffolds the agent-side project
  (`agent.py`, `hitl_support.py`, `service.py`) — run in Step 2.
- **scripts/resume_workflow.py**: verifies, matches, and resumes (or
  `serve`s a webhook endpoint for) signed decision payloads against any
  generated project's `pending_approvals.json` — run in Steps 4-5, reused
  as-is rather than regenerated per project.
- **assets/approval_webhook_schema.json**: canonical schema for the
  outbound, signed state-holding webhook — the generated `hitl_support.py`
  and `resume_workflow.py record-ticket --emit-webhook` both produce
  payloads matching this shape.
- **assets/approval_response_schema.json**: canonical schema for the
  inbound, signed decision payload — `resume_workflow.py` validates every
  decision against this before touching the runner.

- Output Format
Return, in order: (1) which pause mechanism applies and why (durable
`LongRunningFunctionTool` vs. a same-turn `request_input`/`RequestInput`
redirect, per Step 1), (2) the exact `generate_hitl_workflow.py` command
used and the resulting file tree, (3) the exact `resume_workflow.py`
command(s) for the resume side, and (4) confirmation that the Step 5
dry-run chain was exercised — including at least one deliberately-rejected
case (bad signature or unknown ticket) — before calling the gate durable.
Never claim an approval gate is "durable" without having verified the
resume path survives a fresh process (a new `resume_workflow.py` invocation
reading the same `pending_approvals.json`), not just the same Python
session it was created in.
