---
name: adk-cross-session-knowledge-bank
description: "Seeds, queries, and explains Vertex AI Memory Bank cross-session memory for ADK agents: PreloadMemoryTool/LoadMemoryTool recall, generate_memories_callback writes, managed/custom memory topics, and scope-based consolidation. TRIGGER when the user asks to \"implement cross-session memory in ADK\", \"configure Vertex AI Memory Bank\", \"persist agent knowledge/preferences across conversations\", \"use PreloadMemoryTool or LoadMemoryTool\", or seed/query Memory Bank facts by scope. DO NOT TRIGGER for short-term session state (state[\"key\"]) with no cross-session need, generic RAG/document retrieval corpora, or non-Vertex memory stores (Redis, a custom vector DB) unrelated to Agent Engine Memory Bank."
version: 1.0.0
author: Actual Agentic Solutions
tags: [adk, vertex-ai, memory-bank, cross-session-memory, agent-engine]
license: Apache-2.0
compatibility: "google-adk with google-cloud-aiplatform[agent-engines] for real Memory Bank calls; scripts/ --dry-run modes require only the Python standard library (jsonschema optional, for stricter local validation)"
metadata: {}
---

- ADK Cross-Session Memory Bank Integration

- Overview
This skill wires up and directly operates Vertex AI Memory Bank: the
managed service that lets an ADK agent remember user preferences,
terminology, and facts across separate conversations instead of forgetting
everything when a session ends. It covers both layers real integrations
need — the ADK tool layer (`PreloadMemoryTool`, `LoadMemoryTool`,
`after_agent_callback`) an agent uses automatically, and the underlying
Memory Bank API (`vertexai.Client().agent_engines.memories.*`) this skill's
own scripts call directly to seed or inspect memories outside of a live
agent turn.

