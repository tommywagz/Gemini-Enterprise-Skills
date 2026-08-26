---
name: ucp-merchant-servers
description: "Skill for standing up and implementing a UCP (Universal Commerce Protocol) compliant Merchant or Business Server. TRIGGER when: 'UCP merchant server', 'UCP business server', 'UCP server integration', 'UCP shopping service', 'UCP capability profile'. DO NOT TRIGGER when: client-side shopping agents or buying clients (use ucp-consumer-surface-shopping-agents)."
version: 1.0.0
author: Google
tags: [ucp, merchant-server, business-server, commerce, python, nodejs]
license: Apache-2.0
compatibility: ucp-spec >= 2026-04-08
metadata: {}
---

- UCP Business/Merchant Server Builder

- Overview
The Universal Commerce Protocol (UCP) standardizes how AI agents discover capabilities, assemble carts, manage checkout sessions, and settle transactions with online businesses. 
This skill guides the implementation of the server-side architecture of a UCP integration: defining a public capability discovery manifest, routing checkout and cart session states, implementing security signatures (RFC 9421/9530), and firing transaction event webhooks.

- Prerequisites
- Python >= 3.12 (with FastAPI/uv) OR Node.js >= 20 (with Hono/Zod)
- SQLite database files for products and transaction tracking
- Outbound network access for profile/key resolution, and inbound/outbound HTTPS for secure transaction handoffs

- Workflow

- Step 1: Establish the Discovery Profile
Deploy a static JSON document at `/.well-known/ucp` to declare your business capabilities.
- Declare the base UCP spec version (e.g. `2026-04-08`).
- Define services (e.g. `dev.ucp.shopping`) with their REST endpoints and schema OpenAPI references.
- Map the supported capabilities (e.g., checkout, fulfillment, discounts) and their corresponding JSON Schema targets.
- Declare supported payment handlers (e.g., `google_pay`, `shop_pay`, `mock_payment_handler`) with their config metadata and instrument schemas.
- Refer to `references/ucp-spec.md` Section 1 for a complete compliant manifest example.

- Step 2: Scaffolding Routing and Database Layout
Select your target language stack and scaffold the application:
- **For Python/FastAPI:** Set up routes and services using `uv` environment mapping. Refer to `references/python-fastapi-merchant.md` for folder structures and database import parameters.
- **For Node.js/Hono:** Set up Hono routing and Zod schemas. Refer to `references/nodejs-hono-merchant.md` for folder layouts and environment variable configs.
- Maintain separate SQLite databases: `products.db` (product listings/variants) and `transactions.db` (cart and checkout sessions).

- Step 3: Implement Cart & Checkout State Engines
Implement stateful REST endpoints for both Cart and Checkout capabilities:
- **Cart API:** Expose endpoints for `POST /carts`, `GET /carts/{id}`, `PUT /carts/{id}`, and `POST /carts/{id}/cancel` to manage items pre-purchase.
- **Checkout Session API:** Expose `POST /checkout-sessions` (creates transaction session), `GET /checkout-sessions/{id}`, `PUT /checkout-sessions/{id}` (applies discounts or updates fulfillment), and `POST /checkout-sessions/{id}/complete` (processes payment and triggers order generation).
- **Session State Transitions:** Only allow completion if state is `ready_for_complete`. Set checkout status to `completed` once transaction resolves successfully.
- Refer to `references/ucp-spec.md` Section 2 for core JSON request/response conventions.

- Step 4: Hook Request Signature Verification Middleware (RFC 9421)
Secure your API endpoints against replay attacks and unauthorized access:
- Parse the incoming `UCP-Agent` header to extract the caller platform's profile URL.
- Fetch the public keys (`keys[]` or `ucp.keys[]`) from the parsed profile endpoint. Cache keys locally to prevent severe performance bottlenecks.
- Verify the signature over signed headers (specifically `@method`, `@authority`, `@path`, `content-digest`, `idempotency-key`, and `ucp-agent`) using the resolved key.
- Verify the request body bytes match the SHA-256 hash provided in the `Content-Digest` header.
- Reject unsigned/corrupt requests with appropriate UCP error responses (e.g., `signature_invalid`, `digest_mismatch`).
- Refer to `references/ucp-spec.md` Section 3 for implementation mechanics.

