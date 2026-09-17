---
name: agents-cli-plugin-moderator
description: "Configures and deploys a runner-wide ADK BasePlugin that wraps every coordinator and sub-agent with GCP Model Armor safety guardrails, blocking harmful inputs, session-state poisoning, and sensitive-data (PII) exfiltration before/after every LLM and tool call. TRIGGER when the user asks to \"add safety guardrails in ADK\", \"configure Model Armor in agents-cli\", \"block harmful content or prompts\", \"implement exfiltration detection\", \"write a runner-wide safety plugin\", or mentions `BasePlugin`, `before_model_callback`, `sanitizeUserPrompt`/`sanitizeModelResponse`. DO NOT TRIGGER for agent-specific (non-global) callback logic unrelated to safety, generic content moderation outside an ADK Runner, or GCP IAM/Terraform security auditing (use gcp-terraform-security-policy for that)."
version: 1.0.0
author: Actual Agentic Solutions
tags: [adk, agents-cli, model-armor, safety, guardrails, plugin, security]
license: Apache-2.0
compatibility: "ADK Python >= 1.7.0 (BasePlugin/Runner plugins API); Google Cloud Model Armor v1 REST API (regional endpoints); Python 3.9+ for scripts/simulate_moderation_violation.py (standard library only)"
metadata: {}
---

- Model Armor & Safety Guardrail Plugin

- Overview
This skill turns "add safety guardrails to my agent" into a single
runner-wide `BasePlugin` instead of a callback bolted onto one agent. A
Plugin registered on the `Runner` applies globally, in registration order,
to *every* agent, sub-agent, model call, and tool call it manages — and
plugin callbacks run **before** any agent/model/tool-level callback and can
short-circuit them. That precedence is exactly what a coordinator-plus-
sub-agents topology needs: one plugin instance, one policy, no per-agent
copy-paste that silently misses a newly added sub-agent.

The plugin calls Google Cloud Model Armor's `sanitizeUserPrompt` and
`sanitizeModelResponse` REST methods from `before_model_callback` and
`after_model_callback` to screen for prompt injection/jailbreak, responsible-
AI content categories, and sensitive data (PII); it uses `before_tool_callback`
to catch exfiltration risk in outbound tool arguments (e.g., an HTTP-call
tool receiving a credential-shaped string); and it validates session state at
`on_user_message_callback`/`before_agent_callback` to resist session
poisoning from a prior malicious turn. Success looks like: a single
`GuardrailPlugin` class, registered once on the `Runner`, that blocks or
redacts on a documented verdict (`filterMatchState: MATCH_FOUND`) instead of
silently passing unsafe content through, plus a policy config file the user
can retune without touching plugin code.

- Prerequisites
- A GCP project with the Model Armor API enabled and IAM role
  `roles/modelarmor.user` on the calling identity.
- Two Model Armor templates already created (or ready to create) at
  `projects/{PROJECT_ID}/locations/{LOCATION}/templates/{TEMPLATE_ID}` — one
  for prompts, one for responses (see Step 1; do not reuse one template for
  both).
- The ADK Python `Runner`/`InMemoryRunner` construction site in the user's
  code, where a `plugins=[...]` list can be added.
- **Tool boundary:** this skill edits/adds plugin code and local config only.
  It never calls the live Model Armor API itself, never provisions IAM
  roles or templates via `gcloud`, and never runs the user's agent. Use
  `scripts/simulate_moderation_violation.py` (a local stdlib-only mock) to
  validate logic before wiring in real credentials.

- Workflow

- Step 1: Decide the template split and enforcement mode
Read `references/model_armor_api.md` for the full request/response schema.
Two decisions gate everything else:
- **Decoupled templates.** Configure one template scoped to input risks
  (prompt injection/jailbreak `HIGH` or `MEDIUM_AND_ABOVE`, malicious
  uploads) and a separate one scoped to output risks (PII/SDP leakage,
  off-brand content, malicious URLs). Never point both
  `before_model_callback` and `after_model_callback` at the same
  `TEMPLATE_ID` — their risk profiles differ and a shared template makes
  false-positive tuning impossible to reason about.
- **Enforcement mode.** Start every new integration in `Inspect only`
  (log via Cloud Logging, never block) to baseline the false-positive rate
  against real traffic, then flip to `Inspect and block` once the
  `guardrail_policy_config.json` thresholds are confirmed. Encode this as an
  explicit `enforcement_mode` field (see Step 6) — never hardcode "always
  block" in the plugin body.

