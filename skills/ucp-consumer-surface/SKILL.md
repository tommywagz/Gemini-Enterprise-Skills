---
name: ucp-consumer-surface
description: "Skill for building the client / consumer surface of a Universal Commerce Protocol (UCP) integration: a shopping agent or platform that negotiates capabilities against a business's discovery profile, searches/looks up catalog items, builds carts, drives native or embedded checkout to completion, and tracks orders via webhook. TRIGGER when: 'UCP shopping agent', 'UCP consumer client', 'UCP platform integration', 'buy/book/order X through UCP', 'negotiate UCP capabilities', 'UCP checkout client', 'UCP-Agent header'. DO NOT TRIGGER when: building the server/business side of UCP (use ucp-merchant-servers), authoring new UCP extensions/schemas, or wiring AP2 payment mandates beyond submitting a basic payment instrument (use an AP2-specific skill)."
version: 1.0.0
author: Google
tags: [ucp, consumer-surface, shopping-agent, commerce, client, python]
license: Apache-2.0
compatibility: ucp-spec >= 2026-01-11 (validated against 2026-08-25)
metadata: {}
---

- UCP Consumer Surface / Shopping Agent Builder

- Overview
The Universal Commerce Protocol (UCP) lets a shopping platform (this skill's
output) negotiate capabilities with any compliant business, search/browse its
catalog, assemble a cart, drive a checkout session to completion, and track
the resulting order — all through the same reverse-domain-namespaced
capability model regardless of which business is on the other end. This skill
builds the client half only: it never implements business-side routes, a
`/.well-known/ucp` profile to serve, or payment-handler settlement logic —
that is `ucp-merchant-servers`. Success looks like a client that discovers
capabilities defensively (validating namespace authority before trusting a
schema), degrades gracefully when a capability or payment handler isn't
advertised, and never treats a `200` response as success without checking
`ucp.status` and `messages[]`.

- Prerequisites
- Python >= 3.9 for the bundled `scripts/ucp_client_helper.py` (stdlib-only:
  `urllib`, `http.server`, `hashlib`, `json` — no `pip install` required).
- The target business's base URL (its `/.well-known/ucp` profile must be
  reachable at `<base_url>/.well-known/ucp`).
- This platform's own discovery profile URL to publish in the `UCP-Agent`
  header (`profile="https://platform.example/.well-known/ucp"`), and, if the
  business requires signed requests, an ES256/RSA keypair whose public half
  is served from that profile.

- Workflow

- Step 1: Discover and validate the business's capability profile
`GET <base_url>/.well-known/ucp` (no auth required for discovery itself).
Parse the top-level `ucp` object — fall back to the response root for
flat/legacy profiles. For every declared `capabilities[name][]` and
`services[name][]` entry, validate that its `schema` URL's host is
authorized for that reverse-domain `name` **before** fetching that schema or
trusting the entity — see `references/ucp_client_negotiation.md` for the
label-alignment derivation algorithm, or call
`ucp_client_helper.validate_authority_binding(name, schema_url)` directly.
Reject (treat as absent, never activate) any entity that fails this check.
- If a required capability (e.g. `dev.ucp.shopping.checkout`) is absent:
  stop and report to the caller which capability is missing rather than
  guessing at undocumented endpoints.
- If multiple transports are advertised (`rest`, `mcp`, `a2a`, `embedded`)
  for the same service: prefer the transport this platform already has a
  client for; fall back to REST as the baseline (all UCP businesses that
  support REST use the same endpoint-resolution rule: append the OpenAPI
  path to `services[name][].endpoint`).

- Step 2: Negotiate payment handlers
Read `payment_handlers` from the profile into a set of supported handler
`id`s. Never hardcode a `handler_id` in a later `Complete Checkout` call
without first confirming it appears in this set for the current business —
handler support varies per merchant.

- Step 3: Search or look up the catalog (optional, when browsing precedes a known SKU)
Use `POST /catalog/search` (free-text `query`, `filters`, `pagination`) or
`POST /catalog/lookup` (batch `ids`) against the resolved `dev.ucp.shopping`
REST endpoint to resolve product/variant identifiers before cart-building.
Treat `context` (country/region/postal code) as provisional localization
input only — never as authoritative eligibility or tax data. See
`references/ucp_client_negotiation.md` for the shared `context`/`signals`
fields reused across catalog, cart, and checkout requests.

