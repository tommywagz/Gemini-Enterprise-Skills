# Skill Evaluation Report: model-governance

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `model-governance`  
**Skill Path:** `skills/model-governance`  
**Evaluator Worker:** `evaluator-3`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low / Medium | `evaluator-3` / 2026-09-25 |
| **Fable** | `fable` | PENDING | — | — | — | — | — | — |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Purpose & Focus:** Evaluates dense technical instruction comprehension, multi-tier complexity profiling accuracy, strict OpenCode configuration precedence enforcement, and launch command generation precision.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/model-governance/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix
| Metric | Count |
|---|---|
| True Positives (TP) | 10 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 10 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 20 |

### Quantitative Metrics
| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | 100% | **100.0%** (1.0000) | **PASS** |

### Preflight Quality & Token Efficiency Verification
- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 816 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 1,329 words (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

### Security Review
- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Low / Medium**
- **Analysis:**
  - Hardcoded secrets / credentials: None detected
  - Command injection / dangerous shell executions: None detected
  - Path traversal / unsafe file operations: 0 path traversal patterns detected
  - Network calls: 0 runtime network calls; URL patterns in references and assets correspond strictly to schema identifiers and documentation citations.
  - Blast radius: Read-only local configuration file inspection (`opencode.json`). Never writes without explicit instruction, executes no external shell processes, and makes no API calls.

### Integration Evidence
- `scripts/profile_prompt.py`: Accurately classifies prompt cognitive complexity into Tier 1 (frontier reasoning), Tier 2 (balanced workhorse), or Tier 3 (fast routine).
- `scripts/resolve_governance_model.py`: Resolves model candidates against user policies (`balanced`, `cost_optimized`, `result_maximized`) and handles context overflow with structured JSON error envelopes.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurately models OpenCode config precedence (project overrides global) and model pricing tiers. |
| **Output Quality — Completeness** | 5 | Fully covers all 3 tiers, 3 optimization modes, launch command emission, and subagent `opencode.json` patching. |
| **Output Quality — Clarity** | 5 | Concise step-by-step instructions, clear schema examples, and auditable resolution traces. |
| **Output Quality — Formatting** | 5 | Clean Markdown schema, valid JSON fixtures, and well-structured tables. |
| **Instruction Fidelity** | 5 | Strictly enforces non-destructive read-only configuration resolution. |
| **Edge Case Handling** | 5 | Handles missing configs, unconfigured providers, context window overflow, and fallback defaults. |
| **Coexistence** | 5 | Clear trigger boundaries distinct from prompt rewriting, API credential management, and live benchmark evaluation. |
| **User Trust** | 5 | High trust: explains resolution decisions with transparent fall-through logs. |

---

## Findings & Verifications Applied
1. **Eval Suite Architecture:** Evaluated standard 20-prompt suite on **Argon** (`argon-sum`), achieving 100.0% precision, 100.0% recall, 0.0% FPR, and 100.0% assertion pass rate.
2. **Deterministic Token Efficiency:** Validated description at 816 characters and active body at 1,329 words with zero unreferenced resources.
3. **Execution Safety:** Verified that bundled utilities rely purely on standard library modules (`argparse`, `json`, `os`, `re`, `sys`) with 0 external network dependencies.
