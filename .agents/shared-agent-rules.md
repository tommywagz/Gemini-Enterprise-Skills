# Shared Agent Rules

Read `jobs/README.md` first, then this file, before working. `jobs/` is the
shared coordination directory: use relative `jobs/...` paths; writes appear in
every worktree immediately. Never `git add` anything under `jobs/`.

## Workspace and file ownership

Workers operate in isolated worktrees and branches. Read only the inbox,
backlog, and other agents' status files named by your role instruction. Write
only your own status file; append to `jobs/log.md` with `>>`. The orchestrator
writes worker inboxes and is the only process that merges worker branches.

## Lifecycle

| State/event | Required action |
| --- | --- |
| Startup | Append a boot line to `jobs/log.md`; set your status to `WAITING` with branch, worktree, and timestamp. |
| `IDLE` inbox | Poll every 10–30 seconds; do not invent work. After about 10 minutes with no dispatch, set `BLOCKED` and log why. |
| `DISPATCHED` or `REWORK` | Read `feedback` for rework, copy `todo` to your status, set `WORKING` and `task_id`, then follow your role workflow. |
| Working | Keep the role-specific progress fields current at meaningful transitions. |
| Completed | Commit the work, record commit SHA(s) and artifacts, set `COMPLETED`, then resume polling. |
| Blocked or failed | Set `BLOCKED` with a specific `blocked_on`, or `FAILED` with what was tried; never fail silently. |

Use this boot pattern, replacing `<role>` with your role name:

```bash
printf '%s  [<role>] booted on %s\n' \
  "$(date -u +%FT%TZ)" "$(git rev-parse --abbrev-ref HEAD)" >> jobs/log.md
```

Use this polling pattern, replacing `<role>` with your role name:

```bash
until [ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["state"])' jobs/inbox/<role>.json)" != "IDLE" ]; do
  sleep 15
done
```

## Git commit protocol

You may create local commits in your assigned worktree. After a distinct,
validated task step, stage explicit paths and commit with a clear Conventional
Commit message:

```bash
git add <path> [<path>...]
git commit -m "<type>(<scope>): <short description>"
```

Do not commit code with known syntax errors or failing required tests. Never
push, never commit `.env` files, credentials, API keys, `node_modules`, or
temporary lock files. If hooks or linters fail, fix the reported issue and
retry the commit.
