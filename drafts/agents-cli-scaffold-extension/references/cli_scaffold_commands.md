# Scaffold CLI and execution flow

## Contents
- [Generator](#generator)
- [Generated layout](#generated-layout-twelve-files)
- [Install and launch](#install-and-launch)
- [Version baseline](#version-baseline)

## Generator

Run from the installed skill directory; output is independent of current cwd:

```sh
python3 scripts/generate_polyglot_workspace.py --name support-team --output /existing/parent/support-team --agent-name support_agent --web-port 3100 --adk-port 8100 --model gemini-2.5-flash --dry-run
```

Remove `--dry-run` to write the project. Both invocations validate before
writing; dry-run does not create the destination or temporary files.

| Flag | Default / contract |
|---|---|
| `--name` | Required; lowercase-hyphen name, starts with letter, ≤64 chars |
| `--output` | Required new directory; parent must exist; existing symlinks rejected |
| `--agent-name` | `orchestrator`; lowercase Python identifier ≤64 chars, no keywords |
| `--model` | `gemini-2.5-flash`; conservative model ID characters, ≤128 chars |
| `--web-port` | 3000; integer 1024–65535 |
| `--adk-port` | 8000; same range, different from web port |
| `--dry-run` | Validate/render plan, no filesystem writes |

Exit 0 is a successful plan or generation; read the JSON `mode` to distinguish
them. Exit 2 is an input, template, or I/O error. Normal write failures remove
only the directory created by that invocation. A crash can leave a partial
directory; inspect it and use a fresh destination on retry. There is no force
overwrite, shell evaluation, package installation, or CLI registration.

## Generated layout (twelve files)

```text
support-team/
  .gitignore
  WORKSPACE.md
  package.json
  workspace.json
  apps/
    web/
      package.json
      tsconfig.json
      src/app.ts
      src/index.ts
    agents/
      requirements.txt
      support_agent/__init__.py
      support_agent/agent.py
  contracts/message.schema.json
```

`workspace.json` records the configuration and complete generated file list.
Validate it against `assets/workspace_layout_schema.json` with a Draft 2020-12
validator if one is available. The stdlib generator validates its own fixed
contract, JSON parseability, and Python syntax; it is not a schema engine.
The manifest maps destination paths to inline contents or `assets/templates/`
files. `@@name@@`-style tokens are literal replacements. Unknown variables,
parent traversal, absolute template destinations, and duplicate destinations
are errors. Values cannot inject quotes or code through these substitutions.

## Install and launch

All of these commands run from the generated workspace root:

```sh
npm install
python3 -m venv .venv
.venv/bin/python -m pip install -r apps/agents/requirements.txt
npm run build
```

Terminal 1 (the example's custom ADK port):

```sh
WORKSPACE_DEMO=1 .venv/bin/adk api_server --host 127.0.0.1 --port 8100 apps/agents
```

Terminal 2:

```sh
npm run start:web
```

Test in terminal 3:

```sh
curl --fail http://127.0.0.1:3100/api/message -H 'Content-Type: application/json' -d '{"text":"Hello"}'
```

Expected demo text: `DEMO: Hello`. Ctrl+C stops each server. For development,
`npm run dev:web` uses tsx watch. `PORT` changes Hono's port, `ADK_BASE_URL`
changes its upstream origin, and `ADK_MODEL` changes Python's live model.
If changing the Python server port after generation, also set `ADK_BASE_URL`.
All defaults and commands are rendered into `WORKSPACE.md` with the chosen ports.

## Version baseline

Hono 4.9.8, @hono/node-server 1.19.1, TypeScript 5.9.2, tsx 4.20.5,
@types/node 22.18.6, google-adk 1.18.0. These are compatibility pins, not claims
to be the newest releases. Lock resolved transitive versions in the consuming
project. Validate upgrades by compiling TypeScript and exercising the full
session-create→run→model-text response path.

Google's [Agents CLI](https://github.com/google/agents-cli) is a related workflow
entry point. This package provides its own Python command; do not present
`agents-cli scaffold enhance` as a verified upstream command. If integrating
with an installed CLI, inspect that version's help/extension API first.
