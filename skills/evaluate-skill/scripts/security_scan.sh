#!/usr/bin/env bash
# Pattern-based security scan for a skill directory. Prints categorized
# findings and a suggested risk tier per references/security_review.md.
# This is a lead list for manual verification (Steps 3-6 of that file), not
# a verdict — it cannot judge adversarial prose, and a hit inside a fenced
# example that's never executed will still show up here.
#
# Usage: security_scan.sh <skill-dir>

set -euo pipefail

SKILL_DIR="${1:?Usage: security_scan.sh <skill-dir>}"

if [[ ! -d "$SKILL_DIR" ]]; then
  echo "Error: '$SKILL_DIR' is not a directory" >&2
  exit 1
fi

echo "Security scan: $SKILL_DIR"
echo "=================================================="

SCRIPTS=$(find "$SKILL_DIR" -type f \( -name '*.py' -o -name '*.sh' -o -name '*.js' -o -name '*.ts' \) 2>/dev/null || true)

NETWORK_HITS=$(grep -rniE 'https?://|requests\.(get|post)|urllib|curl[[:space:]]|fetch\(|wget[[:space:]]|aws[[:space:]]+s3([[:space:]]|api)' "$SKILL_DIR" 2>/dev/null || true)

HIGH_CLI_HITS=$(grep -rniE 'aws[[:space:]]|kubectl[[:space:]]+(apply|delete)|curl[[:space:]]' "$SKILL_DIR" 2>/dev/null || true)

TRAVERSAL_HITS=$(grep -rn '\.\./' "$SKILL_DIR" 2>/dev/null || true)

CRED_HITS=$(grep -rniE "AKIA[0-9A-Z]{16}|-----BEGIN[A-Z ]*PRIVATE KEY-----|(api[_-]?key|secret|password|token)[[:space:]]*[:=][[:space:]]*[\"']?[A-Za-z0-9/+_-]{16,}" "$SKILL_DIR" 2>/dev/null || true)

echo
echo "-- Scripts present (Medium indicator) --"
echo "${SCRIPTS:-(none)}"

echo
echo "-- Network / external call patterns (High indicator) --"
echo "${NETWORK_HITS:-(none)}"

echo
echo "-- High-privilege CLI patterns (High indicator) --"
echo "${HIGH_CLI_HITS:-(none)}"

echo
echo "-- Path traversal patterns (Critical indicator) --"
echo "${TRAVERSAL_HITS:-(none)}"

echo
echo "-- Possible hardcoded credentials (Critical indicator) --"
echo "${CRED_HITS:-(none)}"

echo
echo "=================================================="
if [[ -n "$TRAVERSAL_HITS" || -n "$CRED_HITS" ]]; then
  TIER="Critical"
elif [[ -n "$NETWORK_HITS" || -n "$HIGH_CLI_HITS" ]]; then
  TIER="High"
elif [[ -n "$SCRIPTS" ]]; then
  TIER="Medium"
else
  TIER="Low"
fi
echo "Suggested risk tier: $TIER"
echo "(pattern match only — manually verify per references/security_review.md before finalizing)"
