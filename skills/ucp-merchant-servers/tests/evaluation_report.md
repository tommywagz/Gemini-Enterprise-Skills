# Skill Evaluation Report: ucp-merchant-servers

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `ucp-merchant-servers`  
**Skill Path:** `skills/ucp-merchant-servers`  
**Evaluator Worker:** `evaluator-5`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-5` / 2026-09-25 |
| **Fable** | `fable` | PENDING | — | — | — | — | — | — |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Focus:** Evaluates dense protocol specification comprehension, Universal Commerce Protocol (UCP) profile metadata, merchant checkout lifecycles, signature verification, and FastAPI/Hono service boilerplates.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/ucp-merchant-servers/tests/eval_suite.json` (22 evals: 10 in-scope positive triggers, 12 out-of-scope negative triggers).
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
  - Description length: 362 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 1064 words / ~850 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 unreferenced files across `references/` -> **PASS**
  - Duplicate paragraphs: 0 duplicate paragraphs detected -> **PASS**

### Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Low**
- **Analysis:**
  - Instructions-only skill with no bundled executable scripts.
  - Scanner output flagged relative module imports (`../models/schemas`) and sample data directories in markdown reference files; manual inspection confirms these are non-executable documentation examples.
  - References contain standard UCP schema URLs (`https://ucp.dev/...`) for documentation purposes.
  - Zero hardcoded credentials, zero destructive shell commands, and zero path traversal vulnerabilities exist.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurate implementation of the Universal Commerce Protocol (UCP) merchant specification. |
| **Output Quality — Completeness** | 5 | Full coverage of `.well-known/ucp` discovery, checkout session states, webhook deliveries, and order fulfillment. |
| **Output Quality — Clarity** | 5 | Clear instructions distinguishing merchant server implementations from consumer client surfaces. |
| **Output Quality — Formatting** | 5 | Clean markdown formatting with complete TypeScript/Hono and Python/FastAPI code snippets. |
| **Instruction Fidelity** | 5 | Adheres to protocol invariants: idempotent order creation, cryptographic webhook signing, and strict profile verification. |
| **Edge Case Handling** | 5 | Addresses expired checkout sessions, conflicting discount codes, delivery webhook retries, and schema validation failures. |
| **Coexistence** | 5 | Clean anti-triggers prevent collisions with UCP consumer surfaces (`ucp-consumer-surface`), schema authoring, or AP2 payments. |
| **User Trust** | 5 | Production-ready patterns aligning with official UCP merchant compliance standards. |

---

## Findings & Verifications Applied

1. **Trigger Routing Precision:** Validated across 12 realistic negative prompts covering consumer UCP shopping agents, AP2 payment mandates, generic Stripe integrations, GraphQL APIs, and routine unit tests. Zero false triggers observed.
2. **Trigger Recall:** Validated across 10 diverse UCP merchant server inquiries (.well-known profile publishing, checkout sessions, webhook handlers, FastAPI backends, Hono gateways). All 10 activated correctly.
3. **Reference Links:** All references (`references/ucp-spec.md`, `references/python-fastapi-merchant.md`, `references/nodejs-hono-merchant.md`) verified present and referenced in `SKILL.md`.
4. **Safety Verification:** Validated that merchant endpoint templates enforce authentication, rate limiting, and signature verification.
