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

### 1. New Skills Staged in AGENTS.md
All proposed skills initially staged in `AGENTS.md` have been fully developed, evaluated, and promoted to active sibling skills in the garden below.

### 2. Sibling Skills (from `@skills/**` folder)
| Local Skill Name | Destination Repository | Status / Clarification | Potential Usefulness & Rationale |
|---|---|---|---|
| `a2a-workflows` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Full multi-agent orchestration and A2A communication wrappers. Fully verified with evaluation report. |
| `adk-agents` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | Primary developer cheatsheet/reference for the core Google ADK Python SDK. Fully verified with evaluation report. |
| `adk-cross-session-knowledge-bank` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Persistent preference and terminology tracking using Vertex AI Memory Bank. Fully verified with evaluation report. |
| `adk-durable-human-in-the-loop` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Asynchronous, cross-restart durable approval gates built on `LongRunningFunctionTool`. Fully verified with evaluation report. |
| `agents-cli-conformance-tester` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | Loopback conformance smoke testing and loopback mock sandbox for local UCP/A2A endpoints. Fully verified with evaluation report. |
| `agents-cli-scaffold-extension` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | Polyglot workspace generator connecting TypeScript/Hono to Python/ADK. Fully verified with verification tests. |
| `ap2-agent-payments` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Agentic commerce payment authorization sample using SD-JWT Checkout/Payment mandates. Fully verified with evaluation report. |
| `evaluate-skill` | `https://github.com/google/agents-cli/tree/main/skills` | 🟡 **System Meta-Skill** | Meta-tooling used by the Evaluator Agent. Stable for squad execution; pending standalone garden-testing promotion. |
| `find-skill` | `https://github.com/google/agents-cli/tree/main/skills` | 🟡 **System Meta-Skill** | Discovery and pre-screening of MCP/Composio skills used by the Finder Agent. Stable for squad execution; pending standalone garden-testing promotion. |
| `gcp-cost-optimizer` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | FinOps advisory scanner identifying GCP waste and generating reviewable Terraform cost optimization. Fully verified with evaluation report. |
| `gcp-terraform-security-policy` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | IaC compliance scanner checks GCP Terraform plans against CIS GCP Benchmarks. Fully verified with evaluation report. |
| `integrate-repo` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | CLI tool for style compliance and CI gate preflights of external/AI-authored code. Fully verified with evaluation report. |
| `model-governance` | `https://github.com/google/agents-cli/tree/main/skills` | 🟢 **Completed & Promoted** | Profiles task complexity and resolves optimal LLM provider and cost/capability tier constraints. Fully verified with evaluation report. |
| `real-estate-floorplan` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Complex spatial research and vector CAD/BIM drafting using listing portals and Floor Builder MCP. Fully verified with evaluation report. |
| `ucp-consumer-surface` | `https://github.com/google/adk-samples/tree/main/skills` | 🟢 **Completed & Promoted** | Headless client-side UCP shopping agents managing discovery, carts, checkouts, and webhooks. Fully verified with evaluation report. |
| `ucp-merchant-servers` | `https://github.com/google/adk-samples/tree/main/skills` | 🔵 **In Progress / Evaluation** | Server-side FastAPI/Hono UCP integration sample. Currently has test suite scaffolded; final evaluation report is pending. |
| `write-skill` | `https://github.com/google/agents-cli/tree/main/skills` | 🟡 **System Meta-Skill** | Scaffolds standard skill packages. Used by the Creator Agent. Stable for squad execution; pending standalone garden-testing promotion. |
| `agents-cli-plugin-moderator` | `https://github.com/google/agents-cli/tree/main/skills` | 🔴 **Staged / Blueprint** | Runner-wide input/output safety, content moderation, and sensitive data exfiltration filter plugin. |
| `agents-cli-benchmark-eval` | `https://github.com/google/agents-cli/tree/main/skills` | 🔴 **Staged / Blueprint** | Standardizes executing and scoring local accuracy/adversarial datasets to emit JUnit XML reports. |
| `gcp-kubernetes-resource-triage` | `https://github.com/google/skills/tree/main` | 🔴 **Staged / Blueprint** | Diagnostic debugger for failing GKE workloads, parsing logs/exit codes to generate patch manifests. |
| `gcp-iam-privilege-audit` | `https://github.com/google/skills/tree/main` | 🔴 **Staged / Blueprint** | Audits active IAM bindings against usage logs (Logging/Recommender) to generate least-privilege Terraform. |
| `adk-oauth-user-consent-flow` | `https://github.com/google/adk-samples/tree/main/skills` | 🔴 **Staged / Blueprint** | Integrates Google Workspace APIs behind user-authenticated OAuth 2.0 credential callbacks. |
| `adk-long-horizon-harness` | `https://github.com/google/adk-samples/tree/main/skills` | 🔴 **Staged / Blueprint** | Headless event-driven (Pub/Sub) and scheduled background agents using context compaction. |

---

## 🌿 Active Skills in the Garden

Below is a detailed reference of the active skills, meta-skills, and staged blueprints available in this repository, including their official names, descriptions, and primary use cases as defined in their respective `SKILL.md` or `instructions/` configurations:

