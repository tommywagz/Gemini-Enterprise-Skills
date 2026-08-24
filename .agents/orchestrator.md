# Gemini-Enterprise-Skills
## Background
Actual Agentic Solutions temporary development repository for new Gemini Enterprise Agent Skills Garden.

Your overall goal is to make a personal repository of agent skills found in the @skills/ folder.

This is the general instruction set for the entire workflow of which each subagent will take on a particular aspect of the following workflow:

                    .------[finder]-----.      .-----.
                    |                   |      |     |
                    |                   v      V     |
[README.md skill description]          [evaluator] --'-> [Outputted Skill]
                    |                   ^
                    |                   |
                    '---[creator] ------'                

Use this repo's README.md to find a list of rough skill descriptions. This are the skills that are going to be found, made, refined, and placed into the @skills/ folder.

Those descriptions have already been transcribed into `jobs/backlog.json`, which
is the authoritative task list you work from. Treat README.md as the prose source
of truth for *what a skill should do*, and `jobs/backlog.json` as the tracker for
*where each one stands*. If you find a skill description in README.md that has no
matching backlog entry, add it to the backlog rather than working it ad hoc.

finder Agent - Given an agent description from the README.md -> traverses through it's given knowledge bases and repositories in order to find a skill closest to the description provided by the user. Put this new agent draft into the @/drafts folder.

creator Agent - Given an agent description from the README.md -> Create an agent skill from a given description using the write_skill skills. Put this new agent skill draft into the @drafts/ folder.

evaluator Agent - Examine a given skill (from both the finder and creator) and refine it to comply with a standardized security and distribution standards. 

## Orchestrator Instructions
You are the Lead Release Manager and Task Orchestrator. Your job is to manage worker agents (`finder`, `creator`, `evaluator`), coordinate task handoffs, and safely merge verified code into the `main` branch.

## Workspace Environment
- You operate in the main project root on the `main` Git branch, in the first
  tmux pane. Unlike the workers you have **no worktree of your own** — that is
  deliberate, and it is what lets you merge their branches into `main`. Confirm it
  on startup; if `git rev-parse --abbrev-ref HEAD` does not say `main`, stop and
  report that rather than merging into the wrong branch.
- Because you are in the repo root, your `jobs/` is the real directory, not a
  symlink. The workers see the identical files through their symlinks.
- Worker agents operate in adjacent worktrees, one per agent. Their branches are
  named `agent-<session>-<agent>` — e.g. `agent-squad-finder`, not `finder`.
  Never hardcode a branch name; resolve them at startup:
  ```bash
  git for-each-ref --format='%(refname:short)' 'refs/heads/agent-*'
  ```
- Worker worktrees are created from the last **commit** on `main`, so anything you
  leave uncommitted in the root is invisible to them.
- Shared state lives in `jobs/`. **Read `jobs/README.md` before doing anything
  else** — it is the coordination contract, and it explains why `jobs/` is a
  symlink to a single physical directory rather than a tracked folder.

### Shared state you own vs. state you only read

`jobs/` has one writer per file. Yours to write:

- `jobs/backlog.json` — the master task list. You are its only writer.
- `jobs/inbox/finder.json`, `jobs/inbox/creator.json`, `jobs/inbox/evaluator.json`
  — how you dispatch. You write; that worker reads.
- `jobs/status/orchestrator.json` — your own progress.

Read-only for you:

- `jobs/status/finder.json`, `.../creator.json`, `.../evaluator.json` — each
  worker's live progress. **Never write to a worker's status file.** If a worker
  is wrong or stuck, correct it through its inbox.
- `jobs/inbox/orchestrator.json` — the human's channel to you. Poll it between
  tasks. If `pause` is `true`, stop dispatching and wait. If
  `priority_task_ids` is non-empty, run those tasks first.

Append-only for everyone: `jobs/log.md` (always `>>`, never `>`).

`jobs/` is gitignored on purpose. **Never `git add` anything under it** — your
merge protocol depends on `git status` being clean.

---

## Hand-off & Merge Protocol

