#!/usr/bin/env python3
import sys

prompt = sys.stdin.read().strip()
responses = {
    "Return the deployment status.": "ready",
    "Describe the rollback procedure.": "Use the approved rollback runbook.",
    "Should the benchmark skill activate?": "trigger",
    "Should a generic unit-test request activate the benchmark skill?": "no",
}
print(responses.get(prompt, "unknown"))
