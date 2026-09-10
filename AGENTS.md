# Gemini-Enterprise-Skills
Actual Agentic Solutions temporary development repository for new Gemini Enterprise Agent Skills Garden

I am trying to make a personal repository of agent skills. Can you make a series of agent skills formatted with the standard agent skill architecture including: name, description, and the skill prompt itself, along with any necessary sub-folders including external and internal references in Markdown. 

# Objective
Make agent skills for the following use cases: 

## Model Governance Assignment
Skill for previewing an agent prompt, workflow, or task specification, analyzing its cognitive and token complexity, and assigning the optimal LLM provider and model tier based on configured user preferences (quality/results, cost minimization, or balanced intelligence-to-token ratio), outputting the launch command and configuration patches.

### Core Capabilities
- **Profile Prompt & Task Complexity** - Analyze incoming prompts, task goals, or multi-agent delegation steps:
  - Classify cognitive workload tier:
    - *Tier 1 (Frontier Reasoning & Complex Architecture):* Complex system design, multi-file refactoring, autonomous squad orchestration, security/privacy audit, deep multi-hop reasoning.
    - *Tier 2 (Balanced Workhorse & Core Coding):* Standard feature implementation, unit test authoring, code documentation, bug fixes, structured API endpoint generation.
    - *Tier 3 (High Throughput & Routine Operations):* Syntax triage, schema/metadata validation, text classification, simple file lookup, commit message formatting.
  - Estimate input and output token consumption, context depth requirements, and whether chain-of-thought/extended reasoning is required.
- **Resolve Multi-Layer Governance Configuration** - Read and merge `opencode.json` configuration files with strict deterministic precedence:
  - User-level defaults (`~/.config/opencode/opencode.json`): Base provider credentials, global model preferences, default budget constraints.
  - Project-level configuration (`./opencode.json`): Repository-specific model overrides, project quotas, approved provider allow-lists (project level strictly overrides user level).
  - Resolve optimization mode: `result_maximized` (select top intelligence model regardless of token cost), `cost_optimized` (select lowest-cost model meeting minimum capability threshold), or `balanced` (maximize intelligence-to-cost ratio).
- **Map to Governed Model Catalog** - Maintain an up-to-date registry of supported models and providers:
  - Google Vertex AI (`gemini-3.6-flash` with reasoning, `gemini-3.5-flash`, Gemini Pro/Flash family).
  - Anthropic (`claude-opus-5`, `claude-3-7-sonnet`, `claude-3-5-haiku`).
  - OpenAI (`o3`, `o4-mini`, `gpt-4o`, `gpt-4o-mini`).
  - Factor in reasoning token overhead, per-token pricing, context window limits, and rate-limit guardrails.
- **Formulate Opencode Launch Command & Config Patching** - Emit the validated execution invocation and configuration updates:
  - Formulate the exact CLI command with `--model <provider/model>` and appropriate execution flags.
  - Generate patch snippets for `opencode.json` agent blocks when delegating to sub-agents (e.g. updating orchestrator, finder, creator, or evaluator models).
  - Produce an audit explanation: chosen model, reasoning tier, expected cost profile, and why alternatives were passed over.

### Routing & Packaging Blueprint
- **Proposed Identity:** `model-governance`
- **Routing Description Checklist:**
  - *Trigger:* TRIGGER when users ask to "assign model for prompt", "select optimal model", "model governance", "match prompt to model tier", "optimize model cost vs intelligence", "configure opencode model", "determine LLM for task", or need an `opencode` launch command with `--model`.
  - *Do Not Trigger:* DO NOT TRIGGER for prompt rewriting/prompt engineering (use prompt optimization skills), provisioning cloud credentials/API keys, or running live benchmark evaluations.
- **Workflow Contract for Creator Agent:**
  1. Parse prompt text or task specification to determine complexity and token volume.
  2. Read `./opencode.json` and fallback to `~/.config/opencode/opencode.json` to resolve active providers, allowed models, and optimization preferences.
  3. Map the task complexity to the optimal provider/model based on the configured objective (results, cost, or balanced).
  4. Generate the exact `opencode launch` command using `--model <provider/model>`.
  5. Provide config update JSON if the assignment applies to a persistent subagent role in `opencode.json`.
