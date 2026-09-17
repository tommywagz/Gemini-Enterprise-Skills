# Context Compaction Patterns

Compaction prevents unbounded event/session history from overrunning the model
context window. Trigger it at a configurable token threshold below the model
maximum, retain a fixed recent tail for immediate continuity, and store a
summary plus provenance outside the prompt. Re-evaluate thresholds using real
token telemetry after deployment.

`EventsCompactionConfig` and `LlmEventSummarizer` names are version-dependent:
verify their exact installed ADK API before implementation. A safe policy is:
preserve immutable event IDs, tool outcomes, approvals, authorization scope,
and audit data verbatim in durable storage; summarize only conversational or
low-risk narrative context. If summarization fails, retain source events and
retry/fail safely rather than deleting them.
