# Integrate Repo – Evaluation Report

Date: 2026-09-07

Skill path evaluated: `skills/integrate-repo`

## Summary

The skill passes the repository's token-efficiency linter, its bundled scanner
was exercised against four real repositories with differing toolchains, and
both bundled scripts were tested independently including their guard paths.

Trigger metrics below are a **static routing review**, not a live model run —
see *Method and its limits*. They are reported separately from the script
results, which were executed.

| Metric | Target | Result | Verified how |
|---|---|---|---|
| Description length | ≤ 1024 chars | 821 | ran (repo linter) |
| Body word count | ≤ 6250 words | 1719 | ran (repo linter) |
| Dead resources | 0 | 0 | ran (repo linter) |
| Body/reference duplication | 0 | 0 | ran (repo linter) |
| Trigger precision | ≥ 0.90 | 1.00 (10/10) | inferred (static review) |
| Trigger recall | ≥ 0.80 | 1.00 (10/10) | inferred (static review) |
| Script exit-code correctness | 100% | 8/8 paths | ran |

Qualitative rubric: Clarity 5, Correctness 4, Security 4, Robustness 4,
Maintainability 4.

## Method and its limits

**Executed.** `scripts/extract_repo_rules.py` was run against four
repositories with different toolchains, and its output inspected against the
actual workflow files:

| Repo | Toolchain | Gates found | Notes |
|---|---|---|---|
| `Gemini-Enterprise-Skills` | none | 0 | correctly reports no CI |
| `headroom` | Python + Rust, pre-commit | 18 | multi-language; pinned `ruff==0.15.17` detected |
| `spontus` | Node/Next.js | 4 | all four resolved through `npm run` aliases |
| `job-agent` | none detected | 0 | workflow present but no gate commands |

Four defects were found and fixed during this testing, each re-verified:

1. **Script aliases were invisible.** CI calling `npm run lint` produced zero
   gates on `spontus`. Added `package.json`/Makefile alias resolution with
   bounded recursion. Most JS/TS repos would have returned an empty gate list
   without this.
2. **Install commands counted as gates.** `pip install ... pytest` was
   reported as a pytest gate on `headroom` (25 gates → 18 after the fix).
3. **Backslash continuations split.** A multi-line `pip install` left the
   fragment `pytest ruff mypy` parsed as a three-tool gate. Continuations are
   now joined before matching.
4. **Prose matched as invocations.** `echo "npm publishes failed"` was
   reported as an unresolved alias. The alias pattern is now anchored to
   command position, and package-manager subcommands are excluded.

`scripts/remediate_compliance.sh` was tested in a scratch git repository
across all guard paths: missing target (exit 2), nonexistent path (exit 2),
non-git directory (exit 2), dirty tree without `--force` (exit 2), dirty tree
with `--dry-run` (exit 0), clean tree (exit 0, checkpoint branch created and
confirmed present via `git branch --list`). One defect was found and fixed:
`--dry-run` was incorrectly blocked by the dirty-tree guard despite writing
nothing.

**Not executed.** Trigger precision and recall in the table above were
assessed by reading the 20 prompts in `tests/eval_suite.json` against the
description's TRIGGER/DO NOT TRIGGER clauses. No routing model was run, so
these are *inferred*, not measured. The suite is deliberately adversarial on
the negative side — prompts 11-20 are adjacent tasks (new-repo scaffolding,
merge conflicts, business-logic refactors, authoring CI, bumping a linter
version) rather than unrelated topics — but a live run is required before
these numbers should be quoted as measured. Prompts 17 and 18 are the two
most likely to misfire in practice, as both mention linters.

## Security Review

1. `scripts/extract_repo_rules.py` is read-only: it opens files under the
   supplied root and writes nothing. Pure stdlib, no subprocess, no network.
2. `scripts/remediate_compliance.sh` is the only script that can modify a
   working tree. It refuses to run outside a git repository, refuses a dirty
   tree without `--force`, and creates a checkpoint branch before any stage.
   `git reset --hard` appears only inside printed guidance strings and is
   never executed by the script.
3. Scanner flagged one network indicator: the `$schema` URL in
   `assets/preflight_checklist.json`. This is a JSON Schema identifier, not a
   fetched resource — false positive.
4. No hardcoded credentials, no path-traversal patterns, no high-privilege CLI
   invocations detected.

Residual risk: the skill instructs an agent to generate and then run shell
scripts that rewrite files. This is inherent to the skill's purpose and is
mitigated by three controls stated in the body — Step 3 is read-only, Step 5
shows script contents to the user before execution, and the checkpoint is
mandatory unless explicitly disabled.

Overall risk tier: **High** (writes to the working tree) — acceptable with the
stated controls and a standard sandbox.

## Production Checklist

- [x] Trigger conditions specific and use domain vocabulary
- [x] Anti-triggers cover common misfires (scaffolding, merge conflicts,
      business-logic refactors, authoring CI)
- [x] Description under 150 words / 1024 chars
- [~] 20-prompt trigger suite present; precision **statically reviewed, not
      measured** — live run outstanding
- [x] Token budget under 5,000 tokens
- [x] Prerequisites stated
- [x] Steps ordered, atomic, produce verifiable artifacts
- [x] Decision branches explicit
- [x] Anti-patterns and error handling included
- [x] Output format defined
- [x] Scripts tested independently before bundling
- [x] Reference files > 100 lines have a table of contents
- [x] Asset formats documented in the skill body
- [x] Fallback instructions when references are unavailable
- [x] Risk tier assessed; no hardcoded credentials
- [ ] A/B comparison with/without skill — not run
- [ ] SME review — outstanding

## Recommended Follow-ups

1. Run the eval suite against a live router to replace the inferred trigger
   metrics with measured ones. Watch prompts 17 and 18.
2. Add a `policy.toml` once the repo adopts them, scoped to read-only git/gh
   plus the fixer binaries. This skill generates and runs shell scripts, so it
   benefits most from an explicit tool allowlist.
3. Extend `TOOL_PATTERNS` as new toolchains appear; the current set covers
   Python, JS/TS, Go, Rust, and JVM. Ruby, PHP, and Swift are unhandled and
   will surface as `unresolved_aliases` rather than silently passing.
