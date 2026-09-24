---
name: integrate-repo
description: "Audits an unintegrated file, folder, or vendored dependency against the host repository's real quality gates, then emits an ordered remediation script and a local CI pre-flight runner. TRIGGER when the user says 'integrate repo', 'make this folder compliant', 'match the repo style', 'align external code with our conventions', 'remediate to match CONTRIBUTING.md', 'make it pass CI locally', 'why does CI fail but lint passes locally', or drops vendored/generated/AI-authored code into a repo and asks to bring it up to standard. DO NOT TRIGGER for scaffolding a brand-new repository or service (use a project-scaffolding skill), for resolving git merge conflicts, for refactoring business logic or fixing test failures unrelated to repo standards, or for authoring the CI pipeline itself rather than conforming to it."
version: 1.0.0
author: Actual Agentic Solutions
tags: [repo-compliance, linting, formatting, ci, pre-flight, code-standards, monorepo]
license: Apache-2.0
compatibility: Python >= 3.10; git >= 2.23. Toolchain-agnostic (Node, Python, Go, Rust, JVM).
metadata: {}
---

- Host Repository Integration & Compliance Remediation

- Overview
Bringing foreign code — a vendored library, a generated client, another team's
folder, an AI-authored module — into a repository fails for a boring reason:
the code is judged by the gates CI actually runs, not by the config files
sitting in the repo root. Those two things drift constantly.

Success is a target path that passes the *same commands CI runs, at the same
tool versions*, with a diff a reviewer can actually read.

The core discipline: **the CI workflow is the source of truth; config files
are only evidence.** A repo can carry a `.eslintrc.json` that no job invokes
and a `ruff.toml` whose `select` list CI overrides on the command line. Audit
what runs, then conform to it.

- Prerequisites
- The **host repository root** (where the standards live) and the **target
  path** (what must comply). If the user names only one, ask which is which —
  guessing inverts the entire audit.
- A clean or committed git state in the host repo. Step 5 writes files.
- Python >= 3.10 for `scripts/extract_repo_rules.py`.
- Package managers only need to be installed for Step 6. Steps 1-5 are static
  analysis and work offline.

- Workflow

- Step 1: Extract the host repo's real rules
Run the scanner from the host repository root:
```
python3 scripts/extract_repo_rules.py <host-repo-root> --json > /tmp/repo_rules.json
```
It inventories formatter/linter/type-checker configs, hook managers
(`.pre-commit-config.yaml`, `.husky/`, `lefthook.yml`), `CONTRIBUTING.md`
requirements, and — most importantly — parses `.github/workflows/*.yml`,
`.gitlab-ci.yml`, and `.circleci/config.yml` into an ordered list of the
`run:` commands that gate a merge. Read the JSON; do not re-derive this by
hand.

Resolve the three conflicts it reports before going further:
- **`config_not_in_ci`** — a config file no CI job invokes. Treat it as
  advisory. Do not remediate against it; say so in the report.
- **`ci_not_in_config`** — CI runs a tool with no config file, so the tool's
  defaults are the standard. Do not invent a config file to "fix" this.
- **`competing_formatters`** — two formatters that will fight over the same
  files (Prettier + Biome, Black + `ruff format`, gofmt + gofumpt). Pick the
  one CI invokes and disable the other for the target path. Running both
  produces churn on every save, forever.

- Step 2: Pin the tool versions CI uses
Version skew is the single most common cause of "it's clean locally but red in
CI". Formatters change their output between minor versions.

Take versions in this order of authority: the lockfile
(`package-lock.json`, `uv.lock`, `poetry.lock`, `Cargo.lock`, `go.sum`) →
the `rev:` field in `.pre-commit-config.yaml` → the pinned action input
(`actions/setup-node` `node-version`, `astral-sh/setup-uv` `version`) →
the manifest range (`devDependencies`, `[tool.ruff]`). A manifest range is a
last resort — `^3.2.0` does not tell you what CI resolved.

The scanner reports these as `tool_versions`. If a version is unresolvable,
record it as `UNPINNED` in the report and use the repo's own runner
(`npx --no-install`, `uv run`, `pre-commit run`) rather than a globally
installed binary, which is almost certainly a different version.

- Step 3: Catalog the delta — read only, no writes
Run every gate from Step 1 against the target path in **check mode**
(`--check`, `--dry-run`, `--diff`, `-l`) and record violations by gate.
Nothing is modified in this step.

