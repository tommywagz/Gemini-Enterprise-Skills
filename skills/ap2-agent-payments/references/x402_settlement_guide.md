# x402 / Crypto Settlement Rail

Read this only when the user asks for stablecoin or on-chain settlement. Sourced
from the reference scenarios in `google-agentic-commerce/AP2` @ 0.2.0 and the
upstream `google-agentic-commerce/a2a-x402` extension.

## Contents
- [The one rule](#the-one-rule)
- [What actually changes](#what-actually-changes)
- [Human present: x402](#human-present-x402)
- [Human not present: x402](#human-not-present-x402)
- [Migration recipe](#migration-recipe)
- [Known limitations](#known-limitations)
- [Audit deltas](#audit-deltas)

## The one rule

**x402 changes settlement, not authorization.** The Checkout Mandate and Payment
Mandate keep the same `vct` values, the same field tables, the same
`checkout_hash` / `transaction_id` linkage, and the same open/closed constraint
model. If your mandate structure changes when you swap the rail, you have put
rail-specific data somewhere it does not belong.

The only mandate-level surface x402 legitimately touches is
`payment_instrument.type` — the spec's Payment Instrument extension point says
new instruments are supported by defining a unique `type` string, with additional
properties for that type if needed. Everything above that is untouched.

## What actually changes

| Layer | Cards | x402 | Same? |
|---|---|---|---|
| Checkout Mandate (`mandate.checkout.1`) | unchanged | unchanged | Yes |
| Payment Mandate (`mandate.payment.1`) | unchanged | unchanged | Yes |
| Constraints (`payment.amount_range`, etc.) | unchanged | unchanged | Yes |
| `payment_instrument.type` | `card` | x402-compatible instrument type | No |
| Credential Provider implementation | `credentials_provider_agent` / `credentials_provider_mcp` | `x402_credentials_provider_mcp` | No |
| Payment processor implementation | `merchant_payment_processor_agent` / `_mcp` | `x402_psp_mcp` | No |
| Step-up auth | mock OTP challenge (`123`) | skipped in the demo | No |
| Settlement | card network authorization | on-chain / stablecoin transfer | No |

Verified dependency signal: the `ap2-samples` package pins `web3==7.15.0` and
pulls `x402-a2a` from `github.com/google-agentic-commerce/a2a-x402`. The scenario
READMEs do **not** name specific chains, networks, or stablecoins — treat any
specific chain claim as unverified until you read the extension's own docs.

## Human present: x402

There is **no `run.sh`** under `human-present/x402/`. The scenario reuses the
cards runner with a flag:

```sh
bash code/samples/python/scenarios/a2a/human-present/cards/run.sh --payment-method x402
```

Equivalently, when launching roles manually, `export PAYMENT_METHOD=x402` before
each `uv run` command. Same four roles, same ports (8000/8001/8002/8003).

Per the README, the differences are: the merchant advertises x402 support via its
A2A agent card and in the cart mandate; the wallet's preferred method is an
x402-compatible instrument; and the OTP challenge is skipped for the x402 demo
whereas the cards flow requires the mock OTP `123`.

That OTP omission is a **demo shortcut, not a design principle**. Dropping the
step-up challenge removes a control that exists in the card flow; do not carry it
into anything real without replacing it with an equivalent.

## Human not present: x402

This one has its own runner:

```sh
bash code/samples/python/scenarios/a2a/human-not-present/x402/run.sh [--enable_broadcast_on_chain]
```

Role swaps versus the cards scenario: `x402_credentials_provider_mcp` replaces
the card credentials provider, `x402_psp_mcp` replaces the card payment
processor, and an x402 PSP trigger listens on `8084`. Agent `8080`, merchant
trigger `8081`, web client `5173` are unchanged.

`--enable_broadcast_on_chain` enables what the README calls blockchain broadcast
simulation. Without it the settlement leg is simulated locally.

Additional prerequisites beyond the card flows: Node.js/npm and `curl` (the
runner builds and serves the web client) and `lsof` (it kills stale ports).

## Migration recipe

Starting from a working card-based flow:

1. **Change nothing above the instrument.** Do not touch mandate construction,
   constraint definitions, hashing, or the chain. Re-run
   `scripts/verify_mandate_signature.py` after the migration and confirm the
   mandate-level results are byte-identical to the card run.
2. Add the x402 instrument type to `payment_instrument.type` and to any
   `payment.allowed_payment_instruments` constraint. An open mandate that only
   allows `card` instruments will correctly reject an x402 payment — that is the
   constraint working, not a bug to route around.
3. Swap the Credential Provider and payment processor implementations for their
   x402 counterparts. Keep the same interface: the CP still verifies the Payment
   Mandate *before* releasing anything, the PSP still verifies the credential is
   scoped to the Checkout.
4. Advertise x402 support on the merchant's A2A agent card so the Shopping Agent
   can discover the rail rather than assuming it.
5. Decide what replaces the OTP step-up. On the card side that challenge is a
   real control; on-chain settlement is typically irreversible, which argues for
   *more* step-up, not less.
6. Keep `payment_amount` in ISO 4217 minor units of the fiat currency the user
   approved. If the user approved USD, the mandate says USD. Any conversion to a
   token amount belongs in the settlement layer, below the mandate — otherwise
   the human never actually approved the number that gets charged.

## Known limitations

Stated in the upstream human-present x402 README, verbatim in substance:

> The AP2 compatible x402 extension is coming soon. The current x402 extension
> will be enhanced to ensure the creation of all key mandates outlined in AP2.

Read that as: **the current x402 sample does not mint the full AP2 mandate set.**
If the user's requirement is provable authorization for a crypto payment, say so
plainly — today the x402 path is a settlement demo, and the mandate coverage that
makes AP2 useful in a dispute is not yet complete on that rail. Track
https://github.com/google-agentic-commerce/a2a-x402/ before promising otherwise.

Also stale on that path: the human-present x402 README narrates the retired v0.1
vocabulary (`IntentMandate`, `CartMandate`) while the code it runs uses the v0.2
SDK. Do not copy its mandate narrative.

## Audit deltas

Add these to the Step 7 checklist when the x402 rail is in play:

1. Mandate structure is unchanged from the card flow — diff it and prove it.
   *critical*
2. `payment.allowed_payment_instruments` includes the x402 instrument type
   explicitly rather than the constraint being dropped. *critical*
3. Something replaces the skipped OTP step-up, or the risk is explicitly accepted
   and recorded. *high*
4. The approved fiat amount in `payment_amount` is what the user saw; any token
   conversion happens below the mandate and is logged. *critical*
5. Irreversibility is accounted for: on-chain settlement has no chargeback, so
   the retained mandate evidence is the *only* dispute mechanism. Confirm the
   evidence tuple is complete before enabling `--enable_broadcast_on_chain` or
   any real broadcast. *critical*
6. No private keys or seed phrases are reachable from an agentic role. *critical*
