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
│   ├── adk-cross-session-knowledge-bank/ # Long-term memory using Vertex AI Memory Bank.
│   ├── adk-durable-human-in-the-loop/    # Asynchronous human-in-the-loop approval gates.
│   ├── agents-cli-conformance-tester/    # UCP/A2A local conformance and smoke testing.
│   ├── agents-cli-scaffold-extension/    # Polyglot TypeScript/Hono + Python/ADK workspaces.
│   ├── ap2-agent-payments/ # Cryptographic agent payments via SD-JWT mandates.
│   ├── evaluate-skill/     # (Symlinked or copied) Skill package evaluation & scoring.
│   ├── find-skill/         # (Symlinked or copied) Skill package discovery.
│   ├── gcp-cost-optimizer/ # FinOps advisory scanner and Terraform cost optimization.
│   ├── gcp-terraform-security-policy/    # IaC security scanner for CIS GCP Benchmarks.
│   ├── integrate-repo/     # External/AI-authored code repository style integrator.
│   ├── model-governance/   # OpenCode model tier and cost/capability selection resolver.
│   ├── real-estate-floorplan/            # Spatial research and procedural CAD drawing.
│   ├── ucp-consumer-surface/             # Headless client-side UCP shopping agents.
│   ├── ucp-merchant-servers/             # Server-side UCP-compliant business endpoints.
│   └── write-skill/        # (Symlinked or copied) Skill package scaffolding/writing.
│
├── instructions/           # Staged and completed skill blueprint definitions (untracked, local references).
│   ├── model_governance.md               # Model Governance prompt profiling blueprint.
│   ├── real_estate_floorplan.md          # Floorplan scraper and vector CAD blueprint.
│   ├── gcp_terraform_security_policy.md  # IaC security scanner and CIS audit blueprint.
│   ├── gcp_cost_optimizer.md             # FinOps advisory and cost optimizer blueprint.
│   ├── adk_cross_session_knowledge_bank.md # Long-term Vertex AI Memory Bank blueprint.
│   ├── adk_durable_human_in_the_loop.md  # Durable asynchronous approval gate blueprint.
│   ├── agents_cli_conformance_tester.md  # Loopback conformance mock sandbox blueprint.
│   ├── agents_cli_scaffold_extension.md  # Polyglot multi-runtime workspace blueprint.
│   ├── agents_cli_plugin_moderator.md    # Model Armor input/output moderation blueprint.
│   ├── agents_cli_benchmark_eval.md      # Quantitative accuracy dataset eval blueprint.
│   ├── gcp_kubernetes_resource_triage.md # GKE pod CrashLoopBackOff/OOM debugging blueprint.
│   ├── gcp_iam_privilege_audit.md        # Least-privilege IAM Recommender audit blueprint.
│   ├── adk_oauth_user_consent_flow.md    # Google Workspace OAuth2 user consent blueprint.
│   └── adk_long_horizon_harness.md       # Headless event-driven/cron compaction blueprint.
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

### Complete Skill Catalog

The following table is the single catalog for every unique skill package under `skills/`, including active skills, meta-skills, and staged blueprints. The `real-estate-floorplan` package under `drafts/` is its draft lineage and is represented by the active package row.

