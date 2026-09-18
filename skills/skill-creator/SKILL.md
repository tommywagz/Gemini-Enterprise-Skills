---
name: skill-creator
description: >-
  Native Antigravity, Jetski, and Gemini CLI skill for authoring, revising, testing,
  and evaluating production-grade Agent Skills. TRIGGER when users ask to "create a skill",
  "revise a skill", "test and evaluate skill", "run skill-creator", "improve skill robustness",
  "score trigger precision and recall", "audit skill security", or execute an automated
  test-adjust-retest cycle on skill packages. DO NOT TRIGGER for generic application code
  unrelated to Agent Skills, writing general documentation (e.g. non-skill READMEs), or
  running regular application test suites (e.g. pytest on service business logic).
version: 1.0.0
author: Actual Agentic Solutions
tags: [skill-creator, meta, jetski, antigravity, gemini-cli, evaluation, testing]
license: Apache-2.0
compatibility: Antigravity, Jetski, Gemini CLI, Claude Code, Google ADK
metadata:
  category: meta-skill
---

# Skill Creator

## Overview
Skill Creator is the unified engineering engine for authoring, evaluating, and refining Agent Skills within Antigravity, Jetski, and Gemini CLI environments. It guides agents through a rigorous, test-driven revision loop: assessing trigger accuracy, enforcing token-efficiency boundaries, scanning for security vulnerabilities, and iteratively adjusting prompts and code until all quality thresholds are satisfied.

---

## Prerequisites
- Path to target skill folder (`skills/<name>/`).
- Active execution runtime: Python >= 3.10, `bash`, and standard CLI utilities.
- Access to bundled validator scripts and rubric references.

---

## The Test-Adjust-Retest Loop

```
  +------------------+      +-------------------+      +------------------+
  | 1. Scan & Audit  | ===> | 2. Score Triggers | ===> | 3. Remediate &   |
  | (Security & Lints|      | & Assertions      |      |    Refine Files  |
  +------------------+      +-------------------+      +--------+---------+
            ^                                                   |
            |                 (Iterate up to 3x)                |
            +---------------------------------------------------+
                                    | (Passed thresholds)
                                    v
                            +-------------------+
                            | 4. Verification & |
                            |    Report Output  |
                            +-------------------+
```

---

## Workflow Steps

### Step 1: Preflight Audit & Token-Efficiency Check
Execute deterministic static checks before touching any instructions:
1. Run the token-efficiency linter:
   ```bash
   python3 scripts/validate_skill_token_efficiency.py
   ```
   Verify that YAML description is under 1024 characters, body word count is under 6,250 words, all files in `references/`, `scripts/`, and `assets/` are cited, and no duplicate paragraphs exist.
2. Review frontmatter schema and formatting rules in `references/formatter_fields.md`.
3. Review instruction layout and freedom levels in `references/writing_principles.md`.

### Step 2: Deterministic Security Scan
Run the automated security pattern scan:
```bash
bash scripts/security_scan.sh <target-skill-path>
```
Consult `references/security_review.md` to classify findings into risk tiers (Low, Medium, High, Critical). If a Critical finding is detected (such as unsanitized credential exposure or arbitrary command execution), halt and resolve immediately before conducting further evaluation.

### Step 3: Run Evaluation Suite & Compute Metrics
Execute the evaluation suite using the scoring runner:
```bash
python3 scripts/score_eval_suite.py <target-skill-path>/tests/eval_suite.json
```
If `tests/eval_suite.json` does not exist or has fewer than 20 cases, construct a balanced suite modeled on `assets/eval_suite_template.json` following test design guidelines in `references/testing_strategies.md`. Ensure at least 10 positive trigger cases and 10 adjacent negative cases.

Compare quantitative outputs against target thresholds in `references/metrics.md`:
- **Trigger Precision:** >= 0.90
- **Trigger Recall:** >= 0.85
- **False Positive Rate:** <= 0.05
- **Assertion Pass Rate:** 1.0 (100%)

### Step 4: Remediate & Refine
If any threshold fails:
1. **Trigger Routing Failures:** Revise `description` in YAML frontmatter using the A/B testing loop from `references/testing_strategies.md`. Add crisp boundaries and explicit `DO NOT TRIGGER` clauses.
2. **Missing Anti-Patterns / Gotchas:** Enhance the markdown body with concrete error handling and edge-case handling.
3. **Dead Resource Warnings:** Cite any orphan files in `references/`, `scripts/`, or `assets/`, or remove them if unneeded. Starter skeletons can be referenced from `assets/skill_template.md`.
4. **Token Bloat:** Offload reference tables or exhaustive examples from `SKILL.md` into markdown files under `references/`.

### Step 5: Retest & Audit Against Production Checklist
Re-run Steps 1, 2, and 3 across the entire suite. Never evaluate only failing cases; verify that no regression was introduced. Continue loop for up to 3 passes. When metrics clear all thresholds, audit the skill against `references/production_checklist.md`.

### Step 6: Generate Evaluation Report
Compile the final results using `assets/evaluation_report_template.md` and save as `<target-skill-path>/tests/evaluation_report.md`. Record before/after confusion matrices, risk tier, and all file patches applied.

---

## Resource Catalog

| Path | Type | Role |
|---|---|---|
| `scripts/validate_skill_token_efficiency.py` | Tool | Verifies character limits, word budget, and dead references |
| `scripts/security_scan.sh` | Tool | Scans scripts and prose for high-privilege commands and credentials |
| `scripts/score_eval_suite.py` | Tool | Computes precision, recall, FPR, and assertion pass rates |
| `references/metrics.md` | Doc | Quantitative targets and qualitative 1-5 scoring rubrics |
| `references/security_review.md` | Doc | Risk tier definitions and security review protocol |
| `references/testing_strategies.md` | Doc | Unit, integration, regression, and A/B description methodology |
| `references/production_checklist.md` | Doc | Comprehensive release readiness checklist |
| `references/writing_principles.md` | Doc | Structural organization and freedom-level guidelines |
| `references/formatter_fields.md` | Doc | Frontmatter specification and routing description rules |
| `assets/eval_suite_template.json` | Template | Seed template for creating 20-50 case evaluation suites |
| `assets/evaluation_report_template.md` | Template | Standard schema for final evaluation reports |
| `assets/skill_template.md` | Template | Scaffold skeleton for new skill definitions |
