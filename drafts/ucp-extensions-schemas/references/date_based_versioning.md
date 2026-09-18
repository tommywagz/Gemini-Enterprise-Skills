# Date-Based Versioning in Universal Commerce Protocol

This reference outlines the date-based versioning lifecycle used throughout the Universal Commerce Protocol (UCP), ensuring cross-vendor stability, forward compatibility, and graceful protocol evolution.

## Table of Contents
- [1. Version String Specification](#1-version-string-specification)
- [2. Versioning Semantics vs Semantic Versioning (SemVer)](#2-versioning-semantics-vs-semantic-versioning-semver)
- [3. Immutability Principle](#3-immutability-principle)
- [4. Breaking vs Non-Breaking Schema Changes](#4-breaking-vs-non-breaking-schema-changes)
- [5. Discovery Profile Negotiation](#5-discovery-profile-negotiation)
- [6. Deprecation and Sunset Strategy](#6-deprecation-and-sunset-strategy)

---

## 1. Version String Specification

UCP identifies protocol releases, capability schemas, and extension definitions using ISO 8601 calendar date identifiers:

- **Format:** `YYYY-MM-DD`
- **Regex Pattern:** `^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$`
- **Examples:** `2026-01-11`, `2026-04-08`, `2026-08-25`, `2026-09-18`

Every canonical schema `$id` and discovery manifest capability MUST include the version date matching the release date of that specification milestone:

```
https://ucp.dev/2026-08-25/schemas/shopping/checkout.json
https://example.com/schemas/2026-09-18/food_ordering.json
```

---

## 2. Versioning Semantics vs Semantic Versioning (SemVer)

Unlike traditional SemVer (`MAJOR.MINOR.PATCH`), UCP adopts date-based versioning because:

1. **Protocol Multi-Party Coordination:** Multi-agent commerce involves hundreds of independent parties (buyers, sellers, orchestrators, gateways). Calendar dates establish unambiguous temporal ordering across decentralized ecosystem participants.
2. **Snapshot Semantics:** A date version represents an immutable snapshot of schemas and capabilities guaranteed to interoperate.
3. **No Hidden Patch Drift:** Clients and servers can immediately determine if their capabilities reflect the same snapshot without relying on ambiguous patch level increments.

---

## 3. Immutability Principle

Once a schema is published under a date-versioned path, it is **strictly immutable**:

- Schemas published at `https://example.com/schemas/2026-09-18/food_ordering.json` MUST NOT have their contents edited in place to introduce schema shifts.
- If errors or omissions are identified that do not break backward compatibility, authoring teams may issue a non-breaking revision on a new calendar date.
- Cache headers on schema endpoints should set long TTLs (e.g. `Cache-Control: public, max-age=31536000, immutable`), reflecting the immutable guarantee.

---

## 4. Breaking vs Non-Breaking Schema Changes

### 4.1 Non-Breaking (Backward Compatible) Updates
The following changes may be introduced in future date releases without breaking existing agents:
- Adding optional properties to objects.
- Adding definitions (`$defs`) not referenced by required fields.
- Adding new optional capabilities to the discovery profile.
- Widening accepted constraints (e.g., increasing `maxLength`, allowing more items in an array).
- Loosening regular expression patterns to accept more valid inputs.

### 4.2 Breaking Changes (Incompatible Shifts)
The following modifications constitute breaking changes and require downstream agents to upgrade:
- Adding a required field to an existing request or response payload.
- Removing or renaming any existing property.
- Changing a property's primitive type (e.g., string to object, integer to string).
- Narrowing validation constraints (e.g., lowering `maximum`, introducing stricter patterns).
- Changing default values that alter business logic or pricing calculations.
- Removing enum entries that valid clients might transmit.

When breaking changes occur, the extension author publishes a new date version and maintains both versions in the discovery manifest during the migration grace period.

---

## 5. Discovery Profile Negotiation

A business declares its supported extension versions within its `/.well-known/ucp` manifest:

```json
{
  "ucp": {
    "version": "2026-08-25",
    "capabilities": [
      {
        "version": "2026-08-25",
        "spec": "https://ucp.dev/2026-08-25/specification/shopping/checkout",
        "schema": "https://ucp.dev/2026-08-25/schemas/shopping/checkout.json",
        "extends": null
      },
      {
        "version": "2026-09-18",
        "spec": "https://example.com/2026-09-18/specification/food_ordering",
        "schema": "https://example.com/schemas/2026-09-18/food_ordering.json",
        "extends": "dev.ucp.shopping.checkout"
      }
    ]
  }
}
```

During discovery, the shopping client evaluates each capability's `version` against its local capability compatibility matrix. If the dates do not match, the client checks if the extension implements backward compatibility or declines to engage the extension.

---

## 6. Deprecation and Sunset Strategy

When retiring an older extension date version:

1. **Deprecation Notice:** Announce deprecation via documentation and optionally include HTTP warning headers or discovery metadata:
   ```json
   {
     "version": "2026-01-11",
     "deprecated": true,
     "sunset": "2026-12-31"
   }
   ```
2. **Dual-Stack Hosting:** Maintain both older and newer date-versioned schema endpoints concurrently for at least 6 months.
3. **Graceful Error Responses:** When an unsupported legacy date version is requested, return standard UCP error payloads with code `UNSUPPORTED_VERSION` and `UPGRADE_REQUIRED`.
