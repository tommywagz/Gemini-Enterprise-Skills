# Gemini-Enterprise-Skills
Actual Agentic Solutions temporary development repository for new Gemini Enterprise Agent Skills Garden

I am trying to make a personal repository of agent skills. Can you make a series of agent skills formatted with the standard agent skill architecture including: name, description, and the skill prompt itself, along with any necessary sub-folders including external and internal references in Markdown. 

# Objective
Make agent skills for the following use cases: 

## AP2 Skill
Building agents that can pay, and agent systems where authorization is provable after the fact. Use https://ap2-protocol.org/llms.txt as the high level reference, the spec at https://ap2-protocol.org/ap2/specification/ and https://ap2-protocol.org/ap2/flows/, and the reference implementation at https://github.com/google-agentic-commerce/AP2 (SDK at `code/sdk/python/ap2/`, runnable scenarios at `code/samples/python/scenarios/a2a/human-present` and `.../human-not-present`, each with its own README and `run.sh`). The samples are ADK agents speaking A2A, so this skill set composes directly with the ADK and A2A skills above:

- **Design AP2 Mandate Flows** - Pick and construct the right Verifiable Digital Credentials for the user's goal: Checkout Mandate (open for pre-purchase constraints, closed to authorize a finalized cart) and Payment Mandate (open for delegated autonomous spend, closed to authorize a specific amount against a specific instrument). Covers signing, verification, and what each mandate is and is not allowed to reveal to each party. References https://ap2-protocol.org/ap2/checkout_mandate/ and https://ap2-protocol.org/ap2/payment_mandate/.
- **Choose Human-Present vs. Human-Not-Present Flows** - Decide whether the goal requires real-time user confirmation or delegated autonomous execution under pre-signed constraints, then scaffold the corresponding scenario. This is a routing decision the orchestrator should make before any payment agent is written, because it changes which mandates exist and when they are signed.
- **Implement AP2 Roles as Sub-Agents** - Generate the role-based agents an AP2 transaction needs - Shopping Agent, Merchant Agent, Credentials Provider, Merchant Payment Processor - as A2A-addressable sub-agents with the correct mandate exchange between them. The orchestrator wires them into whatever workflow the user described; this skill guarantees each role only holds the credentials its role is entitled to.
- **Add x402 / Crypto Payment Rails** - Extend a working card-based flow to stablecoin and crypto settlement via x402, using the corresponding sample scenario as the recipe, without changing the mandate structure above it.
- **Audit AP2 Authorization and Privacy** - Review a generated payment system against https://ap2-protocol.org/ap2/security_and_privacy_considerations/ and the agent authorization framework at https://ap2-protocol.org/ap2/agent_authorization/: mandate scoping and expiry, replay protection, credential leakage between roles, and whether the retained evidence is sufficient to resolve a dispute over who authorized what.

### Routing & Packaging Blueprint
- **Proposed Identity:** `ap2-agent-payments` (or modular family `ap2-mandate-flows`, `ap2-flow-routing`, `ap2-role-subagents`, `ap2-x402-rails`, `ap2-authorization-audit`)
- **Trigger Contract:** TRIGGER when users ask to implement autonomous agent checkout, AP2 payment mandates, signed checkout credentials, x402 crypto settlement rails, or mandate authorization audits. DO NOT TRIGGER for generic UCP cart operations without payment settlement or raw non-agent payment gateway SDK integration (Stripe/PayPal API) without verifiable mandate credentials.
- **Bundle Layout:**
  - `references/`: `ap2_spec_summary.md` (mandate structures and signing RFCs), `role_credential_matrix.md` (who sees what), `x402_settlement_guide.md`.
  - `scripts/`: `verify_mandate_signature.py`, `simulate_ap2_flow.sh`.
  - `assets/`: JSON schemas for Checkout Mandate, Payment Mandate, and dispute audit reports.


## Integrate Repo Skill
Skill for inspecting a host repository's operational environment, coding standards, and quality gates, then auditing an external or unintegrated target file/folder to produce executable remediation scripts and pre-flight runners that bring the target into full compliance with the host repo.