Grounded in the real `cross-session-memory` ADK sample
(`github.com/google/adk-samples/tree/main/core/python/cross-session-memory`)
and the Agent Platform Memory Bank docs — not invented from memory. Every
API call this skill's scripts make traces to a documented example; where a
detail (like semantic-similarity retrieval's exact parameter) wasn't
directly confirmed, the reference files say so explicitly rather than
guessing.

- Prerequisites
- For real (non-dry-run) use: `pip install google-adk
  google-cloud-aiplatform[agent-engines]` and `gcloud auth
  application-default login`, plus a GCP project with Agent Engine access.
- A `--memory-bank-name` (an Agent Engine resource:
  `projects/P/locations/L/reasoningEngines/R`) — either an existing
  instance, or one the user needs to create first
  (`client.agent_engines.create()`, see
  `references/vertex_memory_bank_api.md`).
- None of the above is required for `--dry-run` — use it to validate seed
  files and preview requests with no GCP access at all.

- Workflow

- Step 1: Decide ADK-tool wiring vs. direct API scripting
If the goal is "make my ADK agent remember things across sessions" (the
common case): wire `PreloadMemoryTool()` into the agent's `tools` and
`after_agent_callback=generate_memories_callback` per
`references/vertex_memory_bank_api.md`'s PreloadMemoryTool section — this
is two lines in any existing ADK agent, no coupling to this skill's
scripts required.
If the goal is "seed memories before the first conversation" or "check
what's currently stored" (testing, onboarding, debugging recall): use this
skill's `scripts/preload_memory.py` / `scripts/load_memory.py` directly
(Steps 2-3 below).

- Step 2: Seed memories with `preload_memory.py`
Build a facts file matching `assets/memory_bank_schema.json` (see
`assets/sample_knowledge_base.md` for a worked example spanning all four
managed topics plus a custom-topic pattern), then:
```
scripts/preload_memory.py --facts-file seed.json --dry-run
```
Fix any validation errors, THEN run for real:
```
scripts/preload_memory.py --memory-bank-name projects/P/locations/L/reasoningEngines/R \
    --facts-file seed.json --scope-json '{"user_id":"123"}'
```
- Default mode is consolidation-aware (`GenerateMemories`); only pass
  `--no-consolidate` when guaranteed-distinct records matter more than
  avoiding duplicates (e.g. a disposable test fixture) — see the script's
  own docstring for why this is the exception, not the default.
- Never seed a real user's data this way without their knowledge — see
  the closing note in `assets/sample_knowledge_base.md`.

- Step 3: Verify or inspect with `load_memory.py`
```
scripts/load_memory.py --memory-bank-name projects/P/locations/L/reasoningEngines/R \
    --scope-json '{"user_id":"123"}' --as-prompt
```
`--as-prompt` renders exactly the `<MEMORIES>` block `PreloadMemoryTool`
would inject — use this to confirm a seed actually took effect, or to
debug "why doesn't my agent know X" by checking whether the fact is even
in the scope being queried. Use `--dry-run --local-file seed.json` to
sanity-check scope-matching and rendering before touching the real API.

- Step 4: Read the domain references before answering "why" questions
- `references/vertex_memory_bank_api.md` — PreloadMemoryTool vs.
  LoadMemoryTool, the write path, session-state-vs-memory boundary, the
  full API primitive table, memory topics, local-vs-real Memory Bank.
- `references/long_term_memory_patterns.md` — scope design, Memory Bank
  vs. RAG, perspective consistency, metadata merge strategies, and the
  Cloud-Run-reuses-a-stale-instance gotcha that silently breaks topic
  config changes.
Do not answer a "why isn't this working" question from general LLM
knowledge about memory systems — check these files first; several of the
gotchas here (async consolidation, Cloud Run engine reuse) are
non-obvious and specific to this API.

- Examples

- Example 1: New ADK agent, wire memory from scratch
Input: "Add cross-session memory to my ADK agent so it remembers user
preferences."
Expected output / behavior: add `PreloadMemoryTool()` to `tools` and
`after_agent_callback=generate_memories_callback` per Step 1 — no script
invocation needed for this case. Point to
`references/vertex_memory_bank_api.md` for the consolidation-is-async
gotcha so the user doesn't expect same-session recall of something just
said.

- Example 2: Seed a team glossary before any real conversations happen
Input: "I want the support agent to already know our internal jargon
before it talks to anyone."
Expected output / behavior: build a facts file from
`assets/sample_knowledge_base.md`'s glossary section, `--dry-run` it,
then run `preload_memory.py` for real with an appropriate scope (likely a
`team_id`-based scope per `references/long_term_memory_patterns.md`, not
per-user, since the glossary applies to everyone on the team). Verify with
`load_memory.py --as-prompt`.

- Error Handling
- `preload_memory.py --facts-file` fails schema validation: fix the
  reported field(s) against `assets/memory_bank_schema.json` before
  retrying — never bypass validation by hand-editing the request past
  what the script checked.
- A real `GenerateMemories` call returns 0 generated memories: this is
  valid, not a bug — Memory Bank only persists information matching a
  configured topic (see `references/vertex_memory_bank_api.md`); check the
  target instance's topic configuration before assuming the call failed.
- A seeded fact doesn't show up in `load_memory.py` right after seeding:
  check you queried the same `scope` you seeded with (scope must match
  exactly, not just conceptually overlap) before assuming seeding failed.
- Memory Bank topic/config changes don't take effect after redeploying to
  Cloud Run: see the "Cloud Run still needs an Agent Engine" /
  reused-as-is gotcha in `references/long_term_memory_patterns.md` — a
  pre-existing engine instance is not automatically reconfigured.
- `vertexai` import fails when not using `--dry-run`: tell the user to
  `pip install google-cloud-aiplatform[agent-engines]` — don't silently
  fall back to dry-run behavior, since that would hide that nothing was
  actually written.
- A user asks for semantic/similarity-search retrieval by free-text query:
  `load_memory.py` deliberately does not implement this (the exact API
  parameter wasn't directly confirmed while building this skill) — point
  them at the live "Fetch memories" doc rather than guessing a parameter
  name that may not match the current API.

- Reference Files
- **scripts/preload_memory.py**: seeds Memory Bank from a facts file
  (`direct_memories_source`) or a conversation transcript
  (`direct_contents_source`); `--dry-run` validates and previews with no
  GCP call — run in Step 2.
- **scripts/load_memory.py**: scope-based retrieve, revision history, and
  `<MEMORIES>`-block rendering; `--dry-run --local-file` for offline
  testing — run in Step 3.
- **references/vertex_memory_bank_api.md**: ADK tool layer vs. API layer,
  PreloadMemoryTool/LoadMemoryTool, the write callback, session-state
  boundary, full API primitive table, memory topics — read in Step 1 and
  Step 4.
- **references/long_term_memory_patterns.md**: scope design, Memory Bank
  vs. RAG, perspective consistency, metadata merge strategy, deploy-path
  gotchas — read in Step 4 and whenever a seeded fact isn't behaving as
  expected.
- **assets/memory_bank_schema.json**: canonical JSON Schema for facts-file
  entries — both scripts validate against this; the single source of
  truth for the seed-file shape.
- **assets/sample_knowledge_base.md**: worked example spanning all four
  managed topics plus a custom-topic pattern — copy from this into a real
  facts file rather than inventing seed content structure from scratch.

- Output Format
Return, in order: (1) which layer applies (ADK tool wiring vs. direct API
script) and why, (2) the exact command(s) run including `--dry-run`
validation before any real write, (3) for seeding tasks, the scope used and
a `load_memory.py --as-prompt` verification of what actually landed, and
(4) any applicable gotcha from `references/long_term_memory_patterns.md`
(async consolidation, scope mismatch, Cloud Run engine reuse) that could
explain unexpected behavior. Never claim a fact was successfully
remembered without a `load_memory.py` (or equivalent) verification step
showing it in the retrieved scope.