- Step 4: Build the cart
`POST /carts` with `line_items` (each `{"item": {"id": ...}, "quantity": ...}`)
via `UCPClient.create_cart`. To change contents later, call `update_cart`
with the **complete** desired `line_items` array — Cart Update is a full
replacement, not a patch; omitting an existing line item removes it.
- If the response has `ucp.status: "error"` with `unrecoverable` severity
  (e.g. `out_of_stock`): no cart resource was created — do not attempt to
  `GET` the returned id.
- To apply a discount code, add `discounts.codes: [...]` to the update
  payload and read `discounts.applied[]` / `messages[]` for the outcome.

- Step 5: Convert the cart to a checkout session
`POST /checkout-sessions` with `{"cart_id": ...}` (preferred — inherits
line items, currency, and discounts) or with raw `line_items` for a
cart-less flow. Then progressively fill required fields with `PUT
/checkout-sessions/{id}` (again, full replacement — always echo back
existing `buyer`/`line_items`/`fulfillment` alongside new fields):
1. Add `buyer` (email, name).
2. Add `fulfillment.methods[].destinations[]`; read back the
   business-generated `groups[].options[]` rate quotes.
3. Set `selected_destination_id` and `groups[].selected_option_id` to lock
   in the shipping method.
Poll `status` after each update: `incomplete` → keep filling fields named in
`messages[].path`; `ready_for_complete` → proceed to Step 6.
- If `status` is `complete_in_progress`: do **not** send another Update
  Checkout call for this session — a completion is already running;
  `ucp_client_helper.UCPClient.update_checkout` raises
  `UCPBusinessOutcomeError` if you try.

- Step 6: Complete the checkout
`POST /checkout-sessions/{id}/complete` with `payment.instruments[]`
referencing a `handler_id` confirmed in Step 2. This endpoint places an
order and is irreversible for this client: first show the buyer the final
items, total/currency, fulfillment selection, and selected payment handler,
then obtain explicit confirmation in the current interaction. Pass only the
current discovery result as `allowed_handler_ids` and `user_confirmed=True`
to `UCPClient.complete_checkout`; it rejects missing confirmation and
unadvertised handlers. A successful response has
`status: "completed"` and an `order.id` / `order.permalink_url`. See
`references/ucp_cart_checkout.md` for the full request/response shape and
`assets/checkout_payload_templates.json` for a copy-paste starting payload.

- Step 7: Track the order and verify webhook deliveries
`GET /orders/{id}` for a point-in-time snapshot, and/or register for the
**Order Event Webhook** for asynchronous push updates (shipped, delivered,
refunded). Before trusting any inbound webhook payload:
1. Recompute and compare its `Content-Digest` (`verify_content_digest`).
2. Confirm its `Idempotency-Key`/`Webhook-Id` has not already been
   processed (replay protection — a rejected duplicate is not an error, it
   is the expected retry-safety behavior).
3. If the business signs webhook deliveries (RFC 9421), resolve its public
   key from the validated discovery profile and supply a real cryptographic
   verifier callback to `verify_webhook_delivery`. Set
   `signature_required=True` when signing is declared; the helper rejects a
   missing signature or verifier and does not treat parsing as verification.
Delegate any post-purchase action this client doesn't model (returns,
exchanges, disputes) to `order.permalink_url` rather than reimplementing it.

- Examples

- Example 1: Full happy-path purchase
Input: "Buy 2 of item_123 from business.example.com and ship it to a
Springfield, IL address."
Expected output / behavior: discover the profile and validate authority
binding → confirm `dev.ucp.shopping.cart`/`checkout` capabilities and a
usable payment handler are advertised → create a cart with the line item →
convert to checkout → fill buyer + fulfillment fields across two `PUT`
calls until `status` is `ready_for_complete` → complete with a payment
instrument for a supported handler → return the `order.id` and
`permalink_url`. `scripts/ucp_client_helper.py selftest` exercises this
exact sequence end-to-end against a bundled mock server with no network
access.

