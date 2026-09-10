---
name: model-governance
description: "Profiles an agent prompt, workflow step, or task spec for cognitive/token complexity, resolves the optimal LLM provider and model tier against a governed catalog, and emits the exact opencode run --model provider/model launch command plus opencode.json agent.<name>.model config patches. TRIGGER when the user asks to 'assign a model for this prompt', 'select the optimal model/tier', 'configure opencode model governance', wants a --model provider/model launch command, needs to reconcile ~/.config/opencode/opencode.json against a project opencode.json, or asks to optimize model choice for cost vs. intelligence (result_maximized, cost_optimized, balanced). DO NOT TRIGGER for rewriting or improving prompt wording (prompt engineering), provisioning API keys/credentials, or running live model benchmarks/evals."
version: 1.0.0
author: Actual Agentic Solutions
tags: [opencode, model-selection, governance, cost-optimization, llm-routing]
license: Apache-2.0
compatibility: "OpenCode config schema as of opencode.ai/docs (fetched 2026-09-10); models.dev catalog snapshot dated 2026-09-10"
metadata: {}
---

- Model Governance Assignment

- Overview
This skill turns "what model should run this?" into a deterministic,
auditable decision instead of a guess. It classifies a task into one of
three cognitive tiers, resolves an `opencode.json` governance policy across
the global and project config layers, and picks a specific `provider/model`
from a cost/context-grounded catalog. The catalog and merge rules are
grounded in the live OpenCode config schema and a `models.dev` pricing
snapshot — see the Reference Files section before assuming a model ID or
price is still current.

Success looks like: an exact `opencode run --model provider/model "..."`
command the user can paste and run immediately, plus (when a persistent
agent role is involved) a JSON config patch for `agent.<name>.model`, and a
short trace explaining why that model beat the alternatives ranked above it.

- Prerequisites
- The prompt, task spec, or workflow step to classify (raw text, a file
  path, or piped stdin).
