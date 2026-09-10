# AP2 Spec Summary (v0.2)

Condensed from the normative sources. When this file and the spec disagree, the
spec wins.

- Spec: https://ap2-protocol.org/ap2/specification/
- Checkout Mandate: https://ap2-protocol.org/ap2/checkout_mandate/
- Payment Mandate: https://ap2-protocol.org/ap2/payment_mandate/
- Agent Authorization: https://ap2-protocol.org/ap2/agent_authorization/
- Flows: https://ap2-protocol.org/ap2/flows/
- Security & Privacy: https://ap2-protocol.org/ap2/security_and_privacy_considerations/
- Reference impl: https://github.com/google-agentic-commerce/AP2 (release 0.2.0)

## Contents
- [Mental model](#mental-model)
- [Mandate types and vct strings](#mandate-types-and-vct-strings)
- [Checkout Mandate schema](#checkout-mandate-schema)
- [Payment Mandate schema](#payment-mandate-schema)
- [Common types](#common-types)
- [Constraint catalog](#constraint-catalog)
- [SD-JWT chain mechanics](#sd-jwt-chain-mechanics)
- [Mandate delegation models](#mandate-delegation-models)
- [Verification and processing rules](#verification-and-processing-rules)
- [Receipts](#receipts)
- [Error codes](#error-codes)
- [Flow sequences](#flow-sequences)
- [Threat model and mitigations](#threat-model-and-mitigations)
- [Audit](#audit)
- [Reference implementation map](#reference-implementation-map)

## Mental model

AP2 is a security feature *inside* a commerce protocol, not a commerce protocol
itself. Catalogs, carts, and checkout APIs are out of scope — AP2 assumes some
other protocol (UCP is the designed-for case) produced a merchant-signed
Checkout, and layers verifiable authorization on top of it.

Two mandates, cryptographically linked:

| Mandate | Secures | Created by | Verified by |
|---|---|---|---|
| Checkout Mandate | *what* is being purchased | Shopping Agent, signed on a Trusted Surface | Merchant |
| Payment Mandate | *the payment for* that checkout | Shopping Agent, signed on a Trusted Surface | Credential Provider, Network, Merchant Payment Processor |

The link is the hash of the merchant-signed `checkout_jwt`: it appears as
`checkout_hash` in the Checkout Mandate and as `transaction_id` in the Payment
Mandate. Everything else in the protocol hangs off that equality.

Open vs. closed:

- **Closed** — bound to one specific transaction. Authorizes exactly this cart /
  this amount / this instrument. Verifiers *always* receive a closed mandate.
- **Open** — not yet bound to a transaction. Carries `constraints` describing the
  space of acceptable closed mandates, plus a `cnf` claim naming the agent key
  allowed to close it. Only exists in Human Not Present flows.

Agentic vs. non-agentic: a role is agentic if an LLM handles its communication.
The Shopping Agent is expected to be agentic; Merchant, MPP and Credential
Provider MAY be; the **Trusted Surface MUST NOT be**. Regardless of a role's
agentic status, its validation and processing MUST happen in deterministic code.

## Mandate types and vct strings

Match the exact string, including the numeric suffix. A future incompatible
revision bumps the suffix (`.2`).

| Mandate | `vct` |
|---|---|
| Closed Checkout Mandate | `mandate.checkout.1` |
| Open Checkout Mandate | `mandate.checkout.open.1` |
| Closed Payment Mandate | `mandate.payment.1` |
| Open Payment Mandate | `mandate.payment.open.1` |

Note the ordering is `.checkout.open.1`, not `.checkout.1.open`. The AP2 SDK's
own README lists these without the `.1` suffix and is stale; the generated models
in `code/sdk/python/ap2/sdk/generated/` and the schemas in `code/sdk/schemas/`
are authoritative.

## Checkout Mandate schema

Closed Checkout Mandate content:

| Name | Type | Required | Selectively disclosable | Notes |
|---|---|---|---|---|
| `vct` | string | Yes | No | `mandate.checkout.1` |
| `checkout_jwt` | string | Yes | Yes | base64url merchant-signed JWT of the Checkout payload |
| `checkout_hash` | string | Yes | No | base64url hash of the `checkout_jwt` value |
| `iat` | integer | No | No | Unix epoch |
| `exp` | integer | No | No | Unix epoch |

- `checkout_hash` uses the SD-JWT's `_sd_alg`, or `sha-256` if `_sd_alg` is
  absent. It is the hash of the *serialized `checkout_jwt` string*, not of the
  decoded payload.
- `checkout_jwt` payload contents are out of scope for AP2. With UCP it MUST be
  the Checkout object. The reference sample payload carries `order_id`,
  `merchant`, `line_items`, `total_price`, `currency`, `shipping_policy`,
  `return_policy`.
- The `checkout_jwt` MUST be signed with a non-deterministic signature scheme
  (ES256). A deterministic scheme (Ed25519) makes `checkout_hash` guessable
  unless the Checkout itself carries a high-entropy salt.

An **open** Checkout Mandate replaces the bound fields with `constraints` and
adds `cnf`. It is not required to carry all fields the closed form requires.

## Payment Mandate schema

Closed Payment Mandate content:

| Name | Type | Required | Notes |
|---|---|---|---|
| `vct` | string | Yes | `mandate.payment.1` |
| `transaction_id` | string | Yes | base64url hash of `checkout_jwt` — same value as the Checkout Mandate's `checkout_hash` |
| `payee` | Merchant | Yes | the merchant receiving payment |
| `pisp` | Pisp | No | Payment Initiation Service Provider |
| `payment_amount` | Amount | Yes | ISO 4217 minor units, user-confirmed final value |
| `payment_instrument` | PaymentInstrument | Yes | instrument used |
| `execution_date` | string | No | ISO 8601; absent means immediate |
| `risk_data` | object | No | risk signals collected by the Trusted Surface at signing time |
| `iat` | integer | No | Unix epoch |
| `exp` | integer | No | Unix epoch |

The open Payment Mandate MAY include any property of the closed form, plus
`constraints` and `cnf`.

## Common types

```
Amount            { amount: integer (minor units), currency: ISO-4217 alpha-3 }
Merchant          { id: string, name: string, website?: string }
PaymentInstrument { id: string, type: string, description?: string }
Pisp              { legal_name: string, brand_name: string, domain_name: string }
Item              { id: string (often the SKU), title: string }
LineItemRequirements { id: string, acceptable_items: Item[] (disclosable), quantity: integer }
```

`amount` is **integer minor units**: `27999` = $279.99, `19900` = $199.00.

## Constraint catalog

Constraints appear only on open mandates. Evaluation happens at the verifier,
against the closed mandate. **Any unknown constraint MUST be treated as failing
evaluation** — a verifier that ignores what it does not understand is broken.

### Checkout constraints

| Type | Properties | Evaluation |
|---|---|---|
| `checkout.allowed_merchants` | `allowed: Merchant[]` (disclosable) | The Merchant MUST appear in the *revealed* elements of `allowed`. If `allowed` has no revealed elements, the constraint is invalid. |
| `checkout.line_items` | `items: LineItemRequirements[]` | Each `items` entry must be satisfied by a matching quantity of Checkout items whose ID appears in the revealed `acceptable_items`. No entry and no Checkout item may be used twice. |

`checkout.line_items` is a bipartite matching problem; the spec suggests solving
it as maximal flow: source → each requirement node (capacity = `quantity`), each
Checkout item ID node → sink (capacity = quantity in checkout), infinite-capacity
edges between a requirement and each matching item. The constraint holds when
maximal flow equals both the total requirement quantity and the total checkout
item quantity. It does **not** support splitting one open Checkout Mandate across
multiple Checkouts.

Worked example: a requirement of {1× (Red Style | Blue Style)} + {1× Best Socks}
is satisfied by "Red Style + Best Socks" or "Blue Style + Best Socks", but *not*
by "Red Style + Blue Style", nor by either item alone.

### Payment constraints

| Type | Properties | Evaluation |
|---|---|---|
| `payment.amount_range` | `currency`, `max` (minor units), `min?` | `payment_amount` within `[min, max]` and currency matches. |
| `payment.allowed_payees` | `allowed: Merchant[]` (disclosable) | `payee` MUST be present in `allowed`. |
| `payment.allowed_payment_instruments` | `allowed: PaymentInstrument[]` (disclosable) | `payment_instrument` MUST be present in `allowed`. |
| `payment.allowed_pisps` | `allowed: Pisp[]` | The facilitating PISP MUST be present in `allowed`. |
| `payment.agent_recurrence` | `frequency` ∈ {`ON_DEMAND`,`DAILY`,`WEEKLY`,`BIWEEKLY`,`MONTHLY`,`QUARTERLY`,`ANNUALLY`}, `max_occurrences?` | Requires tracking prior presentations. True when this presentation is far enough in time from the previous one and occurrences ≤ `max_occurrences`. |
| `payment.budget` | `max`, `currency` | Requires tracking cumulative spend. True when requested amount + prior total ≤ `max`. On approval the amount MUST be added to the running total. Use with `agent_recurrence`. |
| `payment.reference` | `conditional_transaction_id` | The Checkout Mandate for the order MUST contain an open Checkout Mandate with a matching digest in its delegate chain. |
| `payment.execution_date` | `not_before?`, `not_after?` | `execution_date` within the window, inclusive. |

`payment.budget` and `payment.agent_recurrence` are **stateful**. A verifier that
does not persist prior presentations cannot honestly evaluate them; if you emit
these constraints you must also build the ledger that backs them.

## SD-JWT chain mechanics

AP2 secures mandates as SD-JWT Verifiable Credentials (RFC 9901), using two
SD-JWT features:

- **Key Binding** — lets the agent prove possession of the key named in the open
  mandate's `cnf`, and bind the presentation to one transaction, after the user
  has left.
- **Selective Disclosure** — lets the agent reveal only the constraint elements
  relevant to this checkout, preserving user privacy.

Mandate content claims:

- `vct` — REQUIRED, identifies the mandate type.
- `constraints` — OPTIONAL array; each entry REQUIRES a unique `type` string.
- `cnf` — OPTIONAL generally, **REQUIRED while the mandate is open** (RFC 7800
  proof-of-possession key).

Closing an open mandate = the agent generates a Key Binding JWT with the key
endorsed in `cnf`. The KB JWT carries `iat`, `aud`, `nonce`, `sd_hash` (binding
to the presented open mandate) and `_sd_alg`.

From the reference SDK (`code/sdk/python/ap2/sdk/README.md`): an SD-JWT root plus
KB-SD-JWT delegation hops joined by `~~`; intermediate hops use
`typ: kb+sd-jwt+kb` and carry `cnf`; the terminal/closed mandate uses
`typ: kb+sd-jwt` and carries no `cnf`. Binding is via `sd_hash` by default.
Algorithm ES256. The SDK notes an explicit deviation from
`draft-gco-oauth-delegate-sd-jwt-00`: it neither emits nor accepts the
dSD-JWT+KB shape.

Serialization reminder: an SD-JWT presentation is `<issuer-jwt>~<disclosure>~…~`
with a trailing `~` before an optional KB-JWT; each disclosure is a base64url
JSON array `[salt, name, value]` (object property) or `[salt, value]` (array
element). Digests must use a salt with sufficient entropy (RFC 9901 §9.1) —
guessable salts reintroduce rainbow-table attacks. The Trusted Surface MAY insert
decoy digests (RFC 9901 §4.2.5).

## Mandate delegation models

Two ways a verifier comes to trust that a human really approved the content:

- **User Credential** — a three-party model (Issuer, Trusted Surface as holder,
  Agent). Delegation rides on OpenID4VP `transaction_data`: an object with
  `type: "delegate"`, `format`, `delegate_payload` (array of mandate content
  objects) and optional `delegate_disclosures`, base64url-encoded. The
  `delegate_payload` MUST be included in the Key Binding of the Authorization
  Response. Using the Digital Credentials API is RECOMMENDED. One credential can
  delegate to many agents without the verifier trusting each agent.
- **Trusted Agent Provider** — the provider of the agent is trusted directly. No
  pre-issued credential; the provider's Trusted Surface renders the content,
  collects consent, and a securely stored provider key signs the mandate. The
  provider MUST ensure the agent cannot access that key or use it without the
  Trusted Surface.

In both cases `user_sk` in the flow diagrams is "the key of whichever party the
verifier trusts to have obtained consent".

## Verification and processing rules

For a chain of SD-JWT mandates:

1. Verify and process the SD-JWT chain per Delegate SD-JWT (signatures,
   disclosure digests, key binding, `sd_hash` linkage).
2. Extract claims from the open mandate content and verify the closed mandate
   carries those values unchanged.
3. Evaluate every constraint from every open mandate against the closed mandate.
   Unknown constraint types MUST fail.

Per-role duties on top of that:

- **Merchant** (Checkout Mandate): run the rules above; verify the
  `checkout_hash` claim equals the hash of the `checkout_jwt` it sent for
  approval; if open Checkout Mandates are included, verify the closed Checkout
  conforms to all constraints. On any failure, return a Checkout Receipt JWT
  carrying the error.
- **Credential Provider / Network** (Payment Mandate): run the rules above before
  returning a payment credential; verify the closed Payment Mandate matches all
  constraints of any included open Payment Mandate. On failure return an error
  Payment Receipt.
- **Merchant Payment Processor**: MUST receive the payment credential from the
  Merchant and verify it is scoped to this Checkout — one way is to carry the
  closed Payment Mandate inside the credential.
- **Dispute**: verify the Checkout Mandate per the Merchant rules; independently
  recompute the hash of the included `checkout_jwt`; check the Checkout Receipt
  `reference` equals the hash of the closed Checkout Mandate (computed as
  `sd_hash` is); verify the Payment Mandate per the MPP rules using the
  `checkout_hash` from the Checkout Mandate; check the Payment Receipt
  `reference` equals the hash of the closed Payment Mandate. Only after all of
  these pass is the mandate content usable as evidence of what each party saw.

## Receipts

Generic Mandate Receipt (verifier-signed JWT):

| Claim | Required | Notes |
|---|---|---|
| `iss` | Yes | the verifier |
| `result` | Yes | `success` \| `error` |
| `reference` | Yes | base64url hash of the received mandate — over the final SD-JWT in the chain, computed as `sd_hash` is, using `_sd_alg` or `sha-256` |
| `error` | If error | error code |
| `error_description` | No | human-readable |

Checkout Receipt adds `status` (`Success`|`Error`), `iat`, and `order_id`
(present iff success). Payment Receipt adds `status`, `iat`, `payment_id`
(always), `psp_confirmation_id` and `network_confirmation_id` (success only).

On receiving a success receipt the agent stores the (open mandate, closed
mandate, receipt) tuple and **reduces the scope of the open mandate**, often
preventing any further presentation.

## Error codes

| Code | Meaning | Recoverable? |
|---|---|---|
| `invalid_credential` | mandate failed verification | No — terminal |
| `unresolved_constraint` | unknown constraint, or verifier could not confirm conformance | Yes — fall back to a directly approved closed mandate or a non-agentic flow |
| `invalid_mandate` | mandate does not authorize the requested action | No — terminal |
| `mandates_not_supported` | verifier does not support mandates | Yes — fall back to a non-agentic flow |

## Flow sequences

### Human Present (direct)

Phase 1 — shopping: user starts with the Shopping Agent → agent assembles a cart
with the Merchant → agent goes to checkout, Merchant returns a signed Checkout
and demands a mandate → agent fetches instrument options from the Credential
Provider and selects one.

Phase 2 — payment:
1. Agent builds Checkout + Payment Mandate content, requests approval via a
   Trusted Surface.
2. Trusted Surface renders it, authenticates the user (e.g. biometric), collects
   consent.
3. Trusted Surface signs both **closed** mandates with `user_sk`; the
   `checkout_jwt` hash permanently links them.
4. Mandates return to the Shopping Agent.
5. Agent → Credential Provider with the Payment Mandate; CP verifies and mints a
   payment token (possibly sharing the mandate with the Network for a scoped
   credential).
6. Agent → Merchant with the token and the Checkout Mandate.
7. Merchant verifies the Checkout Mandate against current cart state and
   initiates payment with the token and `checkout_jwt` hash.
8. MPP verifies the Payment Mandate inside the token and its binding to the
   `checkout_jwt` hash.
9. MPP-signed Payment Receipt → Shopping Agent, Credential Provider, Network;
   Merchant-signed Checkout Receipt → Shopping Agent.

Because the user approves the *closed* Checkout, this flow can often be replaced
by a traditional e-commerce journey where Merchant and Trusted Surface talk
directly.

### Human Not Present (autonomous)

Phase 1a — human present: agent assembles **open** mandate content for the
session → Trusted Surface renders, authenticates, and signs the open Checkout and
open Payment Mandates with `user_sk`. The open Checkout Mandate's hash is
embedded in the open Payment Mandate; `agent_pk` goes in `cnf` to
sender-constrain use. `exp` SHOULD be the smallest value that lets the task
finish. The user leaves.

Phase 1b — human not present: agent assembles a cart and reaches checkout; the
Merchant returns a signed Checkout.

Phase 2 — payment:
1. Agent selects open mandates whose constraints cover this Checkout. To avoid
   double-spend it MUST NOT create overlapping closed mandates until it receives
   a receipt rejecting the prior one.
2. Agent signs both **closed** mandates with `agent_sk`; `checkout_jwt` hash links
   them; the KB-SD-JWT `sd_hash` binds closed to open.
3. Agent → Credential Provider with open + closed Payment Mandates; CP verifies
   and mints a token.
4. Agent → Merchant with the token and open + closed Checkout Mandates.
5. Merchant verifies the closed mandate against cart state *and* that the open
   mandate's constraints are met, then initiates payment with the token,
   `checkout_jwt` hash, and open Checkout Mandate hash.
6. MPP verifies both mandates in the token and both bindings.
7. Receipts distributed as in the direct flow.

Downgrade path: a Merchant or Credential Provider returning
`unresolved_constraint` converts a Human Not Present flow into a Human Present
one by bringing the user back to approve the closed mandates.

Agent-to-agent delegation of mandates is conceptually possible but explicitly
**out of scope** in v0.2.

## Threat model and mitigations

AP2 assumes preventing prompt injection is infeasible; all LLMs and agents are in
the threat model as potential attackers.

| Threat | Mitigation |
|---|---|
| Stolen Payment Mandate reused on an unrelated Checkout | `transaction_id` (closed) / `payment.reference` constraint (open) tie the payment to its checkout |
| Open mandate reused with a different closed mandate | Closed mandates MUST carry `sd_hash` binding them to the presented open mandate |
| Open mandate reused to approve a different closed Checkout Mandate | `sd_hash` binding **plus** `cnf` in the open mandate so only the named agent key can close it |
| Closed Checkout Mandate replayed against a different checkout session | Merchant MUST verify `checkout_hash` matches the hash of the *latest* `checkout_jwt` |
| Shopping Agent or CP manipulates the payment in transit | MPP and CP MUST verify the user signature on the Payment Mandate; `checkout_hash` in `transaction_id` links it to the Checkout; constraint evaluation bounds amount and payee |
| Payment credential/token stolen after release | Token released to the Merchant only after a final Payment Mandate verifies, binding it to that transaction |
| Prompt injection steers product selection | Merchant signature protects offering integrity; constraint enforcement bounds worst-case financial impact even when the LLM chooses badly |
| Double spend against one open mandate | Agent MUST NOT sign overlapping closed mandates without a rejection receipt; receipts MUST be integrity-protected from the agent's LLM; CP/Network/MPP MAY reject overlaps or invalidate prior tokens |

Privacy:

- Open-mandate constraints may encode intent irrelevant to this checkout —
  Selective Disclosure MUST be used to withhold it. Decoy digests MAY be added.
- Checkout and Payment data are minimized per verifier; `checkout_hash` is what
  lets the two be rejoined at dispute time.
- Salts MUST have sufficient entropy. `checkout_hash` relies on the entropy in
  the JWT signature; with a deterministic signature scheme the Checkout MUST
  carry its own salt.

## Audit

Checklist for Step 7 of the skill. Each item is pass/fail/not-applicable, with
severity `critical` | `high` | `medium` | `low`.

**Scoping and expiry**
1. Every open mandate has an `exp`, and it is proportional to the task (hours,
   not months). *critical*
2. Open Payment Mandates bound both amount (`payment.amount_range`) and
   counterparty (`payment.allowed_payees` or `payment.reference`). *critical*
3. `payment.budget` / `payment.agent_recurrence`, if present, are backed by
   persisted state that the LLM cannot rewrite. *high*
4. Open Checkout Mandates constrain merchants and line items. *high*

**Binding and replay**
5. Closed Payment Mandate `transaction_id` == Checkout Mandate `checkout_hash` ==
   recomputed hash of `checkout_jwt`. *critical*
6. Closed mandates carry `sd_hash` binding to the presented open mandate.
   *critical*
7. Open mandates carry `cnf` with the agent key; closed terminal mandates do
   not. *critical*
8. KB JWTs carry a fresh `nonce` and correct `aud` per verifier. *high*
9. `checkout_jwt` uses a non-deterministic signature scheme (ES256). *high*
10. The agent cannot present a second closed mandate against an open mandate
    without an intervening rejection receipt. *critical*

**Credential leakage**
11. No role receives credentials outside its row in
    `references/role_credential_matrix.md`. *critical*
12. Payment tokens are released only after mandate verification. *critical*
13. Only the disclosures required for evaluation are revealed to each verifier;
    the full acceptable-items / allowed-merchants list is not. *high*
14. Salt entropy is adequate and salts are not reused across disclosures. *high*

**Dispute readiness**
15. The (open mandate, closed mandate, receipt) tuple is persisted for both the
    Checkout and Payment legs, keyed by `transaction_id`. *critical*
16. Receipts are signed by the verifier and stored where the agent's LLM cannot
    alter them. *critical*
17. Receipt `reference` values verify against the hashes of the retained closed
    mandates. *high*
18. The retained evidence answers: who approved, what content they saw, at what
    amount, on what instrument, at what time. *critical*

**Determinism**
19. All verification and constraint evaluation runs in deterministic code, not in
    a prompt. *critical*
20. Unknown constraint types fail evaluation rather than being ignored.
    *critical*

## Reference implementation map

Repository `google-agentic-commerce/AP2`, release 0.2.0. Verified paths:

```
code/sdk/python/ap2/sdk/                 mandate.py, constraints.py, jwt_helper.py,
                                         receipt_wrapper.py, checkout_mandate_chain.py,
                                         payment_mandate_chain.py, max_flow_helper.py, utils.py
code/sdk/python/ap2/sdk/sdjwt/           sd_jwt.py, kb_sd_jwt.py, chain.py, common.py
code/sdk/python/ap2/sdk/generated/       checkout_mandate.py, payment_mandate.py,
                                         open_checkout_mandate.py, open_payment_mandate.py,
                                         checkout_receipt.py, payment_receipt.py, types/
code/sdk/schemas/ap2/*.json              canonical JSON schemas
code/samples/python/src/roles/           merchant_agent/, credentials_provider_agent/,
                                         merchant_payment_processor_agent/, shopping_agent/,
                                         shopping_agent_v2/, plus *_mcp variants
code/samples/python/scenarios/a2a/       human-present/{cards,x402}/, human-not-present/{cards,x402}/
```

Key SDK surfaces:

- `ap2.sdk.mandate.MandateClient` — `create`, `present`, `verify`,
  `get_closed_mandate_jwt`; generic `SdJwtMandate[T]`.
- `ap2.sdk.generated.checkout_mandate.CheckoutMandate`,
  `...payment_mandate.PaymentMandate`, `...open_checkout_mandate.OpenCheckoutMandate`,
  `...open_payment_mandate.OpenPaymentMandate`,
  `...checkout_receipt.CheckoutReceipt`, `...payment_receipt.PaymentReceipt`.
- Constraint classes: `AmountRange`, `AllowedPayees`, `AllowedPaymentInstruments`,
  `AllowedPisps`, `Budget`, `AgentRecurrence`, `ExecutionDate`,
  `PaymentReference`, `AllowedMerchants`, `LineItems`, `LineItemRequirements`,
  `Item`.
- `ap2.sdk.generated.types.*` — `Amount`, `Merchant`, `PaymentInstrument`,
  `Buyer`, `Checkout`, `LineItem`, `Jwk`, `Pisp`, `Total`, `ReceiptStatus`.
- `ap2.sdk.constraints.{MandateContext, check_payment_constraints}`,
  `ap2.sdk.sdjwt.chain.{verify_chain, X5cOrKidPublicKeyProvider}`,
  `ap2.sdk.utils.compute_sha256_b64url`.

Known-stale material in that repo, do not copy from it:

- `code/sdk/python/ap2/models/mandate.py` holds the retired v0.1 types
  (`IntentMandate`, `CartMandate`, `PaymentMandateContents`). Effectively dead —
  nothing but that file references `IntentMandate`/`CartMandate`.
- The human-present `cards/README.md` and `x402/README.md` still narrate that
  v0.1 vocabulary while the code they run imports the v0.2 SDK.
- The SDK README's data-model table omits the `.1` `vct` suffix.
- The root README points at `code/sdk/python/ap2/schemas/`, which does not exist;
  the schemas live at `code/sdk/schemas/`.
