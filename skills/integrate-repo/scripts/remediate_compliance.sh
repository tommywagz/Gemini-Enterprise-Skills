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
# --dry-run writes nothing, so a dirty tree is harmless there.
if [[ "$DRY_RUN" -eq 0 && -n "$(git status --porcelain)" && "$FORCE" -ne 1 ]]; then
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
    echo "    restore with: git reset --hard ${CHECKPOINT_REF}" >&2
    return 1
  fi
}

if [[ "$CHECKPOINT" -eq 1 && "$DRY_RUN" -eq 0 ]]; then
  git branch "$CHECKPOINT_REF" >/dev/null 2>&1 || true
  echo "checkpoint: ${CHECKPOINT_REF}  (undo: git reset --hard ${CHECKPOINT_REF})"
fi

echo "target:     ${TARGET}"
echo "repo root:  ${REPO_ROOT}"
echo

# --- Stage 1: codemods / syntax upgrades -------------------------------------
# Rewrite AST shapes first; everything downstream depends on the result.
# e.g. run "pyupgrade" pyupgrade --py310-plus $(git ls-files "$TARGET/*.py")

# --- Stage 2: import sorting -------------------------------------------------
# Changes line counts, so it must precede anything line-sensitive.
# e.g. run "isort" ruff check --select I --fix "$TARGET"

# --- Stage 3: linter autofix -------------------------------------------------
# May emit code that is correct but unformatted — hence stage 4 after it.
# e.g. run "ruff --fix" ruff check --fix "$TARGET"
# e.g. run "eslint --fix" npx --no-install eslint --fix "$TARGET"

# --- Stage 4: formatter (ALWAYS LAST) ----------------------------------------
# e.g. run "ruff format" ruff format "$TARGET"
# e.g. run "prettier" npx --no-install prettier --write "$TARGET"

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
