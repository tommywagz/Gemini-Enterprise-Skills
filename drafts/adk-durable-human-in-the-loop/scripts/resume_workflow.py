#!/usr/bin/env python3
"""resume_workflow.py

Handles the external side of a durable ADK Human-in-the-Loop approval gate:
verifies a signed decision payload from a dashboard/reviewer, matches it
against a previously recorded pending ticket, and resumes the exact paused
ADK invocation via the documented `/run_sse` REST resume contract for
`LongRunningFunctionTool` (see references/adk_graph_hitl_api.md \u00a74 and
references/durable_hitl_patterns.md for why this is signature-verified and
idempotent).

This script has NO required third-party dependencies (stdlib only:
argparse, json, hmac, hashlib, http.server, urllib.request) so it can be
dry-run and unit-exercised with no `google-adk` install and no network
access. `jsonschema` is optional, for stricter schema validation than the
built-in manual checks.

Four subcommands:

  record-ticket   Record a pending approval (normally called by the tool
                  function itself, e.g. ask_for_approval, right after it
                  gets a function_call_id from ADK) and optionally print the
                  signed outbound webhook payload to send to the dashboard.

  verify          Verify a single inbound decision payload (file or stdin)
                  against assets/approval_response_schema.json and its HMAC
                  signature. Prints the verdict; makes no network call.

  resume          Verify an inbound decision payload AND build the /run_sse
                  resume request. --dry-run prints it; without --dry-run,
                  POSTs it to --adk-server-url.

  serve           Run a minimal HTTP server exposing POST /resume that runs
                  the full verify+resume flow per request. Reference
                  implementation only -- single-threaded, no TLS, no auth
                  beyond the payload signature. Put a real reverse proxy /
                  auth layer in front of this in production.

Usage:
    resume_workflow.py record-ticket --ticket-id t1 --app-name approval_gate_app \\
        --user-id user --session-id s_abc --invocation-id invocation-123 \\
        --function-call-id adk-13b8... --tool-name ask_for_approval \\
        --hint "Approve $2,500 reimbursement?" --secret-env-var HITL_WEBHOOK_SECRET \\
        --pending-store ./pending_approvals.json --emit-webhook

    resume_workflow.py resume --input-file decision.json \\
        --pending-store ./pending_approvals.json --secret-env-var HITL_WEBHOOK_SECRET \\
        --dry-run

    resume_workflow.py serve --pending-store ./pending_approvals.json \\
        --secret-env-var HITL_WEBHOOK_SECRET --adk-server-url http://localhost:8000 \\
        --port 8787 --dry-run

Exit codes: 0 = success, 1 = rejected (bad signature / expired / mismatched
ticket -- see stderr for which), 2 = usage/validation error.
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "assets"))
WEBHOOK_SCHEMA_PATH = os.path.join(ASSETS_DIR, "approval_webhook_schema.json")
RESPONSE_SCHEMA_PATH = os.path.join(ASSETS_DIR, "approval_response_schema.json")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_json(obj):
    """Deterministic JSON for signing: sorted keys, no extra whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sign(payload_without_signature, secret):
    mac = hmac.new(secret.encode("utf-8"), canonical_json(payload_without_signature).encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


def verify_signature(payload, secret):
    """Returns True/False. Never raises on a missing/malformed signature --
    treats that as verification failure, per references/durable_hitl_patterns.md \u00a73."""
    if not isinstance(payload, dict) or "signature" not in payload:
        return False
    claimed = payload["signature"]
    body = {k: v for k, v in payload.items() if k != "signature"}
    expected = sign(body, secret)
    try:
        return hmac.compare_digest(claimed, expected)
    except TypeError:
        return False


def get_secret(secret_env_var):
    secret = os.environ.get(secret_env_var)
    if not secret:
        print(f"error: environment variable {secret_env_var} is not set or empty. "
              f"Never pass the secret as a CLI flag (shell history / process list exposure).",
              file=sys.stderr)
        sys.exit(2)
    return secret


def validate_against_schema(payload, schema_path):
    """Full jsonschema validation if the package is installed; otherwise a
    minimal manual required-fields check, mirroring the pattern used across
    this repo's other skill scripts (e.g. adk-cross-session-knowledge-bank)."""
    errors = []
    try:
        import jsonschema
        with open(schema_path) as f:
            schema = json.load(f)
        validator = jsonschema.Draft202012Validator(schema)
        for err in validator.iter_errors(payload):
            errors.append(f"{list(err.path)}: {err.message}")
    except ImportError:
        with open(schema_path) as f:
            schema = json.load(f)
        for field in schema.get("required", []):
            if field not in payload:
                errors.append(f"missing required field '{field}'")
    return errors


class PendingStore:
    """Minimal JSON-file-backed store of open approval tickets. A reference
    implementation for local dev / small deployments -- swap for a real
    table in the same database backing DatabaseSessionService for
    production use (see references/durable_hitl_patterns.md \u00a72)."""

    def __init__(self, path):
        self.path = path

    def _load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path) as f:
            return json.load(f)

    def _save(self, data):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self.path)

    def put(self, ticket_id, record):
        data = self._load()
        data[ticket_id] = record
        self._save(data)

    def get(self, ticket_id):
        return self._load().get(ticket_id)

    def mark_resolved(self, ticket_id, decision):
        data = self._load()
        if ticket_id in data:
            data[ticket_id]["resolved"] = True
            data[ticket_id]["decision"] = decision
            self._save(data)


