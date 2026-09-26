#!/usr/bin/env python3
"""Unified test runner to execute and score evaluation suites across tests/<skill-name>.

Usage:
  python3 tests/run_all_evals.py                   # Run all 38 skill suites
  python3 tests/run_all_evals.py <skill-name>      # Run single skill suite
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT / "tests"


def score_suite(suite_path: Path) -> dict:
    with open(suite_path) as f:
        data = json.load(f)

    evals = data.get("evals", [])
    if not evals:
        return {"error": "no evals found"}

    tp = fp = tn = fn = 0
    total_assertions = 0
    passed_assertions = 0

    for e in evals:
        should = e.get("should_trigger", True)
        actual = e.get("actual_trigger")
        if actual is None:
            continue

        if should and actual:
            tp += 1
        elif should and not actual:
            fn += 1
        elif not should and actual:
            fp += 1
        else:
            tn += 1

        for a in e.get("assertions", []):
            total_assertions += 1
            if a.get("passed", False):
                passed_assertions += 1

    total_graded = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    assertion_rate = passed_assertions / total_assertions if total_assertions > 0 else 0.0

    return {
        "skill_name": data.get("skill_name", suite_path.parent.name),
        "total_evals": len(evals),
        "graded_evals": total_graded,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "assertion_pass_rate": assertion_rate,
        "passes_all_gates": precision >= 0.90 and recall >= 0.85 and fpr <= 0.05 and assertion_rate >= 0.80
    }


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    if target:
        suite_file = TESTS_DIR / target / "eval_suite.json"
        if not suite_file.exists():
            print(f"Error: test suite not found at {suite_file}", file=sys.stderr)
            sys.exit(1)
        suites = [suite_file]
    else:
        suites = sorted(TESTS_DIR.glob("*/eval_suite.json"))

    print(f"Running evaluation scoring across {len(suites)} test suite(s)...\n")

    passed_count = 0
    failed_count = 0

    header = f"{'Skill':<36} | {'Evals':<6} | {'Prec':<7} | {'Recall':<7} | {'FPR':<6} | {'Assert':<7} | {'Status'}"
    print(header)
    print("-" * len(header))

    for s_file in suites:
        res = score_suite(s_file)
        if "error" in res:
            print(f"{s_file.parent.name:<36} | ERROR: {res['error']}")
            failed_count += 1
            continue

        status = "PASS" if res["passes_all_gates"] else "FAIL"
        if res["passes_all_gates"]:
            passed_count += 1
        else:
            failed_count += 1

        print(
            f"{res['skill_name']:<36} | "
            f"{res['total_evals']:<6} | "
            f"{res['precision']*100:>5.1f}% | "
            f"{res['recall']*100:>5.1f}% | "
            f"{res['fpr']*100:>5.1f}% | "
            f"{res['assertion_pass_rate']*100:>5.1f}% | "
            f"{status}"
        )

    print("-" * len(header))
    print(f"Results: {passed_count} PASSED, {failed_count} FAILED out of {len(suites)} suites.")
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
