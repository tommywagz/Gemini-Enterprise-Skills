# Vertex AI Memory Bank: ADK Tools and the Underlying API

## Contents
- Two layers: ADK tools vs. the Memory Bank API
- PreloadMemoryTool vs. LoadMemoryTool
- The write path: `generate_memories_callback`
- Graph/session state boundaries: where state ends and memory begins
- The underlying Memory Bank API primitives
- Memory topics: managed and custom
- Local dev vs. real Memory Bank

Grounded in `google-adk`'s public API (`google.adk.tools.preload_memory_tool`,
`google.adk.memory`), the `cross-session-memory` ADK sample
(`github.com/google/adk-samples/tree/main/core/python/cross-session-memory`),
and the Agent Platform Memory Bank docs
(`docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/*`,
fetched 2026-09-11). Re-verify exact method signatures against those sources
before depending on this file for a production integration — Memory Bank is
still an evolving API.

## Two layers: ADK tools vs. the Memory Bank API

There are two ways to talk to Memory Bank, and this skill's scripts operate
at the *second* layer, not the first:

1. **ADK tool layer** (`PreloadMemoryTool`, `LoadMemoryTool`,
   `after_agent_callback`) — the way a running ADK agent recalls and writes
   memories automatically, mid-conversation. You wire these into an
   `Agent`/`App`; ADK handles the API calls for you.
2. **Memory Bank API layer** (`vertexai.Client().agent_engines.memories.*`)
   — the lower-level SDK calls ADK's tools use internally. `scripts/
   preload_memory.py` and `scripts/load_memory.py` call this layer directly,
   which is useful for seeding memories before an agent's first turn,
   inspecting what's stored outside of a live conversation, or integrating
   Memory Bank with a non-ADK framework (LangGraph, a custom agent).

## PreloadMemoryTool vs. LoadMemoryTool

Both recall memories; they differ in *when* and *how much control the model
has*:

| Tool | When it runs | Model involvement |
|---|---|---|
| `PreloadMemoryTool()` | Automatically, at the start of every turn | None — memories are injected into the system instruction before the model sees the turn |
| `LoadMemoryTool()` | On-demand | The model decides when to call it, like any other tool |

```python
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

root_agent = Agent(
    ...,
    tools=[..., PreloadMemoryTool()],   # recall: automatic, every turn
)
```

`PreloadMemoryTool` is the right default for "the agent should always know
this about the user" (preferences, identity facts). `LoadMemoryTool` fits
better when memory lookups are occasional and you'd rather not spend the
retrieval cost/latency on every single turn regardless of whether it's
needed.

## The write path: `generate_memories_callback`

Memories aren't written automatically just because `PreloadMemoryTool` is
present — an agent needs an explicit write path, typically an
`after_agent_callback`:

```python
from google.adk.agents.callback_context import CallbackContext

async def generate_memories_callback(callback_context: CallbackContext):
    """Sends the session's events to Memory Bank for memory generation."""
    await callback_context.add_session_to_memory()