def build_webhook_payload(args):
    body = {
        "ticket_id": args.ticket_id,
        "app_name": args.app_name,
        "user_id": args.user_id,
        "session_id": args.session_id,
        "invocation_id": args.invocation_id,
        "function_call_id": args.function_call_id,
        "tool_name": args.tool_name,
        "hint": args.hint,
        "payload": json.loads(args.payload_json) if args.payload_json else {},
        "requested_at": now_iso(),
        "expires_at": args.expires_at,
        "response_url": args.response_url,
    }
    return body


def build_resume_request(record, response_payload):
    """Builds the exact /run_sse resume body documented in
    references/adk_graph_hitl_api.md \u00a74."""
    function_response = {
        "id": record["function_call_id"],
        "name": record["tool_name"],
        "response": {
            "status": response_payload["decision"],
            "ticket-id": response_payload["ticket_id"],
            **response_payload.get("response_payload", {}),
        },
    }
    return {
        "app_name": record["app_name"],
        "user_id": record["user_id"],
        "session_id": record["session_id"],
        "invocation_id": record["invocation_id"],
        "new_message": {
            "parts": [{"function_response": function_response}],
            "role": "user",
        },
    }


def process_decision(response_payload, store, secret):
    """Shared verify+match+build logic for the `resume` subcommand and the
    `serve` HTTP handler. Returns (ok, result_or_error, resume_request_or_None)."""
    errors = validate_against_schema(response_payload, RESPONSE_SCHEMA_PATH)
    if errors:
        return False, f"schema validation failed: {'; '.join(errors)}", None

    if not verify_signature(response_payload, secret):
        return False, "signature verification failed", None

    ticket_id = response_payload["ticket_id"]
    record = store.get(ticket_id)
    if record is None:
        return False, f"unknown ticket_id {ticket_id!r} -- no matching pending approval", None

    if record.get("resolved"):
        # Idempotent no-op per references/durable_hitl_patterns.md \u00a74 --
        # not an error, but not re-sent to the runner either.
        return True, f"ticket {ticket_id!r} already resolved as {record.get('decision')!r} -- no-op", None

    if record["invocation_id"] != response_payload["invocation_id"]:
        return False, (f"invocation_id mismatch for ticket {ticket_id!r}: "
                        f"stored={record['invocation_id']!r} inbound={response_payload['invocation_id']!r}"), None
    if record["function_call_id"] != response_payload["function_call_id"]:
        return False, (f"function_call_id mismatch for ticket {ticket_id!r}: "
                        f"stored={record['function_call_id']!r} inbound={response_payload['function_call_id']!r}"), None

    expires_at = record.get("expires_at")
    if expires_at and now_iso() > expires_at:
        return False, f"ticket {ticket_id!r} expired at {expires_at} -- reject and re-request", None

    resume_request = build_resume_request(record, response_payload)
    return True, f"ticket {ticket_id!r} verified: decision={response_payload['decision']!r}", resume_request


def cmd_record_ticket(args):
    store = PendingStore(args.pending_store)
    record = {
        "app_name": args.app_name,
        "user_id": args.user_id,
        "session_id": args.session_id,
        "invocation_id": args.invocation_id,
        "function_call_id": args.function_call_id,
        "tool_name": args.tool_name,
        "expires_at": args.expires_at,
        "resolved": False,
    }
    store.put(args.ticket_id, record)
    print(f"recorded pending ticket {args.ticket_id!r} in {args.pending_store}")

    if args.emit_webhook:
        secret = get_secret(args.secret_env_var)
        body = build_webhook_payload(args)
        body["signature"] = sign(body, secret)
        errors = validate_against_schema(body, WEBHOOK_SCHEMA_PATH)
        if errors:
            print("warning: generated webhook payload failed its own schema check: "
                  + "; ".join(errors), file=sys.stderr)
        print(json.dumps(body, indent=2))
    return 0


