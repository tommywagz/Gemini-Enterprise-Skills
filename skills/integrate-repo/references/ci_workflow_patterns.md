# Extracting Gates from CI Workflows

## Contents
- Why CI is the source of truth
- GitHub Actions
- Script aliases (the most common blind spot)
- GitLab CI
- CircleCI
- Where versions are pinned
- Gates that are not `run:` steps
- Deciding which gates apply to the target path

## Why CI is the source of truth

A repository's config files describe what *someone once intended*. The CI
workflow describes what *blocks a merge today*. When they disagree, conform to
CI and flag the difference — never remediate against a config no job invokes.

Three recurring disagreements, and the correct response to each:

| Situation | Response |
|---|---|
| Config exists, CI never invokes it | Advisory only. Report; do not remediate. |
| CI invokes a tool with no config | The tool's defaults are the standard. Do not add a config file. |
| CI overrides config on the command line (`--select`, `--config`) | The command line wins. Read the flags, not the file. |

## GitHub Actions

Gates live in `.github/workflows/*.yml` under `jobs.<id>.steps[].run`. Both
forms occur and both must be read:

```yaml
- name: Lint
  run: ruff check .              # inline

- name: Checks
  run: |                         # block scalar — often several gates
    ruff check .
    ruff format --check .
    mypy src
```

Also handle:

- **Backslash continuations.** A `pip install foo \` / `bar pytest ruff` pair
  reads as a bare tool list once split by line, and gets misreported as a test
  gate. Join continuations before matching.
- **`working-directory:`** — the gate applies to that subtree, not the repo
  root. A monorepo's real scope lives here.
- **`continue-on-error: true`** — the step runs but does not block a merge.
  Treat as advisory, not a gate.
- **`if:` conditions** — a step gated on `github.event_name == 'push'` may not
  run on the PR the user cares about.
- **Matrix jobs** — `strategy.matrix` multiplies one step across versions. The
  gate is the same command; the *versions* are what vary, which matters for
  Step 2 pinning.

## Script aliases (the most common blind spot)

Most JS/TS repos never name the linter in CI:

```yaml
- run: npm ci
- run: npm run lint
- run: npm test
```

None of those contain the string `eslint`. Resolve through `package.json`:

```json
{ "scripts": { "lint": "eslint .", "test": "vitest run" } }
```

`npm test` / `yarn test` are implicit aliases for the `test` script — there is
no `run` keyword to match on. Aliases also chain (`"ci": "npm run lint && npm
run test"`), so resolution must recurse.

The same applies to `make lint`, `just check`, `task test`, `uv run lint`, and
`poetry run lint` — read the Makefile/justfile target body.

Distinguish package-manager *subcommands* from script names: `npm publish`,
`npm pack`, `npm version`, `npm ci` are not aliases and are not gates.

`scripts/extract_repo_rules.py` does this resolution and reports anything it
could not expand under `unresolved_aliases`. Those are blind spots — read the
script body yourself rather than assuming the gate is absent.

## GitLab CI

`.gitlab-ci.yml` puts commands in `script:`, `before_script:`, and
`after_script:` lists. Only `script:` entries are gates; `before_script:` is
setup. Jobs with `allow_failure: true` are advisory. Watch for `extends:` and
YAML anchors (`<<: *defaults`), which move the real command list elsewhere in
the file.

## CircleCI

`.circleci/config.yml` uses `jobs.<id>.steps[].run`, which may be a string or
a map with a `command:` key. Orbs (`orbs:`) hide their steps in an external
package — treat an orb-provided step as `UNRESOLVED_EXTERNAL`.

## Where versions are pinned

In descending order of authority:

1. **Lockfile** — `package-lock.json`, `pnpm-lock.yaml`, `uv.lock`,
   `poetry.lock`, `Cargo.lock`, `go.sum`. Proof of an actual resolution.
2. **`.pre-commit-config.yaml` `rev:`** — exact, per-hook, and what pre-commit
   will really run.
3. **Pinned action inputs** — `actions/setup-node` `node-version`,
   `actions/setup-python` `python-version`, `astral-sh/setup-uv` `version`.
4. **Explicit install pins in a `run:` step** — `pip install "ruff==0.15.17"`.
   Common and authoritative when present.
5. **Manifest ranges** — `devDependencies`, `[tool.ruff]`. Weakest: `^3.2.0`
   does not say what CI resolved.

If none resolve, record the tool as `UNPINNED` and route execution through the
repo's own runner rather than a global binary.

## Gates that are not `run:` steps

Easy to miss, and they block merges just as hard:

- **Required status checks / branch protection** — configured in repo
  settings, invisible in the workflow file. Check `gh api repos/{owner}/{repo}/branches/{branch}/protection`
  when the user has access.
- **Bot reviewers** — CodeRabbit, Sonar, Codecov thresholds posted as checks.
- **`actions/dependency-review-action`**, license scanners, CLA bots.
- **Composite / reusable workflows** — `uses: org/repo/.github/workflows/x.yml@v1`
  runs gates defined in another repository. Record as `UNRESOLVED_EXTERNAL`
  and ask for the command list; do not guess.

## Deciding which gates apply to the target path

A gate applies if any is true:

- Its command's path argument contains the target (or is `.` / omitted).
- Its `working-directory` is an ancestor of the target.
- Its workflow `on.paths` filter matches files inside the target.
- The tool's own config `include`/`exclude` covers the target's file types.

A gate does **not** apply if the linter config already excludes the path — the
usual case for `vendor/`, `generated/`, `dist/`, and `node_modules/`. When the
target is already excluded, the correct outcome is no remediation; say so
rather than reformatting files CI never inspects.
