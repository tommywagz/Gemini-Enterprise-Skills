# Skill Evaluation Report: write-skill

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `write-skill`  
**Skill Path:** `skills/write-skill`  
**Evaluator Worker:** `evaluator-2`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Medium | `evaluator-5` / 2026-09-25 |
| **Fable** | `fable` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Medium | `evaluator-4` / 2026-09-25 |
| **3.8 Flash** | `gemini-3.8-flash-high` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Medium | `evaluator-2` / 2026-09-25 |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Focus:** Evaluates dense technical instruction comprehension, Agent Skill package scaffolding, YAML frontmatter formatting, token budget optimization, and reference file structural boundaries.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/write-skill/tests/eval_suite.json` (20 evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix (Argon)

| Metric | Count |
|---|---|
| True Positives (TP) | 10 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 10 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 20 |

### Quantitative Metrics (Argon)

| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

---

## Model Evaluation: Fable (`fable`)

- **Evaluation Purpose & Focus:** Evaluates creative reasoning, subtle boundary discrimination, edge-case routing resilience, and negative trigger suppression (preventing false activations when users ask for general software documentation, standard application unit tests, external MCP registry searches, or existing skill evaluation).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/write-skill/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix (Fable)

| Metric | Count |
|---|---|
| True Positives (TP) | 10 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 10 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 20 |

### Quantitative Metrics (Fable)

| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

### Boundary Discrimination & Negative Trigger Suppression Analysis (Fable)
- Fable specifically validated distinct negative triggers and boundary distinctions:
  - Skill Evaluation & Security Auditing (`evaluate-skill`): Accurately suppressed activation on benchmarking trigger precision or red-teaming skill security.
  - External Registry Searching (`find-skill`): Correctly refused prompts seeking existing MCP servers or GitHub awesome-lists.
  - General Project Documentation: Suppressed trigger on authoring general README.md files for frontend/backend projects.
  - Standard Application Code & Unit Testing: Suppressed trigger on writing Python unit tests or application business logic.
  - Direct Skill Invocation: Correctly avoided intercepting instructions to execute an already installed agent skill.

---

## Model Evaluation: 3.8 Flash (`gemini-3.8-flash-high`)

- **Evaluation Purpose & Focus:** Evaluates high-throughput fast-path routing, concise prompt instruction parsing, strict assertion fulfillment, and rapid boundary suppression against general writing tasks.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/write-skill/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix (3.8 Flash)

| Metric | Count | Percentage |
|---|---|---|
| **True Positives (TP)** | 10 | 50% |
| **True Negatives (TN)** | 10 | 50% |
| **False Positives (FP)** | 0 | 0% |
| **False Negatives (FN)** | 0 | 0% |
| **Total Graded Evals** | 20 | 100% |

### Quantitative Metrics (3.8 Flash)

| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

---
## Preflight Quality & Token Efficiency Verification

- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 289 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 382 words / ~300 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 unreferenced files in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicate paragraphs detected -> **PASS**

## Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Medium**
- **Analysis:**
  - Bundles local scaffolding shell script `scaffold_skill.sh`.
  - Scanner output flagged relative path `$SCRIPT_DIR/../assets/skill_template.md` in `scaffold_skill.sh`; manual verification confirms standard local script-relative template resolution.
  - Zero network calls, zero hardcoded credentials, zero destructive shell commands, and zero path traversal vulnerabilities exist.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurate skill layout generation adhering strictly to Antigravity and Gemini CLI specifications. |
| **Output Quality — Completeness** | 5 | Guides directory creation, YAML frontmatter metadata, token-budgeted body, and reference structure. |
| **Output Quality — Clarity** | 5 | Direct, concise instructions emphasizing token conservation and progressive disclosure. |
| **Output Quality — Formatting** | 5 | Clean markdown output conforming to the native skill template. |
| **Instruction Fidelity** | 5 | Adheres strictly to token budgets: enforces frontmatter <= 1024 chars and body <= 6250 words. |
| **Edge Case Handling** | 5 | Prevents common pitfalls: catch-all verbs in descriptions, duplicate text across files, and dead unreferenced assets. |
| **Coexistence** | 5 | Explicit anti-triggers cleanly prevent collisions with general documentation, application code, or skill evaluation (`evaluate-skill`). |
| **User Trust** | 5 | Generates clean, secure, and production-ready Agent Skill directory structures. |

---

## Findings & Verifications Applied

1. **Trigger Routing Precision:** Validated across 10 realistic negative prompts covering writing project READMEs, authoring application Python code, evaluating existing skills, writing API docs, and general blog post writing. Zero false triggers observed.
2. **Trigger Recall:** Validated across 10 in-scope skill authoring prompts (scaffolding a new skill package, writing SKILL.md, restructuring references, optimizing skill descriptions). All 10 activated correctly.
3. **Reference Links:** All references (`references/writing_principles.md`, `references/formatter_fields.md`, `references/full_template.md`, `assets/skill_template.md`, `scripts/scaffold_skill.sh`) verified present and referenced in `SKILL.md`.
4. **Safety Verification:** Confirmed that `scaffold_skill.sh` strictly initializes local folder templates without network operations or elevated privileges.
5. **Fable Model Benchmark & Edge-Case Verification:** Validated 100% precision and recall under Fable (`fable`), verifying robust boundary discrimination against adjacent skills (`evaluate-skill`, `find-skill`) and generic developer queries.
6. **3.8 Flash Benchmark & Tri-Model Certification:** Verified 100% precision, 100% recall, 0% FPR, and 100% assertion pass rate under 3.8 Flash (`gemini-3.8-flash-high`), completing the full tri-model scorecard.
