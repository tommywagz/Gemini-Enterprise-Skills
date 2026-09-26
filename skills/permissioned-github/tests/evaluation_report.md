# Skill Evaluation Report: permissioned-github

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `permissioned-github`  
**Skill Path:** `skills/permissioned-github`  
**Evaluator Worker:** `evaluator-3`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-3` / 2026-09-25 |
| **Fable** | `fable` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-3` / 2026-09-25 |
| **3.8 Flash** | `gemini-3.8-flash-high` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-3` / 2026-09-25 |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Focus:** Strict CLI enforcement (gh with -R ORG/REPO, git over HTTPS), permission format parsing (<binary>.<action>(<resource_json>)), and granular resource scoping.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/permissioned-github/tests/eval_suite.json` (8 evals: 4 in-scope positive triggers, 4 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix (Argon)

| Metric | Count |
|---|---|
| True Positives (TP) | 4 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 4 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 8 |

### Quantitative Metrics (Argon)

| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

---

## Model Evaluation: Fable (`fable`)

- **Evaluation Purpose & Focus:** Negative trigger suppression for Python algorithms, AWS infrastructure setup, TCP/UDP theory, and Go unit testing.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/permissioned-github/tests/eval_suite.json` (8 total evals: 4 in-scope positive triggers, 4 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix (Fable)

| Metric | Count |
|---|---|
| True Positives (TP) | 4 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 4 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 8 |

### Quantitative Metrics (Fable)

| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

---

## Model Evaluation: 3.8 Flash (`gemini-3.8-flash-high`)

- **Evaluation Focus:** Instant permission string synthesis, deterministic CLI parameter formatting, and safe git branch operations.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/permissioned-github/tests/eval_suite.json` (8 total evals: 4 in-scope positive triggers, 4 out-of-scope negative triggers).
- **Iterations Required:** 1 (passed baseline gates on initial iteration).

### Confusion Matrix (3.8 Flash)

| Metric | Count |
|---|---|
| True Positives (TP) | 4 |
| False Positives (FP) | 0 |
| True Negatives (TN) | 4 |
| False Negatives (FN) | 0 |
| Total Graded Evals | 8 |

### Quantitative Metrics (3.8 Flash)

| Metric | Target | Actual Score | Status |
|---|---|---|---|
| **Trigger Precision** | > 90% | **100.0%** (1.0000) | **PASS** |
| **Trigger Recall** | > 85% | **100.0%** (1.0000) | **PASS** |
| **False Positive Rate (FPR)** | < 5% | **0.0%** (0.0000) | **PASS** |
| **Assertion Pass Rate** | > 80% | **100.0%** (1.0000) | **PASS** |

---

## Comparative Model Analysis

| Evaluation Metric | Argon (`argon-sum`) | Fable (`fable`) | 3.8 Flash (`gemini-3.8-flash-high`) | Production Threshold | Evaluation Consensus |
|---|---|---|---|---|---|
| **Trigger Precision** | 100.0% | 100.0% | 100.0% | > 90% | **CONVERGENT PASS** |
| **Trigger Recall** | 100.0% | 100.0% | 100.0% | > 85% | **CONVERGENT PASS** |
| **False Positive Rate** | 0.0% | 0.0% | 0.0% | < 5% | **CONVERGENT PASS** |
| **Assertion Pass Rate** | 100.0% | 100.0% | 100.0% | > 80% | **CONVERGENT PASS** |

### Qualitative Model Behavioral Profiles

1. **Argon (`argon-sum`):** Exhibited exhaustive compliance with structural rules, edge cases, and deterministic formatting specifications.
2. **Fable (`fable`):** Demonstrated nuanced negative trigger discrimination, perfectly suppressing out-of-domain requests without degradation in recall.
3. **3.8 Flash (`gemini-3.8-flash-high`):** Delivered the fastest end-to-end execution with 100% token efficiency and high prompt dispatch fidelity.

---

## Token Efficiency & Security Audit Gate Verification

- **Token Efficiency Check (`validate_skill_token_efficiency.py`):** **PASSED** (0 unreferenced resources, 0 duplicate paragraphs, word count within budget).
- **Deterministic Security Scan (`security_scan.sh`):** **PASSED** (0 Critical vulnerabilities, 0 hardcoded secrets, safe command execution).
- **Promotion Recommendation:** **PROMOTE TO ENTERPRISE CATALOG** (All quality gates passed across all 3 models).
