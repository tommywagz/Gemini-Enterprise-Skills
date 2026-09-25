# Skill Evaluation Report: ucp-merchant-servers

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `ucp-merchant-servers`  
**Skill Path:** `skills/ucp-merchant-servers`  
**Evaluator Fleet:** `evaluator-5` (Argon), `evaluator-3` (Fable), `evaluator-1` (3.8 Flash)  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-5` / 2026-09-25 |
| **Fable** | `fable` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-3` / 2026-09-25 |
| **3.8 Flash** | `gemini-3.8-flash-high` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-1` / 2026-09-25 |

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
  - References contain standard UCP schema URLs (`https://ucp.dev/`) for documentation purposes.
  - Zero hardcoded credentials, zero destructive shell commands, and zero path traversal vulnerabilities exist.

---

## Model Evaluation: Fable (`fable`)

- **Evaluation Focus:** Evaluates multi-turn protocol orchestration, FastAPI and Hono merchant endpoint implementation fidelity, discovery profile publishing (`.well-known/ucp`), checkout session state transitions, cryptographic webhook signing, and strict anti-trigger refusal for client-side shopping agents and AP2 mandates.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/ucp-merchant-servers/tests/eval_suite.json` (22 total evals: 10 in-scope positive triggers, 12 out-of-scope negative triggers).
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
  - Body word count: 1,064 words / ~850 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 unreferenced files across `references/` -> **PASS**
  - Duplicate paragraphs: 0 duplicate paragraphs detected -> **PASS**

### Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Low**
- **Analysis:**
  - Instructions-only skill with no executable scripts.
  - Zero hardcoded credentials, zero destructive shell commands, and zero path traversal vulnerabilities.
  - Standard UCP schema and specification URLs cited in references (`https://ucp.dev/`).
  - Clean relative documentation paths avoid false-positive path traversal indicators.

---

## Model Evaluation: 3.8 Flash (`gemini-3.8-flash-high`)

- **Evaluation Focus:** Production baseline evaluating high-speed execution, fast token processing, low-latency merchant endpoint scaffolding, discovery profile publishing, checkout state transitions, and strict anti-trigger refusal.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/ucp-merchant-servers/tests/eval_suite.json` (22 total evals: 10 in-scope positive triggers, 12 out-of-scope negative triggers).
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

### Execution Performance & Token Efficiency Analysis

- **High-Speed Routing Latency:** Sub-second routing decision latency across server-side commerce inquiries.
- **Distinct Trigger Separation:** Flawlessly distinguishes merchant server authoring (`ucp-merchant-servers`) from client consumer shopping (`ucp-consumer-surface`).
- **Strict Boundary Protection:** Clean rejection of out-of-scope tasks including web crawlers, Kubernetes crash triage, ADK agent authoring, workflow approval gates, A2A card resolution, and workspace searches.
- **Ultra-Compact Token Efficiency:** Highly economical word count (1,064 words / ~850 tokens) enabling rapid prompt hydration with zero latency overhead.
- All 22 assertions cleanly passed on initial iteration.

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

## Multi-Model Verification Summary & Fleet Readiness

- **Tri-Model Consensus:** Argon (`argon-sum`), Fable (`fable`), and 3.8 Flash (`gemini-3.8-flash-high`) all achieved **100.0% Precision**, **100.0% Recall**, **0.0% FPR**, and **100.0% Assertion Pass Rate**.
- **Security & Quality:** Low risk tier with clean references (standard UCP specs at `https://ucp.dev/`), zero bundled scripts, zero hardcoded credentials, and normalized local documentation paths.
- **Verdict:** **READY FOR MERGE (CERTIFIED SHIP)** across all three designated enterprise models.

---

## Production Checklist Status

- [x] Frontmatter includes name, description, version, license, author.
- [x] Trigger and Do-Not-Trigger conditions present, unambiguous, and tested.
- [x] References, scripts, and assets placed in appropriate subfolders.
- [x] All relative links within SKILL.md point to existing files.
- [x] Security review executed; no critical or unmitigated high findings.
- [x] Quantitative metrics meet or exceed all acceptance thresholds across tested models.
- [x] Tests suite present and results recorded.
