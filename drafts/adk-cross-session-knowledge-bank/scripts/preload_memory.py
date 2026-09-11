#!/usr/bin/env python3
"""preload_memory.py

Seeds Vertex AI Memory Bank with facts (user preferences, terminology,
prior conversational context) BEFORE an agent's first real turn, so
`PreloadMemoryTool` recalls them starting from session 1 instead of waiting
for `generate_memories_callback` to extract them organically from a live
conversation. Grounded in the Agent Platform Memory Bank API:
https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/api-quickstart
and .../generate-memories (fetched 2026-09-11 -- re-verify field names
there before depending on this for a production pipeline; the API is still
evolving).

Two source modes, mirroring the two real `GenerateMemories` data sources:

1. --facts-file PATH   (direct_memories_source — the common case)
   A JSON array matching assets/memory_bank_schema.json:
   [{"fact": "...", "scope": {...}, "topic": "...", "metadata": {...}}, ...]
   Pre-extracted facts you already know are true (e.g. a team glossary, a
   settings form the user filled out). Consolidated with any existing
   memories in the same scope by default.

2. --conversation-file PATH   (direct_contents_source)
   A JSON array of turns: [{"role": "user"|"model", "text": "..."}, ...].
   Memory Bank extracts + consolidates facts from this like a real
   conversation, gated by whatever memory topics the target instance is
   configured with -- this can legitimately extract nothing if none of the
   turns match a configured topic. Prefer --facts-file when you already
   know the exact fact you want stored; this mode is for "replay a
   transcript I already have."

Every fact in --facts-file is, by default, sent through `GenerateMemories`
(consolidation-aware: an existing memory covering the same idea is updated
or left alone rather than duplicated). Pass --no-consolidate to instead call
`CreateMemory` once per fact -- a raw, non-deduplicated write the API docs
explicitly warn can produce duplicate memories for the same scope. Only use
--no-consolidate when you specifically want guaranteed-distinct records
(e.g. a test fixture), not for routine seeding.

--dry-run validates the input file against assets/memory_bank_schema.json
(a minimal manual check if the `jsonschema` package isn't installed, a full
schema validation if it is) and prints the exact request payload(s) that
would be sent -- no GCP credentials, network call, or `vertexai` import
required. Always dry-run a new seed file before spending a real
memory-generation call on it.

Usage:
    preload_memory.py --memory-bank-name projects/P/locations/L/reasoningEngines/R \\
        --facts-file seed.json --scope-json '{"user_id":"123"}'
    preload_memory.py --memory-bank-name ... --conversation-file convo.json \\
        --scope-json '{"user_id":"123"}'
    preload_memory.py --facts-file seed.json --dry-run   # no GCP needed

Exit codes: 0 = success (or dry-run validation passed), 1 = one or more
facts failed to write, 2 = usage/validation error.
"""
import argparse
import json
import os
import sys

SCHEMA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "memory_bank_schema.json")
)


def load_facts_file(path):
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"error: {path} must be a JSON array of entries — see {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(2)
    return data


def validate_facts(entries):
    """Validate against assets/memory_bank_schema.json. Uses `jsonschema` if
    installed for a full check; otherwise falls back to a minimal manual
    check of the one required field so this script has no hard dependency
    beyond the standard library."""
    errors = []
    try:
        import jsonschema
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        validator = jsonschema.Draft202012Validator(schema)
        for err in validator.iter_errors(entries):
            errors.append(f"{list(err.path)}: {err.message}")
    except ImportError:
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"[{i}]: entry is not an object")
                continue
            fact = entry.get("fact")
            if not isinstance(fact, str) or not fact.strip():
                errors.append(f"[{i}]: missing or empty required field 'fact'")
            scope = entry.get("scope")
            if scope is not None and (not isinstance(scope, dict) or len(scope) > 5):
                errors.append(f"[{i}]: 'scope' must be an object with at most 5 keys")
    return errors


def load_conversation_file(path):
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"error: {path} must be a JSON array of {{role, text}} turns", file=sys.stderr)
        sys.exit(2)
    for i, turn in enumerate(data):
        if "role" not in turn or "text" not in turn:
            print(f"error: turn [{i}] in {path} is missing 'role' or 'text'", file=sys.stderr)
            sys.exit(2)
    return data


def build_direct_memories_payload(entries, default_scope):
    direct_memories = [{"fact": e["fact"]} for e in entries]
    scopes = [e.get("scope", default_scope) for e in entries]
    return direct_memories, scopes


