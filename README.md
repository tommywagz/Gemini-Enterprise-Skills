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

| Skill (folder) | YAML name / ID | Description | Destination | Status | Primary use case |
|---|---|---|---|---|---|
| `a2a-workflows` | `a2a-workflows` | A2A multi-agent workflows with host-agent orchestration and sub-agent communication. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Resolve agent cards and delegate tasks via A2A. |
| `adk-agents` | `google-agents-cli-adk-code` | ADK agent, tool, callback, and state-management reference patterns. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Bootstrap core ADK agent components. |
| `adk-cross-session-knowledge-bank` | `adk-cross-session-knowledge-bank` | Vertex AI Memory Bank integration for cross-session ADK agent memory. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Persist preferences and terminology across conversations. |
| `adk-durable-human-in-the-loop` | `adk-durable-human-in-the-loop` | Durable asynchronous HITL approval gates with `LongRunningFunctionTool` and signed webhooks. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Pause and resume risky workflows across process lifetimes. |
| `adk-long-horizon-harness` | `adk-long-horizon-harness` | Headless ADK agents triggered by Pub/Sub or cron with context compaction. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Manage multi-day background workflows. |
| `adk-oauth-user-consent-flow` | `adk-oauth-user-consent-flow` | User-authorized OAuth 2.0 flows for ADK Workspace integrations. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Access user data with consented credentials. |
| `agents-cli-benchmark-eval` | `agents-cli-benchmark-eval` | Local agent dataset scoring with JUnit XML and Markdown reports. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Perform CI accuracy testing. |
| `agents-cli-conformance-tester` | `agents-cli-conformance-tester` | Local MUST/SHOULD/MAY conformance tests for UCP or A2A servers. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Run pre-flight protocol compatibility checks. |
| `agents-cli-plugin-moderator` | `agents-cli-plugin-moderator` | Runner-wide ADK safety guardrails, content filters, and exfiltration prevention. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Enforce safety policies across sub-agents. |
| `agents-cli-scaffold-extension` | `agents-cli-scaffold-extension` | Polyglot TypeScript/Hono and Python/ADK agent workspace generator. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Scaffold multi-language agent environments. |
| `ap2-agent-payments` | `ap2-agent-payments` | AP2 payment agents using SD-JWT Checkout and Payment Mandates. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Delegate bounded autonomous spend with audit trails. |
| `evaluate-skill` | `evaluate-skill` | Agent Skill evaluation for routing accuracy, performance, and security. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Run trigger, performance, and security evaluations. |
| `find-skill` | `find-skill` | Safe discovery and installation of Skills, MCP servers, and Composio integrations. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Discover pre-vetted capabilities. |
| `gcp-cost-optimizer` | `gcp-cost-optimizer` | GCP waste audit with reviewable Terraform cost remediations. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Reduce idle or over-provisioned resource spend. |
| `gcp-iam-privilege-audit` | `gcp-iam-privilege-audit` | GCP IAM usage audit with least-privilege Terraform proposals. | [Google Skills](https://github.com/google/skills/tree/main) | 🟢 **Completed & Promoted** | Harden broad roles and service-account access. |
| `gcp-kubernetes-resource-triage` | `gcp-kubernetes-resource-triage` | GKE workload diagnosis with reviewable patch manifests. | [Google Skills](https://github.com/google/skills/tree/main) | 🟢 **Completed & Promoted** | Triage CrashLoopBackOff, OOMKilled, and image-pull failures. |
| `gcp-terraform-security-policy` | `gcp-terraform-security-policy` | GCP Terraform audit against CIS controls and least-privilege IAM. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Block insecure infrastructure before `terraform apply`. |
| `integrate-repo` | `integrate-repo` | Aligns external or AI-authored code with host repository quality gates. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Produce remediation scripts and CI preflights. |
| `model-governance` | `model-governance` | Governed profiling and selection of LLM providers and model tiers. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Select cost-effective models and pin configuration. |
| `real-estate-floorplan` | `real-estate-floorplan` | Listing floor-plan research and vector CAD drafting through MCP servers. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Extract blueprints and export DXF/SVG. |
| `skill-creator` | `skill-creator` | Unified test-driven authoring, evaluation, and refinement engine for Agent Skills. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Author, test, evaluate, and iteratively refine Agent Skills. |
| `ucp-consumer-surface` | `ucp-consumer-surface` | Client-side UCP discovery, catalog, cart, checkout, and webhook flows. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Build headless shopping agents. |
| `ucp-extensions-schemas` | `ucp-extensions-schemas` | Authors and versions UCP capability extension schemas with JSON Schema Draft 2020-12 and discovery integration. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Design and validate forward-compatible commerce extensions. |
| `ucp-merchant-servers` | `ucp-merchant-servers` | Server-side UCP discovery, cart, checkout, and signed event APIs. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Deploy compliant merchant endpoints. |
| `write-skill` | `write-skill` | Authors, restructures, and scaffolds standard Agent Skill packages. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Create compliant prompts and support resources. |

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
