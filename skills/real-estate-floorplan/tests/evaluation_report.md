# Skill Evaluation Report: real-estate-floorplan

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `real-estate-floorplan`  
**Skill Path:** `skills/real-estate-floorplan`  
**Evaluator Fleet:** `evaluator-4` (Argon) & `evaluator-1` (Fable) [3.8 Flash PENDING]  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | High | `evaluator-4` / 2026-09-25 |
| **Fable** | `fable` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | High | `evaluator-1` / 2026-09-25 |
| **3.8 Flash** | `gemini-3.8-flash-high` | **PENDING** | — | — | — | — | — | PENDING |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Focus:** Evaluates dense technical instruction comprehension, multi-stage floor plan pipeline routing, Stage 1 listing discovery (Zillow, Redfin, Apartments.com MCPs), spatial data normalization, Stage 2 CAD/BIM procedural synthesis, and geometric closure validation.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/real-estate-floorplan/tests/eval_suite.json` (20 evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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
  - Description length: 821 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 630 words / ~500 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 unreferenced files in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicate paragraphs detected -> **PASS**

### Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **High**
- **Data Classification:** **Internal / Operational Real Estate CAD Data**
- **Analysis:**
  - Uses bundled local Python tools `normalize_listing_spatial_data.py` and `validate_geometric_closure.py` which rely strictly on standard library modules (`argparse`, `json`, `re`, `sys`, `math`).
  - Zero network calls initiated by local scripts; schema URLs in asset schemas serve solely as metadata validators.
  - Zero hardcoded credentials, zero destructive CLI commands, zero path traversal vulnerabilities.
  - Pattern scanner flagged CAD geometry operations (`add_polyline`, `add_dimension`) and standard JSON schema URLs, properly verified as non-destructive modeling instructions.

---

## Model Evaluation: Fable (`fable`)

- **Evaluation Focus:** Evaluates creative reasoning, edge-case routing resilience, subtle architectural boundary discrimination, and negative trigger suppression (preventing false activations on adjacent real estate finance, general home improvement, mechanical engineering CAD, or video game design).
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/real-estate-floorplan/tests/eval_suite.json` (20 evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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

### Boundary Discrimination & Negative Trigger Suppression Analysis

Fable verified subtle edge cases and non-floorplan real estate / CAD boundaries:
- **Financial & Market Valuation Requests:** Inquiries regarding property valuation, market price estimates, or monthly mortgage loan calculations correctly suppressed without invoking floor plan tools.
- **Generic Home Improvement & Landscaping:** General backyard landscaping and renovation design advice properly rejected as out of scope.
- **Mechanical & Non-Architectural CAD:** Requests for 3D mechanical engine pistons or AutoCAD mechanical gear schematics correctly suppressed in favor of generic CAD tools.
- **3D Video Game Level Modeling:** Arena shooter and video game map layout queries cleanly suppressed.
- **Real Estate Transaction Database / Legal Queries:** Rental lease agreements and property transaction database schema design correctly rejected.
- **Architectural Guidelines & Egress Compliance:** Accurately routes floor plan spec JSON validation to `validate_geometric_closure.py` to check closed loops, portal door swings, and egress clear widths (flagging corridors < 2.6 ft).

---

## Script Verification and Testing

Both bundled scripts were executed and validated:
1. `normalize_listing_spatial_data.py`:
   - Successfully parses free-text room dimension variations (e.g., `"14x16"`, `"14' 6\" x 10' 0\""`, `"18 ft. x 15 ft."`).
   - Lays out rooms on 2D coordinate grid, populates doors/windows, places fixture anchors, and produces valid JSON conforming to `assets/floorplan_spec_schema.json`.
2. `validate_geometric_closure.py`:
   - Calculates room polygon areas with high precision using the Shoelace formula.
   - Evaluates closed loop boundaries, validates wall collinearity within 0.05-ft tolerance, and verifies doorway egress widths.

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Adheres to AIA CAD Layer Guidelines (A-WALL, A-DOOR, A-GLAZ, A-FLOR-FIXT, A-ANNO-DIMS) and validates polygon geometry. |
| **Output Quality — Completeness** | 5 | Fully articulates the two-stage pipeline: listing discovery & extraction, followed by vector CAD synthesis. |
| **Output Quality — Clarity** | 5 | Comprehensive ASCII workflow diagrams, explicit schema structures, and deterministic CLI invocations. |
| **Output Quality — Formatting** | 5 | Standard frontmatter specification, clean table layouts, and structured JSON schemas. |
| **Instruction Fidelity** | 5 | Strictly respects tool call boundaries across Zillow, Redfin, Apartments.com, Floor Builder, and CAD MCP servers. |
| **Edge Case Handling** | 5 | Robustly accommodates missing media, freeform dimension strings, non-rectangular rooms, and wall-portal snapping. |
| **Coexistence** | 5 | Distinct trigger boundaries. Explicit DO NOT TRIGGER for property valuation, mortgage calculation, game level layouts, and mechanical CAD. |
| **User Trust** | 5 | Enforces rigorous verification of closed loops and square footage variances before finalizing vector exports. |

---

## Production Checklist Status

- [x] Frontmatter includes name, description, version, license, author.
- [x] Trigger and Do-Not-Trigger conditions present, unambiguous, and tested.
- [x] References, scripts, and assets placed in appropriate subfolders.
- [x] All relative links within SKILL.md point to existing files.
- [x] Security review executed; no critical or unmitigated high findings.
- [x] Quantitative metrics meet or exceed all acceptance thresholds across tested models.
- [x] Tests suite present and results recorded.
