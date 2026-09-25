# Skill Evaluation Report: a2a-workflows

**Evaluation Workflow:** `evaluate-skill`
**Target Skill:** `a2a-workflows`
**Skill Path:** `skills/a2a-workflows`
**Evaluator Worker:** `evaluator-1`
**Date:** 2026-09-25

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-1` / 2026-09-25 |
| **Fable** | `fable` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-1` / 2026-09-25 |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Purpose & Focus:** Evaluates dense instruction comprehension, deep summarization accuracy, and strict compliance with complex skill constraints (A2A protocol specifications, card resolution, and ADK tool wiring).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/a2a-workflows/tests/eval_suite.json` (22 total evals: 10 in-scope positive triggers, 12 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix
| Metric | Count |
|---|---|
| True Positives (TP) | 10 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 12 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 22 |

### Quantitative Metrics
| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

### Preflight Quality & Token Efficiency Verification
- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 372 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 749 words / ~600 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

### Security Review
- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Low**
- **Analysis:**
  - Hardcoded secrets / credentials: None detected
  - Command injection / shell executions: None detected
  - Path traversal / unsafe file operations: None detected
  - Network calls: Uses safe `httpx.AsyncClient` within structured tools; input validation enforced on remote agent URLs to mitigate SSRF risk.

---

## Model Evaluation: Fable (`fable`)

- **Evaluation Purpose & Focus:** Evaluates creative reasoning, edge-case routing resilience, subtle boundary discrimination, and negative trigger suppression (preventing false activations on adjacent non-A2A multi-agent or standard ADK queries).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/a2a-workflows/tests/eval_suite.json` (22 total evals: 10 in-scope positive triggers, 12 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix
| Metric | Count |
|---|---|
| True Positives (TP) | 10 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 12 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 22 |

### Quantitative Metrics
| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

### Boundary Discrimination & Negative Trigger Suppression Analysis
- Fable specifically verified subtle negative triggers:
  - Standard ADK composite patterns (`SequentialAgent`, `ParallelAgent`, `LoopAgent`): Correctly suppressed.
  - Multi-agent frameworks other than ADK (`LangGraph`, `CrewAI`): Correctly suppressed without cross-talk.
  - Standard single-agent tool definitions and Pydantic schemas: Accurately passed through to standard skills.
  - Malicious prompt injection / data exfiltration prompts: Safely rejected and unactivated.

### Preflight Quality & Token Efficiency Verification
- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 372 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 749 words / ~600 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

### Security Review
- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Low**

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurate protocol implementation following standard A2A specification and ADK guidelines. |
| **Output Quality — Completeness** | 5 | Fully covers multi-agent topologies, HostAgent orchestration, SubAgent cards, card resolution, and parts conversion. |
| **Output Quality — Clarity** | 5 | Clear instructions with robust, cleanly commented Python boilerplate. |
| **Output Quality — Formatting** | 5 | Clean Markdown formatting with precise code blocks and reference paths. |
| **Instruction Fidelity** | 5 | Preserves order of operations and strictly enforces ADK lifecycle rules. |
| **Edge Case Handling** | 5 | Explicitly covers network timeouts (`httpx.HTTPError`), sub-agent downtime, and task cancellations. |
| **Coexistence** | 5 | Well-delineated trigger conditions and anti-triggers (`DO NOT TRIGGER when: normal ADK workflows without A2A`). |
| **User Trust** | 5 | Production-ready patterns and architectures standard across Google Enterprise ADK deployments. |

---

## Findings & Verifications Applied
1. **Trigger Routing Precision:** Validated across 12 realistic negative prompts (standard ADK workflows, tool definitions, Pydantic structured output, composite agents, Cloud Run deployment, HITL workflows, general web scraping). No false triggers observed.
2. **Trigger Recall:** Validated across 10 distinct A2A orchestration and card resolution queries. All triggered accurately.
3. **Reference Links:** All references (`references/a2a-spec.md` and `references/a2a-multiagent-python.md`) exist, are fully referenced in `SKILL.md`, and contain complete architectural guides.
4. **Safety & Robustness:** Verified presence of anti-patterns, input validation guidelines, and fallback instructions.
