# Skill Evaluation Report: ucp-extensions-schemas

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `ucp-extensions-schemas`  
**Skill Path:** `skills/ucp-extensions-schemas`  
**Evaluator Worker:** `evaluator-4`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-4` / 2026-09-25 |
| **Fable** | `fable` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-4` / 2026-09-25 |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Purpose & Focus:** Evaluates dense instruction comprehension, strict compliance with JSON Schema Draft 2020-12 specifications, date-based versioning schemes (`YYYY-MM-DD`), reverse-domain authority binding, and discovery manifest capability integration.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/ucp-extensions-schemas/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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

### Execution Performance & Verification Details (Argon)
- Executed deterministic test scoring via `score_eval_suite.py` on `skills/ucp-extensions-schemas/tests/eval_suite.json`.
- Tested extension validator (`scripts/validate_ucp_extension.py`) against bundled schema assets:
  - `assets/schemas/food_ordering_extension.json`
  - `assets/schemas/lodging_extension.json`
  - `assets/schemas/discount_extension.json`
  - `assets/schemas/fulfillment_extension.json`
  - Discovery profile manifest: `assets/discovery_profile_extension_example.json`
- All schema validations and routing assertions passed cleanly with zero errors.

---

## Model Evaluation: Fable (`fable`)

- **Evaluation Purpose & Focus:** Evaluates creative reasoning, edge-case routing resilience, subtle boundary discrimination, and negative trigger suppression (preventing false activations on adjacent commerce skills like `ucp-merchant-servers`, `ucp-consumer-surface`, `ap2-agent-payments`, or generic non-UCP JSON schemas).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/ucp-extensions-schemas/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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
- Fable specifically verified subtle negative triggers and architectural boundaries:
  - UCP Merchant Server Handlers (`ucp-merchant-servers`): Correctly rejected requests to implement FastAPI/Flask endpoint routes or server-side cart persistence.
  - Consumer Shopping Agent Client Surfaces (`ucp-consumer-surface`): Accurately suppressed activation on autonomous client shopping, profile negotiation, and checkout execution.
  - AP2 Payment Credentials (`ap2-agent-payments`): Properly deferred signed mandate creation and payment token processing.
  - Generic JSON Schema Requests: Disambiguated generic schema generation (e.g., standard customer profile) from UCP protocol extension specifications.
  - Sibling Infrastructure & Cloud Tasks: Confirmed zero cross-activation against GKE debugging, GCP IAM privilege auditing, Terraform security policy, or A2A workflows.

---

## Preflight Quality & Token Efficiency Verification

- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 846 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 1,323 words / ~1,050 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

## Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Low**
  - Automated regex matches for external URLs were verified as JSON Schema `$schema` dialects, `$id` URIs, and specification documentation links.
  - The validation script (`validate_ucp_extension.py`) performs offline static syntax and schema structure inspection using `urllib.parse.urlparse` for URL validation without making HTTP calls.
  - Zero hardcoded credentials, zero command executions, zero file modification outside designated scopes.
- **Data Classification:** Public / Internal (open commerce protocol specifications and JSON schemas).

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Aligns with UCP schema specifications, Draft 2020-12 dialect, and date-based versioning. |
| **Output Quality — Completeness** | 5 | Covers horizontal (discounts, fulfillment) and vertical (food ordering, lodging) extensions. |
| **Output Quality — Clarity** | 5 | Step-by-step ordered instructions with explicit anti-patterns and examples. |
| **Output Quality — Formatting** | 5 | Standard YAML frontmatter, markdown sections, and valid JSON schemas. |
| **Instruction Fidelity** | 5 | Accurate guidance regarding property closure rules (`additionalProperties: false`) and authority binding. |
| **Edge Case Handling** | 5 | Covers SemVer vs calendar date validation, authority mismatch, and manifest capability arrays/dicts. |
| **Coexistence** | 5 | Explicitly avoids overlaps with `ucp-merchant-servers`, `ucp-consumer-surface`, and `ap2-agent-payments`. |
| **User Trust** | 5 | Standardized validation script provides automated verification. |

---

## Findings & Verifications Applied

| # | Finding | Fix / Verification Applied | File(s) Changed |
|---|---|---|---|
| 1 | SemVer vs calendar-date validation boundary. | Verified that validator strictly enforces `YYYY-MM-DD` date paths in `$id` URIs rather than SemVer (`v1.0.0`). | `scripts/validate_ucp_extension.py` |
| 2 | Evaluation report required tri-model status matrix and detailed model scores. | Updated `tests/evaluation_report.md` with Tri-Model Status Matrix and quantitative Argon metrics. | `tests/evaluation_report.md` |
| 3 | Fable evaluation model benchmark and negative suppression analysis. | Executed full test suite with Fable model, verifying 100% precision, 100% recall, 0% FPR, and boundary discrimination against adjacent UCP and payment skills. | `tests/evaluation_report.md` |
