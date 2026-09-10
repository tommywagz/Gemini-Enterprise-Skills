# Model Tier Catalog

## Contents
- How to keep this catalog current
- Tier 1: Frontier Reasoning & Complex Architecture
- Tier 2: Balanced Workhorse & Core Coding
- Tier 3: High Throughput & Routine Operations
- Selection rule per optimization mode

Pricing is USD per 1M tokens. Snapshot pulled live from `https://models.dev/api.json`
on **2026-09-10**. Model pricing and availability change frequently — before
trusting a number here for a real budget decision, re-verify with:

```bash
opencode models --refresh          # refresh the local models.dev cache
opencode models <provider> --verbose   # print live cost/context metadata
```

If a listed model ID no longer appears in `opencode models <provider>`, it has
been deprecated upstream — drop it from consideration and pick the next-ranked
model in the same tier instead of guessing a replacement ID from memory.

Each entry lists: `provider/model` id (exact string for `--model` / config),
input/output cost, context/output token limits, reasoning support, and its
role in selection (see "Selection rule" below).

## Tier 1: Frontier Reasoning & Complex Architecture

Use for: multi-file refactors, system design, autonomous squad orchestration,
security/privacy audits, deep multi-hop reasoning where a wrong answer is
expensive to unwind.

| Rank | Model ID | Input | Output | Context / Output limit | Reasoning | Notes |
|---|---|---|---|---|---|---|
| 1 | `anthropic/claude-opus-5` | $5 | $25 | 1,000,000 / 128,000 | yes (variants: `high` default, `max`) | Highest-quality general reasoning in this catalog; default `result_maximized` pick unless task needs >1M-token context. |
| 2 | `openai/gpt-5-pro` | $15 | $120 | 400,000 (272k in / 272k out) | yes (variants `none`..`xhigh`) | Most expensive model here by far — only justified when Opus 5 and o3 both fail the task, or the user explicitly demands OpenAI's top tier. |
| 3 | `openai/o3` | $2 | $8 | 200,000 / 100,000 | yes | Strong deep reasoning at a fraction of gpt-5-pro's cost; default OpenAI Tier 1 pick for `cost_optimized` and `balanced`. |
| 4 | `google-vertex/gemini-3.1-pro-preview` | $2 | $12 | 1,048,576 / 65,536 | yes (effort `low`/`medium`/`high`) | Only Tier 1 model with a >1M context window; pick this when the task needs to reason over a very large codebase or document set in one pass. |

`balanced_default`: `openai/o3` (strong reasoning, ~4-15x cheaper than the two
frontier flagships, still a named recommended model).

## Tier 2: Balanced Workhorse & Core Coding

Use for: standard feature implementation, unit test authoring, code
documentation, bug fixes, structured API endpoint generation.

| Rank | Model ID | Input | Output | Context / Output limit | Reasoning | Notes |
|---|---|---|---|---|---|---|
| 1 | `anthropic/claude-sonnet-5` | $2 | $10 | 1,000,000 / 128,000 | yes | Newest Sonnet: cheaper and bigger context than 4.5 — default `result_maximized` and `balanced` pick. |
| 2 | `google-vertex/gemini-3.6-flash` | $0.75 | $3.75 | 1,048,576 / 65,536 | yes | Cheapest model in the catalog with a 1M-token context window; default `cost_optimized` pick. |
| 3 | `openai/o4-mini` | $1.1 | $4.4 | 200,000 / 100,000 | yes | Reasoning-capable mini; good for structured codegen when the project is pinned to OpenAI. |
| 4 | `openai/gpt-5.1` | $1.25 | $10 | 400,000 (272k in / 128k out) | yes | General OpenAI workhorse when o4-mini's context ceiling is too low. |
| 5 | `anthropic/claude-sonnet-4-5` | $3 | $15 | 1,000,000 / 64,000 | yes | Prior-gen Sonnet — keep only as a fallback if `claude-sonnet-5` is unavailable on the account. |
| 6 | `google-vertex/gemini-3.5-flash` | $1.5 | $9 | 1,048,576 / 65,536 | yes | Prior-gen Flash — fallback if `gemini-3.6-flash` is unavailable. |

`balanced_default`: `anthropic/claude-sonnet-5`.

## Tier 3: High Throughput & Routine Operations

Use for: syntax triage, schema/metadata validation, text classification,
simple file lookup, commit message formatting.

| Rank | Model ID | Input | Output | Context / Output limit | Reasoning | Notes |
|---|---|---|---|---|---|---|
| 1 | `openai/gpt-5-nano` | $0.05 | $0.4 | 400,000 (272k in / 128k out) | yes | Cheapest model in the entire catalog that still supports reasoning and tool calls; default `cost_optimized` pick. |
| 2 | `google-vertex/gemini-3.5-flash-lite` | $0.3 | $2.5 | 1,048,576 / 65,536 | yes | Cheapest Vertex option; pick when the project is pinned to Google. |
| 3 | `anthropic/claude-haiku-4-5` | $1 | $5 | 200,000 / 64,000 | yes | Default `result_maximized` and `balanced` pick for Tier 3 — noticeably more reliable tool-calling than the nano/lite models at a still-low price. |
| 4 | `openai/gpt-4o-mini` | $0.15 | $0.6 | 128,000 / 16,384 | no | No reasoning support — only use for pure classification/formatting tasks with zero ambiguity; never route agentic tool-calling work here if `gpt-5-nano` is available. |

`balanced_default`: `anthropic/claude-haiku-4-5`.

## Selection rule per optimization mode

Given a classified tier (1/2/3), `scripts/resolve_governance_model.py` applies:

- **`result_maximized`** — pick the tier's `Rank 1` model, ignoring cost,
  unless the task's estimated context requirement exceeds that model's
  context limit — in that case fall through to the next-ranked model that
  fits, in order.
- **`cost_optimized`** — pick the lowest `input + output` cost model in the
  tier whose context limit still covers the task's estimated token count.
  Never drop to a lower tier than the one classified — cost optimization
  trims spend within the minimum-capability floor, it does not lower the
  floor.
- **`balanced`** — pick the tier's `balanced_default` model unless it fails
  the context-limit check, then fall through by rank.

In all three modes, if the resolved model's provider is not present in the
merged `provider` config or lacks credentials (see
`references/opencode_config_spec.md`), skip to the next-ranked model in the
same tier from a different provider — do not silently fall back to a
different tier without saying so in the audit explanation.
