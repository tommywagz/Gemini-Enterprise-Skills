---
name: ucp-extensions-schemas
description: "Guides the authoring, structuring, and date-based versioning of Universal Commerce Protocol (UCP) capability extension schemas (discounts, fulfillment options, food ordering, and lodging verticals) using JSON Schema Draft 2020-12, reverse-domain authority binding, and discovery manifest integration. TRIGGER when: 'author UCP extension', 'design UCP schema', 'version UCP extension', 'date-based versioning for UCP', 'extend UCP checkout schema', 'custom UCP vertical schema', 'UCP food ordering schema', 'UCP lodging schema', 'authority binding validation'. DO NOT TRIGGER when: implementing business server routes and handlers (use ucp-merchant-servers), building client shopping agent negotiation logic (use ucp-consumer-surface), creating AP2 payment mandate credentials (use ap2-agent-payments), or designing generic non-UCP JSON schemas."
version: 1.0.0
author: Google
tags: [ucp, schema-authoring, extensions, date-versioning, json-schema, commerce]
license: Apache-2.0
compatibility: ucp-spec >= 2026-01-11
metadata: {}
---

- UCP Extension and Schema Authoring

- Overview
The Universal Commerce Protocol (UCP) standardizes autonomous commerce between buyers, sellers, and agents. While core capabilities govern fundamental commerce primitives (catalog search, cart building, checkout sessions, order tracking), real-world commerce requires vertical specialization—such as promotions, fulfillment methods, hospitality bookings, and restaurant dining options.

This skill guides developers through authoring, versioning, and validating forward-compatible UCP extension schemas without fracturing the core specification. Success looks like a clean JSON Schema Draft 2020-12 document with verified reverse-domain authority binding, an ISO 8601 calendar date version (`YYYY-MM-DD`), non-colliding additive fields, and seamless discovery manifest integration.

- Prerequisites
- Python >= 3.10 with `jsonschema` (>= 4.0.0) installed for running the local schema validator.
- Knowledge of the target base capability to extend (typically `dev.ucp.shopping.checkout` or `dev.ucp.shopping.cart`).
- A designated public domain name for schema hosting to establish reverse-domain authority (e.g. `example.com` for namespace `com.example.*`).
- Target commercial domain requirements (e.g. discounts, shipping groups, restaurant orders, or lodging reservations).

- Workflow

- Step 1: Define the Extension Scope and Target Capability
Identify whether the business goal belongs to horizontal commerce or an industry vertical:
- **Horizontal Commerce:** Augments general retail checkout sessions (e.g., promotional discount codes, multi-carrier shipping rate groups). Inspect the bundled reference schemas `assets/schemas/discount_extension.json` and `assets/schemas/fulfillment_extension.json`.
- **Industry Vertical:** Tailors checkout sessions to distinct transaction domains:
  - *Food Ordering & Quick-Service:* Meal fulfillment types (pickup, delivery, curbside, dine-in), scheduled time windows, allergen alerts, and item customizations. Review `assets/schemas/food_ordering_extension.json`.
  - *Lodging & Hospitality:* Stay dates, room class, guest headcount, and special requests. Review `assets/schemas/lodging_extension.json`.
Consult `references/vertical_extension_patterns.md` for architectural blueprints across retail categories.

- Step 2: Establish Reverse-Domain Authority and Date-Based Version
Construct the namespace and canonical schema URI adhering to UCP conventions:
1. **Reverse-Domain Namespace:** Convert the publishing organization's domain name into reverse-domain notation. For example, domain `example.com` yields namespace prefix `com.example`. Append the vertical and feature name (e.g., `com.example.food_ordering`). Core extensions retain the `dev.ucp.*` namespace prefix.
2. **Date-Based Version String:** Assign an ISO 8601 calendar date string (`YYYY-MM-DD`, such as `2026-09-18`) representing the schema release snapshot. Never use SemVer (`1.0.0`) for UCP capability versions.
3. **Canonical Schema URI ($id):** Construct the immutable HTTPS schema URL:
   `https://<domain>/schemas/<YYYY-MM-DD>/<extension_name>.json`
   Verify that the reversed host labels align with the namespace prefix. Detailed rules are documented in `references/schema_authoring_conventions.md` and `references/date_based_versioning.md`.

- Step 3: Scaffold the JSON Schema (Draft 2020-12) Document
Create the schema file with standard UCP dialect headers and metadata blocks:
- Set `"$schema": "https://json-schema.org/draft/2020-12/schema"`.
- Set `"$id"` to the canonical schema URL created in Step 2.
- Include a descriptive `title` and `description`.
- Add the required `ucp` metadata container:
  ```json
  {
    "ucp": {
      "namespace": "com.example.food_ordering",
      "version": "2026-09-18",
      "extends": "dev.ucp.shopping.checkout"
    }
  }
  ```
- Declare the root type as `"type": "object"`.
- Do **not** apply `"additionalProperties": false` to the root object. Read `references/schema_authoring_conventions.md` Section 5 to understand why property closure breaks `allOf` composition and forward compatibility.

- Step 4: Model Domain-Specific Vertical Fields with Additive Composition
Define the extension properties in the schema:
1. Encapsulate all extension fields under a single top-level object key named after the capability or vertical (e.g. `food_ordering`, `lodging`, `discounts`). This prevents naming collisions with current or future core protocol fields.
2. Define leaf structures and nested objects inside `"$defs"`. Apply `"additionalProperties": false` only to closed leaf types inside `"$defs"`.
3. Keep field evolution additive: optional properties, relaxed bounds, and non-breaking constraints. Review `assets/sample_payload_food_ordering.json` for a concrete instance illustrating how extension fields integrate into checkout payloads.