root_agent = Agent(
    ...,
    after_agent_callback=generate_memories_callback,
)
```

`add_session_to_memory()` ships the *entire* session's events for
extraction. For incremental processing (e.g. only send the latest turn, not
the whole history again), use `callback_context.add_events_to_memory(events=...)`
with just the subset you want processed.

**Consolidation is asynchronous.** A fact told in session 1 is extracted and
consolidated *after* that turn — it shows up starting in a *later* session,
not necessarily instantly within the same one. Don't design a demo that
expects same-session recall of something just said.

## Graph/session state boundaries: where state ends and memory begins

Both are part of ADK's context model, but they answer different questions:

| Need | Solution |
|---|---|
| Within one conversation (form state, a multi-step task's intermediate values) | **Session state** — `state["key"]`, scoped session/`user:`/`app:`/`temp:` by prefix |
| Across conversations (remember a fact or preference the *next* session should already know) | **Memory Bank** — write via the callback above, recall via `PreloadMemoryTool`/`LoadMemoryTool` |

```python
# Session-specific (default) — gone when the session ends
state["booking_step"] = 2
# User-persistent across sessions, but NOT consolidated/extracted like Memory Bank —
# this is a raw key-value store scoped to the user, not a fact-extraction pipeline
state["user:preferred_language"] = "en"
```

The easy mistake: reaching for `state["user:..."]` to persist something that
should really go through Memory Bank's extraction/consolidation (so it
dedupes against contradictory facts over time), or reaching for Memory Bank
for something that's really just this conversation's scratch state (adding
API latency and consolidation risk for no benefit). Rule of thumb: if the
value should survive a `DELETED` action from a later contradictory
statement (see below), it belongs in Memory Bank, not `state["user:..."]`.

## The underlying Memory Bank API primitives

These are what `scripts/preload_memory.py` and `scripts/load_memory.py` call
via `vertexai.Client().agent_engines.memories`:

| Call | Purpose |
|---|---|
| `memories.generate(name=..., direct_memories_source={"direct_memories":[{"fact":...}]}, scope=...)` | Consolidation-aware write of pre-extracted facts — the common seeding path |
| `memories.generate(name=..., direct_contents_source={"events":[...]}, scope=...)` | Consolidation-aware extraction from raw conversation turns (like the ADK write path, but callable directly) |
| `memories.generate(name=..., vertex_session_source={"session": SESSION_NAME}, scope=...)` | Extraction from an Agent Platform Sessions resource instead of inline events |
| `memories.create(name=..., fact=..., scope=...)` | Raw write, no extraction, no consolidation — can create duplicates for the same scope; use sparingly |
| `memories.retrieve(name=..., scope=...).page` | Scope-based fetch of every memory matching that scope |
| `memories.revisions.list(name=MEMORY_NAME)` | History of a single memory's extraction/consolidation over time |
| `memories.purge(name=..., filter=..., filter_groups=..., force=...)` | Criteria-based bulk delete |
| `memories.delete(name=MEMORY_NAME)` | Delete one memory by resource name |

`generate()` is a **long-running operation**. Each generated memory carries
an `action`: `CREATED` (novel fact), `UPDATED` (merged with an existing
memory), or `DELETED` (new information contradicted an existing memory —
e.g. "forget my dietary preferences" against `EXPLICIT_INSTRUCTIONS`). By
default it blocks until done (`config={"wait_for_completion": True}`); pass
`False` to run it in the background for production agents that shouldn't
add this latency to the current turn.

## Memory topics: managed and custom

Memory Bank only persists information matching a **configured topic** —
anything outside those topics is not extracted, regardless of how the
conversation goes. Four managed topics exist:

- `USER_PERSONAL_INFO` — names, relationships, hobbies, important dates
- `USER_PREFERENCES` — likes, dislikes, preferred styles
- `KEY_CONVERSATION_DETAILS` — milestones, task outcomes
- `EXPLICIT_INSTRUCTIONS` — things the user asks the agent to remember/forget

Custom topics need a `label` + `description` defined when the Memory Bank
instance itself is configured (see `app/app_utils/memory_config.py` in the
`cross-session-memory` sample for the `MemoryBankCustomizationConfig` wiring
— it's the one shared config both Agent Engine and Cloud Run deploy paths
consume). Custom topics work best with a few worked examples included in
that same configuration, since the extraction prompt has nothing to pattern
-match against otherwise.

Direct pre-extracted facts (`direct_memories_source`, what
`preload_memory.py --facts-file` uses) are **not** re-classified against
topics on write — the `topic` field in `assets/memory_bank_schema.json` is
for your own seed-file bookkeeping, not an API-enforced filter for that
write path.

## Local dev vs. real Memory Bank

- **Local dev**: `InMemoryMemoryService` — nothing persists across process
  restarts. Fine for iterating on agent logic, useless for actually testing
  cross-session recall.
- **Real Memory Bank**: only active when `memory_service_uri=agentengine://...`
  is set (Cloud Run wires this automatically by finding-or-creating an
  Agent Engine instance at startup; `adk web` needs the flag passed
  explicitly: `--memory_service_uri=agentengine://<RESOURCE_NAME>`).
- **Memory Bank always lives on an Agent Engine instance**, even when your
  agent itself is deployed to Cloud Run rather than Agent Engine — the
  "container" deploy path still finds-or-creates one purely for session +
  memory storage. See `references/long_term_memory_patterns.md` for the
  gotcha this creates around updating an already-created engine's topic
  configuration.