- The user's optimization objective, if not already set in config:
  `result_maximized` (best available regardless of cost), `cost_optimized`
  (cheapest model meeting the tier's minimum capability), or `balanced`
  (recommended default per tier). If truly unstated and no `governance.mode`
  exists in either config layer, default to `balanced` and say so.
- Read access to the relevant `opencode.json` files: global
  (`~/.config/opencode/opencode.json`) and project (`./opencode.json`).
  Neither needs to exist — treat a missing file as an empty layer, not an
  error.

- Workflow

- Step 1: Profile the prompt's complexity and token footprint
Run `scripts/profile_prompt.py "<the prompt or task text>"` (or `--file
<path>`, or pipe via stdin). It returns JSON with a `tier` (1/2/3),
`tier_name`, the keywords that triggered the classification, and estimated
input/output token counts. Read the `notes` field: if it reports zero
keyword matches, the tier was defaulted to 2 — confirm the classification
with the user rather than proceeding silently, especially if the task
sounds unusually high-stakes or unusually trivial for that default.
- Tier 1 (frontier reasoning): complex system design, multi-file refactors,
  autonomous squad orchestration, security/privacy audits, deep multi-hop
  reasoning.
- Tier 2 (balanced workhorse): standard feature implementation, unit tests,
  documentation, bug fixes, structured API endpoint generation.
- Tier 3 (high throughput): syntax triage, schema/metadata validation, text
  classification, simple file lookups, commit message formatting.

- Step 2: Resolve the governance configuration
Locate and read both config layers (see `references/opencode_config_spec.md`
for the full precedence chain — this skill only needs global + project).
Extract the `governance.mode`, `governance.allowed_providers`, and any
`governance.per_agent_overrides` for the target agent role, applying
**project-over-global** precedence key by key, matching OpenCode's own merge
behavior. If a `min_tier` override exists for this agent role and the
profiled tier from Step 1 is lower, raise the tier to the override's floor
and say so — never silently lower a configured floor.

- Step 3: Resolve the model
Run `scripts/resolve_governance_model.py --tier <N> --mode <mode>
--input-tokens <estimated_input_tokens> --global-config
~/.config/opencode/opencode.json --project-config ./opencode.json
[--agent-name <role>] [--allowed-providers p1,p2]`. This applies the
per-mode selection rule documented in `references/model_tier_catalog.md`:
`result_maximized` takes the tier's top-ranked model that fits the context
window; `cost_optimized` takes the cheapest eligible model in the same tier
(it never drops to a lower tier); `balanced` takes the tier's named default,
falling through by rank if that default is ineligible. A non-zero exit code
means no catalog model in that tier satisfies the context limit or the
allowed-provider constraint — report this explicitly rather than inventing
a model ID from memory or silently trying a different tier.

- Step 4: Emit the launch command
Take the `launch_command` field from Step 3's JSON output verbatim
(`opencode run --model <provider>/<model> "<prompt>"`) and substitute the
real prompt text for `<prompt>`. If the profiler flagged
`chain_of_thought_recommended: true` and the resolved model supports
variants (see `references/opencode_config_spec.md`), append `--variant
high` (or the model's next-higher variant) rather than switching to a more
expensive model purely for more reasoning budget.

- Step 5: Patch persistent agent config, if applicable
If this assignment is for a persistent subagent role (orchestrator, finder,
creator, evaluator, or a custom agent) rather than a one-off `opencode run`,
take the `config_patch` object from Step 3's output and present it as a
merge patch into the project's `opencode.json` under `agent.<name>.model`
(or `agents.<name>.model` if that is the key the project's config already
uses successfully — see the Gotchas section of
`references/opencode_config_spec.md`). Do not overwrite the whole
`opencode.json` file blind; merge the `agent` block key-by-key so other
agents' configuration is preserved.

- Examples

- Example 1: One-off task, no stated preference
Input: "What model should I use to fix this off-by-one bug in the CSV
parser?"
Expected output / behavior: `profile_prompt.py` classifies this as Tier 2
("fix the bug" keyword). No `governance.mode` found in either config layer
→ default to `balanced`. `resolve_governance_model.py --tier 2 --mode
balanced` returns `anthropic/claude-sonnet-5` (or the next eligible rank if
that provider isn't configured). Emit: `opencode run --model
anthropic/claude-sonnet-5 "Fix the off-by-one bug in the CSV parser..."`
plus a one-line note that `balanced` was assumed since no policy was set.

- Example 2: Persistent subagent role with an explicit cost objective
Input: "Configure the finder subagent to be as cheap as possible — it just
does file lookups."
Expected output / behavior: classify as Tier 3 ("simple file lookup").
`--mode cost_optimized --tier 3 --agent-name finder` resolves to
`openai/gpt-5-nano` (cheapest eligible). Return the `config_patch` JSON
(`{"agent": {"finder": {"model": "openai/gpt-5-nano"}}}`) for the user to
merge into `opencode.json`, plus the cost-per-1M-token figures from the
trace so the user can see why it beat the other Tier 3 candidates.

- Error Handling
- `resolve_governance_model.py` exits non-zero / prints `"no_eligible_model"`:
  report the tier and the constraint that eliminated every candidate
  (context limit or `allowed_providers`); ask the user to relax one
  constraint rather than silently picking from a different tier.
- A named provider in `governance.allowed_providers` returns zero models
  from `opencode models <provider>`: the provider ID is likely missing its
  `provider` block in config, not just missing credentials — flag this
  distinction per the Gotchas note in `references/opencode_config_spec.md`.
- Profiler reports zero keyword matches (defaulted to Tier 2): treat as
  low-confidence and confirm the tier with the user before resolving a
  model, especially for anything that sounds like an audit, migration, or
  irreversible operation.
- Estimated input tokens exceed every model's context limit in the assigned
  tier: do not truncate the task silently — tell the user the task needs to
  be chunked, or that a Tier 1 large-context model
  (`google-vertex/gemini-3.1-pro-preview`) is required regardless of the
  assigned tier's cost profile.
- A model ID from the catalog no longer appears in `opencode models
  <provider> --verbose`: it has been deprecated upstream — re-run `opencode
  models --refresh` and substitute the next-ranked catalog model in the same
  tier; do not guess a replacement ID from memory.

- Reference Files
- **scripts/profile_prompt.py**: heuristic tier classifier and token
  estimator — run first, in Step 1.
- **scripts/resolve_governance_model.py**: reads merged config, applies the
  per-mode selection rule against the embedded catalog, and prints the
  launch command / config patch — run in Step 3.
- **references/model_tier_catalog.md**: the full three-tier model catalog
  with pricing, context limits, and per-mode selection rules — read before
  trusting any model ID or price this skill emits.
- **references/opencode_config_spec.md**: config file precedence, the
  `agent.<name>.model` schema, model ID format, reasoning variants, and this
  skill's `governance` key convention — read in Step 2 and Step 5.
- **assets/governance_policy_schema.json**: JSON Schema for the `governance`
  config block, for validating or scaffolding a project's policy.
- **assets/opencode_override_template.json**: fill-in-the-blanks
  `opencode.json` patch combining a `governance` block and an `agent.*`
  model override — copy this when producing a full config file rather than
  a bare patch.

- Output Format
Return, in this order: (1) the profiled tier and the keywords/estimate that
produced it, (2) the resolved model with its cost/context figures and the
resolution trace, (3) the exact `opencode run --model ...` command, and (4)
a config patch JSON block if a persistent agent role was targeted. State
explicitly whenever a value was defaulted (mode, provider allow-list,
tier-vs-floor) rather than user-specified.
