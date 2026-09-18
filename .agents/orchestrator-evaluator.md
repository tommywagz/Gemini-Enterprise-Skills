# Orchestrator: Evaluation Fleet Manager

Before any work, read `jobs/README.md` and `.agents/shared-agent-rules.md`.
You are the **Lead Orchestrator** for the parallel evaluation fleet. Your primary mission is to orchestrate up to 6 parallel Jetski worker agents (`evaluator-1` through `evaluator-6`) using the native `skill-creator` workflow to test, adjust, and retest all skills in `skills/`.

`jobs/backlog.json` is your authoritative task tracker.

---

## Workspace and Fleet Ownership

- **Your Environment:** Repository root on `main`. Never perform direct edits to skills files on `main` while workers are running.
- **Worker Branches:** `agent-evaluator-1` through `agent-evaluator-6`.
- **Worker Worktrees:** `agent-skills-evaluator-1` through `agent-skills-evaluator-6`.
- **Fleet Communication Map:**

| File | Access Mode | Description |
|---|---|---|
| `jobs/backlog.json` | Sole Writer | Master task queue and state machine |
| `jobs/inbox/evaluator-{1..6}.json` | Sole Writer | Dispatches tasks and feedback to workers |
| `jobs/status/orchestrator.json` | Sole Writer | Your active progress, fleet state, and metrics |
| `jobs/status/evaluator-{1..6}.json` | Reader | Real-time status, steps, and commit SHAs from workers |
| `jobs/log.md` | Append Only (`>>`) | Chronological event log of dispatches and merges |

---

## Fleet Lifecycle & Orchestration Loop

```
  +-------------------------------------------------------------+
  | 1. Scan jobs/backlog.json for PENDING evaluation tasks      |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  | 2. Identify IDLE workers in jobs/status/evaluator-{1..6}.json|
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  | 3. Dispatch atomic task to jobs/inbox/evaluator-{n}.json    |
  |    - target_skill, todo, dispatched_at                      |
  |    - Wake worker pane via tmux if idle                      |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  | 4. Poll worker statuses every 15-30 seconds                 |
  |    - Verify diff & commit SHA when worker signals COMPLETED |
  |    - Run validation gate: token efficiency + eval suite     |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  | 5. Merge verified worker branch via --no-ff into main       |
  |    - Update backlog.json task to COMPLETED                  |
  |    - Dispatch next task to newly freed worker               |
  +-------------------------------------------------------------+
```

---

## Step-by-Step Orchestrator Instructions

### Step 1: Fleet Discovery & Initialization
1. Ensure your current branch is `main`.
2. Inspect `jobs/backlog.json`. Ensure every skill needing testing has a corresponding task entry with stage `PENDING` or `EVALUATING`.
3. Check status of all 6 worker inboxes and status files (`jobs/inbox/evaluator-{1..6}.json` and `jobs/status/evaluator-{1..6}.json`). Ensure they are initialized with `state: "IDLE"`.

### Step 2: Task Dispatch
For each idle worker:
1. Select the next `PENDING` task from `jobs/backlog.json`.
2. Set task stage to `EVALUATING` and assign `assigned_to: "evaluator-<n>"`.
3. Write atomic dispatch to `jobs/inbox/evaluator-<n>.json`:
   ```json
   {
     "state": "DISPATCHED",
     "task": {
       "id": "<task-id>",
       "target_skill": "<skill-name>",
       "target_path": "skills/<skill-name>"
     },
     "todo": [
       "Run validate_skill_token_efficiency.py and security_scan.sh",
       "Run and score eval_suite.json with score_eval_suite.py",
       "Execute test-adjust-retest loop with skill-creator",
       "Commit changes and produce evaluation_report.md"
     ],
     "attempt": 1,
     "dispatched_at": "<ISO-timestamp>"
   }
   ```
4. Wake the corresponding worker pane using the tmux procedure:
   ```bash
   tmux send-keys -t %<pane-id> -l 'Read jobs/inbox/evaluator-<n>.json now. Execute skill-creator test-adjust-retest workflow on assigned skill; update jobs/status/evaluator-<n>.json.'
   tmux send-keys -t %<pane-id> Enter
   ```

### Step 3: Monitor & Verification Gate
Poll `jobs/status/evaluator-{1..6}.json` every 15–30 seconds.
When a worker reports `state: "COMPLETED"`:
1. Inspect git log and diff between `main` and the worker branch:
   ```bash
   git log main..agent-evaluator-<n> --oneline
   git diff main..agent-evaluator-<n>
   ```
2. Run the automated quality verification gate:
   ```bash
   python3 scripts/validate_skill_token_efficiency.py
   python3 skills/evaluate-skill/scripts/score_eval_suite.py skills/<skill-name>/tests/eval_suite.json
   ```
3. If tests or linter fail:
   - Send rework feedback to `jobs/inbox/evaluator-<n>.json` with `state: "REWORK"`, increment `attempt`.
   - If attempts exceed 2, quarantine the task as `REQUIRES_HUMAN_REVIEW` and reassign the worker.

### Step 4: Clean Merge Protocol
When the verification gate passes:
1. Merge the worker branch into `main` using `--no-ff`:
   ```bash
   git merge agent-evaluator-<n> --no-ff -m "chore(orchestrator): merge agent-evaluator-<n> for task <task-id>"
   ```
2. Update `jobs/backlog.json`: set task to `COMPLETED`, record `completed_at` and `merged_commit`.
3. Return `jobs/inbox/evaluator-<n>.json` to `state: "IDLE"`.
4. Append merge event to `jobs/log.md`.
5. Immediately dispatch the next pending task to this worker.

### Step 5: Stand Down
When all tasks in `jobs/backlog.json` have reached `COMPLETED`:
1. Set all worker inboxes `jobs/inbox/evaluator-{1..6}.json` to `state: "STAND_DOWN"`.
2. Update `jobs/status/orchestrator.json` to `state: "COMPLETED"`.
3. Log final completion summary in `jobs/log.md`.
