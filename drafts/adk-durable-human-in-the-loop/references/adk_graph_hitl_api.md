# ADK HITL & Resume API Cheatsheet

> Requires `google-adk >= 2.0.0` for graph HITL nodes (`RequestInput`),
> `google-adk >= 1.16.0` for the Resume feature (`ResumabilityConfig`),
> `google-adk >= 1.14.0` for Tool Confirmation. Python examples; the
> mechanics carry over to TypeScript/Go/Java/Kotlin per the official docs
> linked below. Grounded directly in `adk.dev` (fetched for this skill,
> re-verify against the live docs before depending on this for a production
> pipeline — ADK's resume/HITL surface is still evolving fast).

**Official docs:** [Human input](https://adk.dev/graphs/human-input/index.md) ·
[Resume stopped agents](https://adk.dev/runtime/resume/index.md) ·
[Action confirmations](https://adk.dev/tools-custom/confirmation/index.md) ·
[Long running function tools](https://adk.dev/tools-custom/function-tools/index.md#long-run-tool) ·
[API Server](https://adk.dev/runtime/api-server/index.md)

## Table of Contents
- [1. Three ways to pause for a human](#1-three-ways-to-pause-for-a-human)
- [2. LongRunningFunctionTool (the durable-approval-gate primitive)](#2-longrunningfunctiontool-the-durable-approval-gate-primitive)
- [3. Enabling durable resume](#3-enabling-durable-resume)
- [4. Resuming over REST](#4-resuming-over-rest)
- [5. Graph RequestInput nodes](#5-graph-requestinput-nodes)
- [6. Session service durability matrix](#6-session-service-durability-matrix)
- [7. Events you need to detect a pause](#7-events-you-need-to-detect-a-pause)

---

## 1. Three ways to pause for a human

| Mechanism | Where it lives | Resume payload | Survives process restart? |
|---|---|---|---|
| `LongRunningFunctionTool` | Any `FunctionTool` inside an `LlmAgent` | `FunctionResponse` matched by `function_call.id` | **Yes** — no session-service restriction documented. Use this for the durable approval-gate pattern. |
| Tool Confirmation (`require_confirmation=` / `tool_context.request_confirmation()`) | Any `FunctionTool` | `FunctionResponse` named `adk_request_confirmation` | **No** — `DatabaseSessionService` and `VertexAiSessionService` are explicitly unsupported for this feature (see §6). In-memory only. |
| Graph `RequestInput` node | A `Workflow` node (`google.adk.events.RequestInput`) | Framework-managed `resume_inputs` keyed by `interrupt_id` | Undocumented for cross-process resume; treat as same-process/session-lifetime only unless you've verified otherwise against a current build. |

**This skill defaults to `LongRunningFunctionTool` for the durable case** because
it is the only one of the three with both (a) a documented, exact REST resume
payload and (b) no documented session-service restriction. Use a graph
`RequestInput` node only for a same-process, short-lived pause inside a
`Workflow` (§5) — do not use it as the durability primitive for an
externally-signed webhook approval gate.

## 2. LongRunningFunctionTool (the durable-approval-gate primitive)

```python
from typing import Any
from google.adk.tools import LongRunningFunctionTool

def ask_for_approval(purpose: str, amount: float) -> dict[str, Any]:
    """Ask for approval for the reimbursement."""
    # Create a ticket, publish the state-holding webhook (see
    # references/durable_hitl_patterns.md §2), and return an initial,
    # non-final result. The agent run then pauses.
    return {
        "status": "pending",
        "approver": "finance-team",
        "purpose": purpose,
        "amount": amount,
        "ticket-id": "approval-ticket-1",
    }

approval_tool = LongRunningFunctionTool(func=ask_for_approval)
agent = Agent(name="approval_agent", model="gemini-flash-latest",
              instruction="Use ask_for_approval before finalizing any spend over $500.",
              tools=[approval_tool])
```

**Lifecycle:**
1. LLM calls `ask_for_approval`. Your function starts the external
   workflow (creates a ticket, POSTs the webhook) and returns an initial
   dict — no blocking I/O inside the tool itself.
2. ADK packages that initial dict into a `FunctionResponse`, ends the agent
   run, and marks the call in `event.long_running_tool_ids`.
3. Your application (not the agent) later receives the human's decision
   (via the resume webhook you built, §4) and re-invokes `runner.run_async`
   with an updated `FunctionResponse` carrying the final decision.
4. The framework routes that response back to the LLM as if the tool had
   just returned it, and the agent continues.

**Extracting the pending call from a live run** (needed once, to capture
`function_call.id` / `ticket-id` for later matching):

```python
def get_long_running_function_call(event):
    if not event.long_running_tool_ids or not event.content or not event.content.parts:
        return None
    for part in event.content.parts:
        if (part.function_call and part.function_call.id in event.long_running_tool_ids):
            return part.function_call
```

## 3. Enabling durable resume

```python
from google.adk.apps import App, ResumabilityConfig

app = App(
    name="approval_gate_app",
    root_agent=agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)
```

Pair this with a persistent `SessionService` (`DatabaseSessionService` or
`VertexAiSessionService` — see §6) so the paused invocation survives a
process restart, not just an in-process `await`.

## 4. Resuming over REST

The exact, documented payload for resuming a `LongRunningFunctionTool`
pause via the ADK API server (`adk api_server`) — this is what
`scripts/resume_workflow.py` builds and sends:

```bash
curl -X POST http://localhost:8000/run_sse \
 -H "Content-Type: application/json" \
 -d '{
    "app_name": "approval_gate_app",
    "user_id": "user",
    "session_id": "7828f575-2402-489f-8079-74ea95b6a300",
    "invocation_id": "invocation-123",
    "new_message": {
        "parts": [
            {
                "function_response": {
                    "id": "adk-13b84a8c-c95c-4d66-b006-d72b30447e35",
                    "name": "ask_for_approval",
                    "response": {"status": "approved", "ticket-id": "approval-ticket-1"}
                }
            }
        ],
        "role": "user"
    }
}'
```

Requirements (all enforced by `scripts/resume_workflow.py` before it will
send this):
- `function_response.id` **must** equal the `function_call.id` from the
  original `long_running_tool_ids` event — not the ticket ID, not a new
  UUID. Your webhook payload (`assets/approval_webhook_schema.json`) must
  carry this ID through so the resume handler can echo it back.
- If `ResumabilityConfig(is_resumable=True)` is set, `invocation_id` is
  **required** on the resume call — the same invocation that generated the
  original request. Omitting it starts a **new** invocation instead of
  resuming the paused one, which silently drops the pending state.
- `name` matches the original tool's function name (`ask_for_approval`
  above), not a fixed constant (unlike `adk_request_confirmation` for Tool
  Confirmation — see §1's row for that mechanism).

Equivalent in-process call (no HTTP hop, e.g. when your resume handler
lives in the same Python process as the runner):

```python
async for event in runner.run_async(
    user_id="user", session_id="s_abc", invocation_id="invocation-123",
    new_message=types.Content(
        role="user",
        parts=[types.Part(function_response=updated_response)],  # a genai.types.FunctionResponse
    ),
):
    ...
```

## 5. Graph RequestInput nodes

For a **same-process, short-lived** pause inside a graph `Workflow` (not the
durable webhook case — see §1's caveat), use `RequestInput`:

```python
from google.adk.events import RequestInput
from google.adk.workflow import node

@node(rerun_on_resume=False)
async def get_user_approval(ctx, node_input):
    yield RequestInput(message="Please approve this request (Yes/No)",
                        payload=node_input, response_schema=UserFeedback)

@node(rerun_on_resume=True)  # required: this node calls ctx.run_node
async def handle_process(ctx, node_input):
    reply = await ctx.run_node(get_user_approval, node_input)
    if reply.interrupt_ids:   # check BEFORE using reply.output — see gotcha below
        return None
    return "Approved" if reply.output.lower() == "yes" else "Denied"
```

**Gotcha:** `ctx.run_node()` does not raise on interruption — it returns
normally with `interrupt_ids` populated and `output` still unset. Skipping
that check and using `reply.output` directly treats "no answer yet" as an
answer. `rerun_on_resume=True` is required on any orchestrator node calling
`ctx.run_node()`; the leaf `RequestInput` node itself defaults to
`rerun_on_resume=False` (handoff — the reply becomes its output directly).

## 6. Session service durability matrix

| `SessionService` | Durable across restart? | Works with Tool Confirmation? | Works with `LongRunningFunctionTool`? |
|---|---|---|---|
| `InMemorySessionService` | No (dev only) | Yes | Yes |
| `DatabaseSessionService` | Yes | **No — documented limitation** | Yes (no restriction documented) |
| `VertexAiSessionService` | Yes | **No — documented limitation** | Yes (no restriction documented) |

This is the load-bearing reason this skill builds the approval gate on
`LongRunningFunctionTool` rather than Tool Confirmation: Tool Confirmation
is the more ergonomic API, but it is explicitly unsupported with the only
two session services that survive a process restart — which defeats
"durable" entirely. Re-verify this restriction against the current ADK
release before depending on it; the docs mark Tool Confirmation as
*Experimental*.

## 7. Events you need to detect a pause

Your workflow-runner wrapper (`scripts/generate_hitl_workflow.py`'s
generated `service.py`) must watch the event stream for the pause signal
rather than assuming the run always completes:

```python
async for event in runner.run_async(user_id=uid, session_id=sid, new_message=content):
    if event.long_running_tool_ids:
        call = get_long_running_function_call(event)   # §2
        # This is your cue to publish the webhook (references/durable_hitl_patterns.md §2)
        # instead of waiting for a final response that will never come this run.
```

`Runner.run_async` (or the `/run_sse` endpoint) returns/streams normally
when a `LongRunningFunctionTool` pauses — it does not hang. The absence of
`event.is_final_response()` combined with a populated
`event.long_running_tool_ids` is what tells you the invocation is now
durably parked, waiting on the tool response you'll deliver via
`scripts/resume_workflow.py`.
