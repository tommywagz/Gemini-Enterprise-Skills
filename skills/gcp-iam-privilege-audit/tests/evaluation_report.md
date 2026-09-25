# Skill Evaluation Report: gcp-iam-privilege-audit

**Evaluation Workflow:** `evaluate-skill`
**Target Skill:** `gcp-iam-privilege-audit`
**Skill Path:** `skills/gcp-iam-privilege-audit`
**Evaluator Worker:** `evaluator-1`
**Date:** 2026-09-25

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | High (IAM Governance) | `evaluator-1` / 2026-09-25 |
| **Fable** | `fable` | PENDING | — | — | — | — | — | — |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Purpose & Focus:** Evaluates dense instruction comprehension, deep summarization accuracy, and strict compliance with complex skill constraints (IAM policy recommendations, least-privilege role replacement, Workload Identity Federation migration, and review-only Terraform snippets).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/gcp-iam-privilege-audit/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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
  - Description length: 597 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 646 words / ~517 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

### Security Review
- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **High** (Concerns cloud IAM permission auditing and policy recommendations)
- **Remediation & Analysis:**
  - Hardcoded secrets / credentials: None detected (bearer tokens are passed strictly via stdin and never saved to disk).
  - Path traversal check: 0 findings.
  - Network calls: Uses read-only `urllib` calls directed strictly to the official GCP Recommender endpoint (`https://recommender.googleapis.com/...`).
  - High-privilege CLI patterns: None. The skill generates review-only Terraform snippets and does not invoke live mutating commands (`gcloud`, `terraform apply`).
  - Data classification: Policies and service account inventories are treated as Confidential.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurately identifies primitive roles (`roles/editor`, `roles/owner`) and recommends least-privilege predefined replacements. |
| **Output Quality — Completeness** | 5 | Fully covers Recommender output ingestion, key audits, Workload Identity Federation patterns, and Terraform review snippets. |
| **Output Quality — Clarity** | 5 | Clear step-by-step guidance keeping humans strictly in control of policy application. |
| **Output Quality — Formatting** | 5 | Clean Markdown formatting with precise code blocks, tables, and asset links. |
| **Instruction Fidelity** | 5 | Strictly enforces review-only posture; never attempts autonomous IAM mutations. |
| **Edge Case Handling** | 5 | Explicitly covers unavailable reference fallbacks and missing IAM Recommender permissions. |
| **Coexistence** | 5 | Precise trigger boundaries preventing conflicts with Terraform IaC compliance, GKE triage, and FinOps skills. |
| **User Trust** | 5 | Enterprise-grade IAM governance following Google Cloud Architecture Framework security principles. |

---

## Findings & Verifications Applied
1. **Mock Mode Verification:** Verified `scripts/get_iam_recommendations.py --mock` operates completely offline without network calls or credential inputs.
2. **Read-Only Enforcement:** Confirmed instructions never attempt automated `gcloud projects set-iam-policy` or destructive modifications.
3. **Routing Verification:** Tested across 10 in-scope IAM hardening/audit prompts and 10 out-of-scope negative prompts (AWS IAM, Azure RBAC, GKE deployment, CrashLoopBackOff, CIS IaC scans, FinOps). Zero routing errors observed.
