# OpenCode Config Schema & Inheritance Rules

## Contents
- Config file locations and precedence
- Relevant schema keys for governance
- Model ID format
- Reasoning effort / variants
- Governance policy extension (this skill's convention)
- Gotchas

Source: `https://opencode.ai/docs/config/`, `https://opencode.ai/docs/models/`,
`https://opencode.ai/docs/agents/`, `https://opencode.ai/docs/cli/`. Re-fetch
these if the resolver script reports a schema mismatch — this file is a
summary, not the source of truth.

## Config file locations and precedence

Configs are **merged**, not replaced; later sources override earlier ones key
by key, in this order:

1. Remote org config (`.well-known/opencode`)
2. Global (`~/.config/opencode/opencode.json`)
3. Custom (`OPENCODE_CONFIG` env var path)
4. **Project (`opencode.json` in project root)** — highest standard precedence
5. `.opencode/` directory (agents, commands, plugins)
6. Inline (`OPENCODE_CONFIG_CONTENT` env var)
7. Managed config files (admin-controlled, e.g. `/etc/opencode/` on Linux)
8. macOS managed preferences (MDM) — not user-overridable

For this skill's purposes, resolve only layers 2 and 4 (global + project)
unless the user mentions a custom/remote/managed layer — those require
reading `OPENCODE_CONFIG`, `.well-known/opencode`, or the OS-specific managed
path respectively.

## Relevant schema keys for governance

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-5",       // global default model
  "small_model": "openai/gpt-5-nano",         // used for cheap background tasks (titles, etc.)
  "provider": {
    "<provider-id>": {
      "options": { "apiKey": "{env:...}" },
      "models": {
        "<model-id>": {
          "options": { "reasoningEffort": "high" },
          "variants": { "high": { "reasoningEffort": "high" } }
        }
      }
    }
  },
  "agent": {                                   // NOTE: singular key per current docs
    "<agent-name>": {
      "model": "provider/model-id",
      "reasoningEffort": "high",               // provider-specific options pass through directly
      "steps": 20
    }
  }
}
```

- `model` / `small_model` set the process-wide default and cheap-task default.
- `provider.<id>.models.<id>.options` sets per-model defaults globally.
- `agent.<name>.model` overrides the model for one persistent agent role
  (orchestrator, finder, creator, evaluator, or any custom subagent). Agent
  config **overrides** the global `model`/`provider` options for that agent
  only.
- Any key on an agent block beyond the documented ones (`description`,
  `model`, `prompt`, `permission`, `mode`, `temperature`, `steps`, `top_p`,
  `color`, `hidden`, `disable`) is passed straight through to the provider as
  a model option — this is how `reasoningEffort` / `textVerbosity` reach
  OpenAI reasoning models per-agent.

## Model ID format

Always `provider_id/model_id`, e.g. `anthropic/claude-opus-5`,
`google-vertex/gemini-3.6-flash`, `openai/o4-mini`. This exact string is what
both `--model` and `agent.<name>.model` expect. Get the exact live string with:

```bash
opencode models                 # all providers
opencode models anthropic       # filter to one provider
opencode models --verbose       # include cost/context metadata inline
```

Loading priority at runtime: `--model` CLI flag > config `model` key > last
used model > internal default priority. A `--model` flag always wins over
whatever this skill writes into `opencode.json`.

## Reasoning effort / variants

Reasoning-capable models expose built-in variants:

- **Anthropic**: `high` (default), `max`.
- **OpenAI**: roughly `none`/`minimal`/`low`/`medium`/`high`/`xhigh`
  (varies by model).
- **Google**: `low`, `high`.

Select a variant at launch with `--variant <name>` on `opencode run` / the
TUI, or pin one per-model in config under
`provider.<id>.models.<id>.variants`. Prefer `--variant` for a single launch
command (Step 4 of the SKILL.md workflow); prefer a config patch under
`variants` only when the choice should persist across every invocation of
that model.

## Governance policy extension (this skill's convention)

`opencode.json` has no built-in "governance mode" field — `result_maximized`
/ `cost_optimized` / `balanced` is a convention this skill introduces. Store
it under a top-level `governance` key so it survives the standard merge
behavior without colliding with any documented schema field:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "governance": {
    "mode": "balanced",                 // result_maximized | cost_optimized | balanced
    "allowed_providers": ["anthropic", "openai", "google-vertex"],
    "budget_ceiling_usd_per_mtok_output": 30
  }
}
```

`scripts/resolve_governance_model.py` reads this key from both the global and
project config (project wins on conflict, per the precedence order above) and
falls back to `mode: "balanced"` if the key is absent from every layer —
never fail the resolution just because governance policy was never
configured; say so in the audit explanation instead.

## Gotchas

- Some existing project configs in this repo family use a **plural** `agents`
  key instead of the documented singular `agent`. If you find `agents` in a
  target `opencode.json`, do not silently rewrite it to `agent` — confirm
  with `opencode debug config` which key the running binary actually
  resolved before patching, and match whichever key already loads
  successfully.
- `provider.<id>.models` entries are also how you register a fully custom
  provider (e.g. a local or self-hosted endpoint) — if `opencode models
  <provider>` returns nothing for a provider named in governance policy, it
  is either misspelled or missing its `provider` block entirely, not just
  missing credentials.
- `--model` on the CLI always overrides any config file. If a generated
  launch command must be honored exactly, do not also patch `agent.*.model`
  for the same role and expect the config to win — it will not.
