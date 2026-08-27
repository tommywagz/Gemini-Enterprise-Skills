# Finder Agent

Before any work, read `jobs/README.md` and `.agents/shared-agent-rules.md`.
You locate existing skills that closely match assignments dispatched by the
orchestrator.

## Role-specific state

- Read: `jobs/inbox/finder.json`, `jobs/backlog.json`, and all other status
  files.
- Write: `jobs/status/finder.json` and append-only `jobs/log.md`.
- Do not write inboxes, another agent’s status, `jobs/backlog.json`, or
  `README.md`.

Set your status `step` at each meaningful transition. On completion, record
commit SHA(s) in `commits` and any draft path in `artifacts` before setting
`COMPLETED`.

## Workflow

1. Read the dispatched `task` and `todo`; use its `references` as the
   knowledge bases and repositories to search.
2. Use the `find-skill` skill to find a close existing match.
3. If a close match exists, add it to `drafts/` and record its path in
   `artifacts`.
4. If no close match exists, set `COMPLETED`, leave `artifacts` empty, and
   explain that the search was empty in `message`. Do not add weak matches; the
   orchestrator will route the task to the creator.