- Step 2: Scaffold the `GuardrailPlugin` class
Extend `google.adk.plugins.base_plugin.BasePlugin`, calling
`super().__init__(name="model_armor_guardrail")`. Read
`references/safety_plugin_patterns.md` for the exact signature of every
relevant hook and the Observe/Intervene/Amend return-value contract before
writing a single method — a plugin hook that returns a non-`None` value
halts the run and skips every other plugin and the agent/model/tool-level
callback, so getting the return type wrong either silently no-ops your
guardrail or wrongly kills a clean request.

- Step 3: Implement the prompt gate (`before_model_callback`)
Call `sanitizeUserPrompt` with only the **latest** user turn in
`userPromptData.text` — never concatenate conversation history or include
the system prompt (the API's own guidance; history dilutes the signal and
inflates token cost). Inspect
`response.sanitizationResult.filterMatchState`:
- `"MATCH_FOUND"` and `enforcement_mode == "inspect_and_block"`: return a
  fabricated `LlmResponse` (e.g. a fixed refusal `Content`) — this is the
  Intervene path, and it stops the request before it ever reaches the LLM.
- `"MATCH_FOUND"` and `enforcement_mode == "inspect_only"`: log the per-filter
  `filterResults` breakdown (which category matched) and return `None` to let
  the request proceed unmodified.
- `"NO_MATCH_FOUND"`: return `None`.
- `sanitizationResult.invocationResult == "FAILURE"`: this is an
  availability failure, not a content verdict — apply the policy's
  `fail_mode` (`fail_open` vs `fail_closed`, from
  `guardrail_policy_config.json`) rather than silently treating it as a pass.

- Step 4: Implement the response gate (`after_model_callback`)
Call `sanitizeModelResponse` with the model's output text in
`modelResponseData.text` (optionally `userPrompt` for context). On
`MATCH_FOUND` in a `sdp` filter specifically, prefer redaction over a hard
block when the policy allows it: replace only the matched span using the
`sdpFilterResult` finding's `location`, rather than discarding the whole
response — this preserves agent usefulness while still stopping the PII
leak. On `MATCH_FOUND` in `rai` (responsible-AI) categories, replace the
whole `LlmResponse` with a policy-configured refusal `Content`.

