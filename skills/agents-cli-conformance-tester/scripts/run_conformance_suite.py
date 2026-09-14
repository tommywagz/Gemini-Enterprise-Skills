#!/usr/bin/env python3
"""run_conformance_suite.py

Runs the bundled, dependency-free protocol conformance suite
(`assets/mock_conformance_payload.json`) against either:

1. A real local UCP merchant server or A2A host/remote agent
   (`--target-url http://127.0.0.1:<port>`), or
2. This script's own built-in reference mock sandbox
   (`--serve-mock ucp` or `--serve-mock a2a`) -- useful as a baseline
   sanity check of the harness itself, or to see the expected-correct
   shape of every response before pointing the suite at a real,
   in-progress implementation.

This is a lightweight, MUST/SHOULD/MAY-leveled smoke test, NOT a
replacement for the official upstream suites. See
`references/conformance_test_standards.md` for exactly what this subset
covers and what it doesn't, and where to run the official
`Universal-Commerce-Protocol/conformance` (UCP) or `a2aproject/a2a-tck`
(A2A) suites instead.

Network boundary (see `references/local_mock_sandbox.md` for the full
policy): `--target-url` MUST resolve to a loopback address
(127.0.0.1 / ::1 / localhost). Any other host is rejected before a single
request is sent -- this tool is a local dev-loop / CI pre-flight check,
never a general-purpose remote HTTP conformance client.

Uses only the Python standard library -- no pip install required.

Exit codes:
  0  ran to completion, no `must`-level failures
  1  ran to completion, at least one `must`-level failure
  2  usage error, unreadable/invalid suite file, or a rejected (non-loopback)
     target -- never treat exit 2 as "0 findings"

Usage:
    run_conformance_suite.py --target-url http://127.0.0.1:8182 --protocol ucp
    run_conformance_suite.py --target-url http://127.0.0.1:9999 --protocol a2a
    run_conformance_suite.py --serve-mock ucp --format json
    run_conformance_suite.py --serve-mock a2a --format junit --out reports/junit.xml
"""
import argparse
import ipaddress
import json
import os
import re
import socket
import sys
import threading
import xml.sax.saxutils as saxutils
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlparse

PLACEHOLDER_RE = re.compile(r"^\{\{([\w.]+)\}\}$")
LOOPBACK_LITERALS = {"localhost"}


# --------------------------------------------------------------------------
# Loopback enforcement
# --------------------------------------------------------------------------
def is_loopback(url):
    """True only for HTTP(S) URLs whose host resolves entirely to loopback."""
    parsed = urlparse(url)
    host = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        try:
            addresses = {
                result[4][0]
                for result in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            }
        except socket.gaierror:
            return False
    return bool(addresses) and all(ipaddress.ip_address(address).is_loopback for address in addresses)


# --------------------------------------------------------------------------
# JSON path helpers and templating
# --------------------------------------------------------------------------
def get_path(obj, dotted):
    """Dotted-key lookup into nested dicts. Returns (value, found)."""
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None, False
    return cur, True


def resolve_template(value, suite):
    """Recursively replace exact '{{a.b.c}}' string values with suite[a][b][c]."""
    if isinstance(value, str):
        m = PLACEHOLDER_RE.match(value)
        if m:
            resolved, found = get_path(suite, m.group(1))
            return resolved if found else value
        return value
    if isinstance(value, dict):
        return {k: resolve_template(v, suite) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_template(v, suite) for v in value]
    return value


# --------------------------------------------------------------------------
# HTTP client (stdlib only)
# --------------------------------------------------------------------------
def do_request(url, method, body, headers, timeout=10):
    """Returns (status, parsed_json_or_None, raw_text, error_str_or_None)."""
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urlrequest.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.getcode()
    except urlerror.HTTPError as e:
        raw = e.read()
        status = e.code
    except (urlerror.URLError, OSError) as e:
        return None, None, None, str(e)
    text = raw.decode("utf-8", errors="replace") if raw else ""
    try:
        parsed = json.loads(text) if text else None
    except json.JSONDecodeError:
        parsed = None
    return status, parsed, text, None


