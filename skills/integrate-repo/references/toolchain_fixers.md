# Toolchain Check & Fix Flags

## Contents
- How to read this file
- Python
- JavaScript / TypeScript
- Go
- Rust
- JVM
- Competing formatter pairs
- What autofixers do NOT resolve
- Running at the version CI uses

## How to read this file

Two columns matter per tool: the **check** invocation (Step 3, read-only, must
never modify files) and the **fix** invocation (Step 4). Where a tool has no
fix mode, it is a verifier — its findings go to the `manual` bucket.

Scope every command to the target path. Where a tool has no path argument,
that is noted; those need `git ls-files` piping instead.

## Python

| Tool | Check | Fix | Stage |
|---|---|---|---|
| ruff (lint) | `ruff check <path>` | `ruff check --fix <path>` | 3 |
| ruff (imports) | `ruff check --select I <path>` | `ruff check --select I --fix <path>` | 2 |
| ruff (format) | `ruff format --check <path>` | `ruff format <path>` | 4 |
| black | `black --check --diff <path>` | `black <path>` | 4 |
| isort | `isort --check-only --diff <path>` | `isort <path>` | 2 |
| pyupgrade | `pyupgrade --py310-plus <files>` (prints) | same, rewrites in place | 1 |
| flake8 | `flake8 <path>` | none — verifier | — |
| pylint | `pylint <path>` | none — verifier | — |
| mypy | `mypy <path>` | none — verifier | — |
| pyright | `pyright <path>` | none — verifier | — |

`ruff check --fix` applies only rules marked auto-fixable; `--unsafe-fixes`
adds more but can change behavior — never enable it during a compliance pass.

## JavaScript / TypeScript

| Tool | Check | Fix | Stage |
|---|---|---|---|
| eslint | `eslint <path>` | `eslint --fix <path>` | 3 |
| eslint (imports) | `eslint --rule 'import/order: error' <path>` | `--fix` | 2 |
| prettier | `prettier --check <path>` | `prettier --write <path>` | 4 |
| biome (lint) | `biome lint <path>` | `biome lint --write <path>` | 3 |
| biome (format) | `biome format <path>` | `biome format --write <path>` | 4 |
| biome (both) | `biome ci <path>` | `biome check --write <path>` | 3+4 |
| tsc | `tsc --noEmit` | none — verifier | — |

`tsc` takes no path argument — it type-checks the whole `tsconfig.json`
project. To scope it, point at the nearest `tsconfig` with
`tsc --noEmit -p <dir>/tsconfig.json`, or accept whole-project output and
filter to the target path when reporting.

Always invoke through `npx --no-install` (or `pnpm exec` / `yarn exec`) so the
repo's pinned version runs. A bare `eslint` resolves to whatever is global.

## Go

| Tool | Check | Fix | Stage |
|---|---|---|---|
| gofmt | `gofmt -l <path>` | `gofmt -w <path>` | 4 |
| gofumpt | `gofumpt -l <path>` | `gofumpt -w <path>` | 4 |
| goimports | `goimports -l <path>` | `goimports -w <path>` | 2 |
| golangci-lint | `golangci-lint run <path>/...` | `golangci-lint run --fix <path>/...` | 3 |
| go vet | `go vet ./<path>/...` | none — verifier | — |

`gofmt -l` lists offending files and exits `0` even when it finds them — check
for non-empty output, not the exit code. This trips up naive CI replication.

## Rust

| Tool | Check | Fix | Stage |
|---|---|---|---|
| rustfmt | `cargo fmt --check` | `cargo fmt` | 4 |
| clippy | `cargo clippy -- -D warnings` | `cargo clippy --fix --allow-dirty` | 3 |

`cargo fmt` and `cargo clippy` operate per-crate, not per-path. Scope with
`-p <crate>` when the target is one crate in a workspace.

## JVM

| Tool | Check | Fix | Stage |
|---|---|---|---|
| spotless | `./gradlew spotlessCheck` | `./gradlew spotlessApply` | 4 |
| checkstyle | `./gradlew checkstyleMain` | none — verifier | — |
| ktlint | `ktlint <path>` | `ktlint --format <path>` | 3+4 |

Gradle/Maven tasks are project-scoped. Use `--tests`/module selectors rather
than a filesystem path.

## Competing formatter pairs

Both active means churn on every save. Keep whichever CI invokes; disable the
other for the target path.

| Pair | Overlap | Disable the loser via |
|---|---|---|
| Prettier + Biome | JS/TS/JSON/CSS | `.prettierignore` or `biome.json` `files.ignore` |
| Black + `ruff format` | Python | remove the unused one from the hook config |
| gofmt + gofumpt | Go | gofumpt is a superset — keep gofumpt alone |
| ESLint stylistic rules + Prettier | JS/TS layout | `eslint-config-prettier` to switch the rules off |

The ESLint/Prettier case is the subtle one: without `eslint-config-prettier`,
ESLint's stylistic rules and Prettier disagree permanently and `--fix` and
`--write` will undo each other on every run.

## What autofixers do NOT resolve

Route these straight to the `manual` bucket in Step 3 — looping the fixer will
not converge:

- Type errors (`mypy`, `tsc`, `pyright`) — a fix changes types or logic.
- Cyclomatic-complexity and function-length rules.
- Naming-convention rules where the fix is a rename with call-site updates.
- Forbidden-import / dependency-boundary violations — the fix is architectural.
- Missing test coverage against a threshold.
- Most security rules (`bandit`, `gosec`, `semgrep`) — each needs judgment.
- Docstring *content* rules; only presence/format is sometimes fixable.

## Running at the version CI uses

Prefer, in order:

1. `pre-commit run --all-files` (or `--files <paths>`) — uses the `rev:` pins.
2. The repo's own runner: `npx --no-install`, `pnpm exec`, `uv run`,
   `poetry run`, `./gradlew`.
3. A version-pinned one-shot: `uvx ruff@0.6.9`, `npx eslint@9.12.0`.
4. A globally installed binary — last resort, and record it as `UNPINNED`.

A formatter one minor version off CI produces a different result. This is the
most common cause of "clean locally, red in CI"; it is a version problem, not
a code problem, and reformatting the code will not fix it.
