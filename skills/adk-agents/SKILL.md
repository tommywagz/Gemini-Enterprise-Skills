---
name: adk-agents
description: "Guides authoring of Google Agent Development Kit (ADK) agents, tools, workflows, callbacks, and state management in Python. TRIGGER when the user asks to 'write ADK agent code', 'build an agent with ADK', 'add an ADK tool', 'create an ADK callback', 'define an agent with ADK', 'use ADK state management', 'ADK Python API', 'SequentialAgent', 'ParallelAgent', 'LoopAgent', or 'build an ADK Workflow'. DO NOT TRIGGER for project scaffolding (use agents-cli-scaffold-extension), deployment to Cloud Run/GKE, general non-ADK Python scripts, or A2A multi-agent protocol workflows (use a2a-workflows)."
metadata:
  author: Google
  license: Apache-2.0
  version: 1.4.1
  requires:
    bins:
      - agents-cli
    install: "uv tool install google-agents-cli"
---

# ADK Code Reference

Activate `/google-agents-cli-workflow` first for required development phases and scaffolding steps.

## 1. Study Recipes (No Project Needed)

**Read the topic index in `references/samples.md` before answering "how do I build X".** Worked implementations exist for: sandboxed/per-user code execution, agent-loadable `SKILL.md` skills, cross-session memory, approval gates before risky actions, tool guardrails, per-user credentials, and scheduled/event-driven runs.

The index only gives you a name; the recipe is the code. Clone it and read its `AGENTS.md` before you implement anything it covers. Hand-writing a Docker or E2B sandbox wrapper, a skill loader, a moderation callback or a memory store — for a capability the index lists — means you stopped at the name.

## 2. Prerequisites for Writing Code

Do NOT write agent code until a project is scaffolded.

1. Verify project: run `agents-cli info` (proceed if config exists).
2. New project: run `agents-cli scaffold create <name>`.
3. Existing code: run `agents-cli scaffold enhance .`.

> **Language Support:** This reference covers the Python ADK SDK. Support for other languages coming soon.

## Quick Reference — Most Common Patterns

```python
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    return {"city": city, "temp": "22°C", "condition": "sunny"}

root_agent = Agent(
    name="my_agent",
    model="gemini-3.7-flash",
    instruction="You are a helpful assistant that ...",
    tools=[get_weather],
)
```

---

## Edge Cases & Error Handling

| Gotcha / Issue | Root Cause | Remediation |
|---|---|---|
| Pydantic `output_schema` breaks tool use | Setting `output_schema` enforces strict JSON mode, disabling tool calling & sub-agent delegation. | Use multi-agent delegation or sequential agents: one agent calls tools, subsequent agent formats via `output_schema`. |
| `google_search` disables AFC | Mixing `google_search` grounding tool with custom `FunctionTool` disables Automatic Function Calling. | Separate into sub-agents or use custom search function tool implementation. |
| Tool schema parsing failure | Missing docstring or untyped arguments in Python function passed to `tools=[]`. | Ensure every tool function has complete Python type annotations and Sphinx/Google-style docstrings with parameter descriptions. |
| State key collisions | Concurrent sub-agents writing to shared `state["key"]` in `ParallelAgent`. | Namespace state keys by agent or node name (e.g. `state["agent_a:output"]`). |

## Input Validation & Prerequisites

- Ensure Python >= 3.10 is installed and active in the virtual environment.
- Confirm `google-adk` package is installed (`pip install google-adk`).
- Validate model naming: use standard identifiers (e.g. `gemini-3.7-flash`, `gemini-2.5-pro`).
- For A2A communication, ensure `google-adk[a2a]` is installed and route to `a2a-workflows`.

## Fallback Instructions

If references or external doc links are unreachable:
1. Inspect local source code directly: `python3 -c "import google.adk; print(google.adk.__file__)"` and explore symbols with `dir()` or `inspect`.
2. Inspect installed tool signatures: inspect `google.adk.tools`, `google.adk.agents`, and `google.adk.workflow`.
3. Fall back to minimal working definitions using `Agent(name=..., model=..., instruction=...)`.

---

## References

Use cheatsheets for common patterns. For deep knowledge, fetch the docs index or inspect the installed package.

| Reference | When to read |
|------|-------------|
| `references/samples.md` | **Topic-indexed catalog of ADK reference recipes.** Read in workflow Phase 1 — before scaffolding and before writing code — maps a capability to the recipe that implements it. |
| `references/adk-python.md` | Core ADK API: `Agent`, tools, callbacks, plugins, state, artifacts, multi-agent systems, `SequentialAgent` / `ParallelAgent` / `LoopAgent`, custom `BaseAgent`, `ManagedAgent` (server-hosted first-party agents), A2A protocol, A2UI. Default for most agents. |
| `references/adk-workflows.md` | Graph-based Workflow API (ADK 2.0): nodes, edges, fan-out/fan-in, HITL, parallel processing. Use when you need explicit graph topology. |
| `curl https://adk.dev/llms.txt` | Docs index (every page title + URL). Fetch it, then `WebFetch` the specific page for anything beyond the cheatsheets. |
| Installed ADK package | Exact signatures and symbols — inspect the source (see "Inspecting ADK Source Code" in `references/adk-python.md`). |

## Related Skills

- `/google-agents-cli-workflow` — Development workflow, coding guidelines, and operational rules
- `/google-agents-cli-scaffold` — Project creation and enhancement with `agents-cli scaffold create` / `scaffold enhance`
- `/google-agents-cli-eval` — Evaluation methodology, dataset schema, and the eval-fix loop
- `/google-agents-cli-deploy` — Deployment targets, CI/CD pipelines, and production workflows
