---
name: ap2-agent-payments
description: "Builds and audits AP2 (Agent Payments Protocol) payment agents: Checkout and Payment Mandates as SD-JWT verifiable credentials, human-present vs. human-not-present flows, role sub-agents, x402 crypto rails, and authorization/dispute audits. TRIGGER when the user mentions AP2, ap2-protocol.org, 'mandate.checkout.1', 'mandate.payment.1', Checkout Mandate, Payment Mandate, open vs. closed mandate, Credentials Provider or Merchant Payment Processor agents, x402 settlement, google-agentic-commerce/AP2, or asks to let an agent pay, delegate autonomous spend under signed constraints, or prove after the fact who authorized a purchase. DO NOT TRIGGER for UCP cart/catalog/checkout-session work with no payment settlement (use ucp-merchant-servers or ucp-consumer-surface), or for wiring a non-agentic payment gateway SDK (Stripe, PayPal, Adyen) with no verifiable mandate credential."
version: 1.0.0
author: Actual Agentic Solutions
tags: [ap2, payments, agentic-commerce, sd-jwt, mandates, x402, a2a, adk]
license: Apache-2.0
compatibility: AP2 spec v0.2 (mandate vct suffix .1); reference impl google-agentic-commerce/AP2 @ 0.2.0
metadata: {}
---

- AP2 Agent Payments Builder & Auditor

- Overview
AP2 is a security layer over a commerce protocol (it is designed to compose with
UCP). It does not move money. It produces **non-repudiable evidence of what a
human authorized**, so that after the fact a merchant, processor, or dispute
handler can prove which human approved which cart at which price on which
instrument. Everything in AP2 reduces to two verifiable credentials — a
**Checkout Mandate** (secures *what* is bought) and a **Payment Mandate**
(secures *the payment for* that checkout) — cryptographically linked by the hash
of the merchant-signed `checkout_jwt`.

Success looks like: a mandate chain that a verifier can validate offline, with
each role holding only the credentials its role is entitled to, and a retained
mandate + receipt tuple sufficient to resolve a dispute.

Assume the LLM is an attacker. AP2's threat model explicitly states that prompt
injection cannot be prevented, so every agent — including the one you are
building — is inside the threat model. All verification MUST run in
deterministic code, never in a prompt.

- Prerequisites
- The user's goal, and specifically **whether the human is present at the moment
  of purchase**. This is the routing decision in Step 1; do not skip it.
- Python >= 3.11 and `uv` if generating against the reference implementation.
- For running samples: `GOOGLE_API_KEY`, or `GOOGLE_GENAI_USE_VERTEXAI=true` plus
  `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` with ADC. Human-not-present
  scenarios additionally need Node.js/npm, `curl`, and `lsof`.
- A local clone of `https://github.com/google-agentic-commerce/AP2` if you intend
  to run or copy from the scenarios. Set `AP2_REPO=/path/to/AP2`.
- If the transport is A2A or the agents are ADK agents, compose with the
  `a2a-workflows` and `adk-agents` skills for the agent plumbing; this skill owns
  only the mandate and credential layer.

- Workflow

- Step 1: Route the flow — human present or human not present
Decide this **before writing any agent code**. It changes which mandates exist,
who signs them, and when.
- **Human Present (`direct`)** — the user is at the surface and approves the
  finalized cart. The Trusted Surface signs **closed** Checkout and Payment
  Mandates with `user_sk`. There are no open mandates and no agent signing key in
  the authorization path. Choose this when the user said "buy this", "check out
  now", or any single confirmed purchase.
- **Human Not Present (`autonomous`)** — the user pre-authorizes *constraints*
  and leaves. The Trusted Surface signs **open** Checkout and Payment Mandates
  carrying `constraints` plus a `cnf` claim holding the agent's public key; later
  the agent signs **closed** mandates with `agent_sk` and presents the whole
  chain. Choose this when the user said "buy it when it drops below $X",
  "reorder monthly", "book it if it becomes available", or delegated a budget.
- Ambiguous input (e.g. "help me shop"): default to Human Present and say so —
  it is the strictly weaker authorization and cannot silently overspend.
- A Human-Not-Present flow degrades to Human Present at runtime when a verifier
  returns `unresolved_constraint`; build that fallback path, do not treat the
  error as fatal.
