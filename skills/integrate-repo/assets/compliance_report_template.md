# Repository Integration Compliance Report

**Host repository:** `{{HOST_REPO_ROOT}}`
**Target path:** `{{TARGET_PATH}}`
**Date:** {{DATE}}
**Scanner output:** `{{RULES_JSON_PATH}}`

## Verdict

{{VERDICT}}
<!-- One of:
     PASS      — target clears every applicable gate; ready for PR.
     PASS/MANUAL — automated gates clear; N manual items listed below.
     FAIL      — one or more gates still failing; see Remaining work.
     PARTIAL   — some gates could not be executed; see Not verified. -->

## Gate results

| Gate | Tool | Version | Pin source | Status | Verified how |
|---|---|---|---|---|---|
| {{GATE_NAME}} | {{TOOL}} | {{VERSION}} | {{lockfile\|pre-commit rev\|action input\|run-step pin\|manifest range\|UNPINNED}} | {{PASS\|FAIL\|SKIPPED}} | {{ran\|inferred}} |

> `Verified how` must distinguish **ran** (the command was executed and its
> exit code observed) from **inferred** (concluded statically). Never present
> an inferred pass as a verified one.

## Violations found (Step 3 catalog)

| Class | Count | Gate | Resolution |
|---|---|---|---|
| auto-fixable | {{N}} | {{GATE}} | applied by `remediate_compliance.sh` stage {{N}} |
| mechanical | {{N}} | {{GATE}} | applied by `remediate_compliance.sh` stage 5 |
| manual | {{N}} | {{GATE}} | requires a human — listed below |

## Manual items

Items no autofixer can resolve. Each needs a decision, not another fixer run.

1. **{{FILE}}:{{LINE}}** — {{RULE}}: {{WHAT_IS_WRONG}}
   Suggested fix: {{SUGGESTION}}

## Configuration conflicts

From the scanner's `conflicts` block. These are findings about the host repo,
not about the target, and should be surfaced to its maintainers.

- **config_not_in_ci:** {{TOOLS}} — config present, no CI job invokes it.
  Not remediated against.
- **ci_not_in_config:** {{TOOLS}} — CI runs these with no config file; tool
  defaults are the standard.
- **competing_formatters:** {{PAIR}} — {{REASON}}. Kept `{{WINNER}}` (the one
  CI invokes); disabled `{{LOSER}}` for the target path.

## Not verified

Gates that could not be executed, and why. An unverified gate is not a pass.

- **{{GATE}}** — {{reason: tool not installed / UNRESOLVED_EXTERNAL action /
  requires cloud credentials / unresolved script alias}}

## CONTRIBUTING.md requirements

Process requirements a script cannot check. Confirm before opening the PR.

- [ ] Commit messages follow {{CONVENTION}}
- [ ] Changelog entry added
- [ ] Coverage stays at or above {{THRESHOLD}}
- [ ] DCO sign-off / CLA
- [ ] {{OTHER}}

> If `CONTRIBUTING.md` states the project does not accept external
> contributions, say so here and stop — the compliance work may not be
> submittable regardless of gate status.

## Artifacts

| File | Purpose |
|---|---|
| `remediate_compliance.sh` | Ordered autofix runner; checkpointed |
| `run_ci_preflight.sh` | Replays CI gates in check mode |
| `preflight_checklist.json` | Machine-readable gate manifest |
| `{{RULES_JSON_PATH}}` | Raw scanner output |

## Undo

```
git reset --hard {{CHECKPOINT_REF}}
```