- Step 5: Implement Webhook Delivery & Retries
Send transaction status updates (e.g., shipping updates) to the buyer platform:
- Construct the notification payload containing order tracking status.
- Sign the outbound webhook POST payload using your private signing key. Ensure standard headers (`Webhook-Id`, `Webhook-Timestamp`, `Signature`, `Signature-Input`, `Content-Digest`) are populated.
- Implement exponential backoff for failed webhook deliveries: double retry delays (e.g., starting at `0.5s`) up to a maximum of `3` total attempts. Do not retry on permanent 4xx client rejection errors.
- Ensure retries reuse the identical `Webhook-Id` and `Idempotency-Key`.
- Refer to `references/ucp-spec.md` Section 4 for webhook standards.

- Examples

- Example 1: Creating a Checkout Session
Input: A platform agent initiates checkout with a request containing `line_items`, `buyer` details, and `currency` set to `USD`.
Expected output / behavior:
1. The server validates line items against the products database.
2. The server creates a unique session UUID and calculates total pricing.
3. The server responds with a `UnifiedCheckout` session JSON, including item sub-totals, order total, and lists payment handlers available for completion:
   ```json
   {
     "id": "f49bc32e-068e-4b9a-bd17-a02757710f53",
     "status": "ready_for_complete",
     "line_items": [...],
     "totals": [{"type": "total", "amount": 3500}],
     "payment": {"handlers": [...], "instruments": []}
   }
   ```

- Error Handling
- **Invalid Signatures:** Return standard UCP errors (e.g., code `signature_invalid` or `digest_mismatch`) with `401 Unauthorized` or `400 Bad Request` status codes.
- **Request Payload Validation Failures:** Format validation exceptions (like Pydantic/Zod failures) using the unified UCP error envelope:
  ```json
  {
    "ucp": {"version": "2026-04-08", "status": "error"},
    "messages": [
      {
        "type": "ERROR",
        "code": "INVALID_REQUEST",
        "content": "✖ Field is required\n  → at body.buyer.email",
        "severity": "UNRECOVERABLE"
      }
    ]
  }
  ```

- Anti-Patterns to Avoid
- **Static Public Keys:** Do not hardcode caller or platform public keys. Always resolve them dynamically via the `UCP-Agent` profile URL to handle key rotation gracefully, caching them locally with TTL for performance.
- **Bypassing Signature Enforcement:** Never allow state-changing operations (like cart updates or checkout completion) without fully verifying the request signature and body digest unless `--require_signatures=false` is explicitly set in non-production environments.
- **Leaking Secrets:** Never check private webhook signing keys or database credentials into your source repository. Use secure environment variables or secret vaults.
- **SSRF Vulnerabilities:** Do not resolve arbitrary or internal/loopback IP address profile URLs (`127.0.0.1`, `localhost`, private CIDRs) in production when validating the `UCP-Agent` header, to prevent Server-Side Request Forgery.
- **Infinite Webhook Retries:** Do not retry failed webhook deliveries indefinitely or on permanent client-side 4xx errors. Strictly enforce the 3-attempt backoff policy.

- Fallback Instructions
- **Stack Adaptability:** If the desired programming language or framework is not Python/FastAPI or Node.js/Hono (e.g., Java/Spring, Go, or Rust), use the protocol details in `references/ucp-spec.md` as the source of truth to author native implementations:
  1. Set up the static discovery manifest JSON at `/.well-known/ucp`.
  2. Map standard HTTP routes for `/carts` and `checkout-sessions` using your framework's standard router.
  3. Implement the cryptographic request validation middleware using standard libraries for your language (e.g., standard RSA/ECDSA signature verification).
- **Missing References:** If reference files are unavailable or unreadable, default to standard REST/HTTP design principles and enforce standard JWT/JWS cryptographic signing to secure public-facing endpoints.

- Reference Files
- **references/ucp-spec.md**: Master technical specs (discovery, capability endpoints, request signatures, webhook deliveries).
- **references/python-fastapi-merchant.md**: Setup instructions, routes, and server patterns for Python/FastAPI.
- **references/nodejs-hono-merchant.md**: Project layout, environmental configs, and middleware setups for Node.js/Hono.

- Output Format
This skill produces a fully compliant, self-contained, secure UCP Merchant Server implementation. The server MUST publish a compliant profile at `/.well-known/ucp`, enforce signature verification on state-changing requests, compile cleanly without syntax/type errors, and pass the official UCP Conformance Test Suite.
