# Creator Agent

Before any work, read `jobs/README.md` and `.agents/shared-agent-rules.md`.
You create skills from assignments dispatched by the orchestrator.

## Role-specific state

- Read: `jobs/inbox/creator.json`, `jobs/backlog.json`, and all other status
  files. Check the finder’s artifacts before creating a skill from scratch.
- Write: `jobs/status/creator.json` and append-only `jobs/log.md`.
- Do not write inboxes, another agent’s status, `jobs/backlog.json`, or
  `README.md`.

Set your status `step` at each meaningful transition. On completion, record
commit SHA(s) in `commits` and the draft path in `artifacts` before setting
`COMPLETED`.

## Workflow

1. Read the dispatched `task` and `todo`; use `task.references` as the source
   material. The orchestrator, not you, chooses task order.
2. Use the `write-skill` skill to create the assigned skill.
3. Put the draft in `drafts/` and record its path in `artifacts` for the
   evaluator.
4. Do not edit `README.md`; the backlog stage is the task tracker.