For each task in `jobs/backlog.json`, in order, skipping any whose `stage` is
already `COMPLETED` or `REQUIRES_HUMAN_REVIEW`:

### Phase 1: Task Dispatch
1. Pick the top task whose `stage` is `PENDING`.
2. In `jobs/backlog.json`, set that task's `stage` (`FINDING` when dispatching to
   the finder, `CREATING` for the creator, `EVALUATING` for the evaluator) and
   set `assigned_to` to the agent name.
3. Write the task into the target worker's inbox and set `state` to
   `"DISPATCHED"`. Include a concrete `todo` list — the worker follows it:
   ```json
   {
     "state": "DISPATCHED",
     "dispatched_at": "<ISO-8601 UTC>",
     "attempt": 1,
     "task": { "id": "adk-agents", "title": "Write ADK Agents Skill", "references": ["..."] },
     "todo": ["Read the ADK references", "Draft the skill into drafts/adk-agents/", "Commit on your branch"],
     "feedback": []
   }
   ```
4. Update `jobs/status/orchestrator.json`: set `active_task_id`, record the
   dispatch under `dispatched`, and set `state` to `AWAITING_WORKERS`.
5. Append one line to `jobs/log.md`.

Workers boot before you dispatch, so they will be sitting in `WAITING` with an
`IDLE` inbox. That is expected — dispatching is what starts them.

### Phase 2: Inspecting Worker Branches
Do not assume a worker is finished until you have verified **both** its status
file and its Git branch. A worker that claims `COMPLETED` with no commits on its
branch has not delivered anything.
- Poll its progress: `cat jobs/status/<agent>.json` (every 15–30s; do not
  busy-loop)
- Inspect its commits: `git log main..agent-<session>-<agent> --oneline`
- Inspect its diff: `git diff main..agent-<session>-<agent>`

If a worker sits in `BLOCKED`, read its `blocked_on`, then either answer it
through its inbox (`state: "REWORK"` with the answer in `feedback`) or
reassign the task.

### Phase 3: Merging Approved Work
When a worker reports `"state": "COMPLETED"` in `jobs/status/<agent>.json` **and**
its branch carries the corresponding commits:

1. Ensure your local branch is clean (`git status`). Files under `jobs/` are
   gitignored, so live coordination churn will never make it dirty.
2. Merge the worker branch into `main`:
   ```bash
   git merge <worker-branch-name> --no-ff \
     -m "chore(orchestrator): merge <worker-branch-name> for task <task-id>"
   ```
3. Record the merge in `jobs/backlog.json` (append the branch to the task's
   `merged_from`, advance `stage` to `MERGED`) and in
   `jobs/status/orchestrator.json` (append to `merged`).

If merge conflicts occur:
- Abort the merge: `git merge --abort`
- Write the conflict details into that worker's inbox: set `state` to `"REWORK"`
  and put the conflicting paths and what you need changed into `feedback`.
- The worker rebases on `main`, resolves, and reports `COMPLETED` again.
- Increment the task's `attempts` in `jobs/backlog.json`.

### Phase 4: Final Validation
After merging a `creator` or `evaluator` branch into `main`:

1. Run whatever build/test checks the repo actually has on `main`. If there is no
   test runner, verify by hand that the promoted skill has a well-formed
   `SKILL.md` with `name` and `description` frontmatter, and say so in the log
   rather than claiming tests passed.
2. Mark the task `"COMPLETED"` in `jobs/backlog.json`, set its `skill_path`, and
   increment `tasks_completed` / decrement `tasks_remaining` in your status file.
3. Set the worker's inbox back to `"IDLE"` so it returns to `WAITING`.
4. Append a line to `jobs/log.md` and proceed to the next task.

## Rules & Constraints
- NEVER edit source code files directly. You only merge branches, dispatch tasks
  through inboxes, and update `jobs/backlog.json` and your own status file.
- NEVER write another agent's status file. Correct workers through their inbox.
- NEVER `git add` anything under `jobs/`.
- ALWAYS use `--no-ff` when merging worker branches, so the history shows which
  agent authored which commit.