- **Bundle Layout:**
  - `references/`: `model_tier_catalog.md` (models, context limits, pricing, reasoning flags), `opencode_config_spec.md` (schema definition and inheritance rules).
  - `scripts/`: `profile_prompt.py` (token estimator & complexity classifier), `resolve_governance_model.py` (CLI resolver).
  - `assets/`: `governance_policy_schema.json`, `opencode_override_template.json`.


## Real estate floor plan plugin skill
Skill for orchestrating a two-stage spatial research and architectural drafting pipeline using Model Context Protocol (MCP) servers: researching property floor plans across real estate listing platforms (Zillow, Apartments.com, Redfin), and programmatically authoring vector CAD layouts via Floor Builder and CAD MCP servers.

### Architectural Two-Stage Pipeline
- **Stage 1: Multi-Platform Real Estate Listing Research (Discovery & Extraction)**
  - Connect to remote MCP servers for real estate intelligence:
    - *Zillow MCP Server:* Query properties by address, ZPID, or MLS ID. Extract lot dimensions, gross living area (GLA), room dimensions, architectural style, and floor plan image/media URLs.
    - *Apartments.com MCP Server:* Query apartment communities and multi-family floor plan models (e.g. Studio, 1B1B, 2B2B, Penthouse). Extract unit layout blueprints, spatial dimensions, and model-specific amenity layouts.
    - *Redfin MCP Server:* Query MLS property records, public permit schematics, architectural tour media, and listing image galleries for floor plan sketches.
  - Multi-source data synthesis: Correlate and reconcile dimensional data across multiple listing sources, flagging discrepancies in reported square footage or room boundaries.
- **Stage 2: Procedural Drafting & CAD Vector Generation (Authoring & Verification)**
  - Synthesize a canonical Floor Plan Specification schema (JSON) from Stage 1 research:
    - Room polygons (coordinates, boundaries, wall types, ceiling heights).
    - Portals and openings (interior doors, exterior entryways, sliding doors, windows with widths and sill heights).
    - Fixtures and structural elements (kitchen cabinets, sinks, bathroom tubs/vanities, closets, load-bearing walls).
  - Drive procedural generation via *Floor Builder MCP Server*:
    - Automatically generate 2D/2.5D room layouts from normalized boundary and dimension specs.
    - Snap shared walls, align adjacent room enclosures, and insert door swings with proper clearance.
    - Generate automated dimensional annotations and room labels (e.g. "Primary Bedroom 14' x 16'").
  - Drive precision CAD authoring via *CAD / BIM MCP Server*:
    - Generate standard architectural layers per AIA CAD layer guidelines (`WALLS`, `DOORS`, `WINDOWS`, `DIMENSIONS`, `FIXTURES`, `TEXT`).
    - Construct vector geometry with correct line weights and hatch patterns.
    - Export standardized formats: DXF (Drawing Exchange Format), SVG (web vector preview), and DWG.
  - Architectural Integrity & Code Verification:
    - Validate closed polygon loops (no leaking room boundaries).
    - Verify ingress/egress clearance and hallway connectivity.
    - Check drawn square footage against listing reported area and report variance.

### Routing & Packaging Blueprint
- **Proposed Identity:** `real-estate-floorplan`
- **Routing Description Checklist:**
  - *Trigger:* TRIGGER when users ask to "research real estate floor plans", "extract floor plan from Zillow, Redfin, or Apartments.com", "generate CAD floor plan from property listing", "draw floor plan with Floor Builder MCP", "convert listing blueprint to DXF/SVG", or route queries through real estate research and CAD drafting MCP servers.
  - *Do Not Trigger:* DO NOT TRIGGER for property price estimation or mortgage calculations, general 3D video game level modeling, or mechanical CAD drafting unrelated to residential architecture.
