---
name: evaluate-skill
description: >-
  Evaluates an existing Agent Skill for routing accuracy, task performance, or
  security. TRIGGER for "evaluate/test/benchmark a skill", trigger
  precision/recall, red-team/security review, or an eval suite. DO NOT TRIGGER
  for authoring a new skill, general application tests, or generic statistics.
version: 1.1.0
author: Actual Agentic Solutions
tags: [skill-evaluation, meta, agent-skills, security, testing]
license: Apache-2.0
compatibility: Claude Code, Claude Agent SDK
metadata:
  category: meta-skill
---

# Evaluate Skill

Evaluate a skill, improve it when authorized, and stop when the evidence says
it is safe to stop. This evaluates existing skill packages; it does not create
one from a blank goal.

## Inputs

- Target skill directory and requested scope. Default to full evaluation;
  security may be excluded only explicitly.
- User thresholds, if supplied. Otherwise use `references/metrics.md`.

## Workflow

1. Inventory the target `SKILL.md` and every file it references. Stop if a
   target reference or script is missing; do not score an incomplete package.
2. Unless explicitly excluded, run
   `scripts/security_scan.sh <target-skill-dir>`, then read
   `references/security_review.md` to assign the final tier.
   - Critical finding: report and halt before performance work.
   - Performance-only scope: record that security was not assessed.
3. Build or validate the evaluation suite. Read
   `references/test_case_design.md` when designing or validating cases; use
   `assets/eval_suite_template.json` when no suite is supplied. Use 20–50
   roughly balanced trigger/non-trigger cases unless the user requests a
   smaller, explicitly non-representative check.
4. Test routing and score the graded results with
   `scripts/score_eval_suite.py`. Read `references/testing_strategies.md` for
   routing, integration, regression, red-team, or A/B methodology as each is
   performed.
5. Run representative full-skill cases and score qualitative criteria. Read
   `references/metrics.md` for definitions and
   `references/production_checklist.md` for the final checklist.
6. Compare results with thresholds. If all pass, deliver the report.
7. If changes are requested or evaluation includes remediation, fix the target
   files in this order: security, routing, missing safety/output requirements,
   then token efficiency. Re-run the full relevant suite after every change.
   Stop after two consecutive non-improving iterations and recommend
   deprecation rather than looping indefinitely.
8. Fill `assets/evaluation_report_template.md` with scope, before/after
   results, risk tier, fixes, and any excluded checks.

| Condition | Action | Continue? |
| --- | --- | --- |
| Critical security finding | Report immediately. | No |
| Broken target reference | Mark incomplete. | No |
| Fewer than 20 cases | Run if requested; mark metrics unreliable. | Yes |
| Two non-improving iterations | Report plateau and deprecation recommendation. | No |
| Trigger-space conflict | Explain it and ask whether to narrow or consolidate. | No |

## Compact cases

- Full evaluation with clean security → score routing and integration → remediate
  only failing criteria → report before/after results.
- Critical scanner finding → assign and report the risk → stop before tuning.

## Resources

- `scripts/security_scan.sh`: deterministic security pass (step 2).
- `scripts/score_eval_suite.py`: routing metrics (step 4).
- `references/security_review.md`: security order and risk tiers (step 2).
- `references/test_case_design.md`: suite schema and assertions (step 3).
- `references/testing_strategies.md`: test and remediation methods (step 4).
- `references/metrics.md`: targets and qualitative rubric (steps 1, 5–6).
- `references/production_checklist.md`: release checklist (step 5).

## Output

Return the completed evaluation report, all target-file edits, final risk tier,
and pass/fail status for each measured threshold.