| Skill Name (Folder) | YAML Name / ID | Concise Description | Primary Use Case |
|---|---|---|---|
| `a2a-workflows` | `a2a-workflows` | Authoring Agent2Agent (A2A) multi-agent workflows, featuring host-agent orchestration and sub-agent communication. | Implementing host agents that dynamically resolve remote agent cards and delegate tasks via A2A. |
| `adk-agents` | `google-agents-cli-adk-code` | Reference cheatsheet and API patterns for writing ADK agent code, building tools, callbacks, and state management. | Bootstrapping core ADK agent components and studying standard Python SDK patterns. |
| `adk-cross-session-knowledge-bank` | `adk-cross-session-knowledge-bank` | Seeds, queries, and explains Vertex AI Memory Bank cross-session memory for ADK agents to persist facts across conversations. | Integrating persistent, consolidated user preferences and terminology into agent memory. |
| `adk-durable-human-in-the-loop` | `adk-durable-human-in-the-loop` | Scaffolds a durable, asynchronous Human-in-the-Loop (HITL) approval gate utilizing `LongRunningFunctionTool` and HMAC-signed webhooks. | Pausing agent execution for manual approval of risky or financial transactions across process lifetimes. |
| `agents-cli-conformance-tester` | `agents-cli-conformance-tester` | Spins up a local, dependency-free mock sandbox to run a MUST/SHOULD/MAY-leveled conformance suite against local UCP or A2A servers. | Local pre-flight smoke testing and protocol compatibility checks before full upstream compliance validation. |
| `agents-cli-scaffold-extension` | `agents-cli-scaffold-extension` | Generates a polyglot agent workspace linking a TypeScript/Hono HTTP gateway to a Python/ADK multi-agent workflow. | Scaffolding multi-language developer environments with isolated runtime boundaries and clean API contracts. |
| `ap2-agent-payments` | `ap2-agent-payments` | Builds and audits AP2 (Agent Payments Protocol) payment agents with Checkout and Payment Mandates as SD-JWT credentials. | Delegating secure spending limits and budgets to autonomous agents with non-repudiable audit trails. |
| `evaluate-skill` | `evaluate-skill` | Meta-skill for testing and benchmarking existing Agent Skills for routing accuracy, performance, or security compliance. | Testing trigger precision/recall, executing security scans, and compiling compliance reports. |
| `find-skill` | `find-skill` | Meta-skill for searching, screening, and safely installing existing Agent Skills, MCP servers, or Composio integrations. | Discovering and installing pre-vetted capabilities from official registries without executing untrusted code. |
| `gcp-cost-optimizer` | `gcp-cost-optimizer` | Advisory FinOps auditor analyzing GCP resource inventories for idle VMs, unattached disks/static IPs, and over-provisioned services. | Auditing resource waste and generating non-mutating, reviewable Terraform remediation HCL snippets. |
| `gcp-terraform-security-policy` | `gcp-terraform-security-policy` | Audits GCP Terraform configurations (raw files or plans) against CIS GCP Foundation Benchmark controls and least-privilege IAM. | Pre-apply security scanning to block public buckets, open firewalls, and over-privileged roles. |
| `integrate-repo` | `integrate-repo` | Quality-gate and style compliance linter matching external or AI-authored code against the host repository's actual CI workflows. | Aligning vendored/generated files with repo formatting and linting rules and generating pre-flight CI runners. |
| `model-governance` | `model-governance` | Profiles task prompt complexity and resolves optimal LLM provider and tier constraints against a governed catalog. | Determining cost-effective and capable models for tasks and pinning subagent models. |
| `real-estate-floorplan` | `real-estate-floorplan` | Orchestrates a two-stage spatial research and architectural drafting pipeline querying listing portals and drawing CAD layouts. | Extracting residential blueprints from Zillow/Redfin and programmatically exporting DXF/SVG. |
| `ucp-consumer-surface` | `ucp-consumer-surface` | Client-side Universal Commerce Protocol (UCP) shopping agent orchestrating capability discovery, cart building, and checkout. | Implementing headless shopping assistants that securely purchase items and process status webhooks. |
| `ucp-merchant-servers` | `ucp-merchant-servers` | Server-side architecture of a UCP-compliant Business Server, exposing discovery, cart, and checkout state engine APIs. | Deploying secure, compliant merchant endpoints with SQLite state tracking and request signature verification. |
| `write-skill` | `write-skill` | Meta-skill for authoring, scaffolding, auditing, and structuring compliant Agent Skill packages in the standard format. | Structuring workflows, writing trigger patterns, and managing token budgets for new and existing skills. |
| `agents-cli-plugin-moderator` | `agents-cli-plugin-moderator` | Configures and deploys runner-wide safety guardrails, content filters, and exfiltration prevention as ADK `BasePlugin`s. | Intercepting inputs and outputs to enforce safety policies across all sub-agents. |
| `agents-cli-benchmark-eval` | `agents-cli-benchmark-eval` | Designs, executes, and scores local accuracy datasets against ADK agents to emit JUnit XML reports. | Continuous integration accuracy testing and pre-merge validation. |
| `gcp-kubernetes-resource-triage` | `gcp-kubernetes-resource-triage` | Automatically diagnoses and recovers failing GKE workloads (CrashLoopBackOff, OOMKilled) by generating patch manifests. | Triaging container crashes and adjusting resources based on live diagnostics. |
| `gcp-iam-privilege-audit` | `gcp-iam-privilege-audit` | Audits GCP IAM bindings against activity logs (Logging/Recommender) to propose safe least-privilege Terraform patches. | Hardening over-privileged roles and setting up Workload Identity Federation. |
| `adk-oauth-user-consent-flow` | `adk-oauth-user-consent-flow` | Implements user-authenticated OAuth 2.0 flows for Workspace APIs (Drive, Gmail, Calendar) via ADK credential callbacks. | Accessing and editing user data safely through transient, user-authorized credentials. |
| `adk-long-horizon-harness` | `adk-long-horizon-harness` | Configures autonomous headless ADK agents triggered by Pub/Sub or cron, using token-based context compaction. | Managing multi-day, background workflows without requiring live user presence. |

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