def detect_protocol(base_url):
    status, _, _, _ = do_request(base_url.rstrip("/") + "/.well-known/ucp", "GET", None, {})
    if status == 200:
        return "ucp"
    status, _, _, _ = do_request(
        base_url.rstrip("/") + "/.well-known/agent-card.json", "GET", None, {}
    )
    if status == 200:
        return "a2a"
    return None


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------
def score_http_expect(expect, status, parsed):
    """Returns a list of failure-reason strings; empty list means PASS."""
    reasons = []
    if status not in expect.get("status", []):
        reasons.append(f"status {status} not in {expect.get('status')}")
    for p in expect.get("json_paths_present", []):
        _, found = get_path(parsed or {}, p)
        if not found:
            reasons.append(f"missing json path '{p}'")
    arr_contains = expect.get("array_any_contains")
    if arr_contains:
        arr, found = get_path(parsed or {}, arr_contains["path"])
        needle = arr_contains["contains_substring"]
        field = arr_contains["field"]
        if not found or not isinstance(arr, list) or not any(
            isinstance(el, dict) and needle in str(el.get(field, "")) for el in arr
        ):
            reasons.append(
                f"no element in '{arr_contains['path']}' has {field} containing '{needle}'"
            )
    arr_non_empty = expect.get("array_non_empty")
    if arr_non_empty:
        arr, found = get_path(parsed or {}, arr_non_empty)
        if not found or not isinstance(arr, list) or len(arr) == 0:
            reasons.append(f"'{arr_non_empty}' is missing or empty")
    return reasons


def run_protocol_tests(base_url, protocol_block, suite, level_filter):
    results = []
    context = {"discovery": None, "responses": {}}
    all_responses = []
    tests = protocol_block["tests"]
    disc_paths = {
        protocol_block.get("discovery_path"),
        protocol_block.get("agent_card_path"),
    }

    # Pass 1: live HTTP tests, in declared order (post-hoc checks read from these).
    for test in tests:
        req_spec = test.get("request")
        if req_spec is None:
            continue
        tid, level = test["id"], test["level"]
        expect = test["expect"]
        method, path = req_spec["method"], req_spec["path"]
        url = base_url.rstrip("/") + path
        body = resolve_template(req_spec.get("body"), suite) if "body" in req_spec else None
        headers = dict(req_spec.get("headers", {}))
        repeat = req_spec.get("repeat", 1)

        statuses, last_status, last_parsed, conn_error = [], None, None, None
        for _ in range(repeat):
            status, parsed, _raw, err = do_request(url, method, body, headers)
            statuses.append(status)
            last_status, last_parsed = status, parsed
            conn_error = conn_error or err
            all_responses.append({"id": tid, "status": status, "json": parsed})

        context["responses"][tid] = {
            "status": last_status,
            "json": last_parsed,
            "statuses": statuses,
        }
        if path in disc_paths:
            context["discovery"] = last_parsed

        skip_path = expect.get("skip_if_json_path_absent")
        if skip_path is not None:
            val, found = get_path(context["discovery"] or {}, skip_path)
            if not found or not val:
                results.append(
                    {
                        "id": tid,
                        "level": level,
                        "description": test["description"],
                        "outcome": "SKIPPED",
                        "reason": f"discovery path '{skip_path}' absent or falsy",
                        "observed_status": last_status,
                    }
                )
                continue

        if conn_error:
            outcome, reason = "FAIL", f"connection error: {conn_error}"
        else:
            reasons = score_http_expect(expect, last_status, last_parsed)
            if not reasons and req_spec.get("compare_status_equal_across_repeats") and len(set(statuses)) > 1:
                reasons = [f"inconsistent statuses across {repeat} repeats: {statuses}"]
            outcome, reason = ("PASS", "ok") if not reasons else ("FAIL", "; ".join(reasons))

        results.append(
            {
                "id": tid,
                "level": level,
                "description": test["description"],
                "outcome": outcome,
                "reason": reason,
                "observed_status": last_status,
            }
        )

    # Pass 2: post-hoc tests that read from the responses collected above.
    for test in tests:
        if test.get("request") is not None:
            continue
        tid, level, expect = test["id"], test["level"], test["expect"]

        if expect.get("post_hoc_error_envelope_check"):
            offenders = sorted(
                {
                    r["id"]
                    for r in all_responses
                    if r["status"] is not None
                    and 400 <= r["status"] < 500
                    and (not r["json"] or "messages" not in r["json"])
                }
            )
            outcome, reason = (
                ("FAIL", f"4xx response(s) without a messages envelope: {offenders}")
                if offenders
                else ("PASS", "ok")
            )
        elif "post_hoc_enum_check" in expect:
            spec = expect["post_hoc_enum_check"]
            src = context["responses"].get(spec["from_test"])
            if not src:
                outcome, reason = "SKIPPED", f"source test '{spec['from_test']}' did not run"
            else:
                val, found = get_path(src["json"] or {}, spec["path"])
                if not found:
                    outcome, reason = (
                        "SKIPPED",
                        f"path '{spec['path']}' absent from {spec['from_test']} response",
                    )
                elif val not in spec["allowed"]:
                    outcome, reason = "FAIL", f"value '{val}' not in allowed set {spec['allowed']}"
                else:
                    outcome, reason = "PASS", "ok"
        else:
            outcome, reason = "SKIPPED", "unrecognized post-hoc check type"

        results.append(
            {
                "id": tid,
                "level": level,
                "description": test["description"],
                "outcome": outcome,
                "reason": reason,
                "observed_status": None,
            }
        )

    if level_filter and level_filter != "all":
        results = [r for r in results if r["level"] == level_filter]
    return results