- Step 5: Implement the exfiltration gate (`before_tool_callback`)
For every registered tool that makes an outbound call (HTTP fetch, email
send, file upload, code execution with network access), re-run the relevant
argument string through the same `sanitizeUserPrompt`-style scan (or a
lighter regex/SDP-basic-infoType check from
`guardrail_policy_config.json`'s `basic_sdp_infotypes` list) before the tool
executes. Return a replacement result dict to block a tool call whose
arguments contain a credential- or PII-shaped string; return `None` to let
it proceed. Pair this with the ADK safety guidance on sandboxed code
execution: any code-execution tool should already be hermetic (no network,
full state cleanup between users) — the plugin gate is a second layer, not
a substitute for that isolation.

- Step 6: Guard against session-state poisoning
Implement `on_user_message_callback` (or `before_agent_callback` for a
specific sub-agent) to validate any developer-set policy flags in session
state against a value the plugin itself controls — never trust a state
value that could have been written by a prior model turn or tool output
without re-validating it. ADK's docs do not use the term "session
poisoning" verbatim; this pattern is built from the state-validation and
in-tool-guardrail primitives documented in
`references/safety_plugin_patterns.md`'s Session State Integrity section —
read it before assuming a specific API name exists for this.

- Step 7: Author `guardrail_policy_config.json` and register the plugin
Copy/edit `assets/guardrail_policy_config.json`: set the two `template_id`s
from Step 1, per-category confidence thresholds, `enforcement_mode`, and
`fail_mode`. Then register the plugin once, at the `Runner`/`InMemoryRunner`
construction site:
```python
runner = Runner(agent=root_agent, app_name=app_name,
                 plugins=[GuardrailPlugin(config_path="guardrail_policy_config.json")])
```
Never register the same plugin instance on more than one `Runner`, and
never add it as a per-agent `before_model_callback=...` instead — that
loses the global, precedence-first coverage this skill exists to provide.

- Step 8: Validate before wiring real credentials
Run `scripts/simulate_moderation_violation.py --selftest`. It starts a local
stdlib-only mock Model Armor server and a mock `GuardrailPlugin` harness (no
`google-adk` or GCP dependency required), then replays canned cases —
benign text, prompt injection ("ignore previous instructions..."), a
credit-card-shaped PII string, and a hate-speech-shaped string — asserting
each gets the expected `MATCH_FOUND`/`NO_MATCH_FOUND` verdict and the
correct block/redact/allow decision. All cases must pass before pointing
the plugin at a real `TEMPLATE_ID` and regional endpoint.

- Examples

- Example 1: New ADK coordinator with several sub-agents
Input: "Add a safety guardrail plugin so nothing harmful reaches any of my
sub-agents." Expected behavior: scaffold `GuardrailPlugin` per Steps 2-6,
author two templates' worth of config per Step 7, register it once on the
shared `Runner`, and confirm via Step 8's selftest that a prompt-injection
payload is blocked at `before_model_callback` without reaching the model.

- Example 2: Existing agent, PII leaking in responses
Input: "Our support bot sometimes echoes back a customer's card number."
Expected behavior: focus on Step 4 — add/verify the `sdp` output template,
prefer the redact-the-span behavior over a full block, and confirm with a
credit-card-shaped selftest case that the response is redacted, not just
logged.

- Error Handling
- `sanitizationResult.invocationResult == "FAILURE"` (all filters
  skipped/errored): apply the configured `fail_mode`; never treat this the
  same as `NO_MATCH_FOUND`, and never silently default to fail-open without
  it being an explicit policy choice in `guardrail_policy_config.json`.
- A `before_tool_callback` returns `{}` (empty dict) to mean "allow": this is
  wrong — ADK checks the return value with `is None`, so an empty dict still
  counts as an override that replaces the tool result. Return `None`
  explicitly to allow the tool call to proceed.
- Both prompt and response gates point at the same `TEMPLATE_ID`: stop and
  flag this during Step 1 — it defeats the decoupled-template tuning this
  skill depends on.
- The regional endpoint is missing or a global endpoint is used for a
  sanitize call: Model Armor's sanitize methods require a regional endpoint
  (`modelarmor.{LOCATION}.rep.googleapis.com`), not the global
  `modelarmor.googleapis.com` host used for template CRUD — calls to the
  wrong host will fail outright.
- `scripts/simulate_moderation_violation.py --selftest` reports a FAIL: do
  not proceed to wiring real credentials; the block/allow decision logic in
  the plugin (not the mock server) is almost always the bug — recheck the
  `filterMatchState` branch from Steps 3-4.

- Reference Files
- **references/model_armor_api.md**: exact REST method names, paths,
  request/response JSON schema (`SanitizationResult`, `filterMatchState`,
  `filterResults` per category), confidence-level and enforcement-type
  tables, and IAM permissions — read before Step 1 or whenever a field name
  needs verifying.
- **references/safety_plugin_patterns.md**: the full `BasePlugin` hook table
  with exact async signatures, the Observe/Intervene/Amend return-value
  contract, the layered-defense model from ADK's safety guidance, and the
  session-state-integrity pattern — read before Step 2 and whenever a hook's
  behavior needs confirming.
- **scripts/simulate_moderation_violation.py**: stdlib-only mock Model Armor
  server plus a `GuardrailPlugin` decision-logic harness; run
  `--selftest` in Step 8, or `--payload "..." --mode prompt|response` to test
  one string ad hoc, before touching real credentials.
- **assets/guardrail_policy_config.json**: sample policy file — two
  `template_id` placeholders, per-category confidence thresholds,
  `enforcement_mode`, `fail_mode`, and `basic_sdp_infotypes` — copy and edit
  in Step 7 rather than inventing a config shape ad hoc.

- Output Format
Return, in order: (1) the `GuardrailPlugin` class code with all implemented
hooks, (2) the filled-in `guardrail_policy_config.json`, (3) the exact
`Runner(..., plugins=[...])` registration snippet, and (4) the
`simulate_moderation_violation.py --selftest` output confirming every case
passed. Never report the integration as complete without that selftest
output, and never claim "safe in production" from `Inspect only` mode alone
— state explicitly which enforcement mode is active.
