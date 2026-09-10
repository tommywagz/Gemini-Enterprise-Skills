# AP2 Role & Credential Matrix

Who holds what, who verifies what, and what each role must never see. Derived
from https://ap2-protocol.org/ap2/specification/ (Roles, Verification) and
https://ap2-protocol.org/ap2/security_and_privacy_considerations/.

## Contents
- [The five roles](#the-five-roles)
- [Credential visibility matrix](#credential-visibility-matrix)
- [Verification duties](#verification-duties)
- [Key custody](#key-custody)
- [Disclosure policy per verifier](#disclosure-policy-per-verifier)
- [Collapsing roles](#collapsing-roles)
- [Reference implementation wiring](#reference-implementation-wiring)
- [Sub-agent generation checklist](#sub-agent-generation-checklist)

## The five roles

| Role | Abbrev | Responsibility | Agentic? |
|---|---|---|---|
| Shopping Agent | SA | Product discovery, building the checkout, executing the purchase | Expected to be agentic |
| Credential Provider | CP | Source of payment credentials; verifies the agent is authorized to access a credential and scopes it | MAY be either |
| Merchant | M | Provides and completes the Checkout; owns inventory, pricing, and merchant discounts integrity | MAY be either |
| Merchant Payment Processor | MPP | Processes payment; verifies the credential the CP issued was authorized for this Checkout | MAY be either |
| Trusted Surface | TS | UI that obtains informed user consent for an intent before creating a user-signed mandate | **MUST be non-agentic** |

A Network may sit between CP and MPP; where present it shares the CP's Payment
Mandate verification duty.

"Agentic" means an LLM handles the role's communication. Whatever the role's
status, its **validation and processing MUST happen in deterministic code**.

## Credential visibility matrix

`✓` holds/receives · `scoped` receives a transaction-bound derivative only ·
`✗` MUST NOT see.

| Artifact | SA | TS | M | CP | Network | MPP |
|---|---|---|---|---|---|---|
| User intent / shopping task | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| `checkout_jwt` (merchant-signed cart) | ✓ | ✓ (rendered) | ✓ (issuer) | ✗ | ✗ | hash only |
| Closed Checkout Mandate | ✓ | ✓ (signs) | ✓ | ✗ | ✗ | ✗ |
| Open Checkout Mandate | ✓ | ✓ (signs) | ✓ (disclosures needed for evaluation only) | ✗ | ✗ | hash only |
| Closed Payment Mandate | ✓ | ✓ (signs) | ✗ | ✓ | ✓ | ✓ (typically inside the credential) |
| Open Payment Mandate | ✓ | ✓ (signs) | ✗ | ✓ (needed disclosures only) | ✓ | ✓ |
| Raw payment instrument / PAN | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Instrument options list (display metadata) | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ |
| Payment credential / token | scoped | ✗ | scoped (to forward) | ✓ (mints) | ✓ | ✓ (consumes) |
| User signing key `user_sk` | ✗ | ✓ (uses, does not export) | ✗ | ✗ | ✗ | ✗ |
| Agent signing key `agent_sk` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Agent public key (`cnf.jwk`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Checkout Receipt | ✓ | ✗ | ✓ (issues) | ✗ | ✗ | ✗ |
| Payment Receipt | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ (issues) |
| Full line-item detail | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Final amount + payee | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Reading the two most load-bearing rows:

- **The Merchant never sees the Payment Mandate.** It sees the Checkout Mandate
  and a token. Handing a merchant agent the Payment Mandate leaks the user's
  instrument metadata and defeats the point of splitting the two credentials.
- **The Credential Provider never sees the cart.** It sees the Payment Mandate,
  whose `transaction_id` is only a hash. It learns the amount and the payee, not
  what was bought. Sending the CP the line items leaks purchase history to the
  wallet.

## Verification duties

| Role | MUST verify | On failure |
|---|---|---|
| Merchant | Checkout Mandate chain per the Verification and Processing Rules; `checkout_hash` equals the hash of the `checkout_jwt` it issued (latest, not any earlier one); every open Checkout constraint evaluates true against the closed Checkout | Return a Checkout Receipt JWT with the error code |
| Credential Provider (and Network) | Payment Mandate chain per the same rules; closed Payment Mandate satisfies all open Payment Mandate constraints — **before** returning a payment credential | Return an error Payment Receipt to the SA |
| Merchant Payment Processor | The payment credential received from the Merchant is scoped to this Checkout — commonly by carrying the closed Payment Mandate inside the credential; bindings to `checkout_jwt` hash and open Checkout Mandate hash | Return an error Payment Receipt |
| Trusted Surface | That the human actually saw the mandate content and authenticated before signing | Refuse to sign |
| Shopping Agent | Receipts it receives; that it is not presenting an overlapping closed mandate against an already-used open mandate | Do not proceed; surface to the user |

A role MAY delegate its duties to a technology provider (e.g. a merchant letting
its processor verify on its behalf). The delegate then follows that role's rules.
Delegation does not remove the duty.

## Key custody

| Key | Held by | Constraint |
|---|---|---|
| `user_sk` (User Credential model) | Trusted Surface as credential holder | Never exported to the agent |
| Agent Provider signing key (Trusted Agent Provider model) | Agent Provider backend | The provider MUST ensure the agent cannot access it or use it without the Trusted Surface |
| `agent_sk` | Shopping Agent | Only usable against open mandates whose `cnf` names its public key |
| Merchant checkout signing key | Merchant | Must be non-deterministic (ES256) |
| Verifier receipt signing keys | Merchant / CP / MPP | Receipts MUST be integrity-protected from the SA's LLM |

The practical failure here is an "agent provider" implementation where the LLM
process can call the signing endpoint directly. If the agent can obtain a
signature without the Trusted Surface rendering content to a human, the entire
consent story is fictional.

## Disclosure policy per verifier

Selective Disclosure is mandatory, not optional hygiene: the agent MUST present
only the disclosures needed to evaluate the closed mandate.

| Verifier | Reveal | Withhold |
|---|---|---|
| Merchant | The one merchant entry in `checkout.allowed_merchants` that matches; the `acceptable_items` entries that match the actual cart | Other allowed merchants, other acceptable items, all payment constraints |
| Credential Provider / Network | `payment.amount_range`, the matching `payment.allowed_payees` entry, the matching instrument entry, `payment.reference` | Other allowed payees/instruments, all checkout constraints, line items |
| Merchant Payment Processor | Whatever the credential carries — typically the closed Payment Mandate | Open-mandate constraints not needed for scoping |

`checkout.allowed_merchants` evaluation depends on revealed elements: the
constraint is *invalid* if `allowed` has no revealed elements. Withhold the
matching entry and you fail your own constraint.

## Collapsing roles

One entity MAY play several or all roles. When it does it inherits every duty of
every role it plays — the verifications do not cancel out. Two common shortcuts
that are wrong:

- Merchant + MPP collapsed, so nobody checks that the credential is scoped to the
  Checkout. The check still has to happen.
- Shopping Agent + Trusted Surface collapsed into one LLM app. This is the
  disqualifying one: the Trusted Surface MUST be non-agentic. Split the consent
  UI and the signing call into deterministic code the LLM cannot invoke on its
  own.

## Reference implementation wiring

`google-agentic-commerce/AP2` @ 0.2.0. Role implementations live in
`code/samples/python/src/roles/`:

```
merchant_agent/                       credentials_provider_agent/
merchant_payment_processor_agent/     shopping_agent/  (+ subagents/)
shopping_agent_v2/                    merchant_agent_mcp/
credentials_provider_mcp/             merchant_payment_processor_mcp/
x402_credentials_provider_mcp/        x402_psp_mcp/
```

Human-present scenarios (cards and x402) — four processes, A2A-addressable:

| Role | Address |
|---|---|
| Shopping Agent (ADK `adk web`) | `http://0.0.0.0:8000` (dev UI at `:8000/dev-ui`, pick `shopping_agent`) |
| Merchant Agent | `http://localhost:8001/a2a/merchant_agent` |
| Credentials Provider | `http://localhost:8002/a2a/credentials_provider` |
| Merchant Payment Processor | `http://localhost:8003/a2a/merchant_payment_processor_agent` |

Manual launch (one terminal each; prefix with `export PAYMENT_METHOD=x402` for
the x402 variant):

```sh
uv run --package ap2-samples python -m roles.merchant_agent
uv run --package ap2-samples python -m roles.credentials_provider_agent
uv run --package ap2-samples python -m roles.merchant_payment_processor_agent
uv run --package ap2-samples adk web code/samples/python/src/roles
```

Human-not-present / cards — MCP trigger servers rather than A2A agent cards:
shopping agent (`shopping_agent_v2`) on `8080` with its card at
`/a2a/shopping_agent/.well-known/agent-card.json`, merchant trigger `8081`,
credentials provider `8082`, payment processor `8083`, web client `5173`.
Human-not-present / x402: agent `8080`, merchant trigger `8081`, x402 PSP trigger
`8084`, web client `5173`.

Trigger the autonomous purchase:

```sh
curl -X POST "http://localhost:8081/trigger-price-drop?item_id=<item_id>&price=<price>&stock=10"
```

## Sub-agent generation checklist

When generating the role sub-agents:

1. One process per role. Do not co-locate the Credential Provider with the
   Shopping Agent even for a demo — co-location is how PAN data ends up in an
   LLM context window.
2. Give each role only the credentials in its column of the matrix above. Assert
   this in code (reject unexpected fields on inbound payloads) rather than
   relying on the caller.
3. Put mandate verification in a deterministic module the agent calls as a tool,
   with the tool returning a structured pass/fail — never a prose judgement.
4. Make receipt storage append-only from the agent's perspective.
5. Give the Trusted Surface its own non-LLM entry point, and make the signing key
   reachable only from it.
6. Emit an explicit statement in your output of what each generated role holds,
   so the Step 7 audit has something to check against.
