---
name: agents-cli-scaffold-extension
description: "Generates a polyglot agent workspace linking a TypeScript/Hono HTTP gateway to a Python/ADK multi-agent workflow, with package manifests, boundary contracts, and run instructions. TRIGGER when users ask to 'scaffold a multi-agent polyglot workspace', 'agents-cli scaffold enhance multiple languages', 'add Node.js/Python boundaries to an agent project', or connect a Hono handler to an ADK orchestrator. DO NOT TRIGGER for standard single-agent scaffolding, a Python virtual environment alone, generic Hono endpoint authoring, or deploying an existing service."
version: 1.0.0
author: Actual Agentic Solutions
license: Apache-2.0
compatibility: "Generator: Python 3.10+ stdlib. Generated runtime: Node 20+, npm, Python 3.10+, google-adk 1.18.0. Run commands use a POSIX shell."
metadata:
  category: cli
---

# Polyglot Multi-Agent Workspace Generator

## Overview
Create a runnable local workspace with a Hono gateway, a Python ADK
planner/writer workflow, a JSON request contract, and separate dependency
manifests. The gateway creates sessions and calls the documented ADK REST API.
Use the bundled generator as an adjunct to CLI scaffolding; the skill name
does not imply an installed `agents-cli scaffold enhance` command.

## Prerequisites
- A destination whose parent directory exists, and a lowercase-hyphen project
  name. An existing repository is integrated through a new staging directory.
- Python 3.10+ for generation; Node 20+, npm, and Python venv/pip for running.
- Model access only for live mode. Demo mode uses real ADK agents with
  deterministic output and needs no provider credential.
- Defaults: Apache-2.0 skill license, npm workspaces, ports 3000/8000,
  app name `orchestrator`, model `gemini-2.5-flash`, local loopback listeners.
  State these defaults when the user leaves the corresponding inputs unspecified.

## Workflow

### 1. Establish the language boundary
Identify the target directory, app name, port constraints, and requested workflow.
Read [polyglot_workspace_patterns.md](references/polyglot_workspace_patterns.md)
for session ownership and the two-agent pattern. The starter supplies a
planner→writer sequence; adapt its agent instructions to the user's workflow
after generating. Do not silently substitute it for a specified task order.
For a single-language request, use ordinary framework scaffolding instead.

### 2. Preview the generated layout
From this skill's directory, run (replace the output path with the user's):

```sh
python3 scripts/generate_polyglot_workspace.py --name my-workspace --output /path/to/new-workspace --dry-run
```

Read the JSON plan. It validates substitutions, file paths, JSON and Python
syntax without creating the output directory. See
[cli_scaffold_commands.md](references/cli_scaffold_commands.md) for all flags.
If the target already exists, choose a fresh sibling staging directory. The
generator deliberately has no overwrite flag.

### 3. Generate
Run the same command without `--dry-run`. Confirm `mode: generated` and the
`workspace.files` list. The script renders
`assets/scaffold_template_manifest.json` and its linked templates into twelve
files including `workspace.json`; its structure is described by
`assets/workspace_layout_schema.json`.

For an existing repo, inspect its package manager and Python environment first.
Merge the staged `apps/` and `contracts/` files selectively; reconcile workspace
and script keys instead of replacing the repo's package manifest. Preserve its
documentation and dependency locks. Do not run the generator on the repo root.

### 4. Install and build in the generated workspace
Follow generated `WORKSPACE.md` from the workspace root:

```sh
npm install
python3 -m venv .venv
.venv/bin/python -m pip install -r apps/agents/requirements.txt
npm run build
```

These install steps need package registry access; the generator itself does not.
If installation is unavailable, report generation/syntax checks only and name
the unrun checks. Keep the npm lockfile in the generated project and lock the
Python transitive dependencies when adopting the scaffold into CI.

### 5. Verify the cross-runtime path
Start ADK and Hono in separate terminals using the commands in `WORKSPACE.md`.
Use `WORKSPACE_DEMO=1` first. Verify `/list-apps`, gateway `/health`, and a
`POST /api/message` with `{"text":"Hello polyglot"}`. The demo must return
`DEMO: Hello polyglot` and a generated session ID. A health response alone does
not verify the agent connection. Invalid input must return 400; a stopped ADK
server must produce 502 from the gateway.

Stop both processes with Ctrl+C when finished. For live inference, configure
the provider environment for Python, restart without demo mode, and exercise
the same route. Report whether live inference was actually tested; demo success
establishes wiring, not model quality or availability.

### 6. Hand off
Return the generated path, layout, modified integration files (if any), exact
run commands, selected versions, and checks run. Summarize how to change the
workflow in `apps/agents/<agent_name>/agent.py`. Carry forward the identity,
session lifecycle, and timeout semantics documented in the architecture reference.

## Examples
- “Create a Hono front door for a Python agent team.” Generate the default
  two-agent workspace, build it, and verify the demo through the gateway.
- “Add Node.js/Python boundaries to this npm monorepo.” Inspect its workspaces,
  generate in a fresh sibling directory, and integrate selected files without
  overwriting its package.json. Re-run the host repo's build checks.
- “Just create a virtualenv for one Python agent.” This skill does not apply.

## Error handling
- Exit 2: invalid name/model/ports, existing destination, missing parent or
  template, malformed template data, or write failure. Surface stderr; do not
  treat a failed or dry-run plan as generated files.
- ADK app missing: check the Python package `__init__.py`, exported `root_agent`,
  and `apps/agents` positional directory. App name must match the package folder.
- Gateway 502: inspect ADK startup and model configuration; check `ADK_BASE_URL`.
  No upstream response body is echoed to callers.
- Gateway 504: the request exceeded 60 seconds. The agent may still be running;
  do not automatically retry and duplicate work.
- If a bundled template/reference is missing, identify the missing resource
  and repair the package before generating; do not invent replacement CLI APIs.

## Reference files
- [scripts/generate_polyglot_workspace.py](scripts/generate_polyglot_workspace.py):
  deterministic renderer used in steps 2–3; no installations or subprocesses.
- [references/polyglot_workspace_patterns.md](references/polyglot_workspace_patterns.md):
  architecture, API contracts, state ownership, and official sources; step 1.
- [references/cli_scaffold_commands.md](references/cli_scaffold_commands.md):
  exact flags, directory layout, launch flow, and version baseline; steps 2–5.
- [assets/scaffold_template_manifest.json](assets/scaffold_template_manifest.json):
  file destinations, template sources, inline templates, and substitution variables.
- [assets/workspace_layout_schema.json](assets/workspace_layout_schema.json):
  JSON Schema for the generated descriptor; generator also enforces distinct ports
  and valid non-keyword Python app names.
- [tests/verification.md](tests/verification.md): creator checks and reproducible
  generator/runtime test commands for package maintenance.

## Output format
Report generation status, destination tree, chosen names/ports/model, install and
launch commands, and validation evidence. Distinguish dry-run, built, demo-tested,
and live-model-tested states. Do not claim that scaffolding registers a Google
Agents CLI extension or deploys the application.
