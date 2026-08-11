---
name: evaluate-skill
description: >-
  Evaluates an existing Agent Skill's trigger accuracy, task performance,
  and security posture, then iteratively fixes it until it clears user-set
  (or default) thresholds. TRIGGER when the user asks to "evaluate a
  skill", "test a skill", "score/benchmark a skill", "check a skill's
  trigger precision/recall/false-positive rate", "security review a
  skill", "red team a skill", "run an eval suite" against a skill, or
  wants an existing skill's content audited against a production
  checklist, risk-tiered, or A/B tested. DO NOT TRIGGER for: authoring a
  brand-new skill from scratch with no existing skill to assess (use a
  skill-writing skill instead); evaluating general application code or
  tests unrelated to the Agent Skills format; generic ML/statistics
  questions about precision, recall, or false positives with no specific
  Agent Skill in view; or fixing a skill's file layout, folder structure,
  or word count with no metrics, testing, or security ask attached (use a
  skill-authoring skill instead).
version: 1.0.0
author: Actual Agentic Solutions
tags: [skill-evaluation, meta, agent-skills, security, testing]
license: Apache-2.0
compatibility: Claude Code, Claude Agent SDK
metadata:
  category: meta-skill
---

- Evaluate Skill

- Overview
Assesses a target Agent Skill (a `SKILL.md` plus its `scripts/`,
`references/`, `assets/`) against quantitative metrics, qualitative rubrics,
and a security risk tier, then patches the skill's own files and re-tests
until it clears its thresholds or plateaus. This skill evaluates *other*
skills — it does not author new ones from a blank goal.

- Prerequisites
- Path to the target skill's directory.
- Scope: full evaluation (performance + security) or a narrower request
  (e.g. "just security"). If unstated, run the full workflow — security is
  not optional by default, only by explicit request.
- Target thresholds, if the user has their own. If unspecified, use the
  defaults in `references/metrics.md` and say so explicitly.

- Workflow

- Step 1: Scope and read
Read the target skill's `SKILL.md` and *every* referenced file and script in
full before scoring anything — an unread file cannot be judged. Confirm scope
and thresholds per Prerequisites above.

- Step 2: Security review (default-on)
Run `scripts/security_scan.sh <target-skill-dir>` for the deterministic
pattern pass (network calls, high-privilege CLI use, path traversal,
hardcoded credentials), then work through the full 6-step order of
operations in `references/security_review.md` for what the scanner can't
judge — adversarial instructions in prose, and whether a flagged pattern is
actually reachable. Assign a risk tier from `references/security_review.md`.
- If **Critical**: stop. Report the finding immediately and do not proceed
  to Steps 3-8 until it's resolved — do not performance-tune a skill with an
  unresolved critical finding.
- If the user scoped this out ("just check performance"): skip to Step 3
  but note in the final report that security was not assessed.

- Step 3: Build or collect the eval suite
If the user supplies a suite, verify it has a roughly even split of
should-trigger / should-not-trigger prompts and specific, observable
assertions (`references/test_case_design.md`). Otherwise build a 20-50
prompt suite from `assets/eval_suite_template.json`, split roughly evenly.

- Step 4: Unit test the description
Run each prompt against the skill's routing only (not the full body) and
record `actual_trigger` per case, per `references/testing_strategies.md`.
Feed the graded results file to `scripts/score_eval_suite.py` to get Trigger
Precision, Trigger Recall, and False Positive Rate — don't hand-calculate.

- Step 5: Integration test the body
On a representative sample of should-trigger cases, run the full skill and
assert on both process (were the body's steps followed in order, were
anti-patterns respected?) and result correctness. Note Step Error Rate and
Reference Hit Rate along the way.

- Step 6: Score qualitative metrics and the checklist
Rate the 1-5 rubric dimensions in `references/metrics.md`, and work through
every box in `references/production_checklist.md`.

- Step 7: Compare against thresholds
If every quantitative target, qualitative bar, and checklist item passes,
skip to Step 9. Otherwise continue to Step 8.

