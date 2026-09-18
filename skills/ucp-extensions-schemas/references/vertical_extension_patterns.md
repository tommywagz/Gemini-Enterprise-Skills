# Vertical and Domain Extension Patterns

This guide provides concrete schema blueprints and design patterns for authoring horizontal and vertical commerce extensions in the Universal Commerce Protocol (UCP).

## Table of Contents
- [1. Extension Architecture Overview](#1-extension-architecture-overview)
- [2. Horizontal Commerce Extensions](#2-horizontal-commerce-extensions)
  - [2.1 Discount & Promotion Extension](#21-discount--promotion-extension)
  - [2.2 Fulfillment & Shipping Option Extension](#22-fulfillment--shipping-option-extension)
- [3. Industry Vertical Extensions](#3-industry-vertical-extensions)
  - [3.1 Food Ordering Vertical](#31-food-ordering-vertical)
  - [3.2 Lodging & Hospitality Vertical](#32-lodging--hospitality-vertical)
- [4. Anti-Forking Principles](#4-anti-forking-principles)

---

## 1. Extension Architecture Overview

Rather than inventing proprietary endpoint trees for every commerce niche, UCP models diverse commercial domains by extending standard primitives:

- **Cart (`dev.ucp.shopping.cart`):** Tracks items, selections, and preliminary totals.
- **Checkout Session (`dev.ucp.shopping.checkout`):** Collects fulfillment parameters, applies pricing rules, collects buyer information, and executes payment settlement.
- **Order (`dev.ucp.shopping.order`):** Maintains post-checkout lifecycle, tracking, and fulfillment records.

Extensions augment these objects by defining additive fields that nest cleanly under distinct domain keys.

---

## 2. Horizontal Commerce Extensions

Horizontal extensions apply across retail categories and are widely supported by merchant servers.

### 2.1 Discount & Promotion Extension
- **Namespace:** `dev.ucp.shopping.discount`
- **Extends:** `dev.ucp.shopping.checkout`
- **Responsibilities:**
  - Accepts user-entered discount / coupon codes in checkout requests (`discounts.codes: ["SUMMER25"]`).
  - Returns applied discounts, savings calculations, per-line-item allocations, and rejection reasons.
- **Design Pattern:**
  Provide an input structure (`codes: string[]`) alongside an output structure (`applied: DiscountDetail[]`). This separation guarantees that callers can present rejected promotion codes to users with specific messaging.

### 2.2 Fulfillment & Shipping Option Extension
- **Namespace:** `dev.ucp.shopping.fulfillment`
- **Extends:** `dev.ucp.shopping.checkout`
- **Responsibilities:**
  - Manages destination shipping addresses and recipient details.
  - Dynamically calculates shipping option methods (standard, express, overnight, local pickup) with associated carrier details, estimated arrival windows, and fees.
- **Design Pattern:**
  Support a multi-destination array to enable split shipments, and provide an explicit `selected_option_id` to link the buyer's choice to the rated quotes.

---

## 3. Industry Vertical Extensions

Vertical extensions tailor UCP to industries with unique operational semantics without breaking common cart and checkout mechanics.

### 3.1 Food Ordering Vertical
- **Namespace:** `com.example.food_ordering` (or provider reversed domain)
- **Extends:** `dev.ucp.shopping.checkout`
- **Core Entities:**
  1. **Fulfillment Timing:** Order type (`pickup`, `delivery`, `curbside`, `dine_in`), scheduled fulfillment window (asap vs target ISO timestamp), and parking stall or table identifiers.
  2. **Dietary & Allergen Declarations:** Customer allergen alerts (`peanut_free`, `gluten_sensitive`) and cutlery preferences.
  3. **Item Customization:** Modifiers, ingredient add/remove choices, temperature preferences, and preparation special instructions attached to individual line items.
- **Payload Shape:**
  ```json
  {
    "food_ordering": {
      "service_type": "delivery",
      "requested_time": "2026-09-18T12:30:00Z",
      "dietary_notes": "Allergic to shellfish",
      "utensils_requested": false,
      "contactless_delivery": true
    }
  }
  ```

### 3.2 Lodging & Hospitality Vertical
- **Namespace:** `com.example.lodging` (or provider reversed domain)
- **Extends:** `dev.ucp.shopping.checkout`
- **Core Entities:**
  1. **Stay Parameters:** Check-in date (`YYYY-MM-DD`), check-out date (`YYYY-MM-DD`), and total stay nights.
  2. **Occupancy Breakdown:** Count of adult guests, child guests, and infant guests, with ages if required for city occupancy taxes.
  3. **Room Attributes:** Room class identifier, bed configurations, smoking preference, and accessibility requirements.
  4. **Policies:** Cancellation cutoff deadline and deposit terms.
- **Payload Shape:**
  ```json
  {
    "lodging": {
      "property_id": "prop_98124",
      "check_in_date": "2026-10-01",
      "check_out_date": "2026-10-05",
      "guests": { "adults": 2, "children": 0 },
      "room_type_id": "deluxe_king_suite",
      "special_requests": "Late arrival after 20:00"
    }
  }
  ```

---

## 4. Anti-Forking Principles

When adapting UCP to a new commercial domain, adhere strictly to these principles:

1. **Retain Core Session Lifecycles:** Never bypass `POST /checkout-sessions` or `POST /checkout-sessions/{id}/complete`. Even non-physical goods (lodging, meal ordering, digital downloads) utilize checkout sessions to coordinate pricing, buyer verification, and payment authorization.
2. **Reuse Currency and Pricing Types:** All totals, taxes, fees, and line-item prices must reuse UCP's standard monetary amounts (`amount` in minor units or integer cents, accompanied by ISO 4217 `currency`).
3. **Avoid Custom Transport Protocols:** Implement extensions within standard REST, MCP, or A2A transports. Introducing bespoke socket layers or out-of-band protocols breaks compatibility with multi-agent orchestrators.
4. **Preserve Reversible Authority:** All extension schemas must be accessible over HTTPS from domain hosts corresponding to the reverse namespace prefix.
