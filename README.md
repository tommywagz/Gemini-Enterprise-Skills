# Gemini Enterprise Agent Skills Garden

Welcome to the **Gemini Enterprise Agent Skills Garden** repository. This project is a state-of-the-art collaborative, multi-agent development environment designed to autonomously discover, author, evaluate, and refine specialized **Agent Skills** (modular prompt, workflow, and logic packages) for enterprise use cases.

The repository uses a squad of four specialized AI agents coordinated through a central orchestration config (`opencode.json`) and a shared real-time communication folder (`jobs/`) to automate the entire skill-building lifecycle.

---

## 🎯 Project Goal

The primary goal of this repository is to build a robust, scalable "garden" of production-ready, token-efficient, and highly reusable agent skills. These skills conform to a strict architectural template, ensuring they can be consumed by advanced agent systems (such as Claude Code, Claude Agent SDK, or Google ADK) to perform complex tasks (e.g., A2A workflows, autonomous payments via AP2, UCP merchant servers, etc.).

---

## 🗺️ Skill Allocation & Deployment Roadmap

This repository acts as a staging garden. Once skills are fully implemented, tested, and evaluated, they are distributed to their optimal destination repositories. Below is the complete allocation plan and current completion status:

### Complete Skill Catalog

The following table is the single catalog for every unique skill package under `skills/`, including active skills, meta-skills, and staged blueprints. The `real-estate-floorplan` package under `drafts/` is its draft lineage and is represented by the active package row.

