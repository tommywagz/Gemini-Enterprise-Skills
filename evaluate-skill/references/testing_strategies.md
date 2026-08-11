# Testing Strategies

## Contents
- Unit testing (description)
- Integration testing (body)
- Regression testing
- Red team testing
- A/B testing and the description optimization loop
- Evaluation lifecycle (signal → action)

## Unit testing — description

Tests whether the agent knows *when* to call the skill, based on its
description alone — not whether the skill's content is good. Build a 20-50
prompt suite (see `references/test_case_design.md`), split roughly evenly
between prompts that should trigger and prompts that should not, and run
each against the skill's routing. Example result table:

| Test ID | Input | Expected | Result |
|---|---|---|---|
| T001 | "Pod stuck in CrashLoopBackOff on prod cluster" | TRIGGER | PASS |
| T002 | "How do I write a Helm chart?" | NO TRIGGER | PASS |
| T003 | "ECS task failing to start on Fargate" | NO TRIGGER | PASS |
| T004 | "kubectl describe shows ImagePullBackOff" | TRIGGER | PASS |
| T005 | "Pod OOMKilled, memory limit 256Mi" | TRIGGER | PASS |
| T006 | "Terraform plan fails for EKS module" | NO TRIGGER | FAIL ← fix description |

Feed the raw pass/fail results into `scripts/score_eval_suite.py` to get
Trigger Precision, Recall, and False Positive Rate.

## Integration testing — body

End-to-end scenarios with known inputs and expected outputs, run against the
full skill (description + body + bundled files). Assert on both:
- **Process**: were the steps from the skill body actually followed, in
  order, respecting stated anti-patterns?
- **Result**: is the final output correct?

These are more token-heavy than unit tests — size the sample down for
expensive/long-running skills rather than dropping process assertions.

## Regression testing

Re-run the *full* test suite every time a skill is updated, not just the
cases related to the change. Descriptions in particular are sensitive to
small wording changes — a fix for one false positive can silently introduce
another.

## Red team testing

Craft adversarial prompts with ambiguous or conflicting phrasing designed to
trigger a different-but-similar skill, or no skill at all, when this skill
should NOT fire. The assertion under test is always "this skill does NOT
activate" — treat an unwanted activation here the same as a security finding,
not just a precision miss.

## A/B testing and the description optimization loop

Run two description variants for the same skill in parallel; compare
precision, recall, and downstream task completion rate. Use this loop to
converge on a description without overfitting to the test set:

1. **Evaluate** — current description on train + validation sets.
2. **Identify** — failures in the train set.
3. **Revise** — generalize the description; do not overfit to the specific
   failing prompts.
4. **Repeat** — until the train set passes or improvement plateaus.
5. **Select** — the best iteration by validation pass rate (not train pass
   rate — that's the set you were fitting to).

## Evaluation lifecycle

Ongoing signals that should trigger a specific corrective action, not just a
note for later:

| Signal | Action |
|---|---|
| Declining trigger accuracy | Update description or add anti-triggers |
| Coexistence conflicts with another skill | Consolidate or narrow descriptions |
| Consistently low output quality | Rewrite instructions or add validation steps |
| Token usage creeping past 5,000 | Move content to `references/`, trim prose |
| Persistent failures across multiple updates | Deprecate the skill |
