# Polyglot workspace patterns

## Contents
- [Architecture](#architecture)
- [Public application contract](#public-application-contract)
- [ADK wire contract](#adk-wire-contract)
- [State and lifecycle](#state-and-lifecycle)
- [Credential-free verification](#credential-free-verification)
- [Sources and compatibility](#sources-and-compatibility)

## Architecture

```text
caller -- POST /api/message --> Hono (Node)
       -- create session, POST /run --> ADK API server (Python)
       -- planner -> session.state['draft'] -> writer
       <-- final model text <-- event array
```

Use the HTTP boundary to let each runtime retain its package ecosystem. Hono
owns request validation and translating ADK events into a small response.
Python owns agent definitions, credentials, sessions, and workflow ordering.
Never spawn `python` once per web request or share Python objects across Node.
The generated `SequentialAgent` guarantees planner-before-writer; ADK's
`output_key='draft'` makes the planner's final text available to the writer's
`{draft}` instruction. This is an explicit starter workflow, to be adapted to
the user's goal. Each LLM stage is a separate provider call.

## Public application contract

`POST /api/message` accepts only `{"text":"..."}`. Text must contain
non-whitespace, be 1–8000 JavaScript UTF-16 code units, and fit within the 64 KiB
body limit. `contracts/message.schema.json` documents this shape; JSON Schema
counts Unicode code points, so the runtime's length check is conservative for
astral characters. Response: `{"sessionId":"uuid","text":"final text"}`.
Unknown request keys, empty text, and malformed JSON are 400, oversized bodies
are 413. The contract schema is documentation; Hono performs explicit runtime
validation rather than executing a JSON Schema interpreter.

The gateway's trusted `ADK_BASE_URL` configuration is an HTTP(S) origin. The
request cannot select it or a model/app/user ID. HTTP redirects are rejected.
Only the most recent non-partial model text event is returned; planner text,
function-call arguments, and thought-marked parts are not combined into the
user-facing answer. ADK error events and missing text are treated as failures.

## ADK wire contract

For app folder `orchestrator`, the gateway sends:

1. `POST /apps/orchestrator/users/local-developer/sessions/<uuid>` with `{}`.
2. `POST /run` with:

```json
{
  "appName": "orchestrator",
  "userId": "local-developer",
  "sessionId": "same-uuid",
  "newMessage": {"role": "user", "parts": [{"text": "user input"}]}
}
```

The second call returns an array of events, not a single chat-completion
object. `content.role='model'` and `content.parts[].text` identify candidate
text. Folder/app name, Python agent name, and gateway app constant are generated
together. Keeping these in sync prevents the common “app not found” failure.

## State and lifecycle

Every request gets a new UUID session under a local-demo user ID. This avoids
session-create conflicts and concurrent writes to one session. It also means
there is no conversation continuity. Sessions accumulate until the development
store is cleaned up; no persistence guarantee is made by this starter.
For a multi-user service, bind user/session IDs to authenticated identity and
implement ownership, expiry, and cleanup before offering a history endpoint.

Both listeners default to loopback and are development services. Hono's
`/health` is process liveness only. Readiness requires checking ADK's
`/list-apps`; end-to-end readiness requires `/api/message`. Neither process
supervises the other. A gateway timeout or disconnect does not guarantee
cancellation of an ADK invocation. There are no automatic POST retries.

## Credential-free verification

`WORKSPACE_DEMO=1` substitutes two deterministic `BaseAgent` steps inside the
same `SequentialAgent`, ADK API server, and session machinery. The first step
stores text through `EventActions.state_delta`; the second yields a model-role
event with `DEMO: <input>`. This tests real Python-to-Node integration without
calling a model. Live mode instead constructs two `LlmAgent` instances and uses
the selected model. API credentials stay in Python's environment.

## Sources and compatibility

Official sources reviewed 2026-09-14 (no task-specific URLs were supplied):
- [Hono Node.js adapter](https://hono.dev/docs/getting-started/nodejs):
  `serve({fetch, port})`, TypeScript build, and server shutdown.
- [ADK Python quickstart](https://google.github.io/adk-docs/get-started/python/):
  `agent.py`, `__init__.py`, exported `root_agent`, model credentials.
- [ADK API server](https://google.github.io/adk-docs/runtime/api-server/):
  session creation, `/list-apps`, `/run` and camelCase JSON examples.
- [Sequential agents](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/):
  ordered sub-agents and `output_key` state transfer.
- [Custom agents](https://google.github.io/adk-docs/agents/custom-agents/):
  `BaseAgent._run_async_impl`, yielded `Event` and state updates.

Templates pin ADK 1.18.0 as a tested compatibility baseline. Current docs also
describe ADK 2.x graph workflows; do not mix those new APIs into this pinned
starter without upgrading and rerunning integration tests. The CLI command
guide lists exact direct dependency versions; pinning transitives for a
deployment remains the generated project's dependency-management step.
