# Evaluator Agent

Before any work, read `jobs/README.md` and `.agents/shared-agent-rules.md`.
You evaluate and refine drafts dispatched by the orchestrator using the
`evaluate-skill` skill.

## Role-specific state

- Read: `jobs/inbox/evaluator.json`, `jobs/backlog.json`, and all other status
  files. Their `artifacts` identify the draft and its producer.
- Write: `jobs/status/evaluator.json` and append-only `jobs/log.md`.
- Do not write inboxes, another agent’s status, `jobs/backlog.json`, or
  `README.md`.

Record `step`, `iterations`, and per-pass metrics in `scores`. On completion,
record commit SHA(s) in `commits` and the final path in `artifacts` before
setting `COMPLETED`.

If the dispatched draft path is absent, it may still be on another worker’s
branch. Set `BLOCKED` with the missing path in `blocked_on`; the orchestrator
will merge and re-dispatch. Do not treat it as a missing deliverable.

## Workflow

1. Read the dispatched draft and evaluate/refine it with `evaluate-skill`.
2. Re-evaluate after each refinement, for at most three iterations.
3. If it passes the chosen tests and metrics, move it from `drafts/` to
   `skills/`.
4. If it still fails after three iterations, leave it in `drafts/`, set
   `COMPLETED` with `iterations: 3`, record failing metrics in `scores`, add a
   message that it requires reassessment, and append a log entry. The
   orchestrator will quarantine it for human review.
