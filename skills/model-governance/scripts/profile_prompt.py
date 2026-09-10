#!/usr/bin/env python3
"""Classify a prompt/task's cognitive tier and estimate its token footprint.

Usage:
    profile_prompt.py "<prompt text>"
    profile_prompt.py --file task.md
    cat task.md | profile_prompt.py

Outputs a single JSON object on stdout:

{
  "tier": 1,
  "tier_name": "frontier_reasoning",
  "matched_keywords": ["multi-file refactor", "security audit"],
  "estimated_input_tokens": 812,
  "estimated_output_tokens": 300,
  "chain_of_thought_recommended": true,
  "notes": [...]
}

This is a heuristic classifier, not a model call — it exists to give
resolve_governance_model.py a deterministic, auditable starting point. Treat
a "medium confidence" result (zero or ambiguous keyword matches) as a
starting point to confirm with the user, not a final answer.
"""
import argparse
import json
import re
import sys

# Keyword sets are matched as whole-word / phrase, case-insensitive.
# Order matters: Tier 1 is checked first, so a prompt matching both a Tier 1
# and a Tier 3 keyword (e.g. "refactor the commit message format") is
# classified by its highest-complexity signal.
TIER_KEYWORDS = {
    1: [
        "complex system design", "system architecture", "multi-file refactor",
        "multi-agent", "orchestrat", "autonomous squad", "security audit",
        "privacy audit", "threat model", "deep reasoning", "multi-hop",
        "architectural review", "design a protocol", "distributed system",
        "migration plan", "root cause across", "cross-service",
    ],
    2: [
        "implement", "add endpoint", "add feature", "write unit test",
        "write tests", "fix bug", "fix the bug", "bug fix", "add api",
        "document the", "write documentation", "code review",
        "refactor function", "add a feature", "build a component",
        "write a script", "create an endpoint",
    ],
    3: [
        "rename", "format", "lint", "classify", "categorize", "look up",
        "lookup", "validate schema", "validate the schema", "commit message",
        "typo", "syntax check", "metadata validation", "simple file lookup",
        "one-line", "trivial",
    ],
}

TIER_NAMES = {
    1: "frontier_reasoning",
    2: "balanced_workhorse",
    3: "high_throughput",
}

# Cues that a task benefits from extended chain-of-thought / reasoning
# tokens, independent of tier (a Tier 2 task can still want light reasoning).
COT_CUES = [
    "why", "root cause", "debug", "trade-off", "tradeoff", "design",
    "compare", "which approach", "prove", "explain", "diagnose",
]


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars/token for English prose, with a floor.

    This intentionally avoids a tokenizer dependency so the script runs with
    zero extra installs. It undercounts code-heavy or non-English text —
    treat the result as an order-of-magnitude estimate, not an exact budget,
    and always leave headroom against the model's context limit in
    references/model_tier_catalog.md.
    """
    if not text.strip():
        return 0
    return max(1, len(text) // 4)


def classify_tier(text: str):
    lowered = text.lower()
    for tier in (1, 2, 3):
        matches = [kw for kw in TIER_KEYWORDS[tier] if kw in lowered]
        if matches:
            return tier, matches
    return 2, []  # default to the workhorse tier when no keyword matches


def estimate_output_tokens(input_tokens: int, tier: int) -> int:
    # Higher tiers tend to produce longer, more elaborated outputs
    # (architecture docs, multi-file diffs) relative to their input.
    ratio = {1: 0.6, 2: 0.4, 3: 0.15}[tier]
    floor = {1: 500, 2: 200, 3: 50}[tier]
    return max(floor, int(input_tokens * ratio))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", help="Prompt text (or use --file / stdin)")
    parser.add_argument("--file", help="Read prompt text from this file")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    elif args.prompt:
        text = args.prompt
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.error("Provide a prompt argument, --file, or pipe text via stdin")
        return

    tier, matches = classify_tier(text)
    input_tokens = estimate_tokens(text)
    output_tokens = estimate_output_tokens(input_tokens, tier)
    cot = any(re.search(rf"\b{re.escape(cue)}\b", text.lower()) for cue in COT_CUES)

    notes = []
    if not matches:
        notes.append(
            "No tier keyword matched; defaulted to Tier 2 (balanced_workhorse). "
            "Confirm the classification with the user before resolving a model."
        )
    if input_tokens > 50000:
        notes.append(
            "Estimated input exceeds 50k tokens — filter candidate models by "
            "context limit in model_tier_catalog.md before picking one, "
            "regardless of assigned tier."
        )

    result = {
        "tier": tier,
        "tier_name": TIER_NAMES[tier],
        "matched_keywords": matches,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "chain_of_thought_recommended": cot,
        "notes": notes,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