- **Workflow Contract for Creator Agent:**
  1. Query Zillow, Apartments.com, and Redfin MCP servers to retrieve listing floor plan media, room dimensions, and structural descriptions.
  2. Normalize unstructured research data into a canonical Floor Plan JSON Specification.
  3. Invoke Floor Builder MCP tools to construct procedural room layouts, wall polylines, and door/window cutouts.
  4. Invoke CAD MCP tools to generate layered vector geometry (DXF/SVG) following standard architectural layering.
  5. Validate geometric closure, egress pathways, and square footage consistency before returning CAD artifacts.
- **Bundle Layout:**
  - `references/`: `mcp_realestate_servers.md` (tool schemas and auth for Zillow, Apartments.com, Redfin), `mcp_cad_builder_tools.md` (Floor Builder and CAD MCP signatures), `architectural_cad_standards.md` (layer naming and line weights).
  - `scripts/`: `normalize_listing_spatial_data.py` (transforms listing dimensions to canonical schema), `validate_geometric_closure.py` (checks closed loops and clearances).
  - `assets/`: `floorplan_spec_schema.json` (canonical JSON schema), `standard_cad_symbols.dxf` (library of doors, windows, fixtures).


# Repository Attribution Matrix

## 1. Skills from this Document (AGENTS.md)
| Proposed Identity | Destination Repository | Potential Usefulness & Rationale |
|---|---|---|
| `model-governance` | `https://github.com/google/agents-cli/tree/main/skills` | Handles local LLM cognitive/token profiling, dynamic provider configuration routing, and `opencode.json` config/launch command patching within the developer’s CLI. |
| `real-estate-floorplan` | `https://github.com/google/adk-samples/tree/main/skills` | A domain-specific multi-platform real estate listing scraper and vector CAD/BIM drafting workflow; serves as an excellent complex multi-turn integration sample for ADK/MCP. |

## 2. Sibling Skills (from `@skills/**` folder)
| Local Skill Name | Destination Repository | Potential Usefulness & Rationale |
|---|---|---|
| `a2a-workflows` | `https://github.com/google/adk-samples/tree/main/skills` | Sample showing how to implement multi-agent A2A (Agent2Agent) protocol orchestration and sub-agent connection logic using `google-adk`. |
| `adk-agents` | `https://github.com/google/agents-cli/tree/main/skills` | Primary developer-facing CLI reference and cheatsheet for the core Google ADK Python SDK. |
| `ap2-agent-payments` | `https://github.com/google/adk-samples/tree/main/skills` | Cryptographic commerce/payment sample demonstrating Checkout/Payment Mandates via SD-JWT verifiable credentials and role separation. |
| `evaluate-skill` | `https://github.com/google/agents-cli/tree/main/skills` | Meta-skill developer tool used locally or in CI to score agent skill triggers, precision, recall, and run security scans. |
| `find-skill` | `https://github.com/google/agents-cli/tree/main/skills` | Developer tool enabling dynamic discovery and screening of MCP servers, Composio tools, and community skills from within the CLI. |
| `integrate-repo` | `https://github.com/google/agents-cli/tree/main/skills` | Quality-gate linter and formatter conformer used to integrate third-party, vendored, or AI-generated code cleanly into host repository standards. |
| `ucp-merchant-servers` | `https://github.com/google/adk-samples/tree/main/skills` | Complete commerce sample demonstrating standard Universal Commerce Protocol (UCP) server-side FastAPI/Hono integrations. |
| `write-skill` | `https://github.com/google/agents-cli/tree/main/skills` | CLI-integrated generator and standard scaffold utility for writing agentic skill packages. |


# Pitched Potential Skills

## 1. Destination Repo: Cloud Skills (`skills/cloud`)
### Pitch A: `gcp-terraform-security-policy` (GCP IaC Compliance Reviewer)
- **Description:** Scans Terraform configurations against Google Cloud security and organizational policies (e.g., CIS benchmarks, private-by-default buckets, least-privilege IAM roles) before provisioning resources.
- **Trigger:** TRIGGER when users ask to "audit Terraform configurations for GCP", "verify GCP resource compliance", "validate Terraform security policies", or "run GCP IAC security scan".
- **Do Not Trigger:** DO NOT TRIGGER for general Terraform syntax errors (unrelated to GCP compliance) or for multi-cloud Azure/AWS-specific reviews unless specifically targeted at a GCP hybrid scenario.
- **Value:** Invaluable for platform engineering and DevSecOps squads looking to enforce corporate guardrails automatically prior to remote `terraform apply`.

