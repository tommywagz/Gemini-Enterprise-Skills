# ADK BasePlugin Patterns for Safety Guardrails

## Contents
- Plugin vs. Agent Callback (why Plugins for safety)
- Full BasePlugin hook table with exact signatures
- Return-value semantics: Observe / Intervene / Amend
- Worked GuardrailPlugin skeleton
- ADK's layered defense model
- Session state integrity (session-poisoning-adjacent guidance)

Source: `google.github.io/adk-docs/plugins/`, `google.github.io/adk-docs/safety/`,
`google.github.io/adk-docs/callbacks/types-of-callbacks/`, and
`google/adk-python` `src/google/adk/plugins/base_plugin.py` (fetched 2026-09-16).

## Plugin vs. Agent Callback

| | Plugin | Agent Callback |
|---|---|---|
| Scope | **Global** — every agent/tool/model the `Runner` manages | **Local** — only the specific agent instance it's set on |
| Registration | Once, on the `Runner`: `Runner(agent=..., plugins=[...])` | Per agent: `LlmAgent(before_model_callback=...)` |
| Execution order | Plugin hooks run **before** any Agent/Model/Tool callback | Runs after all plugin hooks |
| Use case | Horizontal concerns: logging, policy, security guardrails, caching | Agent-specific logic |

A coordinator with several sub-agents needs the plugin form: one instance
covers every sub-agent automatically, including ones added later, with no
per-agent copy-paste to keep in sync.

## Full BasePlugin hook table (all `async def`, keyword-only args via `*,`)

```python
class GuardrailPlugin(BasePlugin):
    def __init__(self, name: str = "model_armor_guardrail"):
        super().__init__(name=name)

    async def on_user_message_callback(
        self, *, invocation_context, user_message
    ) -> Optional[Content]: ...
    # Fires first. Return Content to REPLACE the user message. None = proceed.

    async def before_run_callback(self, *, invocation_context) -> Optional[Content]: ...
    # Return Content to HALT the run early (used as the result). None = proceed.

    async def before_agent_callback(self, *, agent, callback_context) -> Optional[Content]: ...
    # Return Content to skip the agent entirely, using it as the response.

    async def before_model_callback(
        self, *, callback_context, llm_request
    ) -> Optional[LlmResponse]: ...
    # KEY HOOK for the prompt gate. Return LlmResponse to skip the model call
    # entirely (block verdict). None = proceed with the (possibly mutated) request.

    async def after_model_callback(
        self, *, callback_context, llm_response
    ) -> Optional[LlmResponse]: ...
    # KEY HOOK for the response gate. Return a replacement LlmResponse to
    # override the model's raw output (block/redact). None = pass through.

    async def on_model_error_callback(
        self, *, callback_context, llm_request, error
    ) -> Optional[LlmResponse]: ...
    # Return LlmResponse to suppress the exception (after_model_callback still
    # fires on it). None = re-raise.

    async def before_tool_callback(
        self, *, tool, tool_args, tool_context
    ) -> Optional[dict]: ...
    # KEY HOOK for the exfiltration gate. Return a dict to SKIP tool execution,
    # using the dict as the result (e.g. block a call whose args carry a
    # credential- or PII-shaped string). None = let the tool run.
    # WARNING: ADK checks `is None`, so returning {} still counts as an
    # override — do not use {} to mean "allow".

    async def after_tool_callback(
        self, *, tool, tool_args, tool_context, result
    ) -> Optional[dict]: ...
    # Return a dict to replace the tool's result (redact leaked PII). None = keep it.

    async def on_tool_error_callback(
        self, *, tool, tool_args, tool_context, error
    ) -> Optional[dict]: ...
    # Return dict to suppress (after_tool_callback still fires). None = re-raise.

    async def on_event_callback(self, *, invocation_context, event) -> Optional[Event]: ...
    async def after_agent_callback(self, *, agent, callback_context) -> Optional[Content]: ...
    async def after_run_callback(self, *, invocation_context) -> None: ...
    async def on_agent_error_callback(self, *, agent, callback_context, error) -> None: ...
    # Notification-only; error is ALWAYS re-raised regardless of what you do here.
    async def on_run_error_callback(self, *, invocation_context, error) -> None: ...
    # Same re-raise guarantee.
    async def close(self) -> None: ...
    # Called on runner shutdown; release connections/resources here.
```

Only override the hooks the guardrail actually needs
(`before_model_callback`, `after_model_callback`, `before_tool_callback`,
optionally `on_user_message_callback`/`before_agent_callback` for session
integrity) — `BasePlugin` provides no-op defaults for the rest.

