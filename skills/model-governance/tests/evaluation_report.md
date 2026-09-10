# Skill Evaluation Report: model-governance

**Date:** 2026-09-10  
**Evaluator:** evaluator  
**Iteration:** 1 (of 3)  

## Summary
The `model-governance` skill draft is high quality, fully functional, and ready for production. Both bundled Python scripts (`profile_prompt.py` and `resolve_governance_model.py`) were executed against real test prompts and configuration scenarios, and verified to follow strict precedence and non-destructive read-only execution. The skill passed all quantitative trigger metrics (100% precision, 100% recall, 0% false-positive rate across a 20-prompt adversarial suite) and completely satisfies the Level 1-3 production checklist. Risk tier is evaluated as **Low / Medium** (read-only local Python stdlib scripts, no network requests, no file modification). Promoted from `drafts/model-governance/` to `skills/model-governance/`.

## Risk Tier
**Low / Medium**

Justification: The skill bundles two executable Python CLI utilities (`profile_prompt.py` and `resolve_governance_model.py`) that rely strictly on Python standard library modules (`argparse`, `json`, `os`, `re`, `sys`). The scanner flagged documentation URLs (`models.dev`, `opencode.ai`), but neither script initiates network calls, invokes subprocesses, or writes to the filesystem. Operations are entirely read-only.

## Quantitative Metrics

| Metric | Target | Result | Status |
|---|---|---|---|
| Description Length | ≤ 1024 chars | 814 chars | PASS |
| Body Word Count | ≤ 6250 words | 1449 words | PASS |
| Trigger Precision | > 90% | 1.00 (10/10) | PASS |
| Trigger Recall | > 85% | 1.00 (10/10) | PASS |
| False Positive Rate | < 5% | 0.00 (0/10) | PASS |
| Assertion Pass Rate | > 90% | 1.00 (20/20) | PASS |
| Dead Resources | 0 | 0 | PASS |
| Script Execution Pass Rate | 100% | 8/8 test paths | PASS |

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---|---|
| Output Quality — Accuracy | 5 | Accurately models OpenCode config precedence (project strictly overrides global) and live 2026 model pricing/context. |
| Output Quality — Completeness | 5 | Covers all 3 tiers, 3 optimization modes, launch command emission, and subagent `opencode.json` config patching. |
| Output Quality — Clarity | 5 | Concise step-by-step instructions, clear examples, and concrete error handling. |
| Output Quality — Formatting | 5 | Standard Agent Skills format adhering strictly to frontmatter and section guidelines. |
| Instruction Fidelity | 5 | Perfectly aligns with `AGENTS.md` blueprint requirements. |
| Edge Case Handling | 5 | Robustly handles missing config files, unconfigured providers, context window overflow, low-confidence heuristic defaults, and deprecated models. |
| Coexistence | 5 | Distinct trigger boundaries with clear DO NOT TRIGGER distinctions against prompt rewriting, credential provisioning, and live benchmarks. |
| User Trust | 5 | Auditable resolution trace explaining why a model was chosen and why alternatives were passed over. |

## Script Verification and Testing

Both scripts were tested across multiple operational paths:
1. `profile_prompt.py`:
   - Prompt input via CLI arg: correctly identified Tier 1 keywords ("system architecture", "security audit").
   - Prompt input for Tier 2: correctly classified ("implement", "write unit test").
   - Prompt input for Tier 3: correctly classified ("format", "validate schema", "commit message").
   - Chain-of-thought detection: correctly flagged `chain_of_thought_recommended: true` when reasoning cues ("why", "debug", "tradeoff") are present.
2. `resolve_governance_model.py`:
   - Local project config inspection: correctly parsed `./opencode.json` and recognized that only `google-vertex` was configured, picking `google-vertex/gemini-3.1-pro-preview` for Tier 1 `result_maximized`.
   - Unconstrained / multi-provider resolution: correctly selected `anthropic/claude-opus-5` for Tier 1 `result_maximized`, `openai/o3` for `cost_optimized`, and `anthropic/claude-sonnet-5` for Tier 2 `balanced`.
   - Subagent config patching: correctly output `config_patch` JSON for `--agent-name creator`.
   - Error handling & context overflow: when `--input-tokens 2000000` exceeded all candidates in Tier 3, returned structured JSON error `"no_eligible_model"` and exited with code 1 without crashing or silently downgrading.

## Security Review

- **Order-of-operations checklist:** Completed.
- **Scanner findings:** 8 pattern matches for `https://` URLs in markdown reference files and JSON schema `$schema`/`$id` declarations. Manually verified to be documentation and schema identifiers; zero network calls made at runtime.
- **Privilege & Blast Radius:** Read-only access to specified JSON configuration files (`~/.config/opencode/opencode.json`, `./opencode.json`). No file creation, no deletion, no shell execution.
- **Final Risk Tier:** Low / Medium.

## Changes Applied During Evaluation
- Validated all references, scripts, schemas, and templates.
- Verified executable bits (`chmod +x`) on scripts.
- Generated comprehensive 20-prompt evaluation test suite in `tests/eval_suite.json`.
- Promoted skill directory from `drafts/model-governance/` to `skills/model-governance/`.

## Production Checklist Status
- [x] Frontmatter includes name, description, version, license, author.
- [x] Trigger and Do-Not-Trigger conditions present, unambiguous, and tested.
- [x] References, scripts, and assets placed in appropriate subfolders.
- [x] All relative links within SKILL.md point to existing files.
- [x] Security review executed; no critical or unmitigated high findings.
- [x] Quantitative metrics meet or exceed all acceptance thresholds.
- [x] Tests suite present and results recorded.
