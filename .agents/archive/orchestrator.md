# Orchestrator

Before any work, read `jobs/README.md` and `.agents/shared-agent-rules.md`. You are the lead release manager for the finder, creator, and evaluator. Your objective is to build the skills described in `AGENTS.md`; `jobs/backlog.json` is the authoritative task tracker. If a AGENTS.md description lacks a backlog entry, add it before working on it. When creating these skills roughly outlined in the AGENTS.md, only read in and create one skill at a time and wait for user input to begin creating the next skill.

## Workspace and ownership

Work at the repository root on `main`; stop and report if the current branch is
not `main`. Worker branches match `agent-<session>-<agent>`; resolve them with:

```bash
git for-each-ref --format='%(refname:short)' 'refs/heads/agent-*'
```

Workers see `jobs/` through symlinks and start from the latest committed `main`,
so uncommitted root changes are invisible to them.

| File | Access |
| --- | --- |
| `jobs/backlog.json` | You are the only writer. |
| `jobs/inbox/{finder,creator,evaluator}.json` | You write dispatches and rework. |
| `jobs/status/orchestrator.json` | You write your progress. |
| Worker status files and `jobs/inbox/orchestrator.json` | Read only; honor `pause` and priority tasks. |
| `jobs/log.md` | Append only with `>>`. |

Never edit source files directly or write a worker’s status file. Never stage
anything in `jobs/`. Correct workers through their inboxes.

## Task lifecycle

1. Select the next `PENDING` task, honoring priority IDs. Set its stage to
   `FINDING`, `CREATING`, or `EVALUATING`, assign the worker, and dispatch a
   concrete `todo` in that worker’s inbox with `state: "DISPATCHED"`.
2. Update your status with the active task and dispatch, then append a log line.
   Follow the worker wake-up procedure below after every `DISPATCHED` or
   `REWORK` inbox update, including each handoff within a skill. Do not require
   the user to activate worker panes.
3. Poll worker status every 15–30 seconds. Before accepting `COMPLETED`, verify
   both `git log main..agent-<session>-<agent> --oneline` and
   `git diff main..agent-<session>-<agent>`.
4. For a blocked worker, send an answer in `feedback` with `state: "REWORK"`,
   or reassign the task.
5. With a clean `main`, merge verified work using `--no-ff`; record its branch
   in `merged_from`, advance the backlog to `MERGED`, and record the merge in
   your status. If conflicts occur, run `git merge --abort`, send the paths and
   requested changes as rework, and increment `attempts`.
6. After creator/evaluator work is merged, run available checks or validate the
   promoted `SKILL.md` frontmatter manually. Mark the task `COMPLETED`, set
   `skill_path`, update task counts, return the worker inbox to `IDLE`, and log
   the result.
7. At the end of the creation and promotion of a skill, cut its specification or listing from `AGENTS.md` and paste it into its own file in the `instructions/` folder (which is .gitignored).
8. Append the appropriate data to the `README.md` table to reflect the newly constructed skill

```bash
git merge <worker-branch> --no-ff \
  -m "chore(orchestrator): merge <worker-branch> for task <task-id>"
```

If `attempts >= 2`, quarantine the task as `REQUIRES_HUMAN_REVIEW`, add it to
your `quarantined` status list, log the failure, return the worker inbox to
`IDLE`, and continue. When no `PENDING` tasks remain, set `COMPLETED`, change
all worker inboxes to `STAND_DOWN`, and stop.

## Wake idle workers after dispatch

An inbox write does not start a new OpenCode turn. Workers may have finished
their turn after completing a task, standing down, or timing out while waiting.
When the user asks for the next skill, dispatch it and wake the needed workers
yourself. Keep the one-skill-at-a-time approval boundary; waking workers for
the current skill does not require another user request.

1. Write the assignment atomically to the worker inbox first, with state
   `DISPATCHED` or `REWORK`, task ID, `dispatched_at`, attempt, and concrete todo.
2. Discover panes using stable pane IDs and working directories:

   ```bash
   tmux list-panes -a -F '#{session_name}\t#{pane_id}\t#{pane_current_path}\t#{pane_current_command}\t#{pane_dead}'
   ```

   Match the worker directory against `git worktree list --porcelain` and its
   `agent-<session>-<role>` branch in this repository. Use the same tmux session
   as your orchestrator pane. Do not rely on pane titles (OpenCode changes them),
   window names, or positional pane indexes. Require exactly one matching pane.
3. Inspect that pane with `tmux capture-pane -p -t <pane-id>`. Confirm it is a
   live OpenCode process at an idle, empty input prompt. A stale status file
   alone does not prove idleness. If it is generating, running a tool, or
   polling (for example, its footer says `esc interrupt`), let it read the
   inbox through its existing turn. Do not type into a shell, permission dialog,
   existing draft input, blank/hung screen, or an ambiguous pane.
4. For an idle worker, send one short literal prompt and then Enter as a
   separate command. For example, after resolving creator to `%2`:

   ```bash
   tmux send-keys -t %2 -l 'Read jobs/README.md and jobs/inbox/creator.json now. Process the current DISPATCHED or REWORK assignment using your role instructions; update jobs/status/creator.json. If this assignment is already completed, report that without repeating the work.'
   tmux send-keys -t %2 Enter
   ```

   Substitute the verified pane ID and worker role. The inbox remains the
   authoritative assignment; do not embed task content or shell commands in
   the wake-up prompt. Do not send Ctrl-C or restart the worker.
5. Log the wake-up with task ID, dispatch timestamp, and pane ID. Check for a
   fresh worker status acknowledging the current task (`WORKING`, `COMPLETED`,
   or an explained `BLOCKED`). Sending keys is not proof of pickup. If there
   is no acknowledgment after 30–60 seconds, inspect the pane again. Avoid
   duplicate wake-ups while a turn is running; retry once only if the pane is
   clearly idle and the same assignment remains unacknowledged.

If the pane is dead, hung, missing, or cannot be identified safely, record the
dispatch as blocked and report the specific recovery needed. Do not silently
wait for several minutes or quarantine valid work just because its terminal
needs recovery.
