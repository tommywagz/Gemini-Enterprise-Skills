---
name: adk-long-horizon-harness
description: "Designs and operates headless, long-running ADK agents triggered by Pub/Sub events or Cloud Scheduler cron jobs, with idempotent event handling, structured logs, retries/dead-lettering, and session-context compaction. TRIGGER when users ask to 'build an event-driven ADK agent', 'run ADK on a cron schedule', 'configure Pub/Sub triggers', 'manage long-running background tasks', or use `EventsCompactionConfig`/`LlmEventSummarizer` to summarize session history. DO NOT TRIGGER for interactive single-request ADK agents, generic FastAPI endpoints without an autonomous worker, or one-time local scripts."
version: 1.0.0
author: Actual Agentic Solutions
tags: [adk, pubsub, cloud-scheduler, ambient-agents, cron, compaction]
license: Apache-2.0
compatibility: "ADK with a version-pinned ambient/background runtime; Python/FastAPI app; Google Cloud Pub/Sub and Cloud Scheduler; Bash 4+ mock launcher"
metadata: {}
---

- Headless Event & Cron Orchestrator

- Overview
This skill designs autonomous ADK work as a durable event processor, not an
interactive chat session. It specifies an authenticated ingress, base64 Pub/Sub
structured observability, and session compaction. It includes a local mock
launcher and a Cloud Scheduler Terraform template, but never deploys cloud
resources or starts a production worker without explicit approval.

- Prerequisites
- A version-pinned ADK/FastAPI application and a declared task contract.
- Pub/Sub topic/subscription or a Cloud Scheduler job owned by the deployment
team; least-privilege service accounts and an authenticated HTTP target.
- A durable idempotency/event store and a redaction policy for logs/events.

- Workflow

- Step 1: Define the event contract and ownership
Assign every event an immutable ID, source, schema version, occurred time,
tenant/user boundary, and idempotency key. The handler must acknowledge only
backoff, dead-letter topic, retention, and a human owner for poison events.
Never use an in-memory set as production idempotency storage.

- Step 2: Build authenticated ingress and bounded execution
Read `references/ambient_agents_api.md`. Verify the scheduler/Pub/Sub caller
identity before decoding payloads, enforce request-size limits, decode
`message.data` from base64, validate schema, and place work on a bounded queue.
FastAPI lifespan initializes shared clients and drains/cleans them on shutdown;
it must not launch an unbounded background task per inbound request. Log event
IDs and decisions, never raw credentials or user-sensitive payloads.

- Step 3: Make processing idempotent and failure-aware
Deduplicate before side effects and record state transitions such as received,
running, succeeded, retryable-failed, and permanently-failed. Retry only
transient faults; route deterministic validation/tool-policy failures to DLQ
with a sanitized reason. Do not retry a non-idempotent external action unless

- Step 4: Bound session history
Read `references/context_compaction_patterns.md`. Configure compaction before
the context window approaches exhaustion, retain a fixed recent-event tail,
an `LlmEventSummarizer` only after confirming its exact constructor/config
names in the installed ADK version. Summaries are lossy: never compact audit
evidence, authorization data, or a pending approval state into model-only text.

- Step 5: Test locally, then provide deployment artifacts
Run `scripts/run_ambient_worker.sh --mock-event '{"id":"e-1","task":"test"}'`.
It validates and base64-encodes a mock Pub/Sub envelope locally; it does not
call Google APIs or launch FastAPI. Fill
`assets/cloud_scheduler_cron.tf` with the authenticated endpoint and service
account, then hand it to the infrastructure owner for review. Do not run
`terraform apply` or create subscriptions from this skill.

- Examples

- Example 1: Scheduled nightly reconciliation
Use Cloud Scheduler to publish an event ID/date to Pub/Sub, deduplicate by
date/task, process with bounded concurrency, and DLQ malformed events. Report
the run ID and compact only ordinary conversation history.

- Example 2: Pub/Sub document update
Authenticate push delivery, decode only validated base64 data, persist the
event ID before calling the agent/tool, and redact document contents from logs.

- Error Handling
- Invalid base64/schema: emit sanitized validation error and DLQ; do not invoke
the agent.
- Duplicate event: return the stored terminal state; do not repeat side effects.
- Compaction failure: preserve current state and fail/retry safely; do not drop
history and continue.
- Shutdown: stop accepting work, wait a bounded time for in-flight events, then
leave incomplete work retryable in durable storage.

- Reference Files
- **references/ambient_agents_api.md**: FastAPI/Pub/Sub worker design.
- **references/context_compaction_patterns.md**: compaction safeguards.
- **scripts/run_ambient_worker.sh**: local no-network envelope mock.
- **assets/cloud_scheduler_cron.tf**: review-only Scheduler Terraform block.

- Output Format
Return event contract; auth/idempotency/DLQ design; compaction strategy;
structured logging fields; local mock result; and review-only Terraform.
