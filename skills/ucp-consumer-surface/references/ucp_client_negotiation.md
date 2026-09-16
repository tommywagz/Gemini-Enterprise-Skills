# UCP Client Negotiation: Discovery, Headers, Signing

## Contents
- Discovery: fetching and parsing `/.well-known/ucp`
- Authority binding validation (schema URL provenance)
- Required request headers
- RFC 9421 / RFC 9530 request signing
- Capability negotiation and payment handler selection
- Error model (transport vs. business outcomes)

## Discovery: `/.well-known/ucp`

Every UCP interaction starts with an unauthenticated `GET` to the business's
discovery profile. The profile is a JSON document wrapped in a top-level
`ucp` object (fall back to the response root for flat/legacy profiles):

```json
{
  "ucp": {
    "version": "2026-08-25",
    "services": {
      "dev.ucp.shopping": [
        {
          "version": "2026-08-25",
          "spec": "https://ucp.dev/2026-08-25/specification/overview",
          "transport": "rest",
          "schema": "https://ucp.dev/2026-08-25/services/shopping/rest.openapi.json",
          "endpoint": "https://business.example.com/ucp/v1"
        }
      ]
    },
    "capabilities": {
      "dev.ucp.shopping.catalog.search": [{"version": "2026-08-25", "spec": "...", "schema": "..."}],
      "dev.ucp.shopping.cart": [{"version": "2026-08-25", "spec": "...", "schema": "..."}],
      "dev.ucp.shopping.checkout": [{"version": "2026-08-25", "spec": "...", "schema": "..."}],
      "dev.ucp.shopping.order": [{"version": "2026-08-25", "spec": "...", "schema": "..."}]
    },
    "payment_handlers": {
      "mock_payment_handler": [{"id": "mock_payment_handler", "version": "2026-08-25"}]
    }
  }
}
```

Client responsibilities on discovery:
1. Parse the `version` (protocol version) and pick exactly one supported
   version; there is no mixing of capability schemas across versions.
2. Walk `capabilities` to determine which shopping capabilities the business
   supports (`catalog.search`, `catalog.lookup`, `cart`, `checkout`, `order`,
   and any extensions like `discount` or `fulfillment`).
3. Walk `services[name][]` to resolve the transport binding (`rest`, `mcp`,
   `a2a`, `embedded`) and the `endpoint` base URL. REST paths (e.g.
   `/checkout-sessions`) are appended directly to `endpoint`, no leading
   slash duplication.
4. Walk `payment_handlers` to discover which payment handler IDs (e.g.
   `mock_payment_handler`, `com.shopify.shop_pay`, `com.google.pay`) the
   business accepts. The client's payment logic MUST select from this set —
   never assume a handler is supported.

## Authority binding validation

Before fetching any declared `schema` URL, the client MUST validate that the
URL's host is authorized for that entity's reverse-domain name:

- Parse the URL with a conformant WHATWG URL parser; it MUST use `https` and
  MUST NOT contain userinfo (`user:pass@`).
- The host MUST be a registered domain of at least two labels (reject
  IP-literals and single-label hosts like `localhost`).
- Reverse the host's labels (`ucp.dev` → `dev.ucp`) to form the
  `authority_prefix`.
- Accept if `name` equals `authority_prefix` (exact) or `name` is
  `authority_prefix` followed by `.` and more labels (prefix). Otherwise
  reject the entity — treat it as not present and never activate it.

Example: `dev.ucp.shopping.checkout` served from `schema` host `ucp.dev`
(`authority_prefix = dev.ucp`) is accepted as a prefix match. A capability
named `dev.ucp.shopping.checkout` served from `evil.example` is rejected.

This check is provenance-only, not a fetch-safety control: the client still
applies standard SSRF protections (reject resolution to loopback, link-local,
and cloud-metadata addresses) when actually dereferencing the `schema` URL.

## Required request headers (REST transport)

| Header | Required | Notes |
|---|---|---|
| `UCP-Agent` | Yes | RFC 8941 Dictionary syntax: `profile="https://platform.example/.well-known/ucp"`. Points at the client's own discovery profile so the business can resolve its signing key. |
| `Request-Id` | Yes | UUID per request, for tracing. |
| `Idempotency-Key` | Yes on state-changing ops | UUID; reused verbatim on retry of the *same* logical operation so the business returns the cached result instead of double-processing. |
| `Content-Digest` | Conditional | RFC 9530 SHA-256 digest of the request body; required whenever a body is present if signing is used. |
| `Signature-Input` / `Signature` | Conditional | RFC 9421 HTTP Message Signature headers; required only when the negotiated auth mechanism is message signing (one of several allowed mechanisms — API key, OAuth, mTLS, or signatures). |

## RFC 9421 / RFC 9530 request signing (when used)

1. Compute `Content-Digest: sha-256=:<base64 sha-256 of raw body>:` for any
   request with a body.
2. Build the signature base over the negotiated component list, at minimum
   `@method`, `@authority`, `@path`, plus `content-digest`, `idempotency-key`,
   and `ucp-agent` when present.
3. Sign with the client's private key (ES256 in the reference samples) and
   emit `Signature-Input: sig1=("@method" "@authority" "@path" ...);created=<ts>;keyid="<key-id>"`
   and `Signature: sig1=:<base64 signature>:`.
4. Publish the corresponding public key at the profile URL referenced by the
   `UCP-Agent` header so the business can resolve and cache it — do not
   assume a static, hardcoded business-side key store.
5. Never resolve `UCP-Agent` profile URLs that point at loopback, link-local,
   or private-CIDR addresses in production (SSRF guard applies symmetrically
   on both client and business sides).

See `references/ucp_cart_checkout.md` for the operation-level request/response
shapes these headers wrap.

## Error model

UCP splits errors into two layers; a client MUST handle both:

- **Transport errors** — HTTP status codes for protocol-level failures that
  prevented processing: `400` malformed/missing fields, `401` auth failure,
  `409` idempotency-key reuse with a mismatched body, `422`/`424` discovery
  failures, `429` rate limited, `500`/`503` server errors.
- **Business outcomes** — HTTP `200` with a UCP envelope. Check
  `ucp.status` and the `messages[]` array even on a `200` response before
  trusting the payload; `ucp.status: "error"` with a `messages[].severity`
  of `unrecoverable` means the operation did not happen (e.g. `out_of_stock`,
  `not_found`) even though the transport succeeded. `recoverable` severity
  (e.g. a missing required buyer field) means the client can resubmit with
  corrected data using the *same* resource.

A client MUST inspect `messages[]` on every response, not just non-2xx
status codes, or it will silently treat failed business operations as
successes.
