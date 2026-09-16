#!/usr/bin/env python3
"""ucp_client_helper.py - stdlib-only UCP consumer-surface (client) helper.

Implements the client half of a Universal Commerce Protocol (UCP) shopping
integration: discovery-profile parsing with authority-binding validation,
cart construction, checkout lifecycle transitions, and a webhook
content-digest verification helper. No third-party dependencies -- uses only
`urllib`, `http.server`, `hashlib`, `hmac`, `base64`, and `json` from the
standard library, so it runs anywhere Python 3.9+ runs without `pip install`.

Grounded in:
  - https://ucp.dev/2026-08-25/specification/overview/
  - https://ucp.dev/2026-08-25/specification/shopping/{cart,checkout,order}/rest/
  - https://ucp.dev/2026-08-25/specification/signatures/
  - Universal-Commerce-Protocol/samples rest/python/client/flower_shop/simple_happy_path_client.py

CLI usage:
  python3 ucp_client_helper.py discover --base-url https://business.example.com
  python3 ucp_client_helper.py selftest
  python3 ucp_client_helper.py selftest --verbose

Library usage:
  from ucp_client_helper import UCPClient
  client = UCPClient(agent_profile_url="https://platform.example/.well-known/ucp")
  profile = client.fetch_discovery_profile("https://business.example.com")
  endpoint = client.resolve_service_endpoint(profile, "dev.ucp.shopping")
  cart = client.create_cart(endpoint, line_items=[{"item": {"id": "item_123"}, "quantity": 2}])
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlparse

DEFAULT_TIMEOUT = 10.0
PROTOCOL_VERSION = "2026-08-25"


# ---------------------------------------------------------------------------
# Authority binding (namespace provenance) validation
# ---------------------------------------------------------------------------


class AuthorityBindingError(ValueError):
    """Raised when a declared schema/entity URL fails authority-binding checks."""


def validate_authority_binding(entity_name: str, schema_url: str) -> None:
    """Validate that ``schema_url``'s host is authorized for ``entity_name``.

    Implements the UCP Namespace Governance derivation algorithm: the
    schema's host, reversed into labels, must equal or label-align-prefix
    the reverse-domain entity name. Raises AuthorityBindingError on any
    violation. See references/ucp_client_negotiation.md for the full
    algorithm and worked examples.
    """
    parsed = urlparse(schema_url)
    if parsed.scheme != "https":
        raise AuthorityBindingError(f"schema URL must use https: {schema_url!r}")
    if "@" in (parsed.netloc or ""):
        raise AuthorityBindingError(f"schema URL must not contain userinfo: {schema_url!r}")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise AuthorityBindingError(f"schema URL has no host: {schema_url!r}")
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host) or ":" in host:
        raise AuthorityBindingError(f"IP-literal host is not a valid authority: {host!r}")
    labels = host.split(".")
    if len(labels) < 2:
        raise AuthorityBindingError(f"host must have at least two labels: {host!r}")
    authority_prefix = ".".join(reversed(labels))

    if entity_name == authority_prefix:
        return  # exact match
    if entity_name.startswith(authority_prefix + "."):
        return  # label-aligned prefix match
    raise AuthorityBindingError(
        f"entity {entity_name!r} is not authorized by schema host {host!r} "
        f"(authority_prefix={authority_prefix!r})"
    )


# ---------------------------------------------------------------------------
# RFC 9530 Content-Digest helpers
# ---------------------------------------------------------------------------


def compute_content_digest(body: bytes) -> str:
    """Return an RFC 9530 SHA-256 Content-Digest header value for ``body``."""
    digest = hashlib.sha256(body).digest()
    return "sha-256=:" + base64.b64encode(digest).decode("ascii") + ":"


def verify_content_digest(body: bytes, digest_header: str) -> bool:
    """Verify an RFC 9530 ``Content-Digest`` header value against ``body``."""
    expected = compute_content_digest(body)
    return _constant_time_eq(expected, digest_header.strip())


def _constant_time_eq(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0


def parse_signature_input(header_value: str) -> dict[str, Any]:
    """Parse a simplified RFC 9421 ``Signature-Input`` header.

    Returns {"label": str, "components": [str, ...], "params": {str: str}}.
    This is a pragmatic parser for the common `sig1=("a" "b");created=...;keyid="..."`
    shape produced by UCP reference implementations -- it does not implement
    the complete RFC 9421 Structured Field grammar (no inner-list parameters,
    no non-ASCII keys). Use a full RFC 8941/9421 library for production
    signature *verification*; this helper is for client-side inspection and
    the webhook self-test below.
    """
    match = re.match(r'^\s*([\w-]+)\s*=\s*\((.*?)\)(.*)$', header_value)
    if not match:
        raise ValueError(f"unrecognized Signature-Input shape: {header_value!r}")
    label, components_raw, params_raw = match.groups()
    components = re.findall(r'"([^"]+)"', components_raw)
    params: dict[str, str] = {}
    for key, val in re.findall(r';([\w-]+)=("?[^;]*"?)', params_raw):
        params[key] = val.strip('"')
    return {"label": label, "components": components, "params": params}


def verify_webhook_delivery(
    body: bytes,
    content_digest_header: str,
    signature_input_header: str | None = None,
    signature_header: str | None = None,
    public_key_verifier: Any | None = None,
    signature_required: bool = False,
    seen_idempotency_keys: set[str] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Simulate the client-side checks a webhook receiver applies before trust.

    Returns a dict {"ok": bool, "reasons": [str, ...]}. Checks performed:
      1. Content-Digest matches the delivered body (integrity).
      2. A signature-required delivery has both Signature-Input and Signature
         headers and is accepted by ``public_key_verifier``. The verifier is
         supplied by the caller after resolving the business public key from
         its validated discovery profile.
      3. Replay protection: idempotency_key has not been seen before.
    """
    reasons: list[str] = []
    ok = True

    if not verify_content_digest(body, content_digest_header):
        ok = False
        reasons.append("content_digest_mismatch")

    if signature_input_header:
        try:
            parsed = parse_signature_input(signature_input_header)
            if not parsed["components"]:
                ok = False
                reasons.append("signature_input_no_components")
        except ValueError:
            ok = False
            reasons.append("signature_input_unparseable")

    if signature_required and not (signature_input_header and signature_header):
        ok = False
        reasons.append("required_signature_missing")
    if signature_input_header or signature_header:
        if not (signature_input_header and signature_header and callable(public_key_verifier)):
            ok = False
            reasons.append("signature_verifier_unavailable")
        else:
            try:
                if not public_key_verifier(body, content_digest_header, signature_input_header, signature_header):
                    ok = False
                    reasons.append("signature_verification_failed")
            except Exception:
                ok = False
                reasons.append("signature_verification_error")

    if seen_idempotency_keys is not None and idempotency_key is not None:
        if idempotency_key in seen_idempotency_keys:
            ok = False
            reasons.append("replayed_idempotency_key")
        else:
            seen_idempotency_keys.add(idempotency_key)

    if ok:
        reasons.append("all_checks_passed")
    return {"ok": ok, "reasons": reasons}