- Example 2: Capability not supported
Input: "This business doesn't have a `discount` extension active but I have
a discount code."
Expected output / behavior: check `capabilities` from discovery before
sending `discounts.codes` — if `dev.ucp.shopping.discount` is absent, tell
the user the code cannot be applied here rather than sending it and hoping
the business ignores it silently.

- Error Handling
- **Two-layer error model**: HTTP status codes signal transport failures
  (`400`/`401`/`409`/`429`/`5xx`); a `200` response can still carry
  `ucp.status: "error"` in the body (a business outcome, e.g.
  `out_of_stock`, `not_found`). Always check `messages[]` on every response,
  not only on non-2xx status — `ucp_client_helper.py`'s `_decode_business_response`
  raises `UCPBusinessOutcomeError` for the latter so both paths surface the
  same way to calling code.
- **Authority binding failure**: if a capability's or service's `schema` URL
  fails the namespace-authority check, treat that entity as not present —
  do not fetch its schema and do not activate the capability, even if the
  rest of the profile parses cleanly.
- **Idempotency-Key reuse with a different body**: expect `409 Conflict`;
  never blindly retry with a changed payload under the same key — retries
  of the *same* logical operation must resend an identical body. Pass the
  original `idempotency_key` argument again to the relevant helper method;
  each method otherwise creates a fresh key for a new operation.
- **Missing reference files**: if `references/*.md` are unavailable, fall
  back to the live spec index at `https://ucp.dev/llms.txt` (and the
  version-pinned `https://ucp.dev/<version>/llms.txt`) as the source of
  truth rather than guessing endpoint shapes from memory.

- Anti-Patterns to Avoid
- **Trusting discovery without authority binding**: never fetch or activate
  a capability/service whose `schema` host doesn't match its reverse-domain
  name — this is the mechanism that stops a malicious or misconfigured
  profile from smuggling in an unrelated schema.
- **Partial Cart/Checkout Update payloads**: both are full-replacement
  operations; sending only the new field silently drops every other field
  (line items, buyer, fulfillment) not included in that call.
- **Ignoring `messages[].path`**: the business tells you exactly which
  field is missing or invalid via JSONPath in `messages[]` — resubmitting
  the whole payload again unchanged after an `incomplete` response, instead
  of reading `path`, causes infinite retry loops.
- **Hardcoding a payment `handler_id`**: always source it from the
  business's own `payment_handlers` discovery/checkout response, never from
  a previous integration with a different business.
- **Skipping webhook verification**: never act on a delivered order-status
  webhook without checking its content digest and idempotency key first; for
  a signed delivery, also require a cryptographic signature verifier.

- Reference Files
- **references/ucp_client_negotiation.md**: discovery-profile shape,
  authority binding derivation algorithm, required headers, RFC 9421/9530
  signing, and the two-layer error model.
- **references/ucp_cart_checkout.md**: cart operations, cart-to-checkout
  conversion, the checkout status state machine, native vs. embedded
  checkout, and the order lifecycle/webhook.
- **scripts/ucp_client_helper.py**: stdlib-only `UCPClient` implementing
  discovery + authority validation, cart/checkout/order operations, and
  webhook verification helpers. Run `python3 scripts/ucp_client_helper.py
  selftest --verbose` to regression-test the full lifecycle against a
  bundled in-process mock server (no network, no dependencies), or
  `discover --base-url <url>` against a real business.
- **assets/ucp_client_profile_schema.json**: JSON Schema (Draft 2020-12) for
  the client-consumed subset of a discovery profile — validate a fetched
  profile against it before parsing.
- **assets/checkout_payload_templates.json**: literal example request/
  response bodies for every cart/checkout/order operation and a sample
  order-event webhook delivery, for quick manual testing or as starting
  payloads to adapt.

- Output Format
This skill produces working client code (or, when asked to just execute a
purchase, the actual API call sequence and its outcome) that: validates
authority binding on every discovered entity, never sends partial Cart/
Checkout Update payloads, checks `messages[]` on every response regardless
of HTTP status, sources payment `handler_id`s from that business's own
discovery data, and verifies webhook deliveries before acting on them. When
producing a standalone script, ground it in `ucp_client_helper.py`'s
functions rather than reimplementing discovery or signing from scratch.