def build_direct_contents_payload(turns):
    return {
        "events": [
            {"content": {"role": t["role"], "parts": [{"text": t["text"]}]}}
            for t in turns
        ]
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--facts-file", help="JSON array matching assets/memory_bank_schema.json")
    src.add_argument("--conversation-file", help="JSON array of {role, text} turns")
    ap.add_argument("--memory-bank-name", help="projects/P/locations/L/reasoningEngines/R "
                     "(the Agent Engine instance backing your Memory Bank -- required unless --dry-run)")
    ap.add_argument("--scope-json", default="{}",
                     help='Default scope dict applied when an entry omits its own "scope", '
                          'e.g. \'{"user_id":"123"}\' (default: {})')
    ap.add_argument("--no-consolidate", action="store_true",
                     help="Use raw CreateMemory per fact instead of consolidation-aware GenerateMemories "
                          "-- can produce duplicate memories for the same scope; see this script's docstring")
    ap.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    ap.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    ap.add_argument("--dry-run", action="store_true",
                     help="Validate input and print the request payload(s); no GCP call, no vertexai import")
    args = ap.parse_args()

    try:
        default_scope = json.loads(args.scope_json)
    except json.JSONDecodeError as e:
        print(f"error: --scope-json is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)

    if not args.dry_run and not args.memory_bank_name:
        print("error: --memory-bank-name is required unless --dry-run", file=sys.stderr)
        sys.exit(2)

    if args.facts_file:
        entries = load_facts_file(args.facts_file)
        errors = validate_facts(entries)
        if errors:
            print(f"error: {args.facts_file} failed schema validation:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            sys.exit(2)
        direct_memories, scopes = build_direct_memories_payload(entries, default_scope)
        mode = "no-consolidate (CreateMemory per fact)" if args.no_consolidate else "GenerateMemories (direct_memories_source)"

        if args.dry_run:
            print(f"Validated {len(entries)} fact(s) against {SCHEMA_PATH}. Mode: {mode}.\n")
            for i, (mem, scope) in enumerate(zip(direct_memories, scopes)):
                print(f"[{i}] fact={mem['fact']!r} scope={scope}")
            print("\nDry run only -- no GCP call made. Re-run without --dry-run "
                  "(with --memory-bank-name) to actually write these.")
            sys.exit(0)

        try:
            import vertexai
        except ImportError:
            print("error: 'vertexai' package not installed. Run: "
                  "pip install 'google-cloud-aiplatform[agent-engines]'", file=sys.stderr)
            sys.exit(2)

        client = vertexai.Client(project=args.project, location=args.location)
        failures = 0
        if args.no_consolidate:
            for mem, scope in zip(direct_memories, scopes):
                try:
                    client.agent_engines.memories.create(
                        name=args.memory_bank_name, fact=mem["fact"], scope=scope,
                    )
                    print(f"created: {mem['fact']!r} scope={scope}")
                except Exception as e:  # noqa: BLE001 -- surface any API error per-fact, keep going
                    failures += 1
                    print(f"FAILED: {mem['fact']!r} scope={scope}: {e}", file=sys.stderr)
        else:
            # Group by scope since GenerateMemories takes one scope per call.
            by_scope = {}
            for mem, scope in zip(direct_memories, scopes):
                by_scope.setdefault(json.dumps(scope, sort_keys=True), []).append(mem)
            for scope_json, mems in by_scope.items():
                scope = json.loads(scope_json)
                try:
                    op = client.agent_engines.memories.generate(
                        name=args.memory_bank_name,
                        direct_memories_source={"direct_memories": mems},
                        scope=scope,
                        config={"wait_for_completion": True},
                    )
                    generated = getattr(getattr(op, "response", None), "generatedMemories", [])
                    print(f"scope={scope}: {len(mems)} fact(s) submitted, "
                          f"{len(generated)} memory operation(s) returned")
                except Exception as e:  # noqa: BLE001
                    failures += 1
                    print(f"FAILED for scope={scope}: {e}", file=sys.stderr)
        sys.exit(1 if failures else 0)

    else:
        turns = load_conversation_file(args.conversation_file)
        payload = build_direct_contents_payload(turns)

        if args.dry_run:
            print(f"Validated {len(turns)} turn(s). Would call GenerateMemories with "
                  f"direct_contents_source, scope={default_scope}:\n")
            print(json.dumps(payload, indent=2))
            print("\nDry run only -- no GCP call made. Note: Memory Bank only extracts facts "
                  "matching a configured memory topic; this can legitimately produce zero "
                  "generated memories even on a real call.")
            sys.exit(0)

        try:
            import vertexai
        except ImportError:
            print("error: 'vertexai' package not installed. Run: "
                  "pip install 'google-cloud-aiplatform[agent-engines]'", file=sys.stderr)
            sys.exit(2)

        client = vertexai.Client(project=args.project, location=args.location)
        try:
            op = client.agent_engines.memories.generate(
                name=args.memory_bank_name,
                direct_contents_source=payload,
                scope=default_scope,
                config={"wait_for_completion": True},
            )
            generated = getattr(getattr(op, "response", None), "generatedMemories", [])
            print(f"{len(turns)} turn(s) submitted, {len(generated)} memory operation(s) returned "
                  "(0 is valid -- it means nothing matched a configured topic)")
            sys.exit(0)
        except Exception as e:  # noqa: BLE001
            print(f"FAILED: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
