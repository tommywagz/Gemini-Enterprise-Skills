# Evaluation Metrics

## Contents
- Quantitative metrics (targets)
- Qualitative metrics (rubric)

## Quantitative metrics

Measure these for every skill under evaluation. Defaults below are the
targets to use when the user hasn't set their own threshold — state that
you're using the default when you do.

| Metric | Description | Target |
|---|---|---|
| **Trigger Precision** | True positives / all activations | > 90% |
| **Trigger Recall** | True positives / all applicable scenarios | > 85% |
| **False Positive Rate** | Activations on irrelevant queries | < 5% |
| **Task Completion Rate** | End-to-end completions without user intervention | > 80% |
| **Step Error Rate** | Steps that fail, time out, or produce incorrect intermediates | Baseline |
| **Reference Hit Rate** | Level 3 script/asset invocations (vs. fallback to manual) | Baseline |
| **Token Usage** | Context consumed per activation | < 5,000 tokens |
| **Time to Completion** | Latency from activation to first actionable output | Baseline |

"Baseline" metrics have no fixed target — record the first measurement as the
baseline and track deltas across iterations/regressions instead of a
pass/fail threshold.

Trigger Precision, Recall, and False Positive Rate come from unit testing the
description (see `references/testing_strategies.md`); use
`scripts/score_eval_suite.py` to compute them from raw pass/fail results
instead of hand-calculating.

## Qualitative metrics

Score on a 1-5 rubric per dimension unless noted. These require human or
SME judgment — don't reduce them to the quantitative table.

- **Output Quality**: Does the output meet the standard an expert in the
  skill's domain would produce? Rate accuracy, completeness, clarity, and
  formatting separately — a skill can be accurate but poorly formatted, and
  averaging hides that.
- **Instruction Fidelity**: Did the agent follow the body's steps in the
  right order? Did it respect stated anti-patterns and error handling? This
  is a process check, independent of whether the final output happened to be
  correct.
- **Edge Case Handling**: Does the skill fail gracefully on unexpected
  inputs and communicate its own limits, rather than guessing silently or
  hallucinating a confident-sounding wrong answer?
- **Coexistence**: Does it conflict with other skills in the registry —
  overlapping triggers, contradictory instructions, or ambiguous ownership
  of the same task?
- **User Trust**: Would a domain expert (e.g. an on-call engineer) trust
  this output without verifying it? Gather this via periodic blind user
  studies, not self-assessment.
- **Domain Expert Review**: Have relevant subject-matter experts reviewed
  both the skill body and a sample of its outputs?