def build_report(protocol, base_url, suite, results):
    counts = {}
    for level in ("must", "should", "may"):
        subset = [r for r in results if r["level"] == level]
        counts[level] = {
            "passed": sum(1 for r in subset if r["outcome"] == "PASS"),
            "failed": sum(1 for r in subset if r["outcome"] == "FAIL"),
            "skipped": sum(1 for r in subset if r["outcome"] == "SKIPPED"),
        }
    return {
        "protocol": protocol,
        "target": base_url,
        "suite_version": suite.get("suite_version"),
        "summary": counts,
        "recommendation": "BLOCK" if counts["must"]["failed"] > 0 else "PROCEED",
        "results": results,
    }


def render_junit(report):
    cases = []
    for r in report["results"]:
        attrs = f'classname="{saxutils.escape(report["protocol"])}" name="{saxutils.escape(r["id"])}"'
        if r["outcome"] == "FAIL":
            cases.append(
                f'<testcase {attrs}><failure message="{saxutils.escape(r["reason"])}">'
                f'{saxutils.escape(r["description"])}</failure></testcase>'
            )
        elif r["outcome"] == "SKIPPED":
            cases.append(f'<testcase {attrs}><skipped message="{saxutils.escape(r["reason"])}"/></testcase>')
        else:
            cases.append(f"<testcase {attrs}/>")
    total = len(report["results"])
    failures = sum(1 for r in report["results"] if r["outcome"] == "FAIL")
    skipped = sum(1 for r in report["results"] if r["outcome"] == "SKIPPED")
    header = (
        f'<testsuite name="agents-cli-conformance-tester.{report["protocol"]}" '
        f'tests="{total}" failures="{failures}" skipped="{skipped}">'
    )
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + header + "".join(cases) + "</testsuite>"


# --------------------------------------------------------------------------
# Local mock sandbox (Mode B) -- see references/local_mock_sandbox.md
# --------------------------------------------------------------------------
MOCK_UCP_DISCOVERY = {
    "ucp": {
        "version": "2026-04-08",
        "services": {
            "dev.ucp.shopping": {
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/shopping",
                "rest": {
                    "schema": "https://ucp.dev/2026-04-08/services/shopping/openapi.json",
                    "endpoint": "http://127.0.0.1/",
                },
            }
        },
        "capabilities": [
            {
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/shopping/checkout",
                "schema": "https://ucp.dev/2026-04-08/schemas/shopping/checkout.json",
            }
        ],
    },
    "payment": {"handlers": []},
    "keys": None,
}

MOCK_A2A_AGENT_CARD = {
    "name": "conformance-mock-agent",
    "description": "Reference mock used to self-test the bundled conformance suite.",
    "version": "1.0.0",
    "skills": [
        {
            "id": "echo",
            "name": "Echo",
            "description": "Echoes the input text back as a completed task.",
            "tags": ["demo"],
            "examples": ["hello"],
        }
    ],
    "capabilities": {"streaming": False, "push_notifications": False},
}


class _QuietHandler(BaseHTTPRequestHandler):
    """Base class that silences per-request access logs -- the script's own
    report is the only output this tool prints."""

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return {}


class _MockUcpHandler(_QuietHandler):
    _ERROR_ENVELOPE = {
        "messages": [
            {
                "type": "ERROR",
                "code": "NOT_FOUND",
                "content": "unknown item or path",
                "severity": "UNRECOVERABLE",
            }
        ]
    }

    def do_GET(self):
        if self.path == "/.well-known/ucp":
            self._send_json(200, MOCK_UCP_DISCOVERY)
        else:
            self._send_json(404, self._ERROR_ENVELOPE)

    def do_POST(self):
        body = self._read_json_body()
        line_items = body.get("line_items") or [{}]
        item_id = line_items[0].get("item_id")
        if self.path == "/carts":
            if item_id == "item_1":
                self._send_json(201, {"id": "cart_mock_1", "line_items": line_items})
            else:
                self._send_json(404, self._ERROR_ENVELOPE)
        elif self.path == "/checkout-sessions":
            if item_id == "item_1":
                self._send_json(201, {"id": "checkout_mock_1", "status": "ready_for_complete"})
            else:
                self._send_json(404, self._ERROR_ENVELOPE)
        else:
            self._send_json(404, self._ERROR_ENVELOPE)


