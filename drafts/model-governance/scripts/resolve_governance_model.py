#!/usr/bin/env python3
"""Resolve a governed model assignment from a classified tier + config.

Usage:
    resolve_governance_model.py --tier 2 \
        [--mode balanced|cost_optimized|result_maximized] \
        [--input-tokens 4000] \
        [--global-config ~/.config/opencode/opencode.json] \
        [--project-config ./opencode.json] \
        [--agent-name creator] \
        [--allowed-providers anthropic,openai,google-vertex]

Reads (in this order, project overriding global on conflicting keys, matching
OpenCode's own precedence — see references/opencode_config_spec.md):
  1. global opencode.json  ("governance" key, "provider" block)
  2. project opencode.json ("governance" key, "provider" block)

Then picks a model from the embedded tier catalog (kept in sync with
references/model_tier_catalog.md — update both together) using the
selection rule for the resolved mode, and prints JSON with:
  - the exact `opencode run --model ...` launch command
  - a config patch snippet for `agent.<name>.model` if --agent-name was given
  - the reasoning trace (why this model, why not the ones ranked above it)

Exit code is non-zero if no candidate in the tier satisfies the context
limit or allowed-providers constraint — this is a deliberate hard stop, not
a silent downgrade to a different tier.
"""
import argparse
import json
import os
import sys

# Keep this catalog in sync with references/model_tier_catalog.md.
# Snapshot date: 2026-09-10. Re-verify with `opencode models --refresh`
# before trusting these numbers for a real budget decision.
CATALOG = {
    1: [
        {"id": "anthropic/claude-opus-5", "provider": "anthropic",
         "input_cost": 5, "output_cost": 25, "context": 1_000_000, "rank": 1},
        {"id": "openai/gpt-5-pro", "provider": "openai",
         "input_cost": 15, "output_cost": 120, "context": 400_000, "rank": 2},
        {"id": "openai/o3", "provider": "openai",
         "input_cost": 2, "output_cost": 8, "context": 200_000, "rank": 3},
        {"id": "google-vertex/gemini-3.1-pro-preview", "provider": "google-vertex",
         "input_cost": 2, "output_cost": 12, "context": 1_048_576, "rank": 4},
    ],
    2: [
        {"id": "anthropic/claude-sonnet-5", "provider": "anthropic",
         "input_cost": 2, "output_cost": 10, "context": 1_000_000, "rank": 1},
        {"id": "google-vertex/gemini-3.6-flash", "provider": "google-vertex",
         "input_cost": 0.75, "output_cost": 3.75, "context": 1_048_576, "rank": 2},
        {"id": "openai/o4-mini", "provider": "openai",
         "input_cost": 1.1, "output_cost": 4.4, "context": 200_000, "rank": 3},
        {"id": "openai/gpt-5.1", "provider": "openai",
         "input_cost": 1.25, "output_cost": 10, "context": 400_000, "rank": 4},
        {"id": "anthropic/claude-sonnet-4-5", "provider": "anthropic",
         "input_cost": 3, "output_cost": 15, "context": 1_000_000, "rank": 5},
        {"id": "google-vertex/gemini-3.5-flash", "provider": "google-vertex",
         "input_cost": 1.5, "output_cost": 9, "context": 1_048_576, "rank": 6},
    ],
    3: [
        {"id": "openai/gpt-5-nano", "provider": "openai",
         "input_cost": 0.05, "output_cost": 0.4, "context": 400_000, "rank": 1},
        {"id": "google-vertex/gemini-3.5-flash-lite", "provider": "google-vertex",
         "input_cost": 0.3, "output_cost": 2.5, "context": 1_048_576, "rank": 2},
        {"id": "anthropic/claude-haiku-4-5", "provider": "anthropic",
         "input_cost": 1, "output_cost": 5, "context": 200_000, "rank": 3},
        {"id": "openai/gpt-4o-mini", "provider": "openai",
         "input_cost": 0.15, "output_cost": 0.6, "context": 128_000, "rank": 4},
    ],
}

BALANCED_DEFAULT = {
    1: "openai/o3",
    2: "anthropic/claude-sonnet-5",
    3: "anthropic/claude-haiku-4-5",
}