Scaffold from the matching scenario (see Step 8 for exact commands):
`code/samples/python/scenarios/a2a/human-present/…` or `…/human-not-present/…`.

- Step 2: Construct the mandates
Read `references/ap2_spec_summary.md` before writing mandate code — it carries
the full field tables, the exact `vct` strings, the constraint catalog, and the
SD-JWT chain shape. Then:
1. Get the merchant-signed `checkout_jwt` for the finalized cart. AP2 is agnostic
   to its payload; with UCP it MUST be the Checkout object.
2. Compute `checkout_hash` = base64url(hash(`checkout_jwt`)) using the SD-JWT's
   `_sd_alg`, defaulting to `sha-256`.
3. Build the closed Checkout Mandate (`vct: "mandate.checkout.1"`) with
   `checkout_jwt` (selectively disclosable) and `checkout_hash` (not disclosable).
4. Build the closed Payment Mandate (`vct: "mandate.payment.1"`) setting
   `transaction_id` to that same `checkout_hash`. This link is the entire
   anti-swap defense — never generate `transaction_id` independently.
5. For Human Not Present, also build the open mandates
   (`mandate.checkout.open.1`, `mandate.payment.open.1`) with `constraints`,
   `cnf.jwk` = agent public key, and a **short** `exp` — the smallest window that
   lets the task finish.
- Amounts are integer minor units per ISO 4217 (`19900` = $199.00). Passing a
  float or major units is the single most common bug here.
- The `checkout_jwt` MUST be signed with a non-deterministic scheme (ES256), not
  Ed25519, or the `checkout_hash` becomes guessable by rainbow table.
- Validate generated mandates against `assets/checkout_mandate_schema.json` and
  `assets/payment_mandate_schema.json`.

- Step 3: Pick constraints that actually bound the loss
Only meaningful for open mandates. Every constraint the verifier does not
recognize MUST fail evaluation, so do not invent constraint types unless you also
control the verifier.
- Bound money: `payment.amount_range` (per transaction) plus `payment.budget`
  (cumulative) — `payment.budget` is only meaningful alongside
  `payment.agent_recurrence`, which bounds *how often*.
- Bound counterparties: `payment.allowed_payees`, `checkout.allowed_merchants`,
  `payment.allowed_payment_instruments`, `payment.allowed_pisps`.
- Bound goods: `checkout.line_items` with `acceptable_items` and `quantity`.
- Bound linkage and time: `payment.reference` (ties the Payment Mandate to a
  specific open Checkout Mandate), `payment.execution_date`, and `exp`.
- Anti-pattern: an open Payment Mandate with `amount_range` alone. Without
  `allowed_payees` (or `payment.reference`) it authorizes paying *anyone* up to
  that ceiling.

- Step 4: Split the roles into sub-agents with real credential boundaries
Generate one addressable agent per AP2 role — Shopping Agent, Merchant Agent,
Credentials Provider, Merchant Payment Processor — plus a **non-agentic** Trusted
Surface. Read `references/role_credential_matrix.md` for exactly what each role
may hold, receive, and never see, and for the reference implementation's module
paths and ports.
- The Trusted Surface MUST NOT be an LLM. It is the only component that renders
  mandate content to the human and triggers signing.
- In the Trusted Agent Provider model, the Agent Provider MUST ensure the agent
  cannot reach the signing key or use it without the Trusted Surface.
- Raw payment credentials/tokens are released **only after** a Payment Mandate
  verifies, and go only to the party that needs them. The Shopping Agent gets a
  scoped token, never a PAN.
- One entity MAY play several roles, but it then inherits every one of those
  roles' verification duties — do not collapse roles to skip verification.

- Step 5: Verify at every hop and persist the receipts
Each verifier runs deterministic checks and MUST return a signed receipt either
way (success *or* error). The receipt `reference` is the base64url hash of the
closed mandate, computed the same way as `sd_hash`.
- Merchant verifies the Checkout Mandate: chain integrity, `checkout_hash` equals
  the hash of the `checkout_jwt` it actually issued, and every open-mandate
  constraint evaluates true. Returns a Checkout Receipt (`order_id` on success).
