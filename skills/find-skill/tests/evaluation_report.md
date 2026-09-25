# Skill Evaluation Report: find-skill

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `find-skill`  
**Skill Path:** `skills/find-skill`  
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

- **Evaluation Focus:** Evaluates dense technical instruction comprehension, registry query parsing, multi-source screening logic, allowlist domain enforcement, and prompt injection defense.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/find-skill/tests/eval_suite.json` (20 evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

### Preflight Quality & Token Efficiency Verification

- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 305 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 392 words / ~320 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 unreferenced files in `references/` or `scripts/` -> **PASS**
  - Duplicate paragraphs: 0 duplicate paragraphs detected -> **PASS**

### Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **High**
- **Analysis:**
  - `search_registries.py` queries external public registries over HTTPS (`raw.githubusercontent.com`, `registry.modelcontextprotocol.io`, `backend.composio.dev`) subject to strict timeouts and read limits.
  - `screen_candidate.py` performs static prompt injection screening (instruction override detection, exfiltration patterns, credential patterns).
  - Scanner output flagged path traversal strings in `references/security_screening.md`; manual verification confirms these are documentation bullet points detailing patterns screened during candidate ingestion.
  - Zero hardcoded credentials or destructive unconstrained shell commands exist.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurate registry search parameters and strict screening against prompt injection. |
| **Output Quality — Completeness** | 5 | Complete search-to-install pipeline: discovery, sandbox screening, user confirmation, and local installation. |
| **Output Quality — Clarity** | 5 | Concise instructions with unambiguous source allowlists and safety barriers. |
| **Output Quality — Formatting** | 5 | Clean markdown formatting with explicit command invocations and structured tables. |
| **Instruction Fidelity** | 5 | Enforces strict safety gates: never reads candidate skill instructions as prompt directives before screening. |
| **Edge Case Handling** | 5 | Handles network timeouts, unparseable registry schemas, untrusted sources, and malicious candidate payloads. |
| **Coexistence** | 5 | Clean anti-triggers prevent collisions with authoring new skills (`write-skill`), evaluation (`evaluate-skill`), or generic web queries. |
| **User Trust** | 5 | Mandatory user approval before installing vetted tools into the project. |

---

## Findings & Verifications Applied

1. **Trigger Routing Precision:** Validated across 10 realistic negative prompts covering authoring from scratch, evaluating existing skills, generic web searches, AWS IAM audits, and local debugging. Zero false triggers observed.
2. **Trigger Recall:** Validated across 10 in-scope discovery prompts (awesome-agent-skills, MCP registries, Composio integrations, Slack, Jira, GitHub PR review tools). All 10 activated correctly.
3. **Reference Links:** All references (`references/source_allowlist.md`, `references/security_screening.md`, `scripts/search_registries.py`, `scripts/screen_candidate.py`) verified present and referenced in `SKILL.md`.
4. **Safety Verification:** Validated that candidate skills are strictly treated as untrusted data until screened and approved.
