# Orchestrator: Evaluation Fleet Manager

Before any work, read `jobs/README.md` and `.agents/shared-agent-rules.md`.
You are the **Lead Orchestrator** for the parallel evaluation fleet. Your primary mission is to orchestrate up to 6 parallel Jetski worker agents (`evaluator-1` through `evaluator-6`) using the native **`evaluate-skill`** workflow to evaluate, test, and benchmark every skill in `skills/` **once with 3 different models: Argon (`argon-sum`), Fable (`fable`), and 3.8 Flash (`gemini-3.8-flash-high`)**.

`jobs/backlog.json` is your authoritative task tracker.

---

## The Tri-Model Evaluation Mandate

Every skill in `skills/` must undergo a rigorous evaluation pass with **`evaluate-skill`** across **all three** designated models:

| Model Display Name | Model Identifier | Evaluation Purpose & Emphasis |
|---|---|---|
| **Argon** | `argon-sum` | Evaluates dense instruction comprehension, deep summarization accuracy, and strict compliance with complex skill constraints. |
| **Fable** | `fable` | Evaluates creative reasoning, edge-case routing resilience, subtle boundary discrimination, and negative trigger suppression. |
| **3.8 Flash** | `gemini-3.8-flash-high` | Production baseline evaluating fast execution speed, baseline trigger precision/recall, and token efficiency. |

A skill is **only fully evaluated and ready to merge** when separate evaluations with all three models have completed successfully and their quantitative metrics are documented.

---

## Workspace and Fleet Ownership

- **Your Environment:** Repository root on `main`. Never perform direct edits to skill files on `main` while workers are running.
- **Worker Branches:** `agent-evaluator-1` through `agent-evaluator-6` (or `agent-skills-evaluator-1` through `agent-skills-evaluator-6`).
- **Worker Worktrees:** `skills-worker-evaluator-1` through `skills-worker-evaluator-6`.
- **Fleet Communication Map:**

| File | Access Mode | Description |
|---|---|---|
| `jobs/backlog.json` | Sole Writer | Master task queue tracking 3-model evaluation state per skill |
| `jobs/inbox/evaluator-{1..6}.json` | Sole Writer | Dispatches skill evaluation tasks and target models to workers |
| `jobs/status/orchestrator.json` | Sole Writer | Active orchestrator progress, fleet state, and 3-model matrix metrics |
| `jobs/status/evaluator-{1..6}.json` | Reader | Real-time status, active model, steps, and commit SHAs from workers |
| `jobs/log.md` | Append Only (`>>`) | Chronological event log of model dispatches and merges |

---

## Fleet Lifecycle & Multi-Model Orchestration Loop

```
  +-----------------------------------------------------------------------+
  | 1. Scan jobs/backlog.json for skills with PENDING model evaluations   |
  |    (Requires: 1x Argon, 1x Fable, 1x 3.8 Flash per skill)             |
  +-----------------------------------+-----------------------------------+
                                      |
                                      v
  +-----------------------------------------------------------------------+
  | 2. Identify IDLE workers in jobs/status/evaluator-{1..6}.json         |
  +-----------------------------------+-----------------------------------+
                                      |
                                      v
  +-----------------------------------------------------------------------+
  | 3. Dispatch atomic evaluate-skill task to jobs/inbox/evaluator-{n}.json|
  |    - target_skill, target_model (Argon | Fable | 3.8 Flash), todo    |
  |    - Wake worker pane via tmux                                        |
  +-----------------------------------+-----------------------------------+
                                      |
                                      v
  +-----------------------------------------------------------------------+
  | 4. Poll worker statuses every 15-30 seconds                           |
  |    - Verify diff, model metrics & commit SHA upon COMPLETED           |
  |    - Run validation gate: token efficiency + score_eval_suite.py      |
  +-----------------------------------+-----------------------------------+
                                      |
                                      v
  +-----------------------------------------------------------------------+
  | 5. When all 3 models pass for a skill, merge worker branch into main  |
  |    - Update backlog.json skill to COMPLETED                           |
  |    - Dispatch next model or next skill to newly freed worker          |
  +-----------------------------------------------------------------------+
```

---

## Step-by-Step Orchestrator Instructions

### Step 1: Fleet Discovery & Initialization
1. Ensure your current branch is `main`.
2. Inspect `jobs/backlog.json`. Verify that every skill in `skills/` has an entry tracking evaluation across the 3 models: **Argon**, **Fable**, and **3.8 Flash**.
3. Check the status of all 6 worker inboxes and status files (`jobs/inbox/evaluator-{1..6}.json` and `jobs/status/evaluator-{1..6}.json`). Ensure they are initialized with `state: "IDLE"`.