- Credential Provider and Network verify the Payment Mandate before releasing a
  token. Returns a Payment Receipt.
- Merchant Payment Processor verifies the payment credential is scoped to this
  checkout — typically by carrying the closed Payment Mandate inside the token.
- Error codes are fixed: `invalid_credential`, `unresolved_constraint`,
  `invalid_mandate`, `mandates_not_supported`. Only `unresolved_constraint` and
  `mandates_not_supported` are recoverable — they signal a fallback to a
  human-present or non-agentic flow. The other two are terminal.
- Persist the (open mandate, closed mandate, receipt) tuple keyed by
  `transaction_id`. That tuple *is* the dispute evidence; without it the audit in
  Step 7 has nothing to inspect.
- After a success receipt, reduce the open mandate's remaining scope (decrement
  budget/occurrences), and store it where the LLM cannot rewrite it.

- Step 6: Add the x402 / crypto rail only if asked
x402 changes settlement, not authorization. The mandate structure from Steps 2-3
stays byte-identical. Read `references/x402_settlement_guide.md` before touching
it — it covers what the sample actually swaps (MCP-based x402 Credentials
Provider and PSP roles), the flag that selects the rail, and the upstream caveat
that the current x402 extension does not yet mint every AP2 mandate.
- Anti-pattern: reworking mandates "for crypto". If the mandate shape changes
  when the rail changes, the design is wrong.

- Step 7: Audit authorization and privacy
Run the checker over any mandate chain you produced or received:
```
python3 scripts/verify_mandate_signature.py <mandate-chain-file> \
  --checkout-jwt-file <checkout.jwt> --json
```
It parses the SD-JWT chain, recomputes every disclosure digest, checks the
`sd_hash` binding between chain hops, recomputes `checkout_hash` /
`transaction_id`, checks `exp`/`iat`/`cnf` placement, evaluates the known
constraints, and verifies ES256 signatures when `cryptography` is installed
(otherwise it reports signature checks as `SKIPPED` rather than passing them).
Exit `0` = pass, `1` = verification failure, `2` = usage/parse error.
Then walk the audit checklist in `references/ap2_spec_summary.md` §Audit and
write the result into `assets/dispute_audit_report_schema.json` form. Flag at
minimum: mandates with no `exp` or an `exp` far wider than the task; open
mandates missing `cnf`; a Payment Mandate whose `transaction_id` does not match
the Checkout; disclosures revealed to a role that has no need for them; and any
path where a token is released before mandate verification.

- Step 8: Prove it end to end against the reference scenarios
```
scripts/simulate_ap2_flow.sh --flow human-present     --rail cards --dry-run
scripts/simulate_ap2_flow.sh --flow human-not-present --rail x402  --repo "$AP2_REPO"
```
The script resolves the AP2 repo, checks prerequisites, prints the exact
`run.sh` invocation and role/port map, and executes it unless `--dry-run`. Note
the quirk it handles for you: human-present/x402 has **no** `run.sh` — it reuses
the cards runner with `--payment-method x402`.

- Examples

- Example 1: "Buy this jacket for me now"
Input: user is in the chat, cart is finalized at $199.00 USD.
Expected output / behavior: Human Present. One closed Checkout Mandate
(`mandate.checkout.1`) and one closed Payment Mandate (`mandate.payment.1`,
`payment_amount` = `{"amount": 19900, "currency": "USD"}`), both signed by the
Trusted Surface with `user_sk`, linked by `checkout_hash`. No open mandates, no
`cnf`, no constraint evaluation. Merchant returns a Checkout Receipt with
`order_id`; MPP returns a Payment Receipt.

- Example 2: "Buy the gold sneakers if they drop under $200 in the next hour"
Input: user will not be present at purchase time.
Expected output / behavior: Human Not Present. Trusted Surface signs an open
Checkout Mandate with `checkout.line_items` (the acceptable SKUs, quantity 1) and
`checkout.allowed_merchants`, and an open Payment Mandate with
`payment.amount_range` (`max: 20000`, `currency: "USD"`), `payment.allowed_payees`
and `payment.reference` pointing at the open Checkout Mandate's digest — both
carrying `cnf.jwk` = agent key and `exp` = now + 3600. When the price drops, the
agent signs closed mandates with `agent_sk` and presents open + closed to each
verifier, disclosing only the matching SKU — not the full acceptable-items list.

