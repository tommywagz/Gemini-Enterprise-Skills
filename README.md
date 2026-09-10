# Gemini Enterprise Agent Skills Garden

Welcome to the **Gemini Enterprise Agent Skills Garden** repository. This project is a state-of-the-art collaborative, multi-agent development environment designed to autonomously discover, author, evaluate, and refine specialized **Agent Skills** (modular prompt, workflow, and logic packages) for enterprise use cases.

The repository uses a squad of four specialized AI agents coordinated through a central orchestration config (`opencode.json`) and a shared real-time communication folder (`jobs/`) to automate the entire skill-building lifecycle.

---

## 🎯 Project Goal

The primary goal of this repository is to build a robust, scalable "garden" of production-ready, token-efficient, and highly reusable agent skills. These skills conform to a strict architectural template, ensuring they can be consumed by advanced agent systems (such as Claude Code, Claude Agent SDK, or Google ADK) to perform complex tasks (e.g., A2A workflows, autonomous payments via AP2, UCP merchant servers, etc.).

---

## 📂 Repository Layout

```
/home/tow73/AAS/Gemini-Enterprise-Skills/
├── README.md               # This documentation file.
├── AGENTS.md               # High-level objectives, use cases, and targets.
├── LICENSE                 # Repository license (Apache-2.0).
├── opencode.json           # Orchestration schema & LLM configuration for the squad.
├── .gitignore              # Git ignore rules (ignores /jobs, credentials, temporary folders).
│
├── .agents/                # System prompts & rules defining the agent squad.
│   ├── orchestrator.md     # Lead release manager: coordinates dispatches & merges branches.
│   ├── finder.md           # Finder worker: searches registries for matching skills.
│   ├── creator.md          # Creator worker: drafts new skills from source material.
│   ├── evaluator.md        # Evaluator worker: evaluates, refines, and promotes drafts.
│   ├── shared-agent-rules.md # Coordination, state-polling, and Git protocols for workers.
│   └── skills/             # Meta-skills used directly by the agents to perform their work:
│       ├── find-skill/     # Skill used by Finder to discover existing packages.
│       ├── write-skill/    # Skill used by Creator to draft skill packages.
│       └── evaluate-skill/ # Skill used by Evaluator to run tests and refine skills.
│
├── skills/                 # The "Garden" - finalized, production-ready agent skills.
│   ├── a2a-workflows/      # Multi-agent collaboration & communication workflows.
│   ├── adk-agents/         # Core Google Agent Development Kit (ADK) agent design.
│   ├── ucp-merchant-servers/ # Universal Commerce Protocol (UCP) payment integration.
│   ├── find-skill/         # (Symlinked or copied) Skill package discovery.
│   ├── write-skill/        # (Symlinked or copied) Skill package scaffolding/writing.
│   └── evaluate-skill/     # (Symlinked or copied) Skill package evaluation & scoring.
│
├── jobs/                   # [Untracked/Symlinked] Real-time squad coordination directory.
│   ├── README.md           # Contract and technical design of jobs-based orchestration.
│   ├── backlog.json        # Master task tracker & skill backlog.
│   ├── inbox/              # Dispatch queues for workers (finder.json, creator.json, evaluator.json).
│   ├── status/             # Real-time state files for each agent (orchestrator.json, finder.json, etc.).
│   └── log.md              # Chronological event log of the squad's progress.
│
└── scripts/                # Shared developer/squad tooling.
    └── validate_skill_token_efficiency.py # Pre-commit/CI linter for token efficiency.
```

---

## 🗺️ Skill Allocation & Deployment Roadmap

This repository acts as a staging garden. Once skills are fully implemented, tested, and evaluated, they are distributed to their optimal destination repositories. Below is the complete allocation plan and current completion status:

### 1. New Skills Staged in AGENTS.md
| Skill / Use Case | Destination Repository | Status / Clarification | Potential Usefulness & Rationale |
|---|---|---|---|
| `model-governance` | `https://github.com/google/agents-cli/tree/main/skills` | 🔴 **Unstarted (Backlog)** | Handles local LLM profiling and `opencode.json` launch command patching within the developer’s CLI. |
| `real-estate-floorplan` | `https://github.com/google/adk-samples/tree/main/skills` | 🔴 **Unstarted (Backlog)** | A complex spatial research & vector CAD/BIM workflow; showcases multi-platform MCP integration. |