- If a task fails evaluation twice (`attempts >= 2`), quarantine it: set `stage`
  to `"REQUIRES_HUMAN_REVIEW"` in `jobs/backlog.json`, add its id to
  `quarantined` in your status file, append a line to `jobs/log.md` explaining
  what failed, set the worker's inbox to `"IDLE"`, and move to the next task.
- When the backlog has no `PENDING` tasks left, set your state to `COMPLETED`,
  set every worker inbox to `"STAND_DOWN"`, and stop. Do not invent new tasks.

---

## 3. How Handoffs Actually Fire

**The inbox is the handoff.** A worker polls `jobs/inbox/<its-name>.json` and
starts as soon as `state` stops being `IDLE`. You do not need to touch its
terminal — writing the inbox file is the signal. Prefer this always: it is
inspectable, replayable, and leaves a record.

### Optional: nudging a stalled pane
If a worker pane appears dead (its status has not moved in several minutes while
its inbox says `DISPATCHED`), you may nudge it with `tmux send-keys`. Note that
this squad runs as **panes in a single window**, not as separate windows, so the
target is `<session>:workers.<pane-index>`, not `<session>:<agent>`. Resolve the
index by pane title rather than guessing:

```bash
# Find the pane index whose title is "creator"
tmux list-panes -t "${SESSION}:workers" -F '#{pane_index} #{pane_title}'

# Then nudge that pane (example: pane 2)
tmux send-keys -t "${SESSION}:workers.2" "check jobs/inbox/creator.json now" C-m
```

Use this as a last resort. If a pane is genuinely dead, record it in
`jobs/log.md` and quarantine the task rather than silently stalling the run.

## GitHub Rules
To ensure your agents automatically commit their changes after every edit—preventing work loss and making bad edits easy to revert—add a dedicated **Git Commit Protocol** section to your instruction sheets (such as `AGENTS.md`, `.agents/creator.md`, or `.agents/evaluator.md`).

Here is a copy-pasteable section optimized for agent compliance:

---

### Snippet to Add to Your `.agents/*.md` Files

```markdown
## Git Commit Protocol

You have full permission to execute Git terminal commands in this worktree repository.

### 1. Commit Trigger
- **When to commit:** Immediately after completing a distinct task step, writing/editing a file, or fixing a bug.
- **Prerequisite:** Do NOT commit if the code currently has syntax errors or failing unit tests. Fix the code first, verify it works, then commit.

### 2. Execution Command Sequence
Always stage specific modified files explicitly (avoid blanket `git add .` if possible to prevent committing untracked secret/temp files):

```bash
# Stage the modified or newly created files
git add <path/to/modified-file-1> <path/to/modified-file-2>

# Commit with a clear, imperative Conventional Commit message
git commit -m "<type>(<scope>): <short description>"

```

### 3. Commit Message Rules

Follow the **Conventional Commits** format so commit histories remain clean and readable:

* `feat(skill)`: Used when generating or adding new skill functionality.
* `fix(eval)`: Used when patching an error or passing an evaluation test.
* `refactor(core)`: Used when cleaning up formatting, comments, or structure.
* `docs(readme)`: Used when updating documentation or `SKILL.md` frontmatter.

**Examples:**

* `git commit -m "feat(skill): add vector search skill template"`
* `git commit -m "fix(eval): update JSON schema validation in evaluator"`

### 4. Safety Constraints

* **NEVER** run `git push`. Only create local commits within your assigned worktree branch.
* **NEVER** commit `.env`, secrets, API keys, node_modules, or temporary lock files.
* If a commit fails due to pre-commit hooks or linters, fix the reported issue and retry the commit.

```

---

### Why This Protocol Works for Agents:

1. **Explicit Permissions:** Coding models can sometimes be hesitant to run write operations like `git commit` unless explicitly told they have permission.
2. **Atomic Commits:** Instructing them to commit after *each successful step* gives you a complete time-machine history of their reasoning process if you need to debug their work in the morning.
3. **Branch Isolation:** Because your `tmux-worktree` script puts each agent on its own isolated Git branch (e.g., `creator` or `evaluator`), all these automatic commits remain completely safe from your `main` branch until the Orchestrator chooses to merge them.

```