- Error Handling
- `invalid_credential` — chain signature or digest failed. Terminal. Do not
  retry with the same chain; regenerate from the Trusted Surface.
- `unresolved_constraint` — verifier saw an unknown constraint or could not
  evaluate one. Recoverable: fall back to a Human Present approval of the closed
  mandate. Commonly caused by a custom constraint type the verifier lacks.
- `invalid_mandate` — the mandate does not authorize the requested action
  (amount over range, wrong payee, expired). Terminal for this attempt; re-scope
  and re-approve with the user.
- `mandates_not_supported` — the verifier does not do mandates at all. Fall back
  to a non-agentic checkout.
- `checkout_hash` mismatch — the cart changed after signing (price, tax,
  shipping). Re-fetch the `checkout_jwt` and re-sign; never patch the hash.
- Missing or unreadable reference/asset file in this skill: name the file, do not
  reconstruct the field tables from memory, and pull the canonical definition
  from https://ap2-protocol.org/ap2/specification/ instead.
- `cryptography` not installed: `verify_mandate_signature.py` still validates
  structure and bindings but reports signature checks as `SKIPPED`. Never report
  an audit as passing on the strength of a skipped signature check.

- Anti-Patterns to Avoid
- **Verifying in the prompt.** Mandate verification, constraint evaluation, and
  receipt checking MUST be deterministic code. An LLM "confirming" a signature is
  worth nothing under AP2's threat model.
- **Reusing an open mandate speculatively.** The Shopping Agent MUST NOT sign
  multiple overlapping closed mandates against one open mandate before receiving
  a rejection receipt for the earlier one. That is the double-spend hole.
- **Disclosing the whole constraint set.** Present only the disclosures needed to
  evaluate the closed mandate. The full acceptable-items or allowed-merchants
  list leaks user intent and shopping strategy.
- **Long-lived open mandates.** `exp` far beyond the task turns a scoped
  delegation into a standing authorization to spend.
- **Ed25519 on the `checkout_jwt`.** Deterministic signatures make
  `checkout_hash` rainbow-table-able. Use ES256.
- **Letting the Shopping Agent hold raw instrument data.** It receives a scoped
  token bound to this transaction, nothing more.
- **Trusting the upstream sample READMEs verbatim.** Several still narrate the
  retired v0.1 vocabulary (`IntentMandate`, `CartMandate`) that the current code
  no longer uses; trust `code/sdk/python/ap2/sdk/generated/` and
  `code/sdk/schemas/`.

- Reference Files
- **references/ap2_spec_summary.md**: mandate field tables, exact `vct` strings,
  full constraint catalog with evaluation rules, SD-JWT chain mechanics, receipt
  schemas, and the audit checklist. Read in Steps 2, 3, 5, and 7.
- **references/role_credential_matrix.md**: per-role holds/receives/never-sees
  matrix, verification duties, reference-implementation module paths and ports.
  Read in Step 4.
- **references/x402_settlement_guide.md**: what the x402 rail swaps, how to
  select it, and its current limitations. Read in Step 6 only.
- **scripts/verify_mandate_signature.py**: deterministic mandate-chain verifier
  and constraint evaluator. Run in Step 7.
- **scripts/simulate_ap2_flow.sh**: prerequisite check + scenario runner for the
  four reference flows. Run in Step 8.
- **assets/checkout_mandate_schema.json**, **assets/payment_mandate_schema.json**:
  JSON Schemas for open and closed mandate content — validate generated mandates
  against these in Step 2.
- **assets/dispute_audit_report_schema.json**: output shape for the Step 7 audit.

- Output Format
Deliver: (1) the routing decision from Step 1 with its justification, (2) the
mandate definitions with their constraints, (3) the role sub-agents with an
explicit statement of which credentials each holds, (4) the verification and
receipt-persistence code, and (5) the Step 7 audit report conforming to
`assets/dispute_audit_report_schema.json`. State the AP2 spec version targeted
(v0.2, `vct` suffix `.1`). If any check was skipped — unavailable signing keys,
`cryptography` missing, no live merchant — say so explicitly rather than
reporting a clean pass.