def cmd_verify(args):
    secret = get_secret(args.secret_env_var)
    raw = sys.stdin.read() if args.input_file == "-" else open(args.input_file).read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 2

    errors = validate_against_schema(payload, RESPONSE_SCHEMA_PATH)
    if errors:
        print("REJECTED: schema validation failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if not verify_signature(payload, secret):
        print("REJECTED: signature verification failed", file=sys.stderr)
        return 1
    print(f"OK: signature and schema valid for ticket_id={payload.get('ticket_id')!r}, "
          f"decision={payload.get('decision')!r}")
    return 0


def cmd_resume(args):
    secret = get_secret(args.secret_env_var)
    store = PendingStore(args.pending_store)
    raw = sys.stdin.read() if args.input_file == "-" else open(args.input_file).read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 2

    ok, message, resume_request = process_decision(payload, store, secret)
    if not ok:
        print(f"REJECTED: {message}", file=sys.stderr)
        return 1
    print(message)
    if resume_request is None:
        return 0  # idempotent no-op case

    if args.dry_run:
        print("Dry run only -- would POST to "
              f"{args.adk_server_url.rstrip('/')}/run_sse:\n")
        print(json.dumps(resume_request, indent=2))
        return 0

    store.mark_resolved(payload["ticket_id"], payload["decision"])
    url = args.adk_server_url.rstrip("/") + "/run_sse"
    req = urllib.request.Request(
        url, data=json.dumps(resume_request).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            print(f"resumed invocation {resume_request['invocation_id']!r}: "
                  f"HTTP {resp.status}")
        return 0
    except urllib.error.URLError as e:
        print(f"error: failed to reach ADK API server at {url}: {e}", file=sys.stderr)
        return 1


def cmd_serve(args):
    import http.server

    secret = get_secret(args.secret_env_var)
    store = PendingStore(args.pending_store)
    dry_run = args.dry_run
    adk_server_url = args.adk_server_url

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):  # quieter default logging
            sys.stderr.write("serve: " + (fmt % a) + "\n")

        def do_POST(self):
            if self.path != "/resume":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                self._respond(400, {"error": "invalid JSON"})
                return

            ok, message, resume_request = process_decision(payload, store, secret)
            if not ok:
                self._respond(400, {"error": message})
                return
            if resume_request is None:
                self._respond(200, {"status": "ok", "message": message})
                return

            if dry_run:
                self._respond(200, {"status": "dry-run", "would_send": resume_request})
                return

            store.mark_resolved(payload["ticket_id"], payload["decision"])
            url = adk_server_url.rstrip("/") + "/run_sse"
            req = urllib.request.Request(
                url, data=json.dumps(resume_request).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    self._respond(200, {"status": "resumed", "adk_status": resp.status})
            except urllib.error.URLError as e:
                self._respond(502, {"error": f"failed to reach ADK API server: {e}"})

        def _respond(self, code, body):
            data = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = http.server.HTTPServer(("0.0.0.0", args.port), Handler)
    mode = "DRY-RUN (no ADK calls will be made)" if dry_run else f"forwarding to {adk_server_url}"
    print(f"resume_workflow.py serve: listening on :{args.port}/resume [{mode}]. Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("record-ticket", help="Record a pending approval and optionally emit its signed webhook")
    p.add_argument("--ticket-id", required=True)
    p.add_argument("--app-name", required=True)
    p.add_argument("--user-id", required=True)
    p.add_argument("--session-id", required=True)
    p.add_argument("--invocation-id", required=True)
    p.add_argument("--function-call-id", required=True)
    p.add_argument("--tool-name", required=True)
    p.add_argument("--hint", default="Approval requested.")
    p.add_argument("--payload-json", default=None, help="Extra structured context as a JSON object string")
    p.add_argument("--expires-at", default=None, help="ISO-8601 UTC deadline, e.g. 2026-09-15T00:00:00Z")
    p.add_argument("--response-url", default=None)
    p.add_argument("--pending-store", default="./pending_approvals.json")
    p.add_argument("--secret-env-var", default="HITL_WEBHOOK_SECRET")
    p.add_argument("--emit-webhook", action="store_true", help="Print the signed outbound webhook JSON")
    p.set_defaults(func=cmd_record_ticket)

    p = sub.add_parser("verify", help="Verify an inbound decision payload only (no resume, no network call)")
    p.add_argument("--input-file", default="-", help="Path to the JSON payload, or '-' for stdin (default)")
    p.add_argument("--secret-env-var", default="HITL_WEBHOOK_SECRET")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("resume", help="Verify, match, and resume (or --dry-run print) a single decision payload")
    p.add_argument("--input-file", default="-", help="Path to the JSON payload, or '-' for stdin (default)")
    p.add_argument("--pending-store", default="./pending_approvals.json")
    p.add_argument("--secret-env-var", default="HITL_WEBHOOK_SECRET")
    p.add_argument("--adk-server-url", default="http://localhost:8000")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--dry-run", action="store_true", help="Print the /run_sse request instead of sending it")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("serve", help="Run a minimal HTTP server exposing POST /resume")
    p.add_argument("--pending-store", default="./pending_approvals.json")
    p.add_argument("--secret-env-var", default="HITL_WEBHOOK_SECRET")
    p.add_argument("--adk-server-url", default="http://localhost:8000")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--dry-run", action="store_true", help="Never actually call the ADK server; respond with what would be sent")
    p.set_defaults(func=cmd_serve)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