### Core Capabilities
- **Discover & Extract Repository Standards** - Automatically inspect the host repository root where the agent harness resides:
  - Formatter and linter configurations (`.eslintrc.*`, `biome.json`, `ruff.toml`, `pyproject.toml`, `.prettierrc`, `tsconfig.json`, `Cargo.toml`, `.golangci.yml`).
  - Contribution guidelines, style guides, and PR/issue templates (`CONTRIBUTING.md`, `STYLEGUIDE.md`, `.github/PULL_REQUEST_TEMPLATE.md`).
  - Git hook managers (`.pre-commit-config.yaml`, `.husky/`, `lefthook.yml`).
  - Continuous integration workflows (`.github/workflows/*.ya?ml`, GitLab CI, CircleCI) to extract the exact sequential validation commands and passing criteria.
- **Audit Target Delta & Generate Compliance Matrix** - Inspect the user-specified target folder or file against the extracted repository rules:
  - Identify style, formatting, syntax, and typing discrepancies.
  - Check file and directory naming conventions (kebab-case vs. snake_case vs. camelCase), directory placement, and test co-location conventions.
  - Verify license headers, docstring/JSDoc conventions, and forbidden dependency imports.
  - Execute non-destructive dry-run linting, formatting, and type-checking commands against the target path to catalog all violations.
- **Synthesize Executable Remediation Scripts** - Generate robust, reproducible shell scripts (e.g. `remediate_compliance.sh`) that the user can inspect and execute:
  - Run auto-fixers in proper dependency order (e.g., import sorting -> syntax fixers -> code formatters -> linter fixes).
  - Execute safe file renaming, path migrations, and directory restructuring.
  - Inject required file headers, license notices, and boilerplate templates.
  - Include rollback safety checks (e.g., git stash or temporary branch checkpoints) before executing destructive modifications.
- **Build Local CI/CD Pre-Flight Runner** - Generate a dedicated validation script (e.g. `run_ci_preflight.sh`) that simulates the repository's GitHub Actions / CI pipeline locally against the target path:
  - Run the exact lint, typecheck, build, and unit test commands identified from the CI workflows.
  - Return clear pass/fail status reports with actionable diagnostics for any remaining manual fixes.
- **Audit PR & Contribution Readiness** - Compile a compliance summary report against `CONTRIBUTING.md` requirements (e.g. conventional commit formats, test coverage thresholds, documentation updates) ready for PR submission.

### Routing & Packaging Blueprint
- **Proposed Identity:** `integrate-repo`
- **Routing Description Checklist:**
  - *Trigger:* TRIGGER when users ask to "integrate repo", "make folder compliant with repo", "match repo style and syntax", "remediate project to match CONTRIBUTING.md", "generate scripts to pass repo CI", "align external code with repository conventions", or need local GitHub Actions pre-flight scripts for a folder.
  - *Do Not Trigger:* DO NOT TRIGGER for creating a brand-new repo from scratch (use project scaffolding skills), resolving general git merge conflicts, or refactoring business logic unrelated to repository standards.
- **Workflow Contract for Creator Agent:**
  1. Inspect host repository root to detect build systems, linters, formatters, and CI workflows.
  2. Parse `CONTRIBUTING.md` and `.github/workflows/` to identify required quality gates and commands.
  3. Scan the target file/folder to catalog deviations (syntax, style, structure, licensing).
  4. Generate `remediate_compliance.sh` with ordered automated fix commands and backup safeguards.
  5. Generate `run_ci_preflight.sh` reflecting the exact CI validation gates.
  6. Output an actionable execution summary detailing commands to run and manual fixes required.
- **Bundle Layout:**
  - `references/`: `toolchain_fixers.md` (flags for ruff, eslint, biome, prettier, black, clippy), `ci_workflow_patterns.md` (extracting test matrices from GitHub Actions).
  - `scripts/`: `extract_repo_rules.py` (CLI scanner for linters/CI configs), `remediate_compliance.sh` (template runner).
  - `assets/`: `compliance_report_template.md`, `preflight_checklist.json`.


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