### 2. Sibling Skills (from `@skills/**` folder)
| Local Skill Name | Destination Repository | Status / Clarification | Potential Usefulness & Rationale |
|---|---|---|---|
| `a2a-workflows` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Full multi-agent orchestration and A2A communication wrappers. Fully verified with evaluation report. |
| `adk-agents` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | Primary developer cheatsheet/reference for the core Google ADK Python SDK. Fully verified with evaluation report. |
| `ap2-agent-payments` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Commerce payment authorization sample using SD-JWT credentials and role separation. Fully verified with evaluation report. |
| `evaluate-skill` | `https://github.com/google/agents-cli/tree/main/skills` | 🟡 **System Meta-Skill** | Meta-tooling used by the Evaluator Agent. Stable for squad execution; pending standalone garden-testing promotion. |
| `find-skill` | `https://github.com/google/agents-cli/tree/main/skills` | 🟡 **System Meta-Skill** | Discovery and pre-screening of MCP/Composio skills used by the Finder Agent. Stable for squad execution; pending standalone garden-testing promotion. |
| `integrate-repo` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | CLI tool for style compliance and CI gate preflights. Fully verified with evaluation report. |
| `ucp-merchant-servers` | `https://github.com/google/adk-samples/tree/main/skills` | 🔵 **In Progress / Evaluation** | Server-side FastAPI/Hono UCP integration sample. Currently has test suite scaffolded; final evaluation report is pending. |
| `write-skill` | `https://github.com/google/agents-cli/tree/main/skills` | 🟡 **System Meta-Skill** | Scaffolds standard skill packages. Used by the Creator Agent. Stable for squad execution; pending standalone garden-testing promotion. |

---

## 🤝 Multi-Agent Squad & Coordination

Instead of relying on a single monolith, the repository coordinates an automated software delivery team where each agent runs in its own **isolated Git worktree on its own Git branch**. 

To bypass the latency of committing and merging git changes just to communicate, the agents collaborate in real-time through the shared `/jobs` directory (which is symlinked into every agent's worktree and listed in `.gitignore` to prevent conflicts).

### The Squad Roles
1. **Orchestrator** (`.agents/orchestrator.md`): Runs on `main`. Manages the master backlog, dispatches tasks to worker inboxes, monitors status, performs verification checks, and merges successfully validated worker branches into `main` using a clean `--no-ff` merge protocol.
2. **Finder** (`.agents/finder.md`): Locates existing agent skills matching the target specifications. It executes the `find-skill` meta-skill to search registry sources.
3. **Creator** (`.agents/creator.md`): Takes source specifications and designs a compliant agent skill from scratch using the `write-skill` meta-skill.
4. **Evaluator** (`.agents/evaluator.md`): Picks up drafts from `drafts/`, runs comprehensive evaluation suites, scores them, and refines them up to 3 times. Successful skills are promoted into `skills/`.

### Configuration (`opencode.json`)
The squad is configured to use specialized, state-of-the-art LLMs mapped to specific system prompts:
- **Orchestrator**: `vertex/gemini-3.6-flash`
- **Finder**: `vertex/gemini-3.5-flash`
- **Creator**: `anthropic/claude-opus-5`
- **Evaluator**: `openai/o3`

---

## 📦 Standard Skill Package Format

Every skill in the `skills/` directory adheres to a highly modular, readable, and structured bundle:

```
skills/<skill-name>/
├── SKILL.md                # Main prompt/workflow instruction file with YAML frontmatter.
├── references/             # Markdown-based external specifications, SDK guides, or APIs.
├── scripts/                # Reusable automation and execution scripts.
├── assets/                 # Static templates, config files, and JSON schemas.
└── tests/                  # Automated test configurations and evaluation suites.
    ├── eval_suite.json     # Test cases and expected assertions.
    └── evaluation_report.md # Reports compiled by the Evaluator agent.
```

### `SKILL.md` Architectural Design
- **YAML Frontmatter**: Details the name, description, tags, version, author, compatibility constraints, and target metadata.
- **Overview & Prerequisites**: High-level context and required environment constraints (e.g., packages, engines).
- **Core Workflow**: Detailed, step-by-step instructions for the target agent to execute, including clear trigger criteria (`TRIGGER when...`) and boundaries (`DO NOT TRIGGER when...`).
- **Compact Cases**: Concrete examples of expected behaviors in specific conditions.

---

## 🛡️ Guardrails & Quality Control

To maintain low context-token consumption and ensure extreme reliability, all skill packages are verified using the repository linter.

### Linter (`scripts/validate_skill_token_efficiency.py`)
This tool enforces strict token-efficiency guardrails on every skill package:
1. **Description Character Limit**: YAML frontmatter descriptions must be under **1024 characters** to ensure fast parsing.
2. **Word Count Budget**: The active markdown body of a skill is constrained to **6,250 words** (roughly 5,000 tokens) to ensure the agent's context is preserved for execution.
3. **Dead Resource Elimination**: All files located in `references/`, `scripts/`, or `assets/` must be explicitly cited inside `SKILL.md`. Unreferenced files are flagged as dead code.
4. **De-duplication**: To prevent token bloat, the linter blocks paragraph duplication between a skill's active instruction body (`SKILL.md`) and its supporting reference documents (`references/`).

To run the efficiency check locally, execute:
```bash
python3 scripts/validate_skill_token_efficiency.py
```

---

## 🛠️ Developer Guide

### Prerequisites
- Python >= 3.10
- Git (configured to support worktrees)
- Node.js (if utilizing `opencode` orchestration commands)

### Managing Local Changes
- Do not commit changes directly to `main` without checking current agent worktree tasks.
- **Never track files in `jobs/`**: This directory is shared globally and ignored by git to avoid dirty working trees and merge conflicts.
- Always validate skills using `validate_skill_token_efficiency.py` before proposing additions.