- Step 5: Validate Authority Binding and Schema Conformance
Execute the bundled Python validation utility to verify schema correctness:
```bash
python3 scripts/validate_ucp_extension.py --schema <path_to_schema>
```
To validate an entire directory of schemas:
```bash
python3 scripts/validate_ucp_extension.py --dir assets/schemas
```
To validate a test instance document against your schema:
```bash
python3 scripts/validate_ucp_extension.py --schema assets/schemas/food_ordering_extension.json --data assets/sample_payload_food_ordering.json
```
Ensure:
- Zero JSON Schema Draft 2020-12 syntax errors.
- Version string matches `YYYY-MM-DD` calendar date format.
- Authority binding check passes without mismatch.
- Sample payload passes instance validation.

- Step 6: Publish Discovery Manifest Integration
Expose the newly authored extension in the business's `/.well-known/ucp` profile under `capabilities`:
```json
{
  "ucp": {
    "version": "2026-09-18",
    "capabilities": {
      "com.example.food_ordering": [
        {
          "version": "2026-09-18",
          "spec": "https://example.com/2026-09-18/specification/food_ordering",
          "schema": "https://example.com/schemas/2026-09-18/food_ordering.json",
          "extends": "dev.ucp.shopping.checkout"
        }
      ]
    }
  }
}
```
Verify the entire discovery manifest using the validator:
```bash
python3 scripts/validate_ucp_extension.py --manifest assets/discovery_profile_extension_example.json
```

- Examples

- Example 1: Authoring a Restaurant Food Ordering Vertical Extension
Input: User requests a UCP extension schema for restaurant takeout and curbside pickup with dietary alerts.
Expected output / behavior:
1. Namespace selected: `com.example.food_ordering` with authority prefix matching host `example.com`.
2. Date version assigned: `2026-09-18`.
3. Schema created at `assets/schemas/food_ordering_extension.json` with fields for `service_type`, `requested_time`, `curbside_vehicle`, `dietary_alerts`, and `item_customizations`.
4. Schema validated with `scripts/validate_ucp_extension.py` with zero syntax errors.
5. Sample checkout payload provided in `assets/sample_payload_food_ordering.json` successfully validated.

- Example 2: Upgrading an Existing Extension to a New Date Release
Input: User needs to introduce a breaking field structure to the lodging extension (`com.example.lodging`).
Expected output / behavior:
1. Explain that date-versioned schemas are immutable and cannot be modified in place.
2. Mint a new date release version string: `2026-10-15`.
3. Generate the updated schema at `https://example.com/schemas/2026-10-15/lodging.json`.
4. Update `assets/discovery_profile_extension_example.json` to publish the new capability version while optionally supporting the legacy version during the deprecation grace period.

- Error Handling
- **Authority Binding Mismatch:** If the schema URL host (`other-site.com`) does not align with the namespace (`com.example.food_ordering`), the validator rejects the capability. Fix: host the schema under the domain matching the reverse namespace or adjust the namespace to reflect domain ownership.
- **Malformed Version String:** If SemVer (e.g. `1.2.0`) or invalid calendar dates (e.g. `2026-02-30`) are supplied, validation fails. Fix: use valid calendar dates in `YYYY-MM-DD` ISO 8601 notation.
- **Composition Failures with additionalProperties:** If root object specifies `"additionalProperties": false`, composition with core checkout sessions will fail when validating payloads containing base fields like `line_items` or `buyer`. Fix: keep root object extensible and restrict additional properties only inside `$defs`.
- **Instance Validation Errors:** If payload data types or required fields mismatch, the validator outputs path-specific diagnostic messages. Fix: inspect the JSON path reported and align payload properties with the definition.

- Anti-Patterns to Avoid
- **Root-Level Property Closure:** Never add `"additionalProperties": false` to extensible root definitions; it prevents clean `allOf` merging.
- **In-Place Schema Mutation:** Never overwrite an existing published date-versioned schema file; publish a new calendar date version for updates.
- **Ad-Hoc Proprietary Endpoints:** Never build custom out-of-band REST routes for vertical transactions. Keep checkout and payment lifecycle centered on standard UCP session flows.
- **Unencrypted or Non-Authoritative URIs:** Never use `http://` schemes or IP-literal hosts for `$id` or discovery schema references.

- Reference Files
- **references/schema_authoring_conventions.md**: Core JSON Schema Draft 2020-12 rules, namespace conventions, and authority binding criteria.
- **references/date_based_versioning.md**: In-depth specification of the `YYYY-MM-DD` lifecycle, immutability, and backward compatibility.
- **references/vertical_extension_patterns.md**: Design patterns and schemas for food ordering, lodging, discounts, and fulfillment.
- **scripts/validate_ucp_extension.py**: Executable CLI utility for validating schemas, versions, authority binding, and instance payloads.
- **assets/schemas/discount_extension.json**: Validated extension schema for checkout discounts and promotions.
- **assets/schemas/fulfillment_extension.json**: Validated extension schema for shipping destinations, rate groups, and option quotes.
- **assets/schemas/food_ordering_extension.json**: Validated extension schema for restaurant dining, takeout, and meal customization.
- **assets/schemas/lodging_extension.json**: Validated extension schema for hotel reservations, occupancy, and room types.
- **assets/discovery_profile_extension_example.json**: Sample `/.well-known/ucp` discovery profile declaring extended capabilities.
- **assets/sample_payload_food_ordering.json**: Sample checkout session payload exercising the food ordering extension schema.

- Output Format
Return the complete path tree of created schema assets, scripts, and references, along with confirmation of clean execution from `scripts/validate_ucp_extension.py`. Summarize the declared namespaces, date version, and capability linkages.
