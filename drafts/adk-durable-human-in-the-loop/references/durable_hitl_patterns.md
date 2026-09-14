# Durable HITL Patterns: Suspension, State-Holding Webhooks, and Signed Resume

This is the architecture reference for the parts ADK does **not** provide
out of the box: publishing a state-holding payload to an external system
when a node pauses, and safely verifying + routing a signed reply back to
resume the exact right invocation. ADK gives you the pause/resume primitive
(`references/adk_graph_hitl_api.md`); everything here is the application
layer this skill scaffolds around it.

## Table of Contents
- [1. Why LongRunningFunctionTool, not Tool Confirmation](#1-why-longrunningfunctiontool-not-tool-confirmation)
- [2. The state-holding webhook](#2-the-state-holding-webhook)
- [3. Signature verification on resume](#3-signature-verification-on-resume)
- [4. Idempotency and at-least-once tool execution](#4-idempotency-and-at-least-once-tool-execution)
- [5. Matching a reply to the right invocation](#5-matching-a-reply-to-the-right-invocation)
- [6. Timeouts, expiry, and re-notification](#6-timeouts-expiry-and-re-notification)
- [7. Threat model for the resume endpoint](#7-threat-model-for-the-resume-endpoint)

---

## 1. Why LongRunningFunctionTool, not Tool Confirmation

ADK's Tool Confirmation feature (`require_confirmation=`,
`tool_context.request_confirmation()`) is the more ergonomic-looking API for
a yes/no or structured approval gate. It is explicitly documented as
**not supported** with `DatabaseSessionService` or `VertexAiSessionService`
— the only two session services that survive a process restart. A "durable"
approval gate built on Tool Confirmation would only be durable until the
process hosting it restarts, which is precisely the failure mode a durable
gate exists to survive (deploy, crash, scale-to-zero). `LongRunningFunctionTool`
carries no such documented restriction, so it is this skill's default. If a
future ADK release lifts the Tool Confirmation restriction, re-evaluate —
its structured-payload ergonomics (`tool_confirmation.payload`) are
otherwise a good fit.

## 2. The state-holding webhook

When `ask_for_approval` (or your equivalently named tool) fires, it must
**not** block waiting for the human — it starts the external workflow and
returns immediately with a pending status (§2 of
`references/adk_graph_hitl_api.md`). "Starting the external workflow" means
POSTing a payload matching `assets/approval_webhook_schema.json` to the
dashboard/notification system. That payload is the durable, state-holding
record: everything needed to resume this exact invocation must be in it
(or in a store keyed by its `ticket_id`), because the process that sent it
may not be the process that receives the reply.

Required fields (see the schema for the full set and types):
- `ticket_id` — your own correlation ID, stable across restarts. Generate
  it in the tool, not in the webhook sender, so it exists even if the
  webhook POST itself fails and needs a retry.
- `function_call_id` — the exact `function_call.id` ADK assigned to this
  tool call (from `event.long_running_tool_ids` / the matching
  `function_call` part). This is what must come back verbatim in the
  `function_response.id` on resume (§4 of `adk_graph_hitl_api.md`) —
  losing or regenerating it breaks resume silently (ADK starts a new
  invocation instead of resuming, per that doc's warning).
- `invocation_id`, `session_id`, `user_id`, `app_name` — the four
  coordinates needed to call `runner.run_async(...)` or hit `/run_sse`
  again later, from a possibly-different process.
- `requested_at` (ISO-8601 UTC) and an optional `expires_at` — see §6.
- `hint` / `payload` — the human-readable ask and any structured context
  (amount, purpose, requester) the dashboard should render.

**Persist the webhook payload (or at least its correlation fields) to your
own durable store** (a row in the same database backing
`DatabaseSessionService`, or a separate table) before or atomically with
sending it. If the webhook POST succeeds but your process crashes before
persisting, the human's eventual reply has nothing to match against.

## 3. Signature verification on resume

The reply channel is untrusted network input — treat it exactly like any
other external webhook receiver:

- Sign the **outbound** webhook payload with an HMAC-SHA256 over the
  canonical JSON (sorted keys, no whitespace) using a secret only your
  service and the dashboard share. This lets the dashboard prove to *its*
  users that the approval request is genuine, and is optional if the
  dashboard is a fully trusted internal system reachable only over an
  authenticated channel.
- Require the **inbound** resume payload (`assets/approval_response_schema.json`)
  to carry an HMAC-SHA256 signature over its own canonical JSON, keyed by
  the same (or a separate, reply-specific) shared secret. `scripts/resume_workflow.py`
  verifies this with `hmac.compare_digest` (constant-time) before doing
  anything else — never `==` on signature strings (timing side-channel).
- Reject (don't silently drop) a reply whose `ticket_id` isn't in your
  pending-approvals store, whose signature doesn't verify, or whose
  `expires_at` has passed. Log the rejection with enough context to
  investigate (source IP, ticket_id, reason) without logging the secret or
  the raw signature.
- Rotate the shared secret via an environment variable /
  secret-manager reference, never hardcoded — `scripts/resume_workflow.py`
  reads it from `--secret-env-var` (default `HITL_WEBHOOK_SECRET`), not a
  CLI flag, so it never appears in shell history or process listings.

## 4. Idempotency and at-least-once tool execution

ADK's own Resume feature documentation is explicit: resuming a workflow
runs tools **at least once**, and may run a tool more than once on resume.
Two implications for an approval gate:

1. **The approval-request tool itself** (`ask_for_approval`) may fire more
   than once for the same logical request if the *initiating* invocation
   is itself resumed before the human replies (e.g. the process crashed
   between the tool call and the webhook POST). Make ticket creation
   idempotent — derive `ticket_id` deterministically from stable inputs
   (e.g. a hash of `invocation_id` + tool call site), or check for an
   existing open ticket for the same `function_call_id` before creating a
   new one.
2. **The resume handler must be idempotent too.** A dashboard or human may
   double-click "Approve," or your webhook receiver may retry on a 5xx.
   `scripts/resume_workflow.py` treats a resume call for an already-resolved
   `ticket_id` as a no-op success (logged, not re-sent to the runner) rather
   than erroring or double-resuming.

## 5. Matching a reply to the right invocation

Never trust a resume payload's self-reported `invocation_id` /
`function_call_id` in isolation — cross-check them against what you stored
for that `ticket_id` in §2. A payload should carry all of `ticket_id`,
`invocation_id`, and `function_call_id` for a resume, and the handler
should reject (not "repair") a mismatch between the stored record and the
inbound values — a mismatch is either a bug in the dashboard integration or
an attempted replay/confusion attack, and either way silently trusting the
inbound values is the wrong failure mode.

## 6. Timeouts, expiry, and re-notification

A durable gate can wait indefinitely, but most real approval workflows
shouldn't. Two independent concerns:

- **Expiry**: `expires_at` in the webhook payload is advisory to the
  dashboard/human, but also enforce it server-side in the resume handler —
  reject a reply that arrives after expiry with a clear "ticket expired,
  re-request" response rather than silently resuming a stale approval.
- **Re-notification / escalation**: this skill's scaffold does not
  implement a scheduler for reminder pings or escalation to a backup
  approver — that is deployment-specific (a cron job, a Cloud Scheduler
  trigger, a queue consumer polling `pending_approvals` for tickets past
  some age). Document the gap rather than guessing a scheduling mechanism;
  wire it to whatever job scheduler the host application already uses.

## 7. Threat model for the resume endpoint

The resume endpoint is a webhook receiver exposed to (at minimum) your
dashboard's server, and possibly the public internet if the dashboard is
external. Treat it accordingly:
- Require the shared-secret signature (§3) on every request — no
  unauthenticated resume path, even "just for local dev" (use a
  fixed local-only secret for dev instead of disabling verification).
- Validate the inbound JSON against `assets/approval_response_schema.json`
  before touching any of its fields — malformed input should fail fast
  with a 400, not propagate into the runner call.
- Rate-limit or otherwise bound retries per `ticket_id` at your ingress
  (load balancer / API gateway) — this skill's script does not implement
  rate limiting itself.
- Never log the full inbound payload at a level that could leak an
  approver's identity or the shared secret; log the `ticket_id` and outcome
  (`approved`/`rejected`/`rejected: bad signature`/`rejected: expired`) at
  minimum.
