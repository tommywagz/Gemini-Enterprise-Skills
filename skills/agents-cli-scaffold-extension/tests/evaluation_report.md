# Skill Evaluation Report: agents-cli-scaffold-extension

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `agents-cli-scaffold-extension`  
**Skill Path:** `skills/agents-cli-scaffold-extension`  
**Evaluator Worker:** `evaluator-5`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | High | `evaluator-5` / 2026-09-25 |
| **Fable** | `fable` | PENDING | — | — | — | — | — | — |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Focus:** Evaluates dense technical instruction comprehension, multi-language boundary contracts, generator flags, directory layout verification, and error handling across TypeScript (Hono) and Python (ADK).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/agents-cli-scaffold-extension/tests/eval_suite.json` (20 evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial remediation iteration).

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
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

### Preflight Quality & Token Efficiency Verification

- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 562 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 1061 words / ~850 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: Resolved 9 unreferenced template resources in `assets/templates/` -> **PASS**
  - Duplicate paragraphs: Resolved exact paragraph duplicate with `references/cli_scaffold_commands.md` -> **PASS**

### Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **High**
- **Analysis:**
  - Contains generator script `generate_polyglot_workspace.py` and local test runners `test_generator.py` and `verify_runtime.py`.
  - Security scanner flagged path traversal patterns (`../`) in `tests/test_generator.py`; manual verification confirms these are automated negative test assertions verifying that the generator actively rejects directory traversal attempts (`'../escape'`, `'../bad'`) with exit code 2 and creates no files.
  - Zero hardcoded credentials or destructive unconstrained shell commands exist. Localhost HTTP communication in tests is restricted to local test ports.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurate scaffolding contracts between Hono HTTP gateway and Python ADK agents. |
| **Output Quality — Completeness** | 5 | Full workspace scaffolding coverage: npm workspaces, venv, JSON request schemas, and demo execution. |
| **Output Quality — Clarity** | 5 | Clean step-by-step workflow with clear distinction between CLI scaffolding and framework runtime. |
| **Output Quality — Formatting** | 5 | Well-structured Markdown with explicit command blocks, file references, and error tables. |
| **Instruction Fidelity** | 5 | Adheres to safety policies: never overwrites existing directories without confirmation, advises staging in sibling folders for existing repos. |
| **Edge Case Handling** | 5 | Covers port conflicts, invalid identifier names, upstream 502/504 errors, and missing package dependencies. |
| **Coexistence** | 5 | Anti-triggers clearly delineate single-agent scaffolding, lone virtualenvs, and generic Hono route authoring. |
| **User Trust** | 5 | Transparent generator behavior with dry-run capabilities and deterministic template substitution. |

---

## Findings & Verifications Applied

1. **Remediated Token-Efficiency Violations:**
   - Fixed exact duplicated installation paragraph with `references/cli_scaffold_commands.md` in `SKILL.md`.
   - Referenced all 9 bundled template files (`WORKSPACE.md.tmpl`, `agent.py.tmpl`, `app.ts.tmpl`, `index.ts.tmpl`, `message.schema.json.tmpl`, `package.json.tmpl`, `requirements.txt.tmpl`, `tsconfig.json.tmpl`, `web-package.json.tmpl`) under `assets/templates/` in `SKILL.md` reference files section.
   - Re-verified repository-wide linter: all 25 skills now pass cleanly.
2. **Constructed 20-Prompt Evaluation Suite (`tests/eval_suite.json`):**
   - Added 10 realistic positive prompts covering multi-agent polyglot workspace generation, dry-run previews, Hono-to-ADK gateway routes, custom port flags, monorepo integration, and demo verification.
   - Added 10 realistic negative prompts covering single-agent templates, lone virtualenvs, generic Hono APIs, Docker/Cloud Run deployments, IAM audits, Pub/Sub harnesses, A2A workflows, FinOps, and unit testing.
3. **Execution Verification:**
   - Ran `score_eval_suite.py` on Argon yielding 100% precision, 100% recall, 0% FPR, and 100% assertion pass rate.
