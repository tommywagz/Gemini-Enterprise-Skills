# UCP Schema Authoring Conventions

This guide specifies technical conventions, architectural rules, and JSON Schema practices for authoring Universal Commerce Protocol (UCP) capability extensions.

## Table of Contents
- [1. Reverse-Domain Namespaces](#1-reverse-domain-namespaces)
- [2. Authority Binding Principles](#2-authority-binding-principles)
- [3. JSON Schema Dialect & Header Standards](#3-json-schema-dialect--header-standards)
- [4. Composition vs. Inheritance (allOf & $ref)](#4-composition-vs-inheritance-allof--ref)
- [5. Extensibility & Property Closure Rules](#5-extensibility--property-closure-rules)
- [6. Forward Compatibility Checklist](#6-forward-compatibility-checklist)

---

## 1. Reverse-Domain Namespaces

All UCP capabilities, services, and extensions use reverse-domain notation for uniqueness and organizational ownership.

- **Core Protocol Namespace:** `dev.ucp.*`
  - Examples: `dev.ucp.shopping.cart`, `dev.ucp.shopping.checkout`, `dev.ucp.shopping.discount`, `dev.ucp.shopping.fulfillment`.
- **Third-Party / Vendor Extension Namespaces:** `<reversed-domain>.<vertical>.<capability>`
  - Examples:
    - `com.example.restaurant.food_ordering`
    - `com.hospitality.lodging_reservation`
    - `org.logistics.courier_delivery`

Namespace segments must use lowercase alphanumeric characters and periods. Underscores are permitted within terminal capability identifiers (`food_ordering`) but hyphens should be avoided in namespace paths to maintain cross-language identifier compatibility.

---

## 2. Authority Binding Principles

To prevent namespace squatting and malicious schema spoofing, UCP enforces strict authority binding between the declared namespace and the schema URL:

1. **Host-to-Prefix Alignment:**
   - The host of the schema URI must align with the leading labels of the namespace when reversed.
   - For domain `schemas.example.com`, the authority prefix is `com.example.schemas` or root `com.example`.
   - A schema declaring namespace `com.example.restaurant.food_ordering` MUST be served from `example.com` or a valid subdomain like `schemas.example.com`.
   - Core protocol schemas in namespace `dev.ucp.*` MUST originate from `ucp.dev` or subdomains thereof.

2. **Transport & URI Constraints:**
   - Schema URLs MUST use the HTTPS scheme.
   - User credentials (`user:password@`) are strictly prohibited in schema URLs.
   - IP addresses and unresolvable single-label hosts (e.g., `localhost`) are disallowed in production schemas.

---

## 3. JSON Schema Dialect & Header Standards

All UCP schemas target JSON Schema Draft 2020-12 (`https://json-schema.org/draft/2020-12/schema`).

Every extension schema must specify the following top-level properties:

- `$schema`: Identifies dialect compliance: `"https://json-schema.org/draft/2020-12/schema"`.
- `$id`: Canonical public URI for the schema document. Must include the date version:
  `"https://example.com/schemas/2026-09-18/food_ordering.json"`
- `title`: Short human-readable name of the extension (e.g., `"UCP Food Ordering Extension"`).
- `description`: Detailed explanation of what commerce goals this extension fulfills.
- `type`: Usually `"object"`.
- `ucp`: Metadata container describing extension linkage:
  - `namespace`: Full reverse-domain namespace (e.g., `"com.example.food_ordering"`).
  - `version`: ISO 8601 date string (`"YYYY-MM-DD"`).
  - `extends`: Target core capability being augmented (e.g., `"dev.ucp.shopping.checkout"`).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/2026-09-18/food_ordering.json",
  "title": "UCP Food Ordering Extension",
  "description": "Schema extending checkout sessions with restaurant meal options and pickup windows.",
  "type": "object",
  "ucp": {
    "namespace": "com.example.food_ordering",
    "version": "2026-09-18",
    "extends": "dev.ucp.shopping.checkout"
  }
}
```

---

## 4. Composition vs. Inheritance (allOf & $ref)

JSON Schema does not support object-oriented class inheritance; it uses logical composition via `allOf` and external references (`$ref`).

### 4.1 Augmenting Existing Resources
When extending a base resource such as `dev.ucp.shopping.checkout`, create an extension object that either:
- Nests specialized domain entities under a dedicated extension property key:
  ```json
  {
    "type": "object",
    "properties": {
      "food_ordering": {
        "$ref": "#/$defs/FoodOrderingDetails"
      }
    }
  }
  ```
- Composes the base schema using `allOf`:
  ```json
  {
    "allOf": [
      { "$ref": "https://ucp.dev/2026-08-25/schemas/shopping/checkout.json" },
      {
        "type": "object",
        "properties": {
          "dining_options": { "$ref": "#/$defs/DiningOptions" }
        }
      }
    ]
  }
  ```

Nesting under a dedicated property namespace (`food_ordering`, `lodging`, `discounts`) is preferred because it avoids collision with future properties added to core schemas.

---

## 5. Extensibility & Property Closure Rules

A common mistake in JSON Schema authoring is adding `"additionalProperties": false` to an extensible object definition.

### 5.1 The `additionalProperties` Anti-Pattern
In JSON Schema `allOf` composition:
- `additionalProperties: false` validates each branch independently.
- If schema A defines `field_a` with `additionalProperties: false`, and schema B defines `field_b` with `additionalProperties: false`, validating an instance with both `field_a` and `field_b` FAILS on both branches.
- Therefore, never apply `additionalProperties: false` to top-level checkout or cart objects intended for extension.

### 5.2 Recommended Approaches
- **Open Extensibility:** Omit `additionalProperties` on root objects, allowing extension fields to pass through cleanly.
- **Strict Inner Types:** Apply `additionalProperties: false` only to leaf value objects and closed enums inside `$defs` where no downstream extension is expected.
- **Draft 2020-12 unevaluatedProperties:** When property restriction is strictly required, use `"unevaluatedProperties": false` across the composed boundary after all subschemas have evaluated their properties.

---

## 6. Forward Compatibility Checklist

Before releasing a UCP extension schema, verify these compatibility rules:

1. **Additive Only:** New fields added to an existing version MUST be optional (`required` array cannot add fields post-release).
2. **Type Invariance:** Never alter the type of an existing field (e.g. changing a string ID to an integer or object).
3. **No Field Deletions:** Existing properties and enum values cannot be removed within the same date version.
4. **Relaxation, Not Tightening:** Validation constraints (like `minimum`, `maximum`, `pattern`) can only be widened, never narrowed, in a non-breaking update.
5. **Breaking Changes Require New Date:** If breaking modifications are unavoidable, publish under a newly minted `YYYY-MM-DD` date version.