| Skill (folder) | YAML name / ID | Description | Destination | Status | Primary use case |
|---|---|---|---|---|---|
| `a2a-workflows` | `a2a-workflows` | A2A multi-agent workflows with host-agent orchestration and sub-agent communication. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Resolve agent cards and delegate tasks via A2A. |
| `adk-agents` | `google-agents-cli-adk-code` | ADK agent, tool, callback, and state-management reference patterns. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Bootstrap core ADK agent components. |
| `adk-cross-session-knowledge-bank` | `adk-cross-session-knowledge-bank` | Vertex AI Memory Bank integration for cross-session ADK agent memory. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Persist preferences and terminology across conversations. |
| `adk-durable-human-in-the-loop` | `adk-durable-human-in-the-loop` | Durable asynchronous HITL approval gates with `LongRunningFunctionTool` and signed webhooks. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Pause and resume risky workflows across process lifetimes. |
| `agents-cli-conformance-tester` | `agents-cli-conformance-tester` | Local MUST/SHOULD/MAY conformance tests for UCP or A2A servers. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Run pre-flight protocol compatibility checks. |
| `agents-cli-scaffold-extension` | `agents-cli-scaffold-extension` | Polyglot TypeScript/Hono and Python/ADK agent workspace generator. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Scaffold multi-language agent environments. |
| `ap2-agent-payments` | `ap2-agent-payments` | AP2 payment agents using SD-JWT Checkout and Payment Mandates. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Delegate bounded autonomous spend with audit trails. |
| `evaluate-skill` | `evaluate-skill` | Agent Skill evaluation for routing accuracy, performance, and security. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Run trigger, performance, and security evaluations. |
| `find-skill` | `find-skill` | Safe discovery and installation of Skills, MCP servers, and Composio integrations. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Discover pre-vetted capabilities. |
| `gcp-cost-optimizer` | `gcp-cost-optimizer` | GCP waste audit with reviewable Terraform cost remediations. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Reduce idle or over-provisioned resource spend. |
| `gcp-terraform-security-policy` | `gcp-terraform-security-policy` | GCP Terraform audit against CIS controls and least-privilege IAM. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Block insecure infrastructure before `terraform apply`. |
| `integrate-repo` | `integrate-repo` | Aligns external or AI-authored code with host repository quality gates. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Produce remediation scripts and CI preflights. |
| `model-governance` | `model-governance` | Governed profiling and selection of LLM providers and model tiers. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟢 **Completed & Promoted** | Select cost-effective models and pin configuration. |
| `real-estate-floorplan` | `real-estate-floorplan` | Listing floor-plan research and vector CAD drafting through MCP servers. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Extract blueprints and export DXF/SVG. |
| `ucp-consumer-surface` | `ucp-consumer-surface` | Client-side UCP discovery, catalog, cart, checkout, and webhook flows. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🟢 **Completed & Promoted** | Build headless shopping agents. |
| `ucp-merchant-servers` | `ucp-merchant-servers` | Server-side UCP discovery, cart, checkout, and signed event APIs. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🔵 **In Progress / Evaluation** | Deploy compliant merchant endpoints. |
| `write-skill` | `write-skill` | Authors, restructures, and scaffolds standard Agent Skill packages. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🟡 **System Meta-Skill** | Create compliant prompts and support resources. |
| `agents-cli-plugin-moderator` | `agents-cli-plugin-moderator` | Runner-wide ADK safety guardrails, content filters, and exfiltration prevention. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🔴 **Staged / Blueprint** | Enforce safety policies across sub-agents. |
| `agents-cli-benchmark-eval` | `agents-cli-benchmark-eval` | Local agent dataset scoring with JUnit XML and Markdown reports. | [agents-cli](https://github.com/google/agents-cli/tree/main/skills) | 🔴 **Staged / Blueprint** | Perform CI accuracy testing. |
| `gcp-kubernetes-resource-triage` | `gcp-kubernetes-resource-triage` | GKE workload diagnosis with reviewable patch manifests. | [Google Skills](https://github.com/google/skills/tree/main) | 🔴 **Staged / Blueprint** | Triage CrashLoopBackOff, OOMKilled, and image-pull failures. |
| `gcp-iam-privilege-audit` | `gcp-iam-privilege-audit` | GCP IAM usage audit with least-privilege Terraform proposals. | [Google Skills](https://github.com/google/skills/tree/main) | 🔴 **Staged / Blueprint** | Harden broad roles and service-account access. |
| `adk-oauth-user-consent-flow` | `adk-oauth-user-consent-flow` | User-authorized OAuth 2.0 flows for ADK Workspace integrations. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🔴 **Staged / Blueprint** | Access user data with consented credentials. |
| `adk-long-horizon-harness` | `adk-long-horizon-harness` | Headless ADK agents triggered by Pub/Sub or cron with context compaction. | [adk-samples](https://github.com/google/adk-samples/tree/main/skills) | 🔴 **Staged / Blueprint** | Manage multi-day background workflows. |

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