Beyond tool output, check what linters do not catch:
- **Naming and placement** — file/directory casing (kebab vs. snake vs.
  camel), and whether tests sit beside sources or in a parallel tree. Infer
  from the majority convention in the host repo, not from one example.
- **License headers** — compare against the header on the host repo's own
  recently-added files, not against `LICENSE`.
- **Forbidden imports** — dependency-boundary rules from `import/no-restricted-paths`,
  `ruff` `flake8-tidy-imports`, `depguard`, or an `ARCHITECTURE.md`.
- **Docstring/JSDoc conventions** — presence and style, where CI enforces it
  (`pydocstyle`, `eslint-plugin-jsdoc`).

Classify each violation `auto-fixable`, `mechanical`, or `manual`. That split
drives Steps 4 and 5. See `references/toolchain_fixers.md` for the exact
check-mode and fix-mode flags per tool, and for which rule classes each fixer
genuinely resolves versus only reports.

- Step 4: Order the fixes correctly
Fix order is not cosmetic — the wrong order produces a file that fails the
gate that already passed. Apply in exactly this sequence:

1. **Codemods / syntax upgrades** (`pyupgrade`, `ts-migrate`, `go fix`) —
   these rewrite AST shapes and invalidate anything downstream.
2. **Import sorting** (`isort`, `ruff --select I --fix`, `eslint
   import/order --fix`) — changes line counts, so it must precede anything
   line-sensitive.
3. **Linter autofix** (`ruff check --fix`, `eslint --fix`, `clippy --fix`) —
   may introduce code that is correct but unformatted.
4. **Formatter** (`prettier --write`, `ruff format`, `black`, `gofmt`) —
   **always last**, because the formatter must have the final say on layout.

Running the formatter before the linter is the classic mistake: `eslint --fix`
will happily reflow what Prettier just formatted, and CI then fails on
formatting. Type-checkers (`mypy`, `tsc`) are never fixers — they run in
Step 6 as verification only.

- Step 5: Generate the two scripts
Write both **outside the host repository's working tree** — a scratch directory
alongside the repo, or `.git/integrate-repo/` — executable, and **show the user
the contents before running anything**. Never write them into the target or its
parent: the artifacts would land in the diff under review, and on a repo that
tracks everything they become uncommitted changes in the tree the fixers are
about to rewrite.

`remediate_compliance.sh` — the ordered fixes from Step 4. It must:
- Take a checkpoint first: refuse to run when **tracked** files are modified
  unless `--force`, and create a `pre-remediate/<timestamp>` branch so the user
  can get back. State the exact undo command in the script's output. Untracked
  files must not block the run, but a checkpoint is a commit and cannot restore
  one a fixer rewrites — warn and name any untracked file under the target.
- Scope every command to the target path. Never invoke a repo-wide fixer —
  a 4,000-file reformat buries the 40 files under review.
- Use `git mv` for renames, never `mv`, so history survives.
- Run one gate per step, echoing the gate name. Drive stages 1-4 with the
  template's `fix` helper and stage 5 with `run`: a fixer exits non-zero
  whenever unfixable violations remain — the normal case — and treating that as
  fatal aborts the script before the formatter stage. Only genuinely fatal
  steps (`git mv`, header injection) should stop the run.
- Inject license headers idempotently — check for the marker before writing,
  or reruns stack duplicate headers.

`run_ci_preflight.sh` — replays the Step 1 CI commands in CI order, in check
mode, against the target path. Exit `0` = the target would pass. Emit each
gate's name, command, and pass/fail so the failing gate is obvious.

Copy `assets/preflight_checklist.json` beside them as the machine-readable
gate manifest both scripts read, so the gate list lives in one place.

- Step 6: Verify, then report
Run `run_ci_preflight.sh`. If gates still fail, they are the `manual` class
from Step 3 — do not loop on autofixers, which have already converged.

Fill in `assets/compliance_report_template.md`: per-gate status, what was
auto-fixed, what needs a human, unresolved config/CI conflicts from Step 1,
any `UNPINNED` tools, and the `CONTRIBUTING.md` items a script cannot verify
(commit message format, changelog entry, coverage threshold, sign-off).

- Examples

- Example 1: Vendored SDK folder in a Python monorepo
Input: "make `vendor/acme-client/` comply with our repo."
Expected behavior: Scanner finds `ruff` + `mypy` in CI, and a `.pre-commit-config.yaml`
pinning `ruff` at `v0.6.9` while the venv has `0.9.2` → Step 2 pins to
`0.6.9` via `pre-commit run`. Also finds a `.prettierrc` no workflow invokes →
flagged `config_not_in_ci`, not remediated. `remediate_compliance.sh` runs
`ruff check --fix` then `ruff format`, scoped to `vendor/acme-client/`.
`mypy` reports 12 missing annotations → `manual`, listed in the report.