# ---------------------------------------------------------------------------
# UCP client
# ---------------------------------------------------------------------------


class UCPError(RuntimeError):
    """Raised for transport-layer UCP failures (non-2xx HTTP status)."""


class UCPBusinessOutcomeError(RuntimeError):
    """Raised when a 200 response carries ucp.status == 'error' (business outcome)."""

    def __init__(self, messages: list[dict[str, Any]]):
        self.messages = messages
        super().__init__(json.dumps(messages))


class UCPClient:
    """Minimal stdlib UCP consumer-surface (shopping platform) client."""

    def __init__(self, agent_profile_url: str, timeout: float = DEFAULT_TIMEOUT):
        self.agent_profile_url = agent_profile_url
        self.timeout = timeout

    # -- headers -------------------------------------------------------

    def build_headers(
        self, body: bytes | None = None, idempotent: bool = False, idempotency_key: str | None = None
    ) -> dict[str, str]:
        headers = {
            "UCP-Agent": f'profile="{self.agent_profile_url}"',
            "Request-Id": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }
        if idempotent:
            headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())
        if body is not None:
            headers["Content-Digest"] = compute_content_digest(body)
        return headers

    # -- discovery -------------------------------------------------------

    def fetch_discovery_profile(self, base_url: str, validate_authority: bool = True) -> dict[str, Any]:
        url = base_url.rstrip("/") + "/.well-known/ucp"
        raw = self._get(url, headers={"UCP-Agent": f'profile="{self.agent_profile_url}"'})
        profile = json.loads(raw)
        ucp = profile.get("ucp", profile)
        if validate_authority:
            for name, entries in ucp.get("capabilities", {}).items():
                for entry in entries:
                    schema = entry.get("schema")
                    if schema:
                        validate_authority_binding(name, schema)
            for name, entries in ucp.get("services", {}).items():
                for entry in entries:
                    schema = entry.get("schema")
                    if schema:
                        validate_authority_binding(name, schema)
        return profile

    def resolve_service_endpoint(
        self, profile: dict[str, Any], service_name: str, transport: str = "rest"
    ) -> str:
        ucp = profile.get("ucp", profile)
        for entry in ucp.get("services", {}).get(service_name, []):
            if entry.get("transport") == transport and entry.get("endpoint"):
                return entry["endpoint"].rstrip("/")
        raise KeyError(f"no {transport} endpoint found for service {service_name!r}")

    def list_capabilities(self, profile: dict[str, Any]) -> list[str]:
        ucp = profile.get("ucp", profile)
        return sorted(ucp.get("capabilities", {}).keys())

    def list_payment_handlers(self, profile: dict[str, Any]) -> list[str]:
        ucp = profile.get("ucp", profile)
        handlers: list[str] = []
        for entries in ucp.get("payment_handlers", {}).values():
            for entry in entries:
                if entry.get("id"):
                    handlers.append(entry["id"])
        return handlers

    # -- cart --------------------------------------------------------------

    def create_cart(
        self, endpoint: str, line_items: list[dict], context: dict | None = None, idempotency_key: str | None = None
    ) -> dict:
        body = {"line_items": line_items}
        if context:
            body["context"] = context
        return self._post_json(f"{endpoint}/carts", body, idempotent=True, idempotency_key=idempotency_key)

    def get_cart(self, endpoint: str, cart_id: str) -> dict:
        return self._get_json(f"{endpoint}/carts/{cart_id}")

    def update_cart(
        self, endpoint: str, cart_id: str, line_items: list[dict], discount_codes: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"line_items": line_items}
        if discount_codes:
            body["discounts"] = {"codes": discount_codes}
        return self._put_json(f"{endpoint}/carts/{cart_id}", body, idempotent=True, idempotency_key=idempotency_key)

    def cancel_cart(self, endpoint: str, cart_id: str, idempotency_key: str | None = None) -> dict:
        return self._post_json(f"{endpoint}/carts/{cart_id}/cancel", {}, idempotent=True, idempotency_key=idempotency_key)

    # -- checkout ------------------------------------------------------------

    def create_checkout_from_cart(self, endpoint: str, cart_id: str, idempotency_key: str | None = None) -> dict:
        return self._post_json(f"{endpoint}/checkout-sessions", {"cart_id": cart_id}, idempotent=True, idempotency_key=idempotency_key)

    def create_checkout_from_line_items(
        self, endpoint: str, line_items: list[dict], idempotency_key: str | None = None
    ) -> dict:
        return self._post_json(f"{endpoint}/checkout-sessions", {"line_items": line_items}, idempotent=True, idempotency_key=idempotency_key)

    def get_checkout(self, endpoint: str, checkout_id: str) -> dict:
        return self._get_json(f"{endpoint}/checkout-sessions/{checkout_id}")

    def update_checkout(
        self, endpoint: str, checkout_id: str, payload: dict, idempotency_key: str | None = None
    ) -> dict:
        if payload.get("status") == "complete_in_progress":
            raise UCPBusinessOutcomeError(
                [{"type": "error", "code": "update_during_completion",
                  "content": "checkout is complete_in_progress; do not submit updates"}]
            )
        return self._put_json(f"{endpoint}/checkout-sessions/{checkout_id}", payload, idempotent=True, idempotency_key=idempotency_key)

    def complete_checkout(
        self,
        endpoint: str,
        checkout_id: str,
        payment: dict,
        allowed_handler_ids: set[str],
        user_confirmed: bool = False,
        signals: dict | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """Complete an order only after confirmation and handler validation.

        ``user_confirmed`` must be set only after the caller has shown the
        buyer the final items, total, currency, fulfillment option, and
        payment handler. ``allowed_handler_ids`` must come from the current
        business discovery profile, not from a previous merchant session.
        """
        if not user_confirmed:
            raise UCPBusinessOutcomeError([{
                "type": "error", "code": "buyer_confirmation_required",
                "content": "explicit buyer confirmation is required before completing checkout",
            }])
        instruments = payment.get("instruments") if isinstance(payment, dict) else None
        if not isinstance(instruments, list) or not instruments:
            raise ValueError("payment.instruments must be a non-empty list")
        unadvertised = [item.get("handler_id") for item in instruments if item.get("handler_id") not in allowed_handler_ids]
        if unadvertised:
            raise UCPBusinessOutcomeError([{
                "type": "error", "code": "unadvertised_payment_handler",
                "content": f"payment handler(s) not advertised by this business: {unadvertised}",
            }])
        body: dict[str, Any] = {"payment": payment}
        if signals:
            body["signals"] = signals
        return self._post_json(f"{endpoint}/checkout-sessions/{checkout_id}/complete", body, idempotent=True, idempotency_key=idempotency_key)

    def cancel_checkout(self, endpoint: str, checkout_id: str, idempotency_key: str | None = None) -> dict:
        return self._post_json(f"{endpoint}/checkout-sessions/{checkout_id}/cancel", {}, idempotent=True, idempotency_key=idempotency_key)

    # -- order ---------------------------------------------------------------

    def get_order(self, endpoint: str, order_id: str) -> dict:
        return self._get_json(f"{endpoint}/orders/{order_id}")

    # -- transport helpers -----------------------------------------------

    def _get(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        req = urlrequest.Request(url, headers=headers or {}, method="GET")
        return self._send(req)

    def _get_json(self, url: str) -> dict:
        return self._decode_business_response(self._get(url, headers=self.build_headers()))

    def _post_json(
        self, url: str, body: dict, idempotent: bool = False, idempotency_key: str | None = None
    ) -> dict:
        return self._request_json("POST", url, body, idempotent, idempotency_key)

    def _put_json(
        self, url: str, body: dict, idempotent: bool = False, idempotency_key: str | None = None
    ) -> dict:
        return self._request_json("PUT", url, body, idempotent, idempotency_key)

    def _request_json(
        self, method: str, url: str, body: dict, idempotent: bool, idempotency_key: str | None = None
    ) -> dict:
        payload = json.dumps(body).encode("utf-8")
        headers = self.build_headers(body=payload, idempotent=idempotent, idempotency_key=idempotency_key)
        req = urlrequest.Request(url, data=payload, headers=headers, method=method)
        raw = self._send(req)
        return self._decode_business_response(raw)

    def _send(self, req: urlrequest.Request) -> bytes:
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                return resp.read()
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise UCPError(f"HTTP {exc.code} from {req.full_url}: {body}") from exc
        except urlerror.URLError as exc:
            raise UCPError(f"transport error contacting {req.full_url}: {exc}") from exc

    @staticmethod
    def _decode_business_response(raw: bytes) -> dict:
        data = json.loads(raw)
        ucp = data.get("ucp", {})
        if ucp.get("status") == "error":
            raise UCPBusinessOutcomeError(data.get("messages", []))
        return data


# ---------------------------------------------------------------------------
# Self-test: an in-process mock UCP business server exercising the full
# discover -> cart -> checkout -> complete -> order happy path with no
# network access and no third-party dependencies.
# ---------------------------------------------------------------------------


def _build_mock_server() -> tuple[HTTPServer, int]:
    carts: dict[str, dict] = {}
    checkouts: dict[str, dict] = {}
    orders: dict[str, dict] = {}
    counter = {"n": 0}

    def next_id(prefix: str) -> str:
        counter["n"] += 1
        return f"{prefix}_{counter['n']:04d}"

    def price_line_items(line_items: list[dict]) -> list[dict]:
        catalog = {"item_123": ("Red T-Shirt", 2500), "item_456": ("Blue Jeans", 7500)}
        priced = []
        for li in line_items:
            item_id = li["item"]["id"]
            title, price = catalog.get(item_id, ("Unknown Item", 1000))
            qty = li.get("quantity", 1)
            priced.append({
                "id": li.get("id") or next_id("li"),
                "item": {"id": item_id, "title": title, "price": price},
                "quantity": qty,
                "totals": [
                    {"type": "subtotal", "amount": price * qty},
                    {"type": "total", "amount": price * qty},
                ],
            })
        return priced

    def totals_for(priced_items: list[dict]) -> list[dict]:
        total = sum(li["totals"][-1]["amount"] for li in priced_items)
        return [{"type": "subtotal", "amount": total}, {"type": "total", "amount": total}]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # silence default stderr logging
            pass

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            return json.loads(self.rfile.read(length))

        def _write_json(self, status: int, body: dict) -> None:
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Digest", compute_content_digest(payload))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path == "/.well-known/ucp":
                base = f"http://127.0.0.1:{self.server.server_port}"
                self._write_json(200, {
                    "ucp": {
                        "version": PROTOCOL_VERSION,
                        "services": {
                            "dev.ucp.shopping": [{
                                "version": PROTOCOL_VERSION,
                                "spec": "https://ucp.dev/2026-08-25/specification/overview",
                                "transport": "rest",
                                "schema": "https://ucp.dev/2026-08-25/services/shopping/rest.openapi.json",
                                "endpoint": base,
                            }]
                        },
                        "capabilities": {
                            "dev.ucp.shopping.cart": [{
                                "version": PROTOCOL_VERSION,
                                "spec": "https://ucp.dev/2026-08-25/specification/shopping/cart",
                                "schema": "https://ucp.dev/2026-08-25/schemas/shopping/cart.json",
                            }],
                            "dev.ucp.shopping.checkout": [{
                                "version": PROTOCOL_VERSION,
                                "spec": "https://ucp.dev/2026-08-25/specification/shopping/checkout",
                                "schema": "https://ucp.dev/2026-08-25/schemas/shopping/checkout.json",
                            }],
                        },
                        "payment_handlers": {
                            "mock_payment_handler": [{"id": "mock_payment_handler", "version": PROTOCOL_VERSION}]
                        },
                    }
                })
                return
            if self.path.startswith("/carts/"):
                cart_id = self.path.rsplit("/", 1)[-1]
                cart = carts.get(cart_id)
                if not cart:
                    self._write_json(200, {"ucp": {"version": PROTOCOL_VERSION, "status": "error"},
                                            "messages": [{"type": "error", "code": "not_found",
                                                          "content": "cart not found", "severity": "unrecoverable"}]})
                    return
                self._write_json(200, cart)
                return
            if self.path.startswith("/checkout-sessions/") and not self.path.endswith(("/complete", "/cancel")):
                chk_id = self.path.rsplit("/", 1)[-1]
                self._write_json(200, checkouts[chk_id])
                return
            if self.path.startswith("/orders/"):
                order_id = self.path.rsplit("/", 1)[-1]
                self._write_json(200, orders[order_id])
                return
            self._write_json(404, {"ucp": {"version": PROTOCOL_VERSION, "status": "error"},
                                    "messages": [{"type": "error", "code": "not_found", "content": "no route"}]})

        def do_POST(self):
            body = self._read_json()
            if self.path == "/carts":
                priced = price_line_items(body.get("line_items", []))
                cart_id = next_id("cart")
                cart = {
                    "ucp": {"version": PROTOCOL_VERSION,
                            "capabilities": {"dev.ucp.shopping.cart": [{"version": PROTOCOL_VERSION}]}},
                    "id": cart_id, "line_items": priced, "currency": "USD",
                    "totals": totals_for(priced),
                }
                carts[cart_id] = cart
                self._write_json(201, cart)
                return
            if self.path.endswith("/cancel") and "/carts/" in self.path:
                cart_id = self.path.split("/")[-2]
                cart = carts[cart_id]
                cart["status"] = "canceled"
                self._write_json(200, cart)
                return
            if self.path == "/checkout-sessions":
                if "cart_id" in body:
                    src = carts[body["cart_id"]]
                    line_items = src["line_items"]
                else:
                    line_items = price_line_items(body.get("line_items", []))
                chk_id = next_id("chk")
                checkout = {
                    "ucp": {"version": PROTOCOL_VERSION,
                            "capabilities": {"dev.ucp.shopping.checkout": [{"version": PROTOCOL_VERSION}]},
                            "payment_handlers": {"mock_payment_handler": [{"id": "mock_payment_handler"}]}},
                    "id": chk_id, "status": "incomplete", "currency": "USD",
                    "line_items": line_items, "totals": totals_for(line_items),
                }
                checkouts[chk_id] = checkout
                self._write_json(201, checkout)
                return
            if self.path.endswith("/complete"):
                chk_id = self.path.split("/")[-2]
                checkout = checkouts[chk_id]
                order_id = next_id("order")
                order = {
                    "ucp": {"version": PROTOCOL_VERSION,
                            "capabilities": {"dev.ucp.shopping.order": [{"version": PROTOCOL_VERSION}]}},
                    "id": order_id, "checkout_id": chk_id,
                    "permalink_url": f"http://127.0.0.1:{self.server.server_port}/orders/{order_id}",
                    "currency": checkout["currency"], "line_items": checkout["line_items"],
                    "totals": checkout["totals"],
                }
                orders[order_id] = order
                checkout["status"] = "completed"
                checkout["order"] = {"id": order_id, "permalink_url": order["permalink_url"]}
                self._write_json(200, checkout)
                return
            if self.path.endswith("/cancel") and "/checkout-sessions/" in self.path:
                chk_id = self.path.split("/")[-2]
                checkout = checkouts[chk_id]
                checkout["status"] = "canceled"
                self._write_json(200, checkout)
                return
            self._write_json(404, {"ucp": {"version": PROTOCOL_VERSION, "status": "error"}, "messages": []})

        def do_PUT(self):
            body = self._read_json()
            if "/carts/" in self.path:
                cart_id = self.path.rsplit("/", 1)[-1]
                priced = price_line_items(body.get("line_items", []))
                cart = carts[cart_id]
                cart["line_items"] = priced
                cart["totals"] = totals_for(priced)
                if "discounts" in body:
                    cart["discounts"] = {"codes": body["discounts"]["codes"], "applied": [
                        {"code": c, "amount": 0} for c in body["discounts"]["codes"]
                    ]}
                self._write_json(200, cart)
                return
            if "/checkout-sessions/" in self.path:
                chk_id = self.path.rsplit("/", 1)[-1]
                checkout = checkouts[chk_id]
                if checkout.get("status") == "complete_in_progress":
                    self._write_json(200, {**checkout, "messages": [
                        {"type": "error", "code": "in_progress",
                         "content": "checkout completion already in progress", "severity": "recoverable"}]})
                    return
                priced = price_line_items(body.get("line_items", checkout["line_items"]))
                checkout["line_items"] = priced
                checkout["totals"] = totals_for(priced)
                missing = []
                if "buyer" in body:
                    checkout["buyer"] = body["buyer"]
                elif "buyer" not in checkout:
                    missing.append({"type": "error", "code": "missing", "path": "$.buyer.email",
                                     "content": "Buyer email is required", "severity": "recoverable"})
                if "fulfillment" in body:
                    methods = body["fulfillment"]["methods"]
                    for m in methods:
                        m.setdefault("id", "shipping_1")
                        if m.get("destinations") and not m.get("groups"):
                            m["groups"] = [{
                                "id": "package_1",
                                "options": [
                                    {"id": "standard", "title": "Standard Shipping",
                                     "totals": [{"type": "total", "amount": 500}]},
                                    {"id": "express", "title": "Express Shipping",
                                     "totals": [{"type": "total", "amount": 1000}]},
                                ],
                            }]
                    checkout["fulfillment"] = {"methods": methods}
                elif "fulfillment" not in checkout:
                    missing.append({"type": "error", "code": "missing",
                                     "path": "$.fulfillment.methods", "content": "Fulfillment is required",
                                     "severity": "recoverable"})
                ready = not missing and bool(
                    checkout.get("fulfillment", {}).get("methods", [{}])[0].get("groups", [{}])[0].get("selected_option_id")
                )
                checkout["status"] = "ready_for_complete" if ready else "incomplete"
                checkout["messages"] = missing
                self._write_json(200, checkout)
                return
            self._write_json(404, {"ucp": {"version": PROTOCOL_VERSION, "status": "error"}, "messages": []})

    server = HTTPServer(("127.0.0.1", 0), Handler)
    return server, server.server_port


def run_selftest(verbose: bool = False) -> int:
    server, port = _build_mock_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    failures: list[str] = []

    def check(label: str, cond: bool) -> None:
        status = "PASS" if cond else "FAIL"
        if verbose or not cond:
            print(f"[{status}] {label}")
        if not cond:
            failures.append(label)

    try:
        client = UCPClient(agent_profile_url="https://platform.example/.well-known/ucp")

        profile = client.fetch_discovery_profile(base_url)
        caps = client.list_capabilities(profile)
        check("discovery returns cart+checkout capabilities",
              "dev.ucp.shopping.cart" in caps and "dev.ucp.shopping.checkout" in caps)

        handlers = client.list_payment_handlers(profile)
        check("discovery returns mock_payment_handler", "mock_payment_handler" in handlers)
        check("caller-provided idempotency key is preserved", client.build_headers(
            idempotent=True, idempotency_key="retry-key"
        )["Idempotency-Key"] == "retry-key")

        endpoint = client.resolve_service_endpoint(profile, "dev.ucp.shopping")
        check("resolved endpoint matches mock server", endpoint == base_url)

        cart = client.create_cart(endpoint, line_items=[{"item": {"id": "item_123"}, "quantity": 2}])
        check("cart created with correct total", cart["totals"][-1]["amount"] == 5000)

        cart = client.update_cart(
            endpoint, cart["id"],
            line_items=[{"id": cart["line_items"][0]["id"], "item": {"id": "item_123"}, "quantity": 3}],
            discount_codes=["10OFF"],
        )
        check("cart update reprices quantity", cart["totals"][-1]["amount"] == 7500)
        check("discount code echoed back", cart.get("discounts", {}).get("codes") == ["10OFF"])

        checkout = client.create_checkout_from_cart(endpoint, cart["id"])
        check("checkout created incomplete", checkout["status"] == "incomplete")

        checkout = client.update_checkout(endpoint, checkout["id"], {
            "buyer": {"email": "jane@example.com", "first_name": "Jane", "last_name": "Doe"},
            "line_items": checkout["line_items"],
        })
        check("checkout still incomplete pending fulfillment",
              checkout["status"] == "incomplete" and
              any(m["code"] == "missing" and "fulfillment" in m["path"] for m in checkout["messages"]))

        checkout = client.update_checkout(endpoint, checkout["id"], {
            "buyer": checkout["buyer"],
            "line_items": checkout["line_items"],
            "fulfillment": {"methods": [{"type": "shipping", "destinations": [
                {"street_address": "123 Main St", "address_locality": "Springfield",
                 "address_region": "IL", "postal_code": "62701", "address_country": "US"}
            ]}]},
        })
        check("fulfillment options generated",
              bool(checkout["fulfillment"]["methods"][0]["groups"][0]["options"]))

        method = checkout["fulfillment"]["methods"][0]
        method["groups"][0]["selected_option_id"] = "express"
        checkout = client.update_checkout(endpoint, checkout["id"], {
            "buyer": checkout["buyer"], "line_items": checkout["line_items"],
            "fulfillment": {"methods": [method]},
        })
        check("checkout ready_for_complete after selecting option",
              checkout["status"] == "ready_for_complete")

        payment = {
            "instruments": [{"id": "instr_1", "handler_id": "mock_payment_handler", "type": "card",
                               "credential": {"type": "token", "token": "success_token"}}]
        }
        try:
            client.complete_checkout(endpoint, checkout["id"], payment, set(handlers))
            check("checkout completion requires buyer confirmation", False)
        except UCPBusinessOutcomeError:
            check("checkout completion requires buyer confirmation", True)
        completed = client.complete_checkout(
            endpoint, checkout["id"], payment, allowed_handler_ids=set(handlers), user_confirmed=True
        )
        check("checkout completed with order id", completed["status"] == "completed" and "order" in completed)

        order = client.get_order(endpoint, completed["order"]["id"])
        check("order fetchable post-completion", order["checkout_id"] == checkout["id"])

        # Invalid update while complete_in_progress must be rejected client-side.
        try:
            client.update_checkout(endpoint, checkout["id"], {"status": "complete_in_progress"})
            check("update rejected during complete_in_progress", False)
        except UCPBusinessOutcomeError:
            check("update rejected during complete_in_progress", True)

        # Webhook verification simulation.
        webhook_body = json.dumps({"event_type": "order.delivered", "order_id": order["id"]}).encode()
        digest = compute_content_digest(webhook_body)
        sig_input = 'sig1=("@method" "content-digest");created=1700000000;keyid="business-2026"'
        seen: set[str] = set()
        result = verify_webhook_delivery(
            webhook_body, digest, sig_input, "sig1=:mock:",
            lambda *_: True, True, seen, "wh-key-1",
        )
        check("webhook verification passes on first delivery", result["ok"])
        replay = verify_webhook_delivery(
            webhook_body, digest, sig_input, "sig1=:mock:",
            lambda *_: True, True, seen, "wh-key-1",
        )
        check("webhook verification rejects replayed idempotency key", not replay["ok"])
        tampered = verify_webhook_delivery(
            webhook_body + b"x", digest, sig_input, "sig1=:mock:",
            lambda *_: True, True, seen, "wh-key-2",
        )
        check("webhook verification rejects tampered body", not tampered["ok"])
        missing_verifier = verify_webhook_delivery(webhook_body, digest, sig_input, "sig1=:mock:")
        check("webhook verification rejects unavailable verifier", not missing_verifier["ok"])

        # Authority binding checks.
        try:
            validate_authority_binding("dev.ucp.shopping.checkout", "https://ucp.dev/schema.json")
            check("authority binding accepts ucp.dev prefix match", True)
        except AuthorityBindingError:
            check("authority binding accepts ucp.dev prefix match", False)
        try:
            validate_authority_binding("dev.ucp.shopping.checkout", "https://evil.example/schema.json")
            check("authority binding rejects mismatched host", False)
        except AuthorityBindingError:
            check("authority binding rejects mismatched host", True)

    finally:
        server.shutdown()
        thread.join(timeout=5)

    print(f"\n{len(failures)} failing check(s) out of self-test run.")
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    discover_p = sub.add_parser("discover", help="Fetch and summarize a business's /.well-known/ucp profile")
    discover_p.add_argument("--base-url", required=True)
    discover_p.add_argument("--agent-profile-url", default="https://platform.example/.well-known/ucp")

    selftest_p = sub.add_parser("selftest", help="Run the in-process mock-server regression suite")
    selftest_p.add_argument("--verbose", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "discover":
        client = UCPClient(agent_profile_url=args.agent_profile_url)
        profile = client.fetch_discovery_profile(args.base_url)
        print(json.dumps({
            "capabilities": client.list_capabilities(profile),
            "payment_handlers": client.list_payment_handlers(profile),
        }, indent=2))
        return 0

    if args.command == "selftest":
        return run_selftest(verbose=args.verbose)

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
