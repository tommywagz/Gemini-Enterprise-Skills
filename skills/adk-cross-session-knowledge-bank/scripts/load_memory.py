#!/usr/bin/env python3
"""load_memory.py

Queries persisted Vertex AI Memory Bank memories for a scope, outside of an
agent's live `PreloadMemoryTool`/`LoadMemoryTool` turn. Useful for verifying
a seed from `preload_memory.py` actually landed, debugging "why didn't my
agent recall X", or building a small support tool that inspects what an
agent remembers about a user. Grounded in the Agent Platform Memory Bank
API: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/api-quickstart,
.../fetch-memories, and .../revisions (fetched 2026-09-11 -- re-verify
before depending on this for anything beyond ad hoc inspection).

Modes:

1. --scope-json '{"user_id":"123"}' [--topic USER_PREFERENCES]
   Scope-based retrieve (`client.agent_engines.memories.retrieve`) --
   returns every memory matching that scope. This is the mode this script
   fully implements against the live API; it is confirmed against the
   Memory Bank API quickstart's "Retrieve and use memories" example.

2. --revisions MEMORY_NAME
   Lists `memories.revisions` for one memory resource name, showing the
   intermediate `extracted_memories` and final `fact` for each generation
   request that touched it -- useful for understanding *why* a memory says
   what it currently says.

NOT implemented here: semantic/similarity-search retrieval by a free-text
query (as opposed to an exact scope match). The quickstart references a
"Fetch memories" doc section for this, but this script does not fabricate
that call's exact parameter name -- read
https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/fetch-memories
yourself before wiring that mode into a script, since it may have changed
since this skill was written.

--as-prompt renders retrieved memories into a `<MEMORIES>` block using the
same template pattern shown in the API quickstart's Jinja example, so you
can see exactly what context `PreloadMemoryTool` would inject into the
system instruction.

--dry-run --local-file PATH reads a local JSON array matching
assets/memory_bank_schema.json and filters it client-side by --scope-json,
instead of calling the real API -- use this to check --as-prompt rendering
and your scope-matching expectations without GCP credentials.

Usage:
    load_memory.py --memory-bank-name projects/P/locations/L/reasoningEngines/R \\
        --scope-json '{"user_id":"123"}' [--as-prompt]
    load_memory.py --revisions projects/P/locations/L/reasoningEngines/R/memories/M
    load_memory.py --scope-json '{"user_id":"123"}' --as-prompt --dry-run \\
        --local-file seed.json

Exit codes: 0 = success (including zero matches -- that's a valid result,
not an error), 2 = usage error.
"""
import argparse
import json
import sys

PROMPT_TEMPLATE = """<MEMORIES>
Here is some information about the user:
{facts}
</MEMORIES>"""


def render_as_prompt(facts):
    body = "\n".join(f"* {f}" for f in facts) if facts else "(no memories matched this scope)"
    return PROMPT_TEMPLATE.format(facts=body)


def scope_matches(entry_scope, query_scope):
    if not query_scope:
        return True
    entry_scope = entry_scope or {}
    return all(entry_scope.get(k) == v for k, v in query_scope.items())


def dry_run_local(local_file, scope, topic):
    with open(local_file) as f:
        entries = json.load(f)
    matched = [
        e for e in entries
        if scope_matches(e.get("scope"), scope) and (topic is None or e.get("topic") == topic)
    ]
    return [e["fact"] for e in matched]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--memory-bank-name", help="projects/P/locations/L/reasoningEngines/R (required unless --dry-run)")
    ap.add_argument("--scope-json", default="{}", help='e.g. \'{"user_id":"123"}\' (default: {}, matches everything)')
    ap.add_argument("--topic", default=None,
                     help="Filter to memories tagged with this managed/custom topic label (client-side in --dry-run mode)")
    ap.add_argument("--revisions", metavar="MEMORY_NAME",
                     help="List revisions for one memory resource name instead of scope-based retrieve")
    ap.add_argument("--as-prompt", action="store_true",
                     help="Render results as the <MEMORIES> block PreloadMemoryTool would inject")
    ap.add_argument("--project")
    ap.add_argument("--location", default="us-central1")
    ap.add_argument("--dry-run", action="store_true", help="Read --local-file instead of calling the real API")
    ap.add_argument("--local-file", help="JSON array matching assets/memory_bank_schema.json, for --dry-run")
    args = ap.parse_args()

    try:
        scope = json.loads(args.scope_json)
    except json.JSONDecodeError as e:
        print(f"error: --scope-json is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(scope, dict):
        print("error: --scope-json must decode to a JSON object", file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        if not args.local_file:
            print("error: --dry-run requires --local-file", file=sys.stderr)
            sys.exit(2)
        facts = dry_run_local(args.local_file, scope, args.topic)
        if args.as_prompt:
            print(render_as_prompt(facts))
        else:
            print(json.dumps({"scope": scope, "topic": args.topic, "facts": facts}, indent=2))
        sys.exit(0)

    if not args.memory_bank_name:
        print("error: --memory-bank-name is required unless --dry-run", file=sys.stderr)
        sys.exit(2)

    try:
        import vertexai
    except ImportError:
        print("error: 'vertexai' package not installed. Run: "
              "pip install 'google-cloud-aiplatform[agent-engines]'", file=sys.stderr)
        sys.exit(2)

    client = vertexai.Client(project=args.project, location=args.location)

    if args.revisions:
        revisions = list(client.agent_engines.memories.revisions.list(name=args.revisions))
        print(json.dumps([
            {"name": getattr(r, "name", None), "fact": getattr(r, "fact", None)}
            for r in revisions
        ], indent=2))
        sys.exit(0)

    page = client.agent_engines.memories.retrieve(name=args.memory_bank_name, scope=scope).page
    facts = [getattr(getattr(item, "memory", item), "fact", None) for item in page]
    facts = [f for f in facts if f is not None]
    if args.topic:
        print("note: --topic filtering is only implemented in --dry-run mode against a local "
              "file; the live retrieve() call above returned all memories in scope regardless "
              "of --topic (verify current topic-filter support against the Fetch memories doc "
              "before relying on it in production).", file=sys.stderr)

    if args.as_prompt:
        print(render_as_prompt(facts))
    else:
        print(json.dumps({"scope": scope, "facts": facts}, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