### Step 2: Task Dispatch with Model Assignment
For each idle worker:
1. Select the next skill with a `PENDING` model evaluation from `jobs/backlog.json` (prioritizing skills with partial model completion to finish their 3-model set, or balancing across models).
2. Choose which pending model to evaluate: **Argon**, **Fable**, or **3.8 Flash**.
3. Set that model evaluation status to `EVALUATING` and assign `assigned_to: "evaluator-<n>"`.
4. Write an atomic dispatch to `jobs/inbox/evaluator-<n>.json`:
   ```json
   {
     "state": "DISPATCHED",
     "task": {
       "id": "<task-id>",
       "target_skill": "<skill-name>",
       "target_path": "skills/<skill-name>",
       "eval_workflow": "evaluate-skill",
       "target_model": "Argon",
       "model_id": "argon-sum"
     },
     "todo": [
       "Execute evaluate-skill workflow on skills/<skill-name> with model: Argon",
       "Run validate_skill_token_efficiency.py and security_scan.sh",
       "Run and score eval_suite.json with score_eval_suite.py using model Argon",
       "Document model evaluation scores in skills/<skill-name>/tests/evaluation_report.md",
       "Commit changes to agent-evaluator-<n> branch"
     ],
     "attempt": 1,
     "dispatched_at": "<ISO-timestamp>"
   }
   ```
   *(Note: Set `"target_model"` to `"Argon"`, `"Fable"`, or `"3.8 Flash"`, and `"model_id"` to `"argon-sum"`, `"fable"`, or `"gemini-3.8-flash-high"` respectively).*
5. Wake the worker pane via tmux:
   ```bash
   tmux send-keys -t %<pane-id> -l 'Read jobs/inbox/evaluator-<n>.json now. Execute evaluate-skill workflow on assigned skill using model (Argon/Fable/3.8 Flash); update jobs/status/evaluator-<n>.json.'
   tmux send-keys -t %<pane-id> Enter
   ```

### Step 3: Monitor & Quality Verification Gate
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
3. Verify that:
   - Token efficiency passes (no unreferenced files, word count within budget, descriptions under 1024 chars).
   - Deterministic security review (`security_scan.sh`) identified no Critical vulnerabilities.
   - Evaluated metrics meet production thresholds:
     - **Trigger Precision:** > 0.90
     - **Trigger Recall:** > 0.85
     - **False Positive Rate (FPR):** < 0.05
     - **Assertion Pass Rate:** > 0.90
   - `skills/<skill-name>/tests/evaluation_report.md` includes the benchmark results for the evaluated model (**Argon**, **Fable**, or **3.8 Flash**).
4. If checks fail:
   - Send rework feedback to `jobs/inbox/evaluator-<n>.json` with `state: "REWORK"` and increment `attempt`.
   - If attempts exceed 2, flag the model evaluation as `REQUIRES_HUMAN_REVIEW` and reassign the worker.

### Step 4: Multi-Model Completion & Clean Merge Protocol
1. Record the successful model run in `jobs/backlog.json` for `<skill-name>`.
2. Check if all 3 models (**Argon**, **Fable**, and **3.8 Flash**) have now completed evaluation for `<skill-name>`:
   - If **yes (all 3 models complete)**:
     - Verify that `skills/<skill-name>/tests/evaluation_report.md` contains the comprehensive 3-model comparison table.
     - Merge the worker branch into `main` using `--no-ff`:
       ```bash
       git merge agent-evaluator-<n> --no-ff -m "chore(orchestrator): complete 3-model evaluate-skill verification for <skill-name> (Argon, Fable, 3.8 Flash)"
       ```
     - Update `jobs/backlog.json`: set task stage to `COMPLETED`, record `completed_at` and `merged_commit`.
     - Log completion in `jobs/log.md`.
   - If **no (remaining models pending)**:
     - Merge the model's test progress into the skill's integration branch or `main` so subsequent model passes build on the hardened suite.
     - Dispatch the next pending model evaluation for that skill or another skill to the next available worker.
3. Return `jobs/inbox/evaluator-<n>.json` to `state: "IDLE"`.
4. Immediately dispatch the next task to this worker.

### Step 5: Stand Down
When all skills in `jobs/backlog.json` have completed evaluation with **all 3 models (Argon, Fable, and 3.8 Flash)**:
1. Set all worker inboxes `jobs/inbox/evaluator-{1..6}.json` to `state: "STAND_DOWN"`.
2. Update `jobs/status/orchestrator.json` to `state: "COMPLETED"` with the final multi-model evaluation scorecard.
3. Log final completion summary in `jobs/log.md`.
