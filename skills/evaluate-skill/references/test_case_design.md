# Designing Test Cases & Assertions

## Contents
- Eval suite JSON schema
- Worked example
- Writing effective assertions (good vs. bad)

## Eval suite JSON schema

Each eval suite is a JSON file with one entry per test case. Use
`assets/eval_suite_template.json` as the starting file — copy it, then fill
in `prompt`, `should_trigger`/`expected_output`, and `assertions` for the
skill under test.

```json
{
  "skill_name": "k8s-pod-debugger",
  "evals": [
    {
      "id": 1,
      "prompt": "My pod api-server-7d9f8b-xk2p is stuck in CrashLoopBackOff in the production namespace. How do I fix it?",
      "expected_output": "Systematic diagnosis starting from kubectl logs --previous, checking exit code, then proposing a targeted fix.",
      "assertions": [
        "Agent runs 'kubectl logs ... --previous' or equivalent first",
        "Agent checks the exit code from 'kubectl describe pod'",
        "Agent does NOT recommend deleting and recreating the pod as a first step",
        "Agent provides the exact kubectl command to apply any proposed fix"
      ]
    },
    {
      "id": 2,
      "prompt": "How do I write a Helm chart for my Flask app?",
      "should_trigger": false,
      "assertions": [
        "k8s-pod-debugger skill does NOT activate",
        "Agent handles with general knowledge or a helm-specific skill"
      ]
    },
    {
      "id": 3,
      "prompt": "Pod is OOMKilled every 5 minutes, memory limit is 256Mi",
      "should_trigger": true,
      "assertions": [
        "Agent runs kubectl top pod to check actual memory usage",
        "Agent shows the current resources.limits.memory value",
        "Agent recommends increasing the limit with a specific value",
        "Agent does NOT recommend removing limits"
      ]
    }
  ]
}
```

Build 20-50 prompts per suite, roughly half that should trigger the skill and
half that should not — fewer than 20 makes precision/recall statistically
unreliable. After running each prompt against the skill, record
`actual_trigger` and a `passed` boolean per assertion (see
`scripts/score_eval_suite.py` for the exact results-file shape it expects)
before scoring.

## Writing effective assertions

**Good** — specific, observable, countable:
- "Agent runs `kubectl logs --previous` before recommending any fix" —
  specific and observable.
- "Agent checks exit code before proposing a solution" — process-level
  assertion, not just an output check.
- "The response includes at least one kubectl command the user can
  copy-paste" — countable.

**Bad** — ungradeable or too fragile:
- "The output is helpful" — too vague to grade consistently between graders.
- "The output uses exactly the phrase 'Exit code: 137'" — too brittle; a
  correct answer phrased differently would fail for the wrong reason.

Rule of thumb: an assertion should be answerable with yes/no by someone who
did not write the skill, just by reading the transcript.
