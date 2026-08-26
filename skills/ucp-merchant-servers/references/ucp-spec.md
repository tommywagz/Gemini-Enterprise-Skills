# Universal Commerce Protocol (UCP) Specification Reference

This document serves as the technical reference for the Universal Commerce Protocol (UCP). It covers discovery profiles, standard endpoints for capabilities/extensions, RFC 9421 request signature verification, and webhook-based order tracking.

## Table of Contents
- [1. Discovery Profile (`/.well-known/ucp`)](#1-discovery-profile-well-knownucp)
  - [1.1 Complete Discovery JSON Example](#11-complete-discovery-json-example)
- [2. Core Capabilities & Extensions](#2-core-capabilities--extensions)
  - [2.1 Cart Capability](#21-cart-capability)
  - [2.2 Checkout Capability](#22-checkout-capability)
  - [2.3 Extensions](#23-extensions)
- [3. Cryptographic Request Signatures (RFC 9421)](#3-cryptographic-request-signatures-rfc-9421)
  - [3.1 Verification Mechanics](#31-verification-mechanics)
- [4. Webhook Signing & Outbound Delivery](#4-webhook-signing--outbound-delivery)
  - [4.1 Webhook Signing Flow](#41-webhook-signing-flow)
  - [4.2 Retry & Backoff](#42-retry--backoff)

---

## 1. Discovery Profile (`/.well-known/ucp`)

A UCP-compliant business server MUST publish a discovery manifest at the path `/.well-known/ucp` over HTTPS. This JSON file enables commerce agents to dynamically query the supported services, capability extensions, and payment methods.

### 1.1 Complete Discovery JSON Example
```json
{
  "ucp": {
    "version": "2026-04-08",
    "services": {
      "dev.ucp.shopping": {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping",
        "rest": {
          "schema": "https://ucp.dev/2026-04-08/services/shopping/openapi.json",
          "endpoint": "http://localhost:8182/"
        },
        "mcp": null,
        "a2a": null,
        "embedded": null
      }
    },
    "capabilities": [
      {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping/checkout",
        "schema": "https://ucp.dev/2026-04-08/schemas/shopping/checkout.json",
        "extends": null,
        "config": null
      },
      {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping/discount",
        "schema": "https://ucp.dev/2026-04-08/schemas/shopping/discount.json",
        "extends": "dev.ucp.shopping.checkout",
        "config": null
      },
      {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping/fulfillment",
        "schema": "https://ucp.dev/2026-04-08/schemas/shopping/fulfillment.json",
        "extends": "dev.ucp.shopping.checkout",
        "config": null
      }
    ]
  },
  "payment": {
    "handlers": [
      {
        "id": "mock_payment_handler",
        "name": "dev.ucp.mock_payment",
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/mock",
        "config_schema": "https://ucp.dev/2026-04-08/schemas/mock.json",
        "instrument_schemas": [
          "https://ucp.dev/2026-04-08/schemas/shopping/types/card_payment_instrument.json"
        ],
        "config": {
          "supported_tokens": ["success_token", "fail_token"]
        }
      }
    ]
  },
  "keys": null
}
```

---

## 2. Core Capabilities & Extensions

### 2.1 Cart Capability
Manages pre-purchase state (item collections, variants, pricing, and initial quantities).
- **Create Cart:** `POST /carts`
  - Body: `{"line_items": [{"item_id": "item_1", "quantity": 1}]}`
- **Get Cart:** `GET /carts/{id}`
- **Update Cart:** `PUT /carts/{id}`
- **Cancel Cart:** `POST /carts/{id}/cancel`

### 2.2 Checkout Capability
Negotiates the commerce transaction. Coordinates lines, buyer profile, totals, discounts, and payments.
- **Create Checkout:** `POST /checkout-sessions`
  - Header `UCP-Agent: profile="https://agent.example/profile"` is required to discover the buyer platform key and delivery webhooks.
  - Body: `{"line_items": [...], "buyer": {"full_name": "...", "email": "..."}, "currency": "USD"}`
- **Get Checkout:** `GET /checkout-sessions/{id}`
- **Update Checkout:** `PUT /checkout-sessions/{id}`
  - Modifies line items, buyer info, discount codes (`discounts.codes: ["10OFF"]`), or fulfillment address/option details.
- **Complete Checkout:** `POST /checkout-sessions/{id}/complete`
  - Finalizes the order. Expects payment configuration.
  - Body: `{"payment": {"selected_instrument_id": "...", "instruments": [...]}, "risk_signals": {}}`
- **Cancel Checkout:** `POST /checkout-sessions/{id}/cancel`

### 2.3 Extensions
Extends base capabilities using `allOf` JSON Schema composition:
1. **Fulfillment Extension:** Augments checkout with delivery details (address, selected option ID, available shipping option methods).
2. **Discount Extension:** Manages discount input codes (`codes: ["10OFF"]`) and applied coupon data structures (allocations, priorities, calculations).
3. **AP2 Mandate Extension:** Integrates Checkout and Payment Mandates using detached JWS signatures, verifying cryptographic authorization for autonomous agents.

---

## 3. Cryptographic Request Signatures (RFC 9421)

All inbound state-changing client requests MUST be signed when `--require_signatures` is enabled.

### 3.1 Verification Mechanics
1. **Header Inspection:**
   - Locate the `UCP-Agent` header containing the profile URL: `UCP-Agent: profile="https://agent.example/profile"`.
   - Locate the RFC 9421 `Signature` and `Signature-Input` headers.
   - Locate the RFC 9530 `Content-Digest` header (e.g. `sha-256=:raw-bytes-base64=:`).
2. **Key Resolution:**
   - Fetch the agent's public keys from the resolved `keys[]` or `ucp.keys[]` list at the `UCP-Agent` profile URL.
3. **Signature Verification:**
   - Reconstruct the signed HTTP headers listed in `Signature-Input` (typical target table: `@method`, `@authority`, `@path`, `@query`, `content-digest`, `content-type`, `idempotency-key`, `ucp-agent`).
   - Recompute and verify the `Content-Digest` over the request's raw JSON body bytes.
   - Verify the cryptographic signature using the resolved public key (`ES256` or `Ed25519`).
4. **Error Handling:**
   - Return standard HTTP 401/400 errors: `signature_missing`, `signature_invalid`, `key_not_found`, `digest_mismatch`, `algorithm_unsupported`.

---

## 4. Webhook Signing & Outbound Delivery

Outbound order-event notifications (e.g. `order_shipped`, `order_delivery_updated`) must be delivered as signed webhooks with exponential backoff retry.

### 4.1 Webhook Signing Flow
- Every outgoing webhook POST contains standard headers:
  - `Webhook-Id`: Unique event UUID.
  - `Webhook-Timestamp`: Integer timestamp.
  - `UCP-Agent`: This server's own discovery profile URL.
  - `Content-Digest`: RFC 9530 body hash.
  - `Signature` & `Signature-Input`: Covering standard headers and pseudo-headers.
- The platform verifies webhook signatures using the business's public key published in the profile's `signing_keys[]`.

### 4.2 Retry & Backoff
- On transient HTTP errors (5xx, timeouts):
  - Retry the delivery with exponential backoff (e.g., initial delay `0.5s` doubling per retry up to limit of `3` attempts).
  - Retried attempts MUST preserve the same `Webhook-Id` and `Idempotency-Key` for deduplication.
  - 4xx client errors represent permanent failure and MUST NOT be retried.
