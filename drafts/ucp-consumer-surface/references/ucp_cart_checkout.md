# UCP Cart, Checkout, and Order Lifecycle (Client Side)

## Contents
- Cart operations (pre-purchase)
- Cart-to-checkout conversion
- Checkout lifecycle (create, update, complete, cancel)
- Native vs. embedded checkout
- Order lifecycle and the order event webhook
- Discount and fulfillment extensions (as seen from the client)

## Cart operations

Carts are pre-purchase, low-friction line-item collections. All four
operations live under `/carts` and require the `UCP-Agent` header; state
changing calls also want `Idempotency-Key` and `Request-Id`.

| Operation | Method | Endpoint | Purpose |
|---|---|---|---|
| Create Cart | `POST` | `/carts` | Start a session with initial `line_items`. |
| Get Cart | `GET` | `/carts/{id}` | Fetch current state (e.g. after a business-side price change). |
| Update Cart | `PUT` | `/carts/{id}` | **Full replacement** — resend every `line_item` you want to keep, not a delta/patch. |
| Cancel Cart | `POST` | `/carts/{id}/cancel` | Explicitly abandon a cart session. |

Minimal create request:

```json
POST /carts
UCP-Agent: profile="https://platform.example/.well-known/ucp"

{
  "line_items": [{"item": {"id": "item_123"}, "quantity": 2}],
  "context": {"address_country": "US", "address_region": "CA", "postal_code": "94105"}
}
```

Client rules:
- `context` (country/region/postal code) is provisional localization data,
  not authoritative — it influences estimated pricing/availability only.
  Never rely on it in place of the checkout's authoritative fulfillment
  address for eligibility or tax decisions.
- On `Update Cart`, the request replaces the entire line-item set: always
  echo back existing `line_items` (with their assigned `id`s) alongside any
  additions, or you will silently drop items.
- A cart response with `ucp.status: "error"` and severity `unrecoverable`
  (e.g. `out_of_stock`) means no cart resource was created at all — do not
  attempt to `GET` the (non-existent) cart id.
- `continue_url` in the response is a human-facing handoff link (browser
  recovery, share-cart flows) — not part of the machine API.

## Cart-to-checkout conversion

The recommended pattern is: build the cart first (letting the buyer adjust
quantities and apply discount codes), then convert it to a checkout session
by referencing the cart id — the business inherits line items, currency, and
discounts from the cart instead of you re-submitting everything:

```json
POST /checkout-sessions
{"cart_id": "cart_abc123"}
```

A checkout MAY also be created directly from raw `line_items` without a
prior cart, for flows that skip cart review entirely.

## Checkout lifecycle

| Operation | Method | Endpoint | Purpose |
|---|---|---|---|
| Create Checkout | `POST` | `/checkout-sessions` | From `cart_id` or raw `line_items`. |
| Get Checkout | `GET` | `/checkout-sessions/{id}` | Poll current state. |
| Update Checkout | `PUT` | `/checkout-sessions/{id}` | **Full replacement**; progressively fill `buyer`, `fulfillment`, discount codes. |
| Complete Checkout | `POST` | `/checkout-sessions/{id}/complete` | Submit `payment.instruments[]`; places the order. |
| Cancel Checkout | `POST` | `/checkout-sessions/{id}/cancel` | Abandon before completion. |

### Status field state machine

A checkout's `status` drives what the client should do next:

1. `incomplete` — required data still missing; check `messages[]` for
   `path`-scoped fields (e.g. `$.buyer.email`, `$.fulfillment.methods[0].selected_destination_id`)
   and resubmit `Update Checkout` with those fields filled.
2. `ready_for_complete` — all required data present; safe to call
   `Complete Checkout`.
3. `complete_in_progress` — a completion is already running for this
   session. The client MUST NOT start a new `Update Checkout` while in this
   state; the business will reject it and return the unchanged checkout with
   a recoverable error.
4. `completed` — terminal success; response includes `order.id` and
   `order.permalink_url`.
5. `canceled` — terminal, via `Cancel Checkout`.

### Progressive buyer/fulfillment fill

Because Update Checkout is full-replacement, build the payload by merging
new fields into the *previous* response's `buyer`/`fulfillment`/`line_items`,
not by starting from a blank object each call. Typical sequence:
1. `PUT` with `buyer.email/first_name/last_name`.
2. `PUT` again adding `fulfillment.methods[0].destinations[]` (shipping
   address) — this triggers the business to generate `groups[].options[]`
   (rate quotes).
3. `PUT` again setting `fulfillment.methods[0].selected_destination_id` and
   `groups[0].selected_option_id` to lock in the shipping method.
4. Once `status` is `ready_for_complete`, call `Complete Checkout`.

### Complete Checkout payload

```json
POST /checkout-sessions/{id}/complete
{
  "payment": {
    "instruments": [{
      "id": "instr_1",
      "handler_id": "mock_payment_handler",
      "type": "card",
      "credential": {"type": "token", "token": "success_token"},
      "billing_address": {"street_address": "123 Main St", "address_locality": "Anytown",
                            "address_region": "CA", "address_country": "US", "postal_code": "12345"}
    }]
  },
  "signals": {"dev.ucp.buyer_ip": "203.0.113.42", "dev.ucp.user_agent": "Mozilla/5.0 ..."}
}
```

`handler_id` MUST reference an id the business actually advertised in
discovery's `payment_handlers` — never hardcode a handler id without
checking it against the profile fetched in Step 0.

## Native vs. embedded checkout

- **Native (headless REST/MCP/A2A)**: the client drives the full lifecycle
  above directly against the business's API and never renders business UI.
  Best when the platform owns the entire buying UX.
- **Embedded (iframe/webview, ECP/Embedded Cart & Checkout Protocol)**: the
  client hands off to a business-hosted checkout surface inside an
  iframe/webview and communicates over a postMessage-based handshake instead
  of raw REST calls; the business UI collects payment directly. Prefer this
  when regulatory/PCI scope or a business's proprietary checkout UI must stay
  in the business's control. The message formats and lifecycle events are
  transport-specific — treat `/checkout-sessions` REST calls in this doc as
  the native-transport baseline and consult the business's declared
  `embedded` transport binding for the handshake it expects.

## Order lifecycle and webhook

After `Complete Checkout` returns `order.id`, the client can:
- `GET /orders/{id}` for a current-state snapshot (`line_items[].status`,
  `fulfillment.events[]`, `adjustments[]` for refunds/returns/disputes).
- Register/receive the **Order Event Webhook**: an asynchronous, business ->
  platform push for status changes (shipped, delivered, refunded) that
  arrive independently of any polling. Webhook deliveries are signed by the
  business the same way responses are (`Signature`, `Signature-Input`,
  `Content-Digest`) — verify them before trusting the payload, using the
  business's public key resolved the same way as any other UCP signature
  (via its discovery profile), and reject deliveries whose `Webhook-Id` /
  `Idempotency-Key` you have already processed (replay protection).
- Treat `permalink_url` as the authoritative, business-hosted order details
  page for anything this client doesn't model — deep post-purchase actions
  (returns, exchanges) SHOULD be delegated there rather than reimplemented.

## Discount and fulfillment extensions (client view)

- **Discounts**: submit `discounts.codes: [...]` on Cart or Checkout update;
  read back `discounts.applied[]` for the resolved discount lines and
  `messages[]` for rejected codes (invalid/expired/not-stackable).
- **Fulfillment**: submit desired `fulfillment.methods[].type` (`shipping`,
  `pickup`, etc.) and `destinations[]`; read back business-generated
  `groups[].options[]` (rate/method choices) and select one via
  `selected_option_id` before completing.