## Return-value semantics

- **Observe** (return `None`): workflow proceeds unmodified. Use for
  logging/metrics-only concerns — not the block path.
- **Intervene** (return a non-`None` value): the `Runner` halts, skips
  remaining plugins **and** the agent/model/tool-level callback, and uses
  your returned value as the result. This is the mechanism for a Model Armor
  block verdict: `before_model_callback` returns a fabricated `LlmResponse`
  refusal so the flagged prompt never reaches the model.
- **Amend** (mutate the passed object in place, return `None`): the mutated
  `llm_request`/`tool_args` flows to the next plugin/callback. Use this for
  redact-in-place instead of an outright block (e.g., replacing only the PII
  span Model Armor flagged).

## Worked skeleton (prompt + response + tool gates)

```python
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.models.llm_response import LlmResponse
from google.genai import types

class GuardrailPlugin(BasePlugin):
    def __init__(self, config):
        super().__init__(name="model_armor_guardrail")
        self.config = config  # parsed guardrail_policy_config.json

    async def before_model_callback(self, *, callback_context, llm_request):
        text = _latest_user_text(llm_request)  # only the newest turn, never history
        result = await sanitize_user_prompt(text, self.config.prompt_template)
        if result["filterMatchState"] == "MATCH_FOUND":
            if self.config.enforcement_mode == "inspect_and_block":
                return LlmResponse(content=types.Content(
                    role="model", parts=[types.Part(text=self.config.refusal_text)]))
            _log_match(result)  # inspect_only: log, do not block
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        text = _response_text(llm_response)
        result = await sanitize_model_response(text, self.config.response_template)
        if result["filterMatchState"] != "MATCH_FOUND":
            return None
        sdp = result["filterResults"].get("sdp")
        if sdp and self.config.redact_pii:
            return _redact_response(llm_response, sdp)  # Amend-style replacement
        return LlmResponse(content=types.Content(
            role="model", parts=[types.Part(text=self.config.refusal_text)]))

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        if tool.name not in self.config.network_tools:
            return None  # only gate tools that can exfiltrate data
        if _looks_like_exfiltration(tool_args, self.config.basic_sdp_infotypes):
            return {"error": "blocked_by_guardrail", "reason": "sensitive_data_in_tool_args"}
        return None
```

## ADK's layered defense model (from the safety guide)

1. **Identity & Authorization** — agent-auth vs. user-auth for tool calls.
2. **Guardrails to screen inputs/outputs** — in-tool guardrails, built-in
   model safety filters, **callbacks/plugins** (this skill), Gemini-as-judge.
3. **Sandboxed code execution** — hermetic: no network access, full state
   cleanup between users, to prevent cross-user data exfiltration via a
   code-execution tool.
4. **Evaluation & tracing** — catch regressions in guardrail behavior over time.
5. **Network controls (VPC-SC)** — coarse-grained perimeter control; must be
   paired with layer 2, not a substitute for it.

Named risk sources: "vague instructions, model hallucination, jailbreaks and
prompt injections from adversarial users, and indirect prompt injections via
tool use." Named risk outcomes explicitly include **data exfiltration** and
**leaking sensitive personal data (PII)** — the two this skill targets.

A UI-side exfiltration vector is also called out: unescaped HTML/JS in a
model response rendered in a browser (e.g. an `<img>` tag from an indirect
prompt injection) can leak session content to a third party. Model Armor
does not catch this — it is a rendering-layer concern downstream of
`after_model_callback` that the calling application must escape separately.

## Session state integrity (session-poisoning-adjacent guidance)

ADK's docs do not use the term "session poisoning" verbatim. The closest
documented pattern is validating developer-set state flags in
`before_agent_callback`/`on_user_message_callback` before letting an agent
proceed (the docs' own `check_if_agent_should_run` example reads a state
flag and can skip the agent), combined with **in-tool guardrails** that read
from developer-controlled `ToolContext`/session state rather than trusting
values a prior model turn or tool output could have written. Build a
guardrail for session-state integrity from these two primitives — do not
cite ADK docs for an exact "session poisoning API" that does not exist:

```python
async def on_user_message_callback(self, *, invocation_context, user_message):
    state = invocation_context.session.state
    if not _policy_flags_are_valid(state, self.config.trusted_defaults):
        # a prior turn or tool wrote an unexpected/invalid policy flag —
        # reset to the developer-controlled default rather than trusting it
        _reset_policy_flags(state, self.config.trusted_defaults)
    return None
```
