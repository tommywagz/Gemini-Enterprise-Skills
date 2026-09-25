# Skill Evaluation Report: adk-agents

**Date:** 2026-09-25  
**Evaluator Worker:** evaluator-2  
**Target Model:** Argon  
**Model ID:** `argon-sum`  
**Iteration:** 1 (of 3)  

---

## Executive Summary

The `adk-agents` skill was evaluated under the `evaluate-skill` test-adjust-retest workflow with the **Argon** model (`argon-sum`). The skill provides canonical developer guidelines, cheatsheets, and architectural references for authoring Google Agent Development Kit (ADK) agents, tools, workflows, callbacks, and state management in Python.

With the hardening adjustments applied in Iteration 1 (standardizing the canonical skill name `adk-agents`, refining frontmatter trigger/anti-trigger boundaries, adding edge case gotchas and fallback guidance, and aligning negative assertions), the skill achieved **100% Trigger Precision**, **100% Trigger Recall**, **0% False Positive Rate**, and **100% Assertion Pass Rate** across the 20-prompt test suite.

Verdict: **PASS** (Ready for fleet merge and multi-model benchmarking).

---

## Risk Tier & Security Review

- **Security Risk Tier:** Low (Automated scanner flagged high pattern due to benign documentation URL mentions of `curl https://adk.dev/llms.txt`; manual verification confirms zero executable blast radius, zero hardcoded credentials, zero path traversal, and zero unconstrained shell commands).
- **Blast Radius:** None (Reference and documentation skill only; no local executable scripts or system mutators).
- **Security Scanner Output (`security_scan.sh`):** Passed with 0 Critical vulnerabilities.

---

## Multi-Model Evaluation Comparison Matrix

| Model | Model ID | Precision | Recall | FPR | Assertion Pass Rate | Status | Iterations |
|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **100%** (1.0) | **100%** (1.0) | **0%** (0.0) | **100%** (1.0) | **PASS** | 1 |
| *Fable* | `fable` | Pending | Pending | Pending | Pending | PENDING | — |
| *3.8 Flash* | `gemini-3.8-flash-high` | Pending | Pending | Pending | Pending | PENDING | — |

---

## Quantitative Metrics (Model: Argon / `argon-sum`)

| Metric | Target | Baseline | Hardened | Status |
|---|---|---|---|---|
| **Trigger Precision** | > 90% | 100% | 100% | **PASS** |
| **Trigger Recall** | > 85% | 100% | 100% | **PASS** |
| **False Positive Rate (FPR)** | < 5% | 0% | 0% | **PASS** |
| **Assertion Pass Rate** | > 90% | 100% | 100% | **PASS** |
| **Total Graded Test Cases** | >= 20 | 20 | 20 | **PASS** |
| **Token Word Count Budget** | < 6,250 words | 403 words | 630 words | **PASS** |
| **Description Length** | < 1,024 chars | 542 chars | 598 chars | **PASS** |

### Confusion Matrix (Argon)

| Category | Count | Percentage |
|---|---|---|
| **True Positives (TP)** | 10 | 50% |
| **True Negatives (TN)** | 10 | 50% |
| **False Positives (FP)** | 0 | 0% |
| **False Negatives (FN)** | 0 | 0% |
| **Total Evaluations** | 20 | 100% |

---

## Qualitative Rubric Scores (Argon)

| Dimension | Score (1-5) | Evidence & Notes |
|---|---|---|
| **Accuracy** | 5 | Accurate APIs matching Google ADK Python SDK (`Agent`, `BaseAgent`, `ManagedAgent`, `Workflow`). |
| **Completeness** | 5 | Comprehensive references for primitives, tools, callbacks, state, workflows, and samples. |
| **Clarity** | 5 | Concise code snippets and structured tables for edge cases and references. |
| **Formatting** | 5 | Valid GitHub Flavored Markdown with syntax-highlighted code fences. |
| **Instruction Fidelity** | 5 | Correct guidance on prerequisites and explicit routing to sibling skills. |
| **Edge Case Handling** | 5 | Documented gotchas regarding Pydantic `output_schema`, `google_search` AFC limitations, and state collisions. |
| **Coexistence** | 5 | Explicit anti-triggers cleanly separate `adk-agents` from scaffolding, deployment, and A2A workflows. |
| **User Trust** | 5 | Professional, standards-aligned documentation suitable for production systems. |

---

## Test-Adjust-Retest Remediation Log

| Iteration | Finding / Gap | Remediation Applied | Files Changed | Retest Score |
|---|---|---|---|---|
| **Iter 1** | Mismatched legacy name `google-agents-cli-adk-code` in frontmatter and negative assertions | Renamed skill to canonical `adk-agents` in `SKILL.md` and updated negative test assertions | `SKILL.md`, `tests/eval_suite.json` | 100% Pass |
| **Iter 1** | Missing explicit Edge Cases & Gotchas section | Added Edge Cases table covering Pydantic schema constraints, tool AFC, and state naming | `SKILL.md` | 100% Pass |
| **Iter 1** | Missing Fallback and Input Validation guidance | Added Input Validation & Prerequisites and offline Fallback Instructions | `SKILL.md` | 100% Pass |
| **Iter 1** | Need Argon baseline documentation | Generated comprehensive evaluation report for model `argon-sum` | `tests/evaluation_report.md` | 100% Pass |

---

## Verification & Quality Gates Summary

- [x] **Token Efficiency Validator:** Passed (Description: 598 chars < 1024; Body: 630 words < 6250; 0 unreferenced resources; 0 duplicate paragraphs).
- [x] **Deterministic Security Scanner:** Passed (0 Critical vulnerabilities; benign docs URL pattern confirmed).
- [x] **Graded Evaluation Suite:** Passed (Precision: 1.0, Recall: 1.0, FPR: 0.0, Assertion Pass Rate: 1.0).
- [x] **Target Model Benchmarked:** Argon (`argon-sum`).
