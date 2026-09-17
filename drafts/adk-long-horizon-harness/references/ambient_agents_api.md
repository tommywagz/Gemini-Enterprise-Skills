# Ambient Agent Ingress Patterns

Use FastAPI lifespan (`@asynccontextmanager`) for shared client initialization
and shutdown cleanup. Keep request handlers thin: authenticate caller, enforce
size/schema limits, decode event data, persist/deduplicate, enqueue bounded
work, and return the protocol-appropriate acknowledgement. Do not spawn an
unbounded `asyncio.create_task` per request.

Pub/Sub push envelopes carry base64 in `message.data`; decode with
`base64.b64decode(..., validate=True)`, then UTF-8 decode and JSON/schema
validate before agent work. Record `messageId`, publish time, subscription,
and correlation ID. Configure retry and dead-letter policy outside application
code; application failures must be classified transient vs permanent.

Pin the ADK version and consult its runtime API for exact ambient-agent runner
calls. Keep agent invocation behind an adapter so ingress, idempotency, and
observability remain testable independently of ADK API changes.