- Step 8: Implement improvements, then regression test
Fix the target skill's actual files, matched to the failure:
- Failing trigger tests → revise the description using the A/B loop in
  `references/testing_strategies.md` (evaluate → identify → revise →
  repeat → select) — generalize, don't overfit to the specific failing
  prompt.
- Missing anti-patterns/error handling/output format → add them to the body.
- Token budget over ~5,000 → move content to `references/`, trim prose.
- Any security finding → fix before anything else, regardless of tier.
Re-run the **full** suite (Steps 4-7), not just the previously-failing
cases — a fix can silently break a case that was passing. Repeat until
thresholds are met or two consecutive iterations show no improvement. On a
plateau, stop and recommend deprecation per the evaluation lifecycle table
in `references/testing_strategies.md` instead of looping indefinitely.

- Step 9: Deliver the report
Fill out `assets/evaluation_report_template.md` with before/after metrics,
final risk tier, checklist status, and every fix applied.

- Examples

- Example 1: Full evaluation and improvement loop
Input: "Evaluate my k8s-pod-debugger skill and get it production ready."
Expected output / behavior: Steps 1-9 in full — security tier assigned,
20-50 prompt suite built or reused, description and body patched until the
checklist passes or plateaus, final report delivered.

- Example 2: Security-only scoped review
Input: "Just check this skill for security issues before I install it."
Expected output / behavior: Step 1 (scope narrowed to security) + Step 2 in
full; output the risk tier and findings list; Steps 3-9 skipped and noted
as not run.

- Error Handling
- Target skill directory has a broken reference pointer or missing script:
  do not score partially — flag as incomplete and stop rather than guessing
  at what the missing content would have said.
- One of *this* skill's own reference files (`references/*.md`,
  `scripts/*`, `assets/*`) is missing or unreadable: name the specific
  file, do not fabricate its contents from memory, and fall back to the
  quantitative targets and checklist duplicated in this repo's `CLAUDE.md`
  if present — otherwise pause and tell the user which reference is
  unavailable before continuing that step.
- User wants a "quick check" with fewer than 20 prompts: proceed, but state
  explicitly that precision/recall at that sample size is not statistically
  reliable.
- Improvement loop plateaus (no metric movement across two iterations):
  stop, report as a persistent failure, and recommend deprecation — don't
  keep iterating on a skill that isn't responding to fixes.
- Critical security finding at any point in the loop: halt immediately and
  report before continuing, even mid-iteration.
- Two skills conflict on the same trigger space (coexistence failure):
  report the conflict and ask whether to narrow or consolidate — don't
  silently pick a winner.

- Reference Files
- **scripts/security_scan.sh**: pattern-scans a skill directory for
  network calls, high-privilege CLI use, path traversal, and hardcoded
  credentials; suggests a starting risk tier. Run in Step 2.
- **scripts/score_eval_suite.py**: computes Trigger Precision, Recall,
  False Positive Rate, and assertion pass rate from a graded results JSON.
  Run in Step 4.
- **references/metrics.md**: quantitative metric targets and the
  qualitative 1-5 rubric — read in Steps 1 and 6.
- **references/test_case_design.md**: eval suite JSON schema and the
  good/bad assertion-writing guide — read in Step 3.
- **references/testing_strategies.md**: unit/integration/regression/red-
  team/A-B testing methodology and the evaluation lifecycle table — read in
  Steps 4, 5, and 8.
- **references/security_review.md**: risk tiers and the 6-step security
  order of operations — read in Step 2.
- **references/production_checklist.md**: the full Level 1-3 + validation +
  security checklist — read in Step 6.
- **assets/eval_suite_template.json**: starting file for a new eval suite —
  used in Step 3.
- **assets/evaluation_report_template.md**: final report structure — filled
  in during Step 9.

- Output Format
Return the filled-in evaluation report (from
`assets/evaluation_report_template.md`), the concrete edits applied to the
target skill's files during Step 8 (if any), and the final risk tier plus
pass/fail status against every measured threshold.