class _MockA2aHandler(_QuietHandler):
    def do_GET(self):
        if self.path == "/.well-known/agent-card.json":
            self._send_json(200, MOCK_A2A_AGENT_CARD)
        else:
            self._send_json(404, {"error": {"code": -32601, "message": "not found"}})

    def do_POST(self):
        body = self._read_json_body()
        method = body.get("method")
        req_id = body.get("id")
        if method == "message/send":
            self._send_json(
                200,
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "id": "task_mock_1",
                        "context_id": "ctx_mock_1",
                        "status": {"state": "completed", "timestamp": "2026-01-01T00:00:00Z"},
                        "history": [],
                        "artifacts": [],
                    },
                },
            )
        elif method == "tasks/get":
            task_id = (body.get("params") or {}).get("id")
            if task_id == "conformance-unknown-task-id-0000":
                self._send_json(
                    200,
                    {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32001, "message": "task not found"}},
                )
            else:
                self._send_json(
                    200,
                    {"jsonrpc": "2.0", "id": req_id, "result": {"id": task_id, "status": {"state": "completed"}}},
                )
        else:
            self._send_json(
                200, {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "method not found"}}
            )


def serve_mock(protocol):
    handler_cls = _MockUcpHandler if protocol == "ucp" else _MockA2aHandler
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    return server, thread, f"http://127.0.0.1:{port}"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the bundled local UCP/A2A conformance suite against a "
        "loopback target or this script's own reference mock sandbox."
    )
    parser.add_argument("--target-url", help="e.g. http://127.0.0.1:8182 (must be loopback)")
    parser.add_argument("--serve-mock", choices=["ucp", "a2a"], help="run against the built-in reference mock instead of a real target")
    parser.add_argument("--protocol", choices=["ucp", "a2a", "auto"], default="auto")
    parser.add_argument("--suite", help="path to the test suite JSON (default: bundled assets/mock_conformance_payload.json)")
    parser.add_argument("--level", choices=["must", "should", "may", "all"], default="all")
    parser.add_argument("--format", choices=["json", "junit"], default="json")
    parser.add_argument("--out", help="write the report here instead of stdout")
    args = parser.parse_args(argv)

    if not args.target_url and not args.serve_mock:
        parser.error("one of --target-url or --serve-mock is required")
    if args.target_url and args.serve_mock:
        parser.error("--target-url and --serve-mock are mutually exclusive")

    suite_path = args.suite or os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "mock_conformance_payload.json")
    )
    try:
        with open(suite_path) as f:
            suite = json.load(f)
    except OSError as e:
        print(f"error: cannot read suite file '{suite_path}': {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: suite file '{suite_path}' is not valid JSON: {e}", file=sys.stderr)
        return 2

    server = None
    try:
        if args.serve_mock:
            protocol = args.serve_mock
            server, _thread, base_url = serve_mock(protocol)
        else:
            base_url = args.target_url
            if not is_loopback(base_url):
                print(
                    f"error: --target-url must be a loopback address "
                    f"(127.0.0.1 / ::1 / localhost); refusing to test '{base_url}'",
                    file=sys.stderr,
                )
                return 2
            protocol = args.protocol
            if protocol == "auto":
                protocol = detect_protocol(base_url)
                if protocol is None:
                    print(
                        "error: could not auto-detect protocol; neither /.well-known/ucp "
                        "nor /.well-known/agent-card.json responded with 200. Pass --protocol explicitly.",
                        file=sys.stderr,
                    )
                    return 2

        if protocol not in suite.get("protocols", {}):
            print(f"error: suite file has no '{protocol}' protocol block", file=sys.stderr)
            return 2

        results = run_protocol_tests(base_url, suite["protocols"][protocol], suite, args.level)
        report = build_report(protocol, base_url, suite, results)
        output = json.dumps(report, indent=2) if args.format == "json" else render_junit(report)

        if args.out:
            os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None
            with open(args.out, "w") as f:
                f.write(output)
        else:
            print(output)

        must_failures = [r for r in results if r["level"] == "must" and r["outcome"] == "FAIL"]
        return 1 if must_failures else 0
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    sys.exit(main())
