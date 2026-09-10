#!/usr/bin/env python3
"""Verify an AP2 mandate chain: structure, bindings, constraints, signatures.

AP2 (https://ap2-protocol.org/) secures Checkout and Payment Mandates as SD-JWT
verifiable credentials. Delegation hops are joined by '~~': an issuer-signed
SD-JWT root, zero or more intermediate KB-SD-JWT hops that carry a `cnf` claim,
and a terminal closed mandate that does not.

This checker is deliberately dependency-light. Structure, disclosure digests,
`sd_hash` chain binding, `checkout_hash` / `transaction_id` linkage, expiry,
`cnf` placement and constraint evaluation all run on the standard library.
ES256 signature verification requires `cryptography`; when it is absent those
checks are reported as SKIPPED and are never counted as passing.

Usage:
    verify_mandate_signature.py CHAIN_FILE [options]

    CHAIN_FILE  A file containing either the compact chain
                (`<sd-jwt>~<disclosure>~...~[~~<hop>...]`) or a JSON object
                with a "chain" string property. Use "-" to read stdin.

Options:
    --checkout-jwt-file PATH  Merchant-signed checkout JWT, for recomputing
                              `checkout_hash` when it is not disclosed in-chain.
    --checkout-hash VALUE     Expected checkout hash, to cross-check a Payment
                              Mandate presented without its Checkout Mandate.
    --jwk-file PATH           JWK or JWKS for the root issuer key.
    --now EPOCH               Override "now" for expiry checks (testing).
    --json                    Emit a JSON report instead of text.
    --quiet                   Suppress PASS/SKIP lines in text mode.

Exit codes:
    0  every executed check passed (skipped checks are reported, not counted)
    1  at least one check failed
    2  usage error or the chain could not be parsed
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from typing import Any

CLOSED_CHECKOUT_VCT = "mandate.checkout.1"
OPEN_CHECKOUT_VCT = "mandate.checkout.open.1"
CLOSED_PAYMENT_VCT = "mandate.payment.1"
OPEN_PAYMENT_VCT = "mandate.payment.open.1"
KNOWN_VCTS = {
    CLOSED_CHECKOUT_VCT,
    OPEN_CHECKOUT_VCT,
    CLOSED_PAYMENT_VCT,
    OPEN_PAYMENT_VCT,
}
OPEN_VCTS = {OPEN_CHECKOUT_VCT, OPEN_PAYMENT_VCT}

KNOWN_CONSTRAINTS = {
    "checkout.allowed_merchants",
    "checkout.line_items",
    "payment.amount_range",
    "payment.allowed_payees",
    "payment.allowed_payment_instruments",
    "payment.allowed_pisps",
    "payment.agent_recurrence",
    "payment.budget",
    "payment.reference",
    "payment.execution_date",
}
# Constraints that cannot be evaluated from a single presentation because they
# depend on a persisted ledger of prior presentations.
STATEFUL_CONSTRAINTS = {"payment.agent_recurrence", "payment.budget"}

HASH_ALGS = {"sha-256": hashlib.sha256, "sha-384": hashlib.sha384, "sha-512": hashlib.sha512}

PASS, FAIL, SKIP, WARN = "PASS", "FAIL", "SKIP", "WARN"


class ChainError(Exception):
    """The presentation could not be parsed."""


# --------------------------------------------------------------------------
# encoding helpers
# --------------------------------------------------------------------------


def b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def digest_of(value: str, alg: str = "sha-256") -> str:
    fn = HASH_ALGS.get(alg.lower())
    if fn is None:
        raise ChainError(f"unsupported hash algorithm: {alg}")
    return b64url_encode(fn(value.encode("ascii")).digest())


def decode_jwt_segment(segment: str) -> dict[str, Any]:
    try:
        return json.loads(b64url_decode(segment))
    except Exception as exc:  # noqa: BLE001 - reported to the caller as a parse failure
        raise ChainError(f"could not decode JWT segment: {exc}") from exc


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------


class Report:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def add(self, status: str, check: str, detail: str = "", where: str = "") -> None:
        self.checks.append(
            {"status": status, "check": check, "detail": detail, "where": where}
        )

    def ok(self, check: str, detail: str = "", where: str = "") -> None:
        self.add(PASS, check, detail, where)

    def fail(self, check: str, detail: str = "", where: str = "") -> None:
        self.add(FAIL, check, detail, where)

    def skip(self, check: str, detail: str = "", where: str = "") -> None:
        self.add(SKIP, check, detail, where)

    def warn(self, check: str, detail: str = "", where: str = "") -> None:
        self.add(WARN, check, detail, where)

    def counts(self) -> dict[str, int]:
        out = {PASS: 0, FAIL: 0, SKIP: 0, WARN: 0}
        for entry in self.checks:
            out[entry["status"]] += 1
        return out

    @property
    def failed(self) -> bool:
        return any(entry["status"] == FAIL for entry in self.checks)


# --------------------------------------------------------------------------
# SD-JWT parsing
# --------------------------------------------------------------------------


class Hop:
    """One SD-JWT (or KB-SD-JWT) link in a delegate chain."""

    def __init__(self, index: int, raw: str) -> None:
        self.index = index
        self.raw = raw
        parts = raw.split("~")
        self.jwt = parts[0]
        tail = parts[1:]
        # A trailing '~' yields a final empty element: no key-binding JWT.
        self.kb_jwt: str | None = None
        if tail and tail[-1] == "":
            tail = tail[:-1]
        elif tail and tail[-1].count(".") == 2:
            self.kb_jwt = tail[-1]
            tail = tail[:-1]
        self.disclosure_strings: list[str] = [item for item in tail if item]

        segments = self.jwt.split(".")
        if len(segments) != 3:
            raise ChainError(f"hop {index}: issuer JWT does not have three segments")
        self.header = decode_jwt_segment(segments[0])
        self.payload = decode_jwt_segment(segments[1])
        self.signing_input = f"{segments[0]}.{segments[1]}"
        self.signature = b64url_decode(segments[2])

        self.alg: str = self.header.get("alg", "")
        self.typ: str = self.header.get("typ", "")
        self.sd_alg: str = self.payload.get("_sd_alg", "sha-256")

        self.disclosures: dict[str, list[Any]] = {}
        for raw_disclosure in self.disclosure_strings:
            try:
                decoded = json.loads(b64url_decode(raw_disclosure))
            except Exception as exc:  # noqa: BLE001
                raise ChainError(f"hop {index}: undecodable disclosure: {exc}") from exc
            if not isinstance(decoded, list) or len(decoded) not in (2, 3):
                raise ChainError(f"hop {index}: malformed disclosure {decoded!r}")
            self.disclosures[digest_of(raw_disclosure, self.sd_alg)] = decoded

        self.used_digests: set[str] = set()
        self.resolved = self._resolve(self.payload)

    # -- selective disclosure resolution ---------------------------------

    def _resolve(self, node: Any) -> Any:
        if isinstance(node, dict):
            out: dict[str, Any] = {}
            for key, value in node.items():
                if key in ("_sd", "_sd_alg"):
                    continue
                out[key] = self._resolve(value)
            for sd_digest in node.get("_sd", []) or []:
                if not isinstance(sd_digest, str):
                    continue
                disclosure = self.disclosures.get(sd_digest)
                if disclosure is None:
                    continue  # undisclosed by design; not an error
                self.used_digests.add(sd_digest)
                if len(disclosure) != 3:
                    raise ChainError(
                        f"hop {self.index}: object disclosure must be [salt, name, value]"
                    )
                _, name, value = disclosure
                out[name] = self._resolve(value)
            return out
        if isinstance(node, list):
            out_list: list[Any] = []
            for element in node:
                if isinstance(element, dict) and set(element.keys()) == {"..."}:
                    ref = element["..."]
                    disclosure = self.disclosures.get(ref)
                    if disclosure is None:
                        out_list.append({"...": ref, "_undisclosed": True})
                        continue
                    self.used_digests.add(ref)
                    if len(disclosure) != 2:
                        raise ChainError(
                            f"hop {self.index}: array disclosure must be [salt, value]"
                        )
                    out_list.append(self._resolve(disclosure[1]))
                else:
                    out_list.append(self._resolve(element))
            return out_list
        return node

    # -- mandate extraction ----------------------------------------------

    def mandates(self) -> list[dict[str, Any]]:
        """Mandate content objects carried by this hop."""
        found: list[dict[str, Any]] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if isinstance(node.get("vct"), str) and node["vct"].startswith("mandate."):
                    found.append(node)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for element in node:
                    walk(element)

        walk(self.resolved)
        return found


def parse_chain(text: str) -> list[Hop]:
    text = text.strip()
    if text.startswith("{"):
        try:
            doc = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ChainError(f"input looks like JSON but does not parse: {exc}") from exc
        chain = doc.get("chain") or doc.get("presentation") or doc.get("sd_jwt")
        if not isinstance(chain, str):
            raise ChainError(
                'JSON input must carry the compact chain in a "chain" string property'
            )
        text = chain.strip()
    if not text:
        raise ChainError("empty input")
    hops = [Hop(i, raw) for i, raw in enumerate(text.split("~~")) if raw]
    if not hops:
        raise ChainError("no SD-JWT hops found")
    return hops


# --------------------------------------------------------------------------
# signature verification (optional dependency)
# --------------------------------------------------------------------------


def load_es256_key(jwk: dict[str, Any]):
    from cryptography.hazmat.primitives.asymmetric import ec

    if jwk.get("kty") != "EC" or jwk.get("crv") != "P-256":
        raise ValueError(f"unsupported JWK kty/crv: {jwk.get('kty')}/{jwk.get('crv')}")
    x = int.from_bytes(b64url_decode(jwk["x"]), "big")
    y = int.from_bytes(b64url_decode(jwk["y"]), "big")
    return ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()


def verify_es256(signing_input: str, signature: bytes, jwk: dict[str, Any]) -> None:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

    if len(signature) != 64:
        raise ValueError(f"ES256 signature must be 64 bytes, got {len(signature)}")
    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    key = load_es256_key(jwk)
    key.verify(
        encode_dss_signature(r, s), signing_input.encode("ascii"), ec.ECDSA(hashes.SHA256())
    )


def cryptography_available() -> bool:
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return False
    return True


# --------------------------------------------------------------------------
# constraint evaluation
# --------------------------------------------------------------------------


def _is_disclosed(entry: Any) -> bool:
    return not (isinstance(entry, dict) and entry.get("_undisclosed"))


def _revealed(entries: Any) -> list[Any]:
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if _is_disclosed(entry)]


def _matches(candidate: Any, allowed_entry: Any) -> bool:
    """An allowed entry matches when every field it declares is equal."""
    if not isinstance(candidate, dict) or not isinstance(allowed_entry, dict):
        return candidate == allowed_entry
    return all(candidate.get(key) == value for key, value in allowed_entry.items())


def _parse_iso8601(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _max_flow(capacity: dict[int, dict[int, int]], source: int, sink: int) -> int:
    """Edmonds-Karp on a tiny graph; used for checkout.line_items matching."""
    flow = 0
    while True:
        parents: dict[int, int] = {source: source}
        queue = [source]
        while queue and sink not in parents:
            node = queue.pop(0)
            for neighbour, cap in capacity.get(node, {}).items():
                if cap > 0 and neighbour not in parents:
                    parents[neighbour] = node
                    queue.append(neighbour)
        if sink not in parents:
            return flow
        bottleneck = float("inf")
        node = sink
        while node != source:
            bottleneck = min(bottleneck, capacity[parents[node]][node])
            node = parents[node]
        node = sink
        while node != source:
            prev = parents[node]
            capacity[prev][node] -= bottleneck
            capacity.setdefault(node, {})
            capacity[node][prev] = capacity[node].get(prev, 0) + bottleneck
            node = prev
        flow += int(bottleneck)


def evaluate_constraint(
    constraint: dict[str, Any],
    closed: dict[str, Any],
    checkout: dict[str, Any] | None,
) -> tuple[str, str]:
    """Return (status, detail) for one constraint against the closed mandate."""
    ctype = constraint.get("type")
    if ctype not in KNOWN_CONSTRAINTS:
        return FAIL, f"unknown constraint type {ctype!r} MUST fail evaluation"
    if ctype in STATEFUL_CONSTRAINTS:
        return SKIP, (
            f"{ctype} is stateful: it requires a persisted ledger of prior "
            "presentations that a single presentation cannot supply"
        )

    if ctype == "payment.amount_range":
        amount = closed.get("payment_amount")
        if not isinstance(amount, dict):
            return FAIL, "closed Payment Mandate has no payment_amount"
        if amount.get("currency") != constraint.get("currency"):
            return FAIL, (
                f"currency {amount.get('currency')!r} != constraint "
                f"{constraint.get('currency')!r}"
            )
        value = amount.get("amount")
        if not isinstance(value, int):
            return FAIL, f"payment_amount.amount must be integer minor units, got {value!r}"
        low = constraint.get("min")
        high = constraint.get("max")
        if isinstance(low, (int, float)) and value < low:
            return FAIL, f"amount {value} below min {low}"
        if isinstance(high, (int, float)) and value > high:
            return FAIL, f"amount {value} above max {high}"
        return PASS, f"amount {value} within [{low}, {high}] {amount.get('currency')}"

    if ctype == "payment.allowed_payees":
        allowed = _revealed(constraint.get("allowed"))
        if not allowed:
            return FAIL, "no revealed entries in allowed: constraint is invalid"
        payee = closed.get("payee")
        if any(_matches(payee, entry) for entry in allowed):
            return PASS, f"payee {payee!r} present in revealed allowed payees"
        return FAIL, f"payee {payee!r} not in revealed allowed payees"

    if ctype == "payment.allowed_payment_instruments":
        allowed = _revealed(constraint.get("allowed"))
        if not allowed:
            return FAIL, "no revealed entries in allowed: constraint is invalid"
        instrument = closed.get("payment_instrument")
        if any(_matches(instrument, entry) for entry in allowed):
            return PASS, "payment_instrument present in revealed allowed instruments"
        return FAIL, f"payment_instrument {instrument!r} not in revealed allowed instruments"

    if ctype == "payment.allowed_pisps":
        allowed = _revealed(constraint.get("allowed"))
        pisp = closed.get("pisp")
        if pisp is None:
            return FAIL, "constraint restricts PISPs but the closed mandate names none"
        if any(_matches(pisp, entry) for entry in allowed):
            return PASS, "pisp present in allowed PISPs"
        return FAIL, f"pisp {pisp!r} not in allowed PISPs"

    if ctype == "payment.execution_date":
        raw = closed.get("execution_date")
        if raw is None:
            return PASS, "no execution_date: immediate execution"
        when = _parse_iso8601(raw)
        if when is None:
            return FAIL, f"execution_date {raw!r} is not ISO 8601"
        for bound_name, comparator in (("not_before", "lt"), ("not_after", "gt")):
            bound_raw = constraint.get(bound_name)
            if not bound_raw:
                continue
            bound = _parse_iso8601(bound_raw)
            if bound is None:
                return FAIL, f"{bound_name} {bound_raw!r} is not ISO 8601"
            if comparator == "lt" and when < bound:
                return FAIL, f"execution_date {raw} earlier than not_before {bound_raw}"
            if comparator == "gt" and when > bound:
                return FAIL, f"execution_date {raw} later than not_after {bound_raw}"
        return PASS, f"execution_date {raw} within window"

    if ctype == "payment.reference":
        expected = constraint.get("conditional_transaction_id")
        if not expected:
            return FAIL, "payment.reference has no conditional_transaction_id"
        return SKIP, (
            "payment.reference requires the Checkout Mandate delegate chain to "
            f"confirm digest {expected!r}; present both chains to evaluate it"
        )

    if ctype == "checkout.allowed_merchants":
        allowed = _revealed(constraint.get("allowed"))
        if not allowed:
            return FAIL, "no revealed entries in allowed: constraint is invalid"
        if checkout is None:
            return SKIP, "checkout payload unavailable; supply --checkout-jwt-file"
        merchant = checkout.get("merchant")
        if any(_matches(merchant, entry) for entry in allowed):
            return PASS, "merchant present in revealed allowed merchants"
        return FAIL, f"merchant {merchant!r} not in revealed allowed merchants"

    if ctype == "checkout.line_items":
        if checkout is None:
            return SKIP, "checkout payload unavailable; supply --checkout-jwt-file"
        requirements = constraint.get("items") or []
        cart: dict[str, int] = {}
        for line in checkout.get("line_items") or []:
            product = line.get("product") if isinstance(line, dict) else None
            item_id = (product or {}).get("id") if isinstance(product, dict) else None
            if item_id is None and isinstance(line, dict):
                item_id = line.get("id")
            if item_id is None:
                continue
            cart[item_id] = cart.get(item_id, 0) + int(line.get("quantity", 1))
        if not cart:
            return FAIL, "checkout has no resolvable line items"

        source, sink = 0, 1
        capacity: dict[int, dict[int, int]] = {source: {}, sink: {}}
        req_nodes: dict[int, dict[str, Any]] = {}
        node = 2
        total_required = 0
        for requirement in requirements:
            quantity = int(requirement.get("quantity", 0))
            total_required += quantity
            capacity.setdefault(source, {})[node] = quantity
            req_nodes[node] = requirement
            node += 1
        item_nodes: dict[str, int] = {}
        for item_id, quantity in cart.items():
            item_nodes[item_id] = node
            capacity.setdefault(node, {})[sink] = quantity
            node += 1
        for req_node, requirement in req_nodes.items():
            acceptable = _revealed(requirement.get("acceptable_items"))
            for entry in acceptable:
                entry_id = entry.get("id") if isinstance(entry, dict) else None
                if entry_id in item_nodes:
                    capacity.setdefault(req_node, {})[item_nodes[entry_id]] = 10**9
        total_in_cart = sum(cart.values())
        flow = _max_flow(capacity, source, sink)
        if flow == total_required == total_in_cart:
            return PASS, f"line items matched ({flow} of {total_required})"
        return FAIL, (
            f"maximal flow {flow} != required {total_required} or cart total "
            f"{total_in_cart}; the checkout does not match the authorized items"
        )

    return FAIL, f"constraint {ctype!r} recognised but not implemented"


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------


def check_structure(hops: list[Hop], report: Report) -> None:
    for hop in hops:
        where = f"hop[{hop.index}]"
        if hop.alg == "ES256":
            report.ok("alg is ES256", f"typ={hop.typ or 'unset'}", where)
        elif hop.alg in ("EdDSA", "Ed25519"):
            report.fail(
                "signature algorithm",
                f"{hop.alg} is deterministic; AP2 requires a non-deterministic "
                "scheme so checkout_hash cannot be rainbow-tabled",
                where,
            )
        else:
            report.warn("signature algorithm", f"unexpected alg {hop.alg!r}", where)

        unused = set(hop.disclosures) - hop.used_digests
        if unused:
            report.fail(
                "disclosure digests resolve",
                f"{len(unused)} disclosure(s) match no digest in the payload: "
                f"{sorted(unused)[:3]}",
                where,
            )
        elif hop.disclosures:
            report.ok(
                "disclosure digests resolve",
                f"{len(hop.disclosures)} disclosure(s) resolved via {hop.sd_alg}",
                where,
            )


def check_chain_binding(hops: list[Hop], report: Report) -> None:
    if len(hops) == 1:
        report.skip(
            "sd_hash chain binding",
            "single-hop presentation: no open mandate to bind to",
            "chain",
        )
        return
    for index in range(1, len(hops)):
        previous, current = hops[index - 1], hops[index]
        where = f"hop[{index}]"
        sd_hash = current.payload.get("sd_hash")
        if not sd_hash:
            report.fail(
                "sd_hash chain binding",
                "delegate hop carries no sd_hash; it is not bound to the open mandate",
                where,
            )
            continue
        candidates = {
            digest_of(previous.raw, current.sd_alg): "hop as presented",
            digest_of(previous.raw.rstrip("~") + "~", current.sd_alg): "hop with trailing ~",
        }
        if sd_hash in candidates:
            report.ok(
                "sd_hash chain binding",
                f"binds to hop[{index - 1}] ({candidates[sd_hash]})",
                where,
            )
        else:
            report.fail(
                "sd_hash chain binding",
                f"sd_hash {sd_hash!r} does not match the preceding hop under "
                f"{current.sd_alg}",
                where,
            )


def check_mandates(
    hops: list[Hop],
    report: Report,
    now: int,
    checkout_jwt: str | None,
    expected_checkout_hash: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    all_mandates: list[dict[str, Any]] = []
    checkout_payload: dict[str, Any] | None = None
    terminal_index = len(hops) - 1

    for hop in hops:
        where = f"hop[{hop.index}]"
        mandates = hop.mandates()
        if not mandates:
            report.warn("mandate content present", "no mandate content in this hop", where)
            continue
        for mandate in mandates:
            all_mandates.append(mandate)
            vct = mandate.get("vct")
            if vct in KNOWN_VCTS:
                report.ok("vct is a known AP2 mandate type", str(vct), where)
            else:
                report.fail(
                    "vct is a known AP2 mandate type",
                    f"{vct!r} is not one of {sorted(KNOWN_VCTS)}; implementations "
                    "MUST match the exact string including the version suffix",
                    where,
                )
            is_open = vct in OPEN_VCTS

            if is_open:
                cnf = mandate.get("cnf")
                if isinstance(cnf, dict) and cnf.get("jwk"):
                    report.ok("open mandate carries cnf", "agent key is endorsed", where)
                else:
                    report.fail(
                        "open mandate carries cnf",
                        "an open mandate without cnf can be closed by any key",
                        where,
                    )
                if mandate.get("exp") is None:
                    report.fail(
                        "open mandate has exp",
                        "an open mandate with no expiry is a standing authorization",
                        where,
                    )
                else:
                    window = int(mandate["exp"]) - int(mandate.get("iat", now))
                    detail = f"exp in {window}s from iat"
                    if window > 86400:
                        report.warn(
                            "open mandate exp is task-scoped",
                            detail + "; AP2 RECOMMENDS the smallest window that "
                            "completes the task",
                            where,
                        )
                    else:
                        report.ok("open mandate exp is task-scoped", detail, where)
            elif hop.index == terminal_index and mandate.get("cnf"):
                report.warn(
                    "terminal closed mandate has no cnf",
                    "the reference SDK emits typ=kb+sd-jwt without cnf for the "
                    "terminal mandate",
                    where,
                )

            exp = mandate.get("exp")
            if isinstance(exp, int):
                if exp < now:
                    report.fail(
                        "mandate not expired",
                        f"exp {exp} ({datetime.fromtimestamp(exp, timezone.utc).isoformat()}) "
                        f"is before now {now}",
                        where,
                    )
                else:
                    report.ok("mandate not expired", f"{exp - now}s remaining", where)

            if vct == CLOSED_CHECKOUT_VCT:
                inline_jwt = mandate.get("checkout_jwt")
                claimed = mandate.get("checkout_hash")
                source_jwt = inline_jwt if isinstance(inline_jwt, str) else checkout_jwt
                if not claimed:
                    report.fail(
                        "checkout_hash present", "closed Checkout Mandate requires it", where
                    )
                elif source_jwt is None:
                    report.skip(
                        "checkout_hash matches checkout_jwt",
                        "checkout_jwt not disclosed; pass --checkout-jwt-file to check",
                        where,
                    )
                else:
                    recomputed = digest_of(source_jwt.strip(), hop.sd_alg)
                    if recomputed == claimed:
                        report.ok(
                            "checkout_hash matches checkout_jwt",
                            f"{claimed[:16]}… under {hop.sd_alg}",
                            where,
                        )
                    else:
                        report.fail(
                            "checkout_hash matches checkout_jwt",
                            f"claimed {claimed!r} != recomputed {recomputed!r}; the "
                            "cart changed after signing or the mandate was swapped",
                            where,
                        )
                if isinstance(inline_jwt, str) and inline_jwt.count(".") == 2:
                    try:
                        checkout_payload = decode_jwt_segment(inline_jwt.split(".")[1])
                    except ChainError:
                        checkout_payload = None

            if vct == CLOSED_PAYMENT_VCT:
                for field in ("transaction_id", "payee", "payment_amount", "payment_instrument"):
                    if mandate.get(field) is None:
                        report.fail(
                            "closed Payment Mandate is complete",
                            f"required field {field!r} is missing",
                            where,
                        )
                amount = mandate.get("payment_amount")
                if isinstance(amount, dict) and not isinstance(amount.get("amount"), int):
                    report.fail(
                        "payment_amount uses integer minor units",
                        f"got {amount.get('amount')!r}; ISO 4217 minor units are integers "
                        "(19900 = $199.00)",
                        where,
                    )
                elif isinstance(amount, dict):
                    report.ok(
                        "payment_amount uses integer minor units",
                        f"{amount.get('amount')} {amount.get('currency')}",
                        where,
                    )

    checkout_hashes = {
        m.get("checkout_hash") for m in all_mandates if m.get("vct") == CLOSED_CHECKOUT_VCT
    }
    checkout_hashes.discard(None)
    if expected_checkout_hash:
        checkout_hashes.add(expected_checkout_hash)
    if checkout_jwt and not checkout_hashes:
        checkout_hashes.add(digest_of(checkout_jwt.strip()))

    transaction_ids = {
        m.get("transaction_id") for m in all_mandates if m.get("vct") == CLOSED_PAYMENT_VCT
    }
    transaction_ids.discard(None)

    if not transaction_ids:
        report.skip(
            "transaction_id equals checkout_hash",
            "no closed Payment Mandate in this presentation",
            "chain",
        )
    elif not checkout_hashes:
        report.skip(
            "transaction_id equals checkout_hash",
            "no Checkout Mandate or checkout hash supplied; pass --checkout-jwt-file "
            "or --checkout-hash",
            "chain",
        )
    elif transaction_ids <= checkout_hashes:
        report.ok(
            "transaction_id equals checkout_hash",
            "the Payment Mandate is bound to its Checkout",
            "chain",
        )
    else:
        report.fail(
            "transaction_id equals checkout_hash",
            f"transaction_id {sorted(transaction_ids)} != checkout_hash "
            f"{sorted(checkout_hashes)}; a Payment Mandate bound to a different "
            "checkout is the manipulated-checkout attack",
            "chain",
        )

    return all_mandates, checkout_payload


def check_constraints(
    mandates: list[dict[str, Any]],
    report: Report,
    checkout_payload: dict[str, Any] | None,
) -> None:
    open_mandates = [m for m in mandates if m.get("vct") in OPEN_VCTS]
    closed_payment = next(
        (m for m in mandates if m.get("vct") == CLOSED_PAYMENT_VCT), None
    )
    closed_checkout = next(
        (m for m in mandates if m.get("vct") == CLOSED_CHECKOUT_VCT), None
    )
    if not open_mandates:
        report.skip("constraint evaluation", "no open mandate in this presentation", "chain")
        return

    for mandate in open_mandates:
        vct = mandate.get("vct")
        closed = closed_payment if vct == OPEN_PAYMENT_VCT else closed_checkout
        constraints = mandate.get("constraints") or []
        if not constraints:
            report.fail(
                "open mandate carries constraints",
                f"{vct} with no constraints authorizes the agent without bounds",
                vct or "open mandate",
            )
            continue
        if closed is None:
            report.skip(
                "constraint evaluation",
                f"{vct} present but its closed counterpart is not in this presentation",
                vct or "open mandate",
            )
            continue
        for constraint in constraints:
            if not isinstance(constraint, dict):
                report.fail("constraint evaluation", f"malformed constraint {constraint!r}", vct)
                continue
            status, detail = evaluate_constraint(constraint, closed, checkout_payload)
            report.add(status, f"constraint {constraint.get('type')}", detail, vct or "")

    if closed_payment is not None:
        payment_constraints = {
            c.get("type")
            for m in open_mandates
            if m.get("vct") == OPEN_PAYMENT_VCT
            for c in (m.get("constraints") or [])
            if isinstance(c, dict)
        }
        bounds_money = "payment.amount_range" in payment_constraints
        bounds_payee = bool(
            payment_constraints & {"payment.allowed_payees", "payment.reference"}
        )
        if bounds_money and bounds_payee:
            report.ok(
                "open Payment Mandate bounds amount and counterparty",
                "amount_range plus allowed_payees/reference",
                "audit",
            )
        else:
            report.fail(
                "open Payment Mandate bounds amount and counterparty",
                "an open Payment Mandate needs both a money bound "
                "(payment.amount_range) and a counterparty bound "
                "(payment.allowed_payees or payment.reference); missing "
                + ("amount bound " if not bounds_money else "")
                + ("counterparty bound" if not bounds_payee else ""),
                "audit",
            )


def check_signatures(hops: list[Hop], report: Report, root_jwk: dict[str, Any] | None) -> None:
    if not cryptography_available():
        report.skip(
            "ES256 signature verification",
            "the `cryptography` package is not installed; install it with "
            "`pip install cryptography` — a skipped signature check is NOT a pass",
            "chain",
        )
        return

    for hop in hops:
        where = f"hop[{hop.index}]"
        jwk: dict[str, Any] | None = None
        source = ""
        if hop.index == 0:
            if root_jwk:
                jwk, source = root_jwk, "--jwk-file"
        else:
            for mandate in hops[hop.index - 1].mandates():
                cnf = mandate.get("cnf")
                if isinstance(cnf, dict) and isinstance(cnf.get("jwk"), dict):
                    jwk, source = cnf["jwk"], f"cnf.jwk of hop[{hop.index - 1}]"
                    break
        if jwk is None:
            report.skip(
                "ES256 signature verification",
                "no verification key available for this hop"
                + (
                    " (root issuer key: pass --jwk-file)"
                    if hop.index == 0
                    else " (preceding hop endorsed no cnf.jwk)"
                ),
                where,
            )
            continue
        try:
            verify_es256(hop.signing_input, hop.signature, jwk)
        except Exception as exc:  # noqa: BLE001 - any failure is a verification failure
            report.fail("ES256 signature verification", f"{type(exc).__name__}: {exc}", where)
        else:
            report.ok("ES256 signature verification", f"key from {source}", where)


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def load_jwk(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    if isinstance(doc, dict) and "keys" in doc:
        keys = doc["keys"]
        if not keys:
            raise ValueError(f"{path}: JWKS contains no keys")
        return keys[0]
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: expected a JWK object or JWKS")
    return doc


def render_text(report: Report, quiet: bool) -> str:
    lines: list[str] = []
    order = {FAIL: 0, WARN: 1, SKIP: 2, PASS: 3}
    for entry in sorted(report.checks, key=lambda e: order[e["status"]]):
        if quiet and entry["status"] in (PASS, SKIP):
            continue
        where = f" [{entry['where']}]" if entry["where"] else ""
        detail = f" — {entry['detail']}" if entry["detail"] else ""
        lines.append(f"{entry['status']:4} {entry['check']}{where}{detail}")
    counts = report.counts()
    lines.append("")
    lines.append(
        f"{counts[PASS]} passed, {counts[FAIL]} failed, "
        f"{counts[WARN]} warnings, {counts[SKIP]} skipped"
    )
    if counts[SKIP]:
        lines.append("Skipped checks were NOT verified. Do not report them as passing.")
    lines.append("RESULT: " + ("FAIL" if report.failed else "PASS"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify an AP2 mandate chain (structure, bindings, constraints, signatures).",
        epilog="Exit codes: 0 pass, 1 verification failure, 2 usage/parse error.",
    )
    parser.add_argument("chain_file", help="compact SD-JWT chain, JSON wrapper, or '-' for stdin")
    parser.add_argument("--checkout-jwt-file", help="merchant-signed checkout JWT")
    parser.add_argument("--checkout-hash", help="expected checkout hash (base64url)")
    parser.add_argument("--jwk-file", help="JWK or JWKS for the root issuer key")
    parser.add_argument("--now", type=int, default=None, help="override current epoch seconds")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit a JSON report")
    parser.add_argument("--quiet", action="store_true", help="text mode: show only FAIL and WARN")
    args = parser.parse_args(argv)

    try:
        raw_chain = read_input(args.chain_file)
    except OSError as exc:
        print(f"error: cannot read {args.chain_file}: {exc}", file=sys.stderr)
        return 2

    checkout_jwt = None
    if args.checkout_jwt_file:
        try:
            checkout_jwt = read_input(args.checkout_jwt_file).strip()
        except OSError as exc:
            print(f"error: cannot read {args.checkout_jwt_file}: {exc}", file=sys.stderr)
            return 2

    root_jwk = None
    if args.jwk_file:
        try:
            root_jwk = load_jwk(args.jwk_file)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    try:
        hops = parse_chain(raw_chain)
    except ChainError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    now = args.now if args.now is not None else int(time.time())
    report = Report()
    check_structure(hops, report)
    check_chain_binding(hops, report)
    mandates, checkout_payload = check_mandates(
        hops, report, now, checkout_jwt, args.checkout_hash
    )
    if checkout_payload is None and checkout_jwt and checkout_jwt.count(".") == 2:
        try:
            checkout_payload = decode_jwt_segment(checkout_jwt.split(".")[1])
        except ChainError:
            checkout_payload = None
    check_constraints(mandates, report, checkout_payload)
    check_signatures(hops, report, root_jwk)

    if args.as_json:
        print(
            json.dumps(
                {
                    "result": "FAIL" if report.failed else "PASS",
                    "hops": len(hops),
                    "mandates": [m.get("vct") for m in mandates],
                    "counts": report.counts(),
                    "checks": report.checks,
                    "checked_at": datetime.fromtimestamp(now, timezone.utc).isoformat(),
                },
                indent=2,
            )
        )
    else:
        print(render_text(report, args.quiet))

    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
