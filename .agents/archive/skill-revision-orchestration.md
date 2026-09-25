# Skill Revision Orchestration Specification

## Executive Summary
This document defines the automated orchestration protocol for comprehensively revising, testing, and hardening all Agent Skills in `skills/` using the native `skill-creator` skill in Google Antigravity, Jetski, and Gemini CLI environments. 

The system utilizes a high-throughput, safety-bounded multi-agent fleet coordinated via `opencode.json` and the shared real-time `jobs/` bus.

---

## Architecture Overview

```
                          +-------------------------------+
                          |   Orchestrator Agent          |
                          |   (Branch: main)              |
                          |   Instruction: orchestrator-  |
                          |   evaluator.md                |
                          +---------------+---------------+
                                          |
               +--------------------------+--------------------------+
               | Dispatch via jobs/inbox/ | Monitor via jobs/status/ |
               v                          v                          v
    +--------------------+     +--------------------+     +--------------------+
    | Evaluator Worker 1 | ... | Evaluator Worker N | ... | Evaluator Worker 6 |
    | Worktree: eval-1   |     | Worktree: eval-N   |     | Worktree: eval-6   |
    | Branch: agent-*-1  |     | Branch: agent-*-N  |     | Branch: agent-*-6  |
    +---------+----------+     +---------+----------+     +---------+----------+
              |                          |                          |
              +--------------------------+--------------------------+
                                         |
                                         v
                      +--------------------------------------+
                      | Native `skill-creator` Loop          |
                      | 1. Deterministic Security Scan       |
                      | 2. Token-Efficiency & Dead Ref Linter|
                      | 3. Routing & Assertion Eval Suite    |
                      | 4. Iterative Remediation (Test->Adj) |
                      | 5. Regression Retest (Up to 3 passes)|
                      | 6. Evaluation Report Generation      |
                      +--------------------------------------+
```

---

## Safe Concurrency Bounds
To guarantee optimal throughput without risking API quota throttling or workstation degradation:
1. **Parallel Worker Cap:** Exactly **6 concurrent worker agents** (`evaluator-1` through `evaluator-6`) plus **1 orchestrator agent** (7 total agent processes).
2. **Quota Preservation:** Running 7 agents against Google Vertex AI (`gemini-3.8-flash`) generates approximately 70–140 RPM and 400k TPM, safely under standard enterprise quotas (300+ RPM / 1M+ TPM).
3. **Worktree Isolation:** Each worker operates inside a separate git worktree on an isolated branch (`agent-evaluator-1` to `agent-evaluator-6`), preventing `.git/index.lock` collisions.
4. **Shared Real-Time State:** Fast, zero-lock communication occurs exclusively through `jobs/inbox/evaluator-{1..6}.json` and `jobs/status/evaluator-{1..6}.json`.

---

## The Worker "Test-Adjust-Retest" Cycle
Each worker follows the contract defined in `.agents/evaluator-worker-template.md`:

1. **Preflight Audit:**
   - Execute `bash skills/evaluate-skill/scripts/security_scan.sh skills/<target-skill>`.
   - Execute `python3 scripts/validate_skill_token_efficiency.py` to catch unreferenced files, token bloat, or description formatting flaws.
2. **Execute Evaluation Suite:**
   - Run `python3 skills/evaluate-skill/scripts/score_eval_suite.py skills/<target-skill>/tests/eval_suite.json`.
   - Score the confusion matrix: True Positives, True Negatives, False Positives, False Negatives.
3. **Threshold Gates:**
   - **Trigger Precision:** $\ge 0.90$
   - **Trigger Recall:** $\ge 0.85$
   - **False Positive Rate:** $\le 0.05$
   - **Assertion Pass Rate:** $1.00$ ($100\%$)
   - **Linter Status:** $0$ errors
4. **Remediate & Refine:**
   - If trigger precision/recall fails, refine YAML frontmatter description using A/B boundaries.
   - If linter flags dead code, cite or purge unreferenced resources.
   - If security scan flags critical risks, sanitize scripts and credentials immediately.
   - If body lacks operational edge cases, enhance with concrete gotchas and error handling.
5. **Retest & Verify:**
   - Re-run the full evaluation suite and linter. Iterate up to 3 times until all gates pass.
6. **Publish Report & Handoff:**
   - Update `skills/<target-skill>/tests/evaluation_report.md` with final metrics.
   - Commit cleanly with Conventional Commits (`chore(evaluator): verify and harden <skill>`).
   - Signal `COMPLETED` in `jobs/status/evaluator-{n}.json`.

---

## Orchestrator Merge & Verification Protocol
1. Orchestrator monitors `jobs/status/evaluator-{1..6}.json`.
2. Upon receiving `COMPLETED`, orchestrator runs verification on `main`:
   ```bash
   git log main..<worker-branch> --oneline
   git diff main..<worker-branch>
   python3 scripts/validate_skill_token_efficiency.py
   python3 skills/evaluate-skill/scripts/score_eval_suite.py skills/<target-skill>/tests/eval_suite.json
   ```
3. Merges via `--no-ff`:
   ```bash
   git merge <worker-branch> --no-ff -m "chore(orchestrator): merge <worker-branch> for task <task-id>"
   ```
4. Updates `jobs/backlog.json` to mark task `COMPLETED`.
5. Dispatches the next pending task to the freed worker.
