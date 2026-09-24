#!/usr/bin/env bash
# Template remediation runner emitted by the `integrate-repo` skill (Step 5).
#
# Applies the host repo's auto-fixable gates to ONE target path, in the only
# order that converges: codemods -> import sort -> lint --fix -> format.
# Running the formatter earlier lets the linter reflow it, and CI then fails
# on formatting.
#
# The agent fills in the GATE_* arrays from the scanner's gate list. Every
# command must be scoped to "$TARGET" — a repo-wide fixer buries the files
# under review in an unreviewable diff.
#
# Usage:
#   remediate_compliance.sh <target-path> [--force] [--dry-run] [--no-checkpoint]
#
# Exit codes: 0 = all stages applied, 1 = a stage failed, 2 = usage/guard error.

set -euo pipefail

TARGET=""
FORCE=0
DRY_RUN=0
CHECKPOINT=1

usage() {
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-2}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)         FORCE=1 ;;
    --dry-run)       DRY_RUN=1 ;;
    --no-checkpoint) CHECKPOINT=0 ;;
    -h|--help)       usage 0 ;;
    -*)              echo "unknown flag: $1" >&2; usage 2 ;;
    *)               TARGET="$1" ;;
  esac
  shift
done

[[ -n "$TARGET" ]] || { echo "error: target path required" >&2; usage 2; }
[[ -e "$TARGET" ]] || { echo "error: no such path: $TARGET" >&2; exit 2; }

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: not inside a git repository — refusing to run fixers without an undo path" >&2
  exit 2
}
cd "$REPO_ROOT"

# --- Guard: never rewrite files on top of uncommitted work silently ----------
# Only TRACKED modifications are at risk: those are what a fixer can overwrite
# and what the checkpoint restores. Untracked files must not block the run —
# the generated scripts and the rules JSON are themselves untracked, so
# counting them would make this script refuse on every first run.
# --dry-run writes nothing, so a dirty tree is harmless there.
if [[ "$DRY_RUN" -eq 0 && -n "$(git status --porcelain --untracked-files=no)" && "$FORCE" -ne 1 ]]; then
  cat >&2 <<'EOF'
error: working tree is dirty.

Autofixers rewrite files in place. Commit or stash your work first, or pass
--force if you accept that this run will be mixed into your uncommitted diff.
EOF
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CHECKPOINT_REF="pre-remediate/${STAMP}"

run() {
  # run <stage-label> <command...>
  local label="$1"; shift
  echo "==> ${label}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '    (dry-run) %q ' "$@"; echo
    return 0
  fi
  if ! "$@"; then
    echo "!!! stage failed: ${label}" >&2
    echo "    if this left the tree in a bad state, restore with:" >&2
    echo "      git reset --hard ${CHECKPOINT_REF}" >&2
    return 1
  fi
}

fix() {
  # fix <stage-label> <command...>
  #
  # Use for stages 1-4 (codemods, import sort, linter --fix, formatter). A
  # fixer exits non-zero whenever unfixable violations remain, which is the
  # normal case in any real repository — it is NOT a stage failure, and must
  # not abort the run before the formatter has had its turn. Whether the
  # target actually passes is decided by run_ci_preflight.sh in Step 6, not
  # here. Use `run` instead for stages that must be fatal, such as `git mv`.
  local label="$1"; shift
  echo "==> ${label}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '    (dry-run) %q ' "$@"; echo
    return 0
  fi
  if ! "$@"; then
    echo "    note: ${label} left violations it cannot fix automatically."
    echo "          Expected — these are the 'manual' class; run_ci_preflight.sh lists them."
  fi
  return 0
}

if [[ "$CHECKPOINT" -eq 1 && "$DRY_RUN" -eq 0 ]]; then
  git branch "$CHECKPOINT_REF" >/dev/null 2>&1 || true
  echo "checkpoint: ${CHECKPOINT_REF}  (undo: git reset --hard ${CHECKPOINT_REF})"
fi

# The checkpoint is a commit, so it cannot restore an UNTRACKED file a fixer
# rewrites in place. Name them rather than blocking: the run is still safe for
# everything git is tracking.
if [[ "$DRY_RUN" -eq 0 ]]; then
  untracked="$(git ls-files --others --exclude-standard -- "$TARGET")"
  if [[ -n "$untracked" ]]; then
    echo "warning: untracked files under ${TARGET} are not covered by the checkpoint:" >&2
    printf '  %s\n' $untracked >&2
  fi
fi

echo "target:     ${TARGET}"
echo "repo root:  ${REPO_ROOT}"
echo

# --- Stage 1: codemods / syntax upgrades -------------------------------------
# Rewrite AST shapes first; everything downstream depends on the result.
# Stages 1-4 use `fix` (tolerates leftover unfixable violations), stage 5 uses
# `run` (a failed rename or header injection IS fatal).
# e.g. fix "pyupgrade" pyupgrade --py310-plus $(git ls-files "$TARGET/*.py")

# --- Stage 2: import sorting -------------------------------------------------
# Changes line counts, so it must precede anything line-sensitive.
# e.g. fix "isort" ruff check --select I --fix "$TARGET"

# --- Stage 3: linter autofix -------------------------------------------------
# May emit code that is correct but unformatted — hence stage 4 after it.
# e.g. fix "ruff --fix" ruff check --fix "$TARGET"
# e.g. fix "eslint --fix" npx --no-install eslint --fix "$TARGET"

# --- Stage 4: formatter (ALWAYS LAST) ----------------------------------------
# e.g. fix "ruff format" ruff format "$TARGET"
# e.g. fix "prettier" npx --no-install prettier --write "$TARGET"

# --- Stage 5: mechanical fixes -----------------------------------------------
# Renames MUST use `git mv` so history survives:
#   run "rename" git mv "$TARGET/oldName.ts" "$TARGET/old-name.ts"
#
# License headers must be idempotent — check for the marker before writing, or
# reruns stack duplicates:
#   while IFS= read -r f; do
#     grep -q "SPDX-License-Identifier" "$f" || {
#       printf '%s\n%s\n' "$LICENSE_HEADER" "$(cat "$f")" > "$f"
#     }
#   done < <(git ls-files "$TARGET/*.py")

echo
echo "remediation complete."
if [[ "$DRY_RUN" -eq 0 ]]; then
  echo "review:  git diff --stat ${CHECKPOINT_REF}.."
  echo "verify:  ./run_ci_preflight.sh ${TARGET}"
  echo "undo:    git reset --hard ${CHECKPOINT_REF}"
fi