- Example 2: The "passes locally, fails in CI" report
Input: "lint passes on my machine but CI fails on this folder."
Expected behavior: Skip to Step 2. Diff the local binary version against the
lockfile/`rev:` pin. The usual finding is a globally installed formatter a
minor version ahead of CI. Fix by routing through the repo's runner, not by
reformatting the code.

- Error Handling
- **No CI workflows found** — fall back to hook manager, then config files, and
  state the reduced confidence in the report. Do not fabricate a pipeline.
- **CI uses a composite/reusable action** (`uses:` with no `run:`) — the gates
  are in another repo. Record the action ref as `UNRESOLVED_EXTERNAL` and ask
  the user for the command list rather than guessing.
- **Monorepo, multiple toolchains** — resolve the config nearest the target
  path; nearest wins over root. If the target spans two packages with
  different toolchains, split the audit per package.
- **Target is generated code** — check for a `generated/` exclusion in the
  linter config first. If CI already excludes it, the correct outcome is *no
  remediation*; report that rather than reformatting a generated file that
  will be overwritten.
- **Dirty working tree** — stop before Step 5. Do not stash the user's
  uncommitted work without explicit confirmation.
- **A fixer rewrites more than the target path** — abort, restore from the
  Step 5 checkpoint, and re-scope. Never hand back a diff wider than requested.
- **Missing or unreadable reference/script in this skill** — name the file and
  fall back to the tool's own `--help`. Do not reconstruct the flag tables from
  memory; a wrong `--check` flag silently rewrites files during Step 3, which
  is meant to be read-only.
- **`extract_repo_rules.py` reports `unresolved_aliases`** — CI runs a script
  alias whose body could not be resolved (a custom binary, or a nested
  Makefile target). Open the script and read it. An unresolved alias is a
  blind spot, not an absent gate; never report a pass while one is outstanding.

- Anti-Patterns to Avoid
- **Trusting config files over CI.** A `.eslintrc` no job runs is not a
  standard. Conform to the commands that gate the merge.
- **Running fixers before cataloging.** Step 3 is read-only for a reason: once
  autofixers run, the original violation set is unrecoverable and the report
  becomes fiction.
- **Repo-wide formatting.** Scope to the target. A reformat of untouched files
  is an unreviewable diff and will be rejected.
- **Formatter before linter.** See Step 4 — guarantees a CI formatting failure.
- **Installing tools to make gates pass.** Adding a dependency changes the
  host repo's contract. Report the missing tool; let the user decide.
- **Treating `mypy`/`tsc` as fixers.** They verify. Auto-inserting `# type: ignore`
  or `any` to silence them defeats the gate.
- **Silently "improving" business logic** while remediating style. Compliance
  changes and behavior changes must not share a commit.

- Reference Files
- **scripts/extract_repo_rules.py**: scans a repo root for configs, hooks,
  `CONTRIBUTING.md` gates and CI `run:` commands; emits JSON with
  `tool_versions` and the three conflict classes. Run in Step 1.
- **scripts/remediate_compliance.sh**: checkpoint-guarded, correctly ordered
  fix runner. Used as the template emitted in Step 5.
- **references/toolchain_fixers.md**: per-tool check-mode and fix-mode flags,
  what each fixer actually resolves, and competing-formatter pairs. Read in
  Steps 3 and 4.
- **references/ci_workflow_patterns.md**: extracting gates from GitHub
  Actions, GitLab CI and CircleCI — matrices, composite actions, `working-directory`,
  and where versions are pinned. Read in Steps 1 and 2.
- **assets/compliance_report_template.md**: the Step 6 report shape.
- **assets/preflight_checklist.json**: machine-readable gate manifest emitted
  in Step 5 and consumed by both generated scripts.

- Output Format
Deliver: (1) the resolved gate list with tool versions and their pin source;
(2) the violation catalog from Step 3, split auto-fixable / mechanical /
manual; (3) `remediate_compliance.sh` and `run_ci_preflight.sh`, shown before
execution; (4) the Step 6 pre-flight result per gate; and (5) the completed
compliance report. State explicitly which gates were **verified by running**
versus **inferred statically** — never present an inferred pass as a
verified one.