| Skill (folder) | Description | Destination | Status | Primary use case |
|---|---|---|---|---|
| `a2a-workflows` | A2A multi-agent workflows with host-agent orchestration and sub-agent communication. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Resolve agent cards and delegate tasks via A2A. |
| `adk-agents` | ADK agent, tool, callback, and state-management reference patterns. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Bootstrap core ADK agent components. |
| `adk-cross-session-knowledge-bank` | Vertex AI Memory Bank integration for cross-session ADK agent memory. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Persist preferences and terminology across conversations. |
| `adk-durable-human-in-the-loop` | Durable asynchronous HITL approval gates with `LongRunningFunctionTool` and signed webhooks. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Pause and resume risky workflows across process lifetimes. |
| `adk-long-horizon-harness` | Headless ADK agents triggered by Pub/Sub or cron with context compaction. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Manage multi-day background workflows. |
| `adk-oauth-user-consent-flow` | User-authorized OAuth 2.0 flows for ADK Workspace integrations. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Access user data with consented credentials. |
| `agents-cli-benchmark-eval` | Local agent dataset scoring with JUnit XML and Markdown reports. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Perform CI accuracy testing. |
| `agents-cli-conformance-tester` | Local MUST/SHOULD/MAY conformance tests for UCP or A2A servers. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Run pre-flight protocol compatibility checks. |
| `agents-cli-plugin-moderator` | Runner-wide ADK safety guardrails, content filters, and exfiltration prevention. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Enforce safety policies across sub-agents. |
| `agents-cli-scaffold-extension` | Polyglot TypeScript/Hono and Python/ADK agent workspace generator. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Scaffold multi-language agent environments. |
| `ap2-agent-payments` | AP2 payment agents using SD-JWT Checkout and Payment Mandates. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Delegate bounded autonomous spend with audit trails. |
| `evaluate-skill` | Agent Skill evaluation for routing accuracy, performance, and security. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Run trigger, performance, and security evaluations. |
| `find-skill` | Safe discovery and installation of Skills, MCP servers, and Composio integrations. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Discover pre-vetted capabilities. |
| `gcp-cost-optimizer` | GCP waste audit with reviewable Terraform cost remediations. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Reduce idle or over-provisioned resource spend. |
| `gcp-iam-privilege-audit` | GCP IAM usage audit with least-privilege Terraform proposals. | [Google Skills](https://github.com/google/skills/tree/main) | 🟢 **Completed & Promoted** | Harden broad roles and service-account access. |
| `gcp-kubernetes-resource-triage` | GKE workload diagnosis with reviewable patch manifests. | [Google Skills](https://github.com/google/skills/tree/main) | 🟢 **Completed & Promoted** | Triage CrashLoopBackOff, OOMKilled, and image-pull failures. |
| `gcp-terraform-security-policy` | GCP Terraform audit against CIS controls and least-privilege IAM. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Block insecure infrastructure before `terraform apply`. |
| `integrate-repo` | Aligns external or AI-authored code with host repository quality gates. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Produce remediation scripts and CI preflights. |
| `model-governance` | Governed profiling and selection of LLM providers and model tiers. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Select cost-effective models and pin configuration. |
| `real-estate-floorplan` | Listing floor-plan research and vector CAD drafting through MCP servers. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Extract blueprints and export DXF/SVG. |
| `skill-creator` | Unified test-driven authoring, evaluation, and refinement engine for Agent Skills. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Author, test, evaluate, and iteratively refine Agent Skills. |
| `ucp-consumer-surface` | Client-side UCP discovery, catalog, cart, checkout, and webhook flows. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Build headless shopping agents. |
| `ucp-extensions-schemas` | Authors and versions UCP capability extension schemas with JSON Schema Draft 2020-12 and discovery integration. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Design and validate forward-compatible commerce extensions. |
| `ucp-merchant-servers` | Server-side UCP discovery, cart, checkout, and signed event APIs. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Deploy compliant merchant endpoints. |
| `write-skill` | Authors, restructures, and scaffolds standard Agent Skill packages. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Create compliant prompts and support resources. |
| `black-box-evaluation-suite-builder` | Executable black-box suites for deployment, use, failure recovery, shutdown, latency, and agent capabilities. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Scaffold and execute boundary-oracle test and benchmark suites. |
| `agentapi` | Programmatic agent session management, external command dispatching, and message routing. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Drive agent conversations programmatically from sidecars or scripts. |
| `jetski-customizations` | Comprehensive guide and discovery engine for Jetski rules, agents, plugins, and hooks. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Configure team guidelines and custom runtime extensions. |
| `web-app-development` | Full-stack web application development, Vite/Next.js scaffolding, and responsive design. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Build and restyle modern web apps and interactive UI. |
| `automation` | Interactive guide to design and create scheduled background sidecars and cron workflows. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Create recurring automated background tasks. |
| `generative-ui` | Interactive widgets, dynamic forms, and real-time generative UI previews. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Render generative UI elements. |
| `migrate-workflows` | Migration workflows across agent configurations, models, and environments. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Migrate agent configurations. |
| `permissioned-github` | Permissioned GitHub integrations, PR review workflows, and commit management. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Enforce safe repository operations. |
| `plugin` | Jetski plugin packaging, capabilities, and distribution. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Bundle extensions into installable plugins. |
| `ui-plugin-development` | UI plugin development for auxiliary panels and rich canvas views. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Build auxiliary UI plugin panels. |
| `ui-plugin-navigation` | UI navigation controls, view transitions, and layout orchestration. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Orchestrate pane navigation and transitions. |
| `antigravity-guide` | Antigravity development guide, CLI reference, and offline sitemap. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Guide Antigravity platform usage. |
| `codesearch` | Indexed workspace-scoped code search for CitC and Git repositories. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Search large multi-repository codebases. |

---

## 🤝 Multi-Agent Squad & Coordination

Instead of relying on a single monolith, the repository coordinates an automated software delivery team where each agent runs in its own **isolated Git worktree on its own Git branch**. 

To bypass the latency of committing and merging git changes just to communicate, the agents collaborate in real-time through the shared `/jobs` directory (which is symlinked into every agent's worktree and listed in `.gitignore` to prevent conflicts).

### The Fleet Roles
1. **Orchestrator-Evaluator** (`.agents/orchestrator-evaluator.md`): Runs on `main` in the repository root. Manages the master backlog (`jobs/backlog.json`), dispatches multi-model evaluation tasks (Argon, Fable, 3.8 Flash) to worker inboxes, monitors status, performs verification checks, and merges successfully validated worker branches into `main` using a clean `--no-ff` merge protocol.
2. **Evaluator Workers 1–6** (`.agents/worker-evaluator-1.md` through `.agents/worker-evaluator-6.md`): Run in isolated Git worktrees (`skills-worker-evaluator-{1..6}`) on separate branches (`agent-*-evaluator-{1..6}`). Execute the `evaluate-skill` test-adjust-retest workflow across designated models, scoring trigger precision, recall, false-positive rate, and assertion pass rates.

*(Note: Legacy skill-creation agents `orchestrator`, `finder`, `creator`, and `evaluator` are archived in `.agents/archive/`.)*

### Configuration (`jetski.json` / `opencode.json`)
The evaluation fleet is configured in `jetski.json` (and mirrored in `opencode.json`) using Google Vertex AI models mapped to each agent prompt:
- **`orchestrator-evaluator`**: `gemini-3.8-flash-high` (`.agents/orchestrator-evaluator.md`, `worktree: false`)
- **`evaluator-1` through `evaluator-6`**: `gemini-3.8-flash-high` (`.agents/worker-evaluator-{1..6}.md`, `worktree: true`)


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
