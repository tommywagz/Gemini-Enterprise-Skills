#!/usr/bin/env bash
# Regression tests for scripts/remediate_compliance.sh guard and stage helpers.
#
# Covers the two failure modes that made the template unusable on a first run:
#   1. untracked files (including the generated scripts themselves) counted as
#      a dirty tree, so the script refused to start;
#   2. a fixer exiting non-zero on leftover unfixable violations treated as a
#      fatal stage failure, aborting before the formatter stage.
# Both are asserted here alongside the safety properties they must not weaken.
#
# Usage: tests/test_runner_guards.sh
# Exit: 0 = all assertions passed, 1 = at least one failed.

set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$SKILL_DIR/scripts/remediate_compliance.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0
check() { # check <description> <expected> <actual>
  if [[ "$2" == "$3" ]]; then
    printf 'PASS  %s\n' "$1"; PASS=$((PASS + 1))
  else
    printf 'FAIL  %s (expected %s, got %s)\n' "$1" "$2" "$3"; FAIL=$((FAIL + 1))
  fi
}

new_repo() { # new_repo <name> -> prints path
  local d="$WORK/$1"
  mkdir -p "$d/vendor"
  git -C "$d" init -q
  printf 'x = 1\n' > "$d/vendor/mod.py"
  git -C "$d" add -A
  git -C "$d" -c user.email=t@example.com -c user.name=t commit -qm init
  printf '%s' "$d"
}

# 1. The generated script lives in the tree and must not block the run.
repo="$(new_repo untracked)"
cp "$TEMPLATE" "$repo/vendor/../remediate_compliance.sh"
chmod +x "$repo/remediate_compliance.sh"
(cd "$repo" && ./remediate_compliance.sh vendor >/dev/null 2>&1)
check "untracked artifacts do not block the run" 0 $?

# 2. A modified TRACKED file must still block: that is what a fixer destroys.
repo="$(new_repo tracked)"
printf 'x = 2\n' > "$repo/vendor/mod.py"
(cd "$repo" && "$TEMPLATE" vendor >/dev/null 2>&1)
check "modified tracked file still blocks" 2 $?

# 3. --force overrides that block.
(cd "$repo" && "$TEMPLATE" vendor --force >/dev/null 2>&1)
check "--force overrides the tracked-file block" 0 $?

# 4. --dry-run writes nothing, so it runs even with tracked modifications.
(cd "$repo" && "$TEMPLATE" vendor --dry-run >/dev/null 2>&1)
check "--dry-run runs on a dirty tree" 0 $?

# 5. Untracked files under the target are named: a commit-based checkpoint
#    cannot restore one a fixer rewrites in place.
repo="$(new_repo warn)"
printf 'y = 1\n' > "$repo/vendor/untracked.py"
warning="$(cd "$repo" && "$TEMPLATE" vendor 2>&1 >/dev/null | grep -c 'not covered by the checkpoint')"
check "untracked file under target is warned about" 1 "$warning"

# 6. `fix` tolerates a non-zero fixer and lets later stages run;
#    `run` stays fatal. Simulated without external tools.
repo="$(new_repo helpers)"
python3 - "$TEMPLATE" "$repo/filled.sh" <<'PY'
import sys
tpl = open(sys.argv[1]).read()
tpl = tpl.replace('# e.g. fix "ruff --fix" ruff check --fix "$TARGET"',
                  'fix "leaves violations" false\ntouch "$REPO_ROOT/stage3.marker"')
tpl = tpl.replace('# e.g. fix "ruff format" ruff format "$TARGET"',
                  'fix "formatter" touch "$REPO_ROOT/stage4.marker"')
open(sys.argv[2], "w").write(tpl)
PY
chmod +x "$repo/filled.sh"
(cd "$repo" && ./filled.sh vendor >/dev/null 2>&1)
check "non-zero fixer does not abort the run" 0 $?
check "stage after a non-zero fixer still runs" 0 $([[ -f "$repo/stage4.marker" ]] && echo 0 || echo 1)

# 7. `run` must remain fatal for genuinely fatal steps.
repo="$(new_repo fatal)"
python3 - "$TEMPLATE" "$repo/filled.sh" <<'PY'
import sys
tpl = open(sys.argv[1]).read()
tpl = tpl.replace('# e.g. fix "ruff --fix" ruff check --fix "$TARGET"',
                  'run "fatal step" false')
tpl = tpl.replace('# e.g. fix "ruff format" ruff format "$TARGET"',
                  'fix "formatter" touch "$REPO_ROOT/stage4.marker"')
open(sys.argv[2], "w").write(tpl)
PY
chmod +x "$repo/filled.sh"
(cd "$repo" && ./filled.sh vendor >/dev/null 2>&1)
check "run stays fatal" 1 $?
check "no stage runs after a fatal run" 1 $([[ -f "$repo/stage4.marker" ]] && echo 0 || echo 1)

# 8. Refuse outside a git repository: there would be no undo path.
mkdir -p "$WORK/nogit/vendor"
(cd "$WORK/nogit" && "$TEMPLATE" vendor >/dev/null 2>&1)
check "refuses outside a git repository" 2 $?

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
