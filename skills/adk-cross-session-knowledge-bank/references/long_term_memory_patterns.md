# Long-Term Memory Patterns: Terminology Persistence & Context Recall

## Contents
- Seeding a team glossary as memory (vs. RAG)
- Scope design: per-user vs. per-user-per-session
- Perspective consistency matters for consolidation
- Metadata and merge strategy
- Recall patterns: automatic injection vs. manual prompt assembly
- Deploy-path gotchas that affect whether seeding actually takes effect

Practical patterns for using Memory Bank to persist terminology and
preferences across sessions, building on the API primitives in
`references/vertex_memory_bank_api.md`. Grounded in the `cross-session-memory`
ADK sample's `AGENTS.md` (`github.com/google/adk-samples/tree/main/core/python/cross-session-memory`)
and the Memory Bank `generate-memories` doc, fetched 2026-09-11.

## Seeding a team glossary as memory (vs. RAG)

Memory Bank and RAG solve different problems — don't reach for Memory Bank
for a large, static reference corpus:

| Use Memory Bank when... | Use RAG / a retrieval corpus when... |
|---|---|
| The facts are about *this specific user* (their preferences, their team's jargon, what they've told the agent) | The facts are *general reference material* everyone querying the agent should be able to look up (a product manual, a full API reference) |
| The set is small and personal — dozens to low hundreds of facts per scope | The set is large and shared — thousands of documents |
| Facts should self-consolidate (a new statement can update or delete an old one) | Documents are versioned/replaced explicitly, not "merged" by an LLM |

`assets/sample_knowledge_base.md`'s "team terminology glossary" example
works as Memory Bank content specifically because it's scoped to *this
team's* jargon a *specific user* needs recalled personally — if you're
building a company-wide glossary every user should be able to query, that's
a RAG corpus, not a Memory Bank seed.

## Scope design: per-user vs. per-user-per-session

`scope` controls what's eligible for consolidation together — pick it based
on how broadly a fact should apply:

- `{"user_id": "123"}` — the default and most common. A preference or fact
  that should follow the user across every session.
- `{"user_id": "123", "session_id": "456"}` — narrower, session-scoped
  facts. Useful for facts that are only relevant to one ongoing task (e.g.
  "the current support ticket is about a billing dispute") that shouldn't
  bleed into unrelated future sessions.
- Custom scopes (e.g. `{"team_id": "platform-eng"}`) for facts shared across
  a *group* of users rather than one individual — useful for exactly the
  team-glossary use case, since every team member's agent session can pull
  the same `team_id` scope.

Only memories with **identical** scope are considered for consolidation —
`{"user_id": "123"}` and `{"user_id": "123", "session_id": "456"}` are
different scopes and won't merge with each other even though one implies
the other conceptually. Pick one scope shape per kind of fact and stay
consistent, rather than mixing granularities for the same fact type.

## Perspective consistency matters for consolidation

Memory Bank's default generation perspective is **first-person** (e.g. "I
live in Austin" not "The user lives in Austin"). When seeding pre-extracted
facts via `direct_memories_source` (what `preload_memory.py --facts-file`
uses), write them in that same first-person perspective — `assets/
memory_bank_schema.json` and `assets/sample_knowledge_base.md` both follow
this convention deliberately. Mixing perspectives across seeded and
organically-extracted memories in the same scope makes consolidation
compare semantically-different-looking strings that actually mean the same
thing, which can produce duplicate-looking memories the model then has to
reconcile via later contradiction-based deletion instead of clean
consolidation up front.

## Metadata and merge strategy

Attach structured metadata (`string_value` / `double_value` / `bool_value` /
`timestamp_value`) to memories for filtering or lifecycle management — e.g.
tagging seeded facts with `{"source": {"string_value": "onboarding-form"}}`
so you can later distinguish "the user told the agent this in conversation"
from "this was seeded from a settings form." Three merge strategies control
how new metadata interacts with existing memories during consolidation:

- `MERGE` (default) — combine with existing metadata; new values win on key
  collision.
- `OVERWRITE` — replace the metadata entirely.
- `REQUIRE_EXACT_MATCH` — only consolidate with memories whose metadata is
  identical to what's being submitted; anything else is treated as a
  distinct, non-matching memory even in the same scope.

`REQUIRE_EXACT_MATCH` is useful when you deliberately want seeded facts
(tagged `source: onboarding-form`) to never silently merge with organically
extracted ones (untagged, or tagged `source: conversation`) — otherwise a
later conversational statement could quietly overwrite a fact the user
explicitly set in a settings form.

## Recall patterns: automatic injection vs. manual prompt assembly

Two ways to get memories in front of the model, matching the two API layers
in `references/vertex_memory_bank_api.md`:

1. **`PreloadMemoryTool`** (ADK layer) — zero extra code, memories are
   injected into the system instruction automatically every turn. Use this
   for the common case.
2. **Manual retrieve + template** (API layer, what `load_memory.py
   --as-prompt` demonstrates) — call `memories.retrieve(scope=...)`
   yourself and render the results into a prompt block, e.g. with the
   `<MEMORIES>` template shown in the Memory Bank API quickstart. Use this
   when you need to inspect or filter memories *before* they reach the
   model (e.g. drop anything tagged with a `source` you don't trust for
   this particular use case), which `PreloadMemoryTool`'s automatic
   injection doesn't give you a hook for.

## Deploy-path gotchas that affect whether seeding actually takes effect

From the `cross-session-memory` sample's `AGENTS.md` (verified against the
actual source, not paraphrased from memory):

- **Cloud Run still needs an Agent Engine.** Even the "container" deploy
  path finds-or-creates an Agent Engine instance purely for session +
  memory storage — Memory Bank always lives on Agent Engine regardless of
  where your agent's request-handling code runs.
- **A pre-existing Agent Engine instance found by the Cloud Run path is
  reused as-is.** If you change your topic configuration
  (`memory_bank_config` / `MemoryBankCustomizationConfig`) after that
  instance already exists, the Cloud Run deploy path will **not**
  re-apply it — only the Agent Engine deploy path's `deploy.py`
  re-applies `context_spec` on update. If a topic change isn't taking
  effect, check whether you're on the Cloud Run path reusing a stale
  instance.
- **Local `InMemoryMemoryService` seeding doesn't persist.** Running
  `preload_memory.py` (or any real seeding) only has a lasting effect
  against a real `agentengine://` instance — seeding while `adk web` is
  running without `--memory_service_uri` set will look like it worked but
  vanishes on restart, the same as any other local-only memory.
