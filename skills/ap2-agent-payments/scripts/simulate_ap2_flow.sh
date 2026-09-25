#!/usr/bin/env bash
# Run (or plan) one of the four AP2 reference scenarios from
# github.com/google-agentic-commerce/AP2.
#
# It resolves the repo, checks prerequisites, prints the role/port map and the
# exact upstream command, then executes it unless --dry-run is given.
#
# Usage:
#   simulate_ap2_flow.sh --flow <human-present|human-not-present>
#                        [--rail <cards|x402>] [--repo PATH]
#                        [--dry-run] [--broadcast] [--] [extra args...]
#
#   --flow       required. Which AP2 mode to run.
#   --rail       cards (default) or x402.
#   --repo       path to a clone of google-agentic-commerce/AP2.
#                Falls back to $AP2_REPO, then ./AP2, then parent directory AP2.
#   --dry-run    print the plan and exit 0 without running anything.
#   --broadcast  human-not-present + x402 only: pass
#                --enable_broadcast_on_chain to the upstream runner.
#   --           everything after this is forwarded to the upstream run.sh.
#
# Exit codes: 0 ok · 1 prerequisite/verification failure · 2 usage error.
#
# This script never clones, never writes into the repo, and never sets
# credentials. If the repo is missing it tells you the clone command and stops.

set -euo pipefail

FLOW=""
RAIL="cards"
REPO="${AP2_REPO:-}"
DRY_RUN=0
BROADCAST=0
EXTRA=()

die() { printf 'error: %s\n' "$1" >&2; exit "${2:-2}"; }
say() { printf '%s\n' "$1"; }
hdr() { printf '\n== %s ==\n' "$1"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --flow)      FLOW="${2:-}"; shift 2 ;;
    --rail)      RAIL="${2:-}"; shift 2 ;;
    --repo)      REPO="${2:-}"; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    --broadcast) BROADCAST=1; shift ;;
    -h|--help)   sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --)          shift; EXTRA=("$@"); break ;;
    *)           die "unknown argument: $1" ;;
  esac
done

case "$FLOW" in
  human-present|human-not-present) ;;
  "") die "--flow is required (human-present | human-not-present)" ;;
  *)  die "--flow must be human-present or human-not-present (got: $FLOW)" ;;
esac
case "$RAIL" in
  cards|x402) ;;
  *) die "--rail must be cards or x402 (got: $RAIL)" ;;
esac
if [[ $BROADCAST -eq 1 && ( "$FLOW" != "human-not-present" || "$RAIL" != "x402" ) ]]; then
  die "--broadcast only applies to --flow human-not-present --rail x402"
fi

# ---------------------------------------------------------------- repo
if [[ -z "$REPO" ]]; then
  for candidate in "./AP2" "$(dirname "$PWD")/AP2" "$HOME/AP2"; do
    if [[ -d "$candidate/code/samples/python/scenarios" ]]; then REPO="$candidate"; break; fi
  done
fi
if [[ -z "$REPO" ]]; then
  cat >&2 <<'EOF'
error: could not locate a clone of google-agentic-commerce/AP2.

Clone it, then re-run with --repo or AP2_REPO:

    git clone https://github.com/google-agentic-commerce/AP2.git
    AP2_REPO=$PWD/AP2 simulate_ap2_flow.sh --flow human-present --rail cards
EOF
  exit 2
fi
[[ -d "$REPO" ]] || die "--repo path does not exist: $REPO"
REPO="$(cd "$REPO" && pwd)"
SCENARIOS="$REPO/code/samples/python/scenarios/a2a"
[[ -d "$SCENARIOS" ]] || die "not an AP2 checkout (missing $SCENARIOS): $REPO"

# ------------------------------------------------------- runner selection
# Quirk: human-present/x402 ships no run.sh. It reuses the cards runner with
# --payment-method x402. Upstream README omits the leading `bash`.
RUNNER=""
RUNNER_ARGS=()
if [[ "$FLOW" == "human-present" ]]; then
  RUNNER="$SCENARIOS/human-present/cards/run.sh"
  [[ "$RAIL" == "x402" ]] && RUNNER_ARGS+=(--payment-method x402)
else
  RUNNER="$SCENARIOS/human-not-present/$RAIL/run.sh"
  [[ $BROADCAST -eq 1 ]] && RUNNER_ARGS+=(--enable_broadcast_on_chain)