def load_json(path):
    if not path:
        return {}
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_governance(global_cfg, project_cfg):
    """Project config wins key-by-key over global, matching OpenCode's own
    merge behavior (project has higher precedence than global)."""
    merged = dict(global_cfg.get("governance", {}))
    merged.update(project_cfg.get("governance", {}))
    return merged


def configured_providers(global_cfg, project_cfg):
    providers = set(global_cfg.get("provider", {}).keys())
    providers |= set(project_cfg.get("provider", {}).keys())
    return providers


def pick_model(tier, mode, input_tokens, allowed_providers, configured):
    candidates = CATALOG[tier]

    def eligible(m):
        if m["context"] < input_tokens:
            return False
        if allowed_providers and m["provider"] not in allowed_providers:
            return False
        # If the caller told us nothing about configured providers, don't
        # filter on it -- that's an "unknown" state, not a "deny" state.
        if configured and m["provider"] not in configured:
            return False
        return True

    trace = []
    ranked = sorted(candidates, key=lambda m: m["rank"])

    if mode == "cost_optimized":
        pool = [m for m in ranked if eligible(m)]
        if not pool:
            return None, trace + ["No candidate in tier satisfies context/provider constraints."]
        best = min(pool, key=lambda m: m["input_cost"] + m["output_cost"])
        trace.append(f"cost_optimized: chose cheapest eligible model in tier {tier}.")
        return best, trace

    if mode == "result_maximized":
        for m in ranked:
            if eligible(m):
                trace.append(
                    f"result_maximized: rank {m['rank']} model eligible, "
                    f"ignoring cost (${m['input_cost']}/${m['output_cost']} per 1M)."
                )
                return m, trace
            trace.append(f"result_maximized: rank {m['rank']} ({m['id']}) skipped — ineligible.")
        return None, trace + ["No candidate in tier satisfies context/provider constraints."]

    # balanced (default)
    default_id = BALANCED_DEFAULT[tier]
    default_model = next((m for m in ranked if m["id"] == default_id), None)
    if default_model and eligible(default_model):
        trace.append(f"balanced: using tier {tier}'s balanced_default ({default_id}).")
        return default_model, trace
    trace.append(f"balanced: default {default_id} ineligible, falling through by rank.")
    for m in ranked:
        if eligible(m):
            trace.append(f"balanced: falling through to rank {m['rank']} ({m['id']}).")
            return m, trace
    return None, trace + ["No candidate in tier satisfies context/provider constraints."]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tier", type=int, required=True, choices=[1, 2, 3])
    parser.add_argument("--mode", choices=["balanced", "cost_optimized", "result_maximized"])
    parser.add_argument("--input-tokens", type=int, default=0)
    parser.add_argument("--global-config", default="~/.config/opencode/opencode.json")
    parser.add_argument("--project-config", default="./opencode.json")
    parser.add_argument("--agent-name", default=None)
    parser.add_argument("--allowed-providers", default=None,
                         help="Comma-separated override; else read from governance policy")
    args = parser.parse_args()

    global_cfg = load_json(args.global_config)
    project_cfg = load_json(args.project_config)
    governance = merge_governance(global_cfg, project_cfg)

    mode = args.mode or governance.get("mode", "balanced")
    allowed_providers = (
        set(args.allowed_providers.split(","))
        if args.allowed_providers
        else set(governance.get("allowed_providers", []))
    )
    configured = configured_providers(global_cfg, project_cfg)

    model, trace = pick_model(
        args.tier, mode, args.input_tokens, allowed_providers, configured
    )

    if model is None:
        print(json.dumps({
            "error": "no_eligible_model",
            "tier": args.tier,
            "mode": mode,
            "trace": trace,
        }, indent=2))
        sys.exit(1)

    launch_command = f'opencode run --model {model["id"]} "<prompt>"'
    output = {
        "tier": args.tier,
        "mode": mode,
        "chosen_model": model["id"],
        "cost_per_1m": {"input": model["input_cost"], "output": model["output_cost"]},
        "context_limit": model["context"],
        "launch_command": launch_command,
        "trace": trace,
    }
    if args.agent_name:
        output["config_patch"] = {
            "agent": {
                args.agent_name: {"model": model["id"]}
            }
        }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