### Pitch B: `gcp-cost-optimizer` (Google Cloud FinOps Auditor)
- **Description:** Analyzes active Google Cloud inventory reports (e.g., idle Compute Engine instances, unattached persistent disks, under-utilized BigQuery slots, or excessively provisioned Cloud Run scaling settings) and generates prescriptive recommendations or Terraform configurations to minimize spend.
- **Trigger:** TRIGGER when users ask to "reduce Google Cloud costs", "find idle GCP resources", "optimize BigQuery slot utilization", or "run a GCP spend audit".
- **Do Not Trigger:** DO NOT TRIGGER for billing alert setups, cloud payment credential updates, or generic code optimizations.
- **Value:** Provides a clear, high-ROI corporate financial operations (FinOps) helper that cuts wasted cloud spend.

## 2. Destination Repo: ADK Sample Skills (`adk-samples/skills`)
### Pitch A: `adk-cross-session-knowledge-bank` (Memory Bank Integration Sample)
- **Description:** Sample demonstrating how to persist user preferences, key terminology, and conversational context across discrete sessions using the Vertex AI Memory Bank (`PreloadMemoryTool` and `LoadMemoryTool`).
- **Trigger:** TRIGGER when users ask to "implement cross-session memory in ADK", "configure Vertex AI Memory Bank", "persist agent knowledge across conversations", or "use PreloadMemoryTool/LoadMemoryTool".
- **Do Not Trigger:** DO NOT TRIGGER for standard transient session state-key management (single-turn variables) or raw client-side SQLite setup.
- **Value:** Deeply explains and scaffolds ADK’s advanced long-term memory capabilities, a frequent point of friction for production agent developers.

### Pitch B: `adk-durable-human-in-the-loop` (Durable Approval Gates)
- **Description:** Scaffolds and guides the setup of a durable, asynchronous Human-In-The-Loop (HITL) approval gate within an ADK Graph-based Workflow. It pauses the node execution, publishes a state-holding webhook payload to an external workflow dashboard, and safely resumes upon receiving a signed approval payload.
- **Trigger:** TRIGGER when users ask to "add workflow approval gate in ADK", "suspend ADK graph execution", "implement human sign-off", or "integrate ADK asynchronous resume".
- **Do Not Trigger:** DO NOT TRIGGER for basic synchronous CLI input prompts (`request_input`) or transient function-level confirmation challenges.
- **Value:** Offers a robust, real-world pattern for integrating agentic graphs with enterprise-grade operational workflows.

## 3. Destination Repo: Agents CLI Skills (`agents-cli/skills`)
### Pitch A: `agents-cli-conformance-tester` (Protocol Conformance Scanner)
- **Description:** Spins up a local mock sandbox to execute conformance suites against local UCP merchant servers or A2A host agents, outputting verified protocol-compliance test summaries.
- **Trigger:** TRIGGER when users ask to "run UCP conformance tests", "verify A2A compliance of local server", "agents-cli test-compliance", or "check protocol compatibility".
- **Do Not Trigger:** DO NOT TRIGGER for standard PyTest/Vitest unit-testing or generic code-linting.
- **Value:** Greatly accelerates local protocol-compliant development by avoiding manual verification.

### Pitch B: `agents-cli-scaffold-extension` (Polyglot Multi-Agent Workspace Generator)
- **Description:** Extends standard CLI scaffolding actions to generate hybrid, polyglot agent workspaces (e.g., automatically linking a TypeScript/Hono web handler with a Python/ADK processing orchestrator).
- **Trigger:** TRIGGER when users ask to "scaffold a multi-agent polyglot workspace", "agents-cli scaffold enhance multiple languages", or "add Node.js/Python boundaries to agent project".
- **Do Not Trigger:** DO NOT TRIGGER for standard single-agent folder scaffolding or simple python virtual-env setup.
- **Value:** Provides a seamless enterprise layout that coordinates larger development teams working across multiple runtimes.

