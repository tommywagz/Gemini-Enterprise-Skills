# Skill Evaluation Report: real-estate-floorplan

**Evaluation Workflow:** `evaluate-skill`  
**Target Skill:** `real-estate-floorplan`  
**Skill Path:** `skills/real-estate-floorplan`  
**Evaluator Worker:** `evaluator-4`  
**Date:** 2026-09-25  

---

## Tri-Model Evaluation Status Matrix

| Model Display Name | Model Identifier | Evaluation Status | Trigger Precision | Trigger Recall | False Positive Rate | Assertion Pass Rate | Risk Tier | Evaluator / Date |
|---|---|---|---|---|---|---|---|---|
| **Argon** | `argon-sum` | **COMPLETED** | 100.0% | 100.0% | 0.0% | 100.0% | Low | `evaluator-4` / 2026-09-25 |
| **Fable** | `fable` | PENDING | — | — | — | — | — | — |
| **3.8 Flash** | `gemini-3.8-flash-high` | PENDING | — | — | — | — | — | — |

---

## Model Evaluation: Argon (`argon-sum`)

- **Evaluation Purpose & Focus:** Evaluates dense instruction comprehension, strict compliance with spatial geometry schemas, CAD layer conventions (AIA CLG standards), room polygon closure calculations, and portal validation.
- **Execution Workflow:** Native `evaluate-skill` test-adjust-retest harness.
- **Test Suite:** `skills/real-estate-floorplan/tests/eval_suite.json` (20 total evals: 10 in-scope positive triggers, 10 out-of-scope negative triggers).
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
- Executed deterministic test scoring via `score_eval_suite.py` on `skills/real-estate-floorplan/tests/eval_suite.json`.
- Tested bundled spatial utilities:
  - `normalize_listing_spatial_data.py`: parses free-text room dimension formats, lays out rooms in 2D coordinate space conforming to `floorplan_spec_schema.json`.
  - `validate_geometric_closure.py`: validates Shoelace polygon area, verifies closed wall loops, and checks door/window portal positioning tolerances.
- All 20 assertion conditions passed with zero degradations.

---

## Preflight Quality & Token Efficiency Verification

- **Linter Tool:** `scripts/validate_skill_token_efficiency.py`
  - Description length: 821 characters (limit: 1024 characters) -> **PASS**
  - Body word count: 630 words / ~500 tokens (limit: 6250 words / ~5000 tokens) -> **PASS**
  - Unreferenced resources: 0 found in `references/`, `scripts/`, or `assets/` -> **PASS**
  - Duplicate paragraphs: 0 duplicates detected against reference documents -> **PASS**

## Security Review

- **Scanner Tool:** `skills/evaluate-skill/scripts/security_scan.sh`
- **Assigned Risk Tier:** **Low**
  - Uses remote MCP servers (`zillow-mcp-server`, `apartments-mcp-server`, `floor-builder-mcp-server`) for data querying and CAD rendering.
  - Bundled Python utilities rely strictly on Python standard library modules (`argparse`, `json`, `re`, `sys`) with no network access, file writing, or subprocess execution.
  - Zero hardcoded credentials, zero path traversals.
- **Data Classification:** Public / Internal (real estate listing data and geometric layout specifications).

---

## Qualitative Assessment (1-5 Rubric)

| Dimension | Score | Evaluation Notes |
|---|---|---|
| **Output Quality — Accuracy** | 5 | Accurately models real-estate listings platforms and CAD mapping standard (AIA CLG Guidelines). |
| **Output Quality — Completeness** | 5 | Detailed step-by-step description of scraping, normalization, validation, and CAD generation pipelines. |
| **Output Quality — Clarity** | 5 | Clear structure with explicit call orders, prerequisite lists, and schema references. |
| **Output Quality — Formatting** | 5 | Conforms strictly to standard skill frontmatter specification. |
| **Instruction Fidelity** | 5 | Covers Zillow, Apartments.com, Redfin, Floor Builder, and CAD MCP servers correctly. |
| **Edge Case Handling** | 5 | Outlines handling for non-rectangular rooms, micro-gaps, door swings, and missing floor plan media. |
| **Coexistence** | 5 | Explicit DO NOT TRIGGER boundaries for property price valuation, mortgage calculations, 3D video game level design, or mechanical CAD. |
| **User Trust** | 5 | Clearly specifies verification of closed loops and square footage tolerances before exporting CAD artifacts. |

---

## Findings & Verifications Applied

| # | Finding | Fix / Verification Applied | File(s) Changed |
|---|---|---|---|
| 1 | Free-text room dimension variations. | Verified normalization logic handles diverse dimension strings ("14x16", "14' 6\" x 10' 0\"", etc.) into numeric coordinates. | `scripts/normalize_listing_spatial_data.py` |
| 2 | Evaluation report required tri-model status matrix and detailed model scores. | Updated `tests/evaluation_report.md` with Tri-Model Status Matrix and quantitative Argon metrics. | `tests/evaluation_report.md` |
