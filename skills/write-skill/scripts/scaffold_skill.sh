#!/usr/bin/env bash
# Scaffold a new Agent Skill folder in the standard format.
#
# Usage:
#   scaffold_skill.sh <skill-name> [output-dir] [components]
#
#   <skill-name>   required. lowercase letters, numbers, hyphens only.
#   [output-dir]   optional. where to create the skill folder. default: current dir.
#   [components]   optional. comma-separated subset of: references,scripts,assets
#                  default: references,scripts,assets. pass "" for none.
#
# Example:
#   scaffold_skill.sh k8s-pod-debugger ./skills references,scripts

set -euo pipefail

SKILL_NAME="${1:?Usage: scaffold_skill.sh <skill-name> [output-dir] [components]}"
OUT_DIR="${2:-.}"
COMPONENTS="${3:-references,scripts,assets}"

if [[ ! "$SKILL_NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "Error: skill name must be lowercase letters, numbers, and hyphens only (got: '$SKILL_NAME')" >&2
  exit 1
fi

SKILL_DIR="$OUT_DIR/$SKILL_NAME"
if [[ -e "$SKILL_DIR" ]]; then
  echo "Error: '$SKILL_DIR' already exists — refusing to overwrite" >&2
  exit 1
fi

mkdir -p "$SKILL_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../assets/skill_template.md"

if [[ -f "$TEMPLATE" ]]; then
  sed "s/{{SKILL_NAME}}/$SKILL_NAME/g" "$TEMPLATE" > "$SKILL_DIR/SKILL.md"
else
  printf -- '---\nname: %s\ndescription: TODO\n---\n\n- Overview\nTODO\n' "$SKILL_NAME" > "$SKILL_DIR/SKILL.md"
fi

if [[ -n "$COMPONENTS" ]]; then
  IFS=',' read -ra PARTS <<< "$COMPONENTS"
  for part in "${PARTS[@]}"; do
    mkdir -p "$SKILL_DIR/$part"
  done
fi

echo "Scaffolded skill at: $SKILL_DIR"
find "$SKILL_DIR" | sort
