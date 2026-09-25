# Skill Evaluation Report: ucp-consumer-surface

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `ucp-consumer-surface`  
**Skill Path:** `skills/ucp-consumer-surface`  
**Evaluator Worker:** `evaluator-3`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | High (Commerce Client Surface) | `evaluator-3` / 2026-09-25 |
| **Fable** | `fable` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | High (Commerce Client Surface) | `evaluator-3` / 2026-09-25 |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Purpose & Focus:** Evaluates dense technical instruction comprehension, multi-step commerce client lifecycle execution (discovery, capability negotiation, cart building, checkout state progression, payment handler binding, irreversible order confirmation, and RFC 9421/9530 webhook signature verification).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/ucp-consumer-surface/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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

### Functional & Integration Self-Test Verification
- **Test Runner:** `scripts/ucp_client_helper.py selftest --verbose`
- **Results:** 21 / 21 checks passed (0 failures).
- **Verified Behaviors:**
  1. Discovery capability resolution and payment handler extraction.
  2. Caller-provided `idempotency_key` preservation across retries.
  3. Full-replacement cart payload updates and item repricing.
  4. Progressive checkout transitions (`incomplete` -> `ready_for_complete`).
  5. Mandatory explicit buyer confirmation gate prior to irreversible completion (`user_confirmed=True`).
  6. Rejection of unadvertised or invalid payment handlers.
  7. Concurrency lockouts preventing mutations during `complete_in_progress`.
  8. Webhook `Content-Digest` verification, replay rejection, and signature requirement enforcement.
  9. Reverse-domain namespace authority binding derivation (`validate_authority_binding`).

### Preflight Quality & Token Efficiency Verification
- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 753 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 1,692 words (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

### Security Review
- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **High** (Client e-commerce purchasing and external network calls)
- **Security Findings & Safeguards:**
  - Hardcoded secrets / credentials: None detected.
  - Path traversal / unsafe file operations: 0 findings.
  - High-privilege CLI patterns: None detected.
  - Network calls: Directed exclusively via stdlib `urllib` to caller-specified business URLs and discovery profiles.
  - Blast radius & safeguards: Irreversible purchase completions require explicit interactive buyer confirmation (`user_confirmed=True`) and handler authorization. Webhooks enforce replay protection and cryptographic verification. Self-test runs in-process on loopback interface with zero live external traffic.

---

## Model Evaluation: Fable (`fable`)

- **Evaluation Purpose & Focus:** Evaluates multi-turn commerce conversation management, strict compliance with UCP confirmation safety boundaries, checkout progression logic, and handling of ambiguous or out-of-scope triggers (e.g. server-side routes or non-UCP payment flows).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/ucp-consumer-surface/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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

### Functional & Integration Self-Test Verification
- **Test Runner:** `scripts/ucp_client_helper.py selftest --verbose`
- **Results:** 21 / 21 checks passed (0 failures).
- **Verified Behaviors:**
  - Robust routing and conversational disambiguation between consumer shopping client vs. merchant server hosting.
  - Verification of non-negotiable buyer confirmation gate (`user_confirmed=True`) prior to order placement.
  - Idempotency key preservation across retry cycles.
  - Full-replacement cart and checkout update semantics.
  - Inbound webhook tamper rejection and authority binding checks.

### Preflight Quality & Token Efficiency Verification
- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 753 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 1,692 words (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

### Security Review
- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **High** (Commerce Client Surface)
- **Security Findings & Safeguards:**
  - 0 Critical vulnerabilities, 0 path traversals, 0 hardcoded secrets.
  - Safe boundary enforcement: checkout completion is guarded against premature or unconfirmed execution.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Fully grounded in official UCP 2026-08-25 specifications, RFC 9421/9530 signing, and reverse-domain authority binding rules. |
| **Output Quality — Completeness** | 5 | End-to-end client flow covered: discovery, catalog lookup, cart update, checkout session, buyer confirmation, order tracking, and webhooks. |
| **Output Quality — Clarity** | 5 | Step-by-step workflow with clear distinction between HTTP status codes and the UCP body-level business outcome error model. |
| **Output Quality — Formatting** | 5 | Standard YAML frontmatter, clean Markdown tables, and structured JSON Schema / payload templates. |
| **Instruction Fidelity** | 5 | Cleanly respects boundary lines: defers server-side routes to `ucp-merchant-servers` and payment mandates to AP2 skills. |
| **Edge Case Handling** | 5 | Explicitly models partial payload anti-patterns, missing capabilities, out-of-stock errors, and webhook replay protection. |
| **Coexistence** | 5 | Operates alongside `ucp-merchant-servers`, `ucp-extensions-schemas`, and `ap2-agent-payments` without trigger overlap. |

---

## Findings & Verifications Applied
1. **Eval Suite Verification:** Evaluated 20 standard routing prompts on **Argon** (`argon-sum`) and **Fable** (`fable`), scoring 100.0% precision, 100.0% recall, 0.0% FPR, and 100.0% assertion pass rate.
2. **Deterministic Token Efficiency:** Validated description length at 753 characters and body word count at 1,692 words with zero unreferenced resources.
3. **End-to-End Client Lifecycle:** Validated all 21 automated self-tests in `scripts/ucp_client_helper.py`, covering discovery, cart creation, checkout state machine progression, buyer confirmation gates, and webhook verification.
4. **Zero-Dependency Tooling:** Verified that all client and testing helpers rely strictly on standard library modules (`urllib`, `http.server`, `hashlib`, `hmac`, `base64`, `json`).