fi
[[ ${#EXTRA[@]} -gt 0 ]] && RUNNER_ARGS+=("${EXTRA[@]}")

if [[ ! -f "$RUNNER" ]]; then
  die "expected runner not found: $RUNNER
The upstream layout may have changed. Check:
  $SCENARIOS/$FLOW/" 1
fi

# ------------------------------------------------------------ prereqs
FAILURES=0
check_cmd() {
  local cmd="$1" why="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '  ok      %-8s %s\n' "$cmd" "$(command -v "$cmd")"
  else
    printf '  MISSING %-8s %s\n' "$cmd" "$why"
    FAILURES=$((FAILURES + 1))
  fi
}

hdr "prerequisites"
check_cmd uv "required: the samples are a uv workspace"
check_cmd python3 "required: Python >= 3.11"
if command -v python3 >/dev/null 2>&1; then
  PYVER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    printf '  ok      %-8s %s\n' "python" "$PYVER >= 3.11"
  else
    printf '  MISSING %-8s %s\n' "python" "$PYVER is below the required 3.11"
    FAILURES=$((FAILURES + 1))
  fi
fi
if [[ "$FLOW" == "human-not-present" ]]; then
  check_cmd npm  "required: the runner builds and serves the web client"
  check_cmd curl "required: used to trigger the autonomous purchase"
  check_cmd lsof "required: the runner uses it to free stale ports"
fi

# Model credentials: either an AI Studio key or Vertex AI configuration.
if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
  printf '  ok      %-8s GOOGLE_API_KEY is set\n' "creds"
elif [[ "${GOOGLE_GENAI_USE_VERTEXAI:-}" == "true" ]]; then
  if [[ -n "${GOOGLE_CLOUD_PROJECT:-}" && -n "${GOOGLE_CLOUD_LOCATION:-}" ]]; then
    printf '  ok      %-8s Vertex AI (%s / %s), ADC required\n' \
      "creds" "$GOOGLE_CLOUD_PROJECT" "$GOOGLE_CLOUD_LOCATION"
  else
    printf '  MISSING %-8s GOOGLE_GENAI_USE_VERTEXAI=true needs GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION\n' "creds"
    FAILURES=$((FAILURES + 1))
  fi
elif [[ -f "$REPO/.env" ]]; then
  printf '  ok      %-8s %s exists; the runner loads it with --env-file\n' "creds" "$REPO/.env"
else
  printf '  MISSING %-8s set GOOGLE_API_KEY, or GOOGLE_GENAI_USE_VERTEXAI=true plus\n' "creds"
  printf '          %-8s GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION, or add %s/.env\n' "" "$REPO"
  FAILURES=$((FAILURES + 1))
fi

# ------------------------------------------------------------- role map
hdr "roles"
if [[ "$FLOW" == "human-present" ]]; then
  cat <<'EOF'
  Shopping Agent (ADK dev UI)   http://0.0.0.0:8000/dev-ui   -> pick "shopping_agent"
  Merchant Agent                http://localhost:8001/a2a/merchant_agent
  Credentials Provider          http://localhost:8002/a2a/credentials_provider
  Merchant Payment Processor    http://localhost:8003/a2a/merchant_payment_processor_agent
EOF
  if [[ "$RAIL" == "cards" ]]; then
    say "  Step-up: the card flow prompts for a mock OTP -> 123"
  else
    say "  Step-up: SKIPPED on the x402 demo path. That is a demo shortcut, not a design."
  fi
else
  say "  Shopping Agent (shopping_agent_v2)  http://localhost:8080/a2a/shopping_agent/.well-known/agent-card.json"
  say "  Merchant trigger                    http://localhost:8081"
  if [[ "$RAIL" == "cards" ]]; then
    say "  Credentials Provider                http://localhost:8082"
    say "  Merchant Payment Processor          http://localhost:8083"
  else
    say "  x402 PSP trigger                    http://localhost:8084"
    say "  Roles swapped: x402_credentials_provider_mcp and x402_psp_mcp"
  fi
  say "  Web client                          http://localhost:5173"
  say ""
  say "  Trigger the autonomous purchase once the stack is up:"
  say '    curl -X POST "http://localhost:8081/trigger-price-drop?item_id=<item_id>&price=<price>&stock=10"'
fi

# --------------------------------------------------------- what to watch
hdr "what to verify in this run"
cat <<'EOF'
  1. The mandates the flow mints, and whether they are open, closed, or both.
  2. That the Payment Mandate transaction_id equals the Checkout Mandate
     checkout_hash. Capture the chain and run:
       verify_mandate_signature.py <chain-file> --checkout-jwt-file <checkout.jwt>
  3. Which role receives which credential. The Merchant must never receive the
     Payment Mandate; the Credential Provider must never receive the line items.
  4. That both receipts are returned and persisted.
EOF
if [[ "$RAIL" == "x402" ]]; then
  cat <<'EOF'
  5. x402 caveat, stated upstream: the current x402 extension does not yet mint
     every AP2 mandate. Do not report full AP2 authorization coverage from an
     x402 sample run.
EOF
fi

# ------------------------------------------------------------- execute
hdr "command"
printf '  cd %s\n' "$REPO"
printf '  bash %s' "${RUNNER#$REPO/}"
for arg in ${RUNNER_ARGS+"${RUNNER_ARGS[@]}"}; do printf ' %q' "$arg"; done
printf '\n'

if [[ $DRY_RUN -eq 1 ]]; then
  hdr "dry run"
  if [[ $FAILURES -gt 0 ]]; then
    say "  Plan printed. $FAILURES prerequisite(s) missing — resolve them before a real run."
  else
    say "  Plan printed. Prerequisites satisfied. Re-run without --dry-run to execute."
  fi
  exit 0
fi

if [[ $FAILURES -gt 0 ]]; then
  die "$FAILURES prerequisite(s) missing; refusing to run. Re-run with --dry-run to see the plan." 1
fi

hdr "running"
cd "$REPO"
exec bash "$RUNNER" ${RUNNER_ARGS+"${RUNNER_ARGS[@]}"}
