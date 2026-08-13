#!/usr/bin/env python3
"""Score a graded eval suite: trigger precision/recall/FPR and assertion pass rate.

Usage: score_eval_suite.py <results.json>

Input schema (start from assets/eval_suite_template.json, then add
'actual_trigger' and 'passed' after running each prompt against the skill):
{
  "skill_name": "...",
  "evals": [
    {
      "id": 1,
      "prompt": "...",
      "should_trigger": true,        # optional, defaults to true
      "actual_trigger": true,        # required: did the skill actually activate?
      "assertions": [
        {"text": "...", "passed": true}
      ]
    }
  ]
}
"""
import json
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: score_eval_suite.py <results.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    evals = data.get("evals", [])
    if not evals:
        print("Error: no evals found in input file", file=sys.stderr)
        sys.exit(1)

    tp = fp = tn = fn = 0
    total_assertions = 0
    passed_assertions = 0
    ungraded_ids = []

    for e in evals:
        should_trigger = e.get("should_trigger", True)
        if "actual_trigger" not in e:
            ungraded_ids.append(e.get("id"))
            continue
        actual_trigger = e["actual_trigger"]

        if should_trigger and actual_trigger:
            tp += 1
        elif should_trigger and not actual_trigger:
            fn += 1
        elif not should_trigger and actual_trigger:
            fp += 1
        else:
            tn += 1

        for a in e.get("assertions", []):
            if isinstance(a, dict) and "passed" in a:
                total_assertions += 1
                if a["passed"]:
                    passed_assertions += 1

    if ungraded_ids:
        print(
            f"Warning: {len(ungraded_ids)} eval(s) missing 'actual_trigger', "
            f"skipped: {ungraded_ids}",
            file=sys.stderr,
        )

    graded = tp + fp + tn + fn
    if graded == 0:
        print("Error: no graded evals (all missing 'actual_trigger')", file=sys.stderr)
        sys.exit(1)

    def safe_div(n, d):
        return round(n / d, 4) if d else None

    result = {
        "skill_name": data.get("skill_name", "unknown"),
        "graded_evals": graded,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "trigger_precision": safe_div(tp, tp + fp),
        "trigger_recall": safe_div(tp, tp + fn),
        "false_positive_rate": safe_div(fp, fp + tn),
        "assertion_pass_rate": safe_div(passed_assertions, total_assertions),
        "targets": {
            "trigger_precision": "> 0.90",
            "trigger_recall": "> 0.85",
            "false_positive_rate": "< 0.05",
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
