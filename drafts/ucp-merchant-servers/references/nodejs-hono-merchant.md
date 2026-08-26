# Node.js/Hono UCP Merchant Server Reference

This reference guide documents the Node.js, Hono, and Zod implementation conventions, folder layout, and execution steps for a UCP Merchant/Business server.

---

## 1. Directory Structure

A standardized Node.js UCP server follows this project structure:
```
rest/nodejs/
├── src/
│   ├── index.ts              # Entry point, initializes the Hono app
│   ├── config.ts             # Environment variables (REQUIRE_SIGNATURES, etc.)
│   ├── api/                  # UCP Route handlers
│   │   ├── discovery.ts      # Exposes GET /.well-known/ucp
│   │   ├── checkout.ts       # Handles create, update, complete, and cancel checkout
│   │   └── order.ts          # Tracks post-purchase orders and processes webhooks
│   ├── data/                 # Database layer
│   │   └── database.ts       # Handles SQLite connections using better-sqlite3
│   ├── models/               # Zod validation schemas & types
│   │   └── schemas.ts        # Maps to UCP capability profiles
│   └── utils/                # Cryptographic and signature utilities
│       ├── digest.ts         # RFC 9530 Content-Digest generation
│       └── signature.ts      # RFC 9421 signature signing & verification
├── databases/                # Stores products.db and transactions.db SQLite files
├── package.json              # NPM dependencies and scripts
└── tsconfig.json             # TypeScript compiler options
```

---

## 2. Dependencies & Tooling

- **Runtime:** Node.js >= 20.
- **Framework:** Hono (highly performant, lightweight, web-standard routing).
- **Validation:** Zod schemas are used for runtime request payload parsing.
- **Database:** `better-sqlite3` or similar lightweight package for transactional safety with SQLite database files.

---

## 3. Database Initialization

The server checks and initializes SQLite schemas dynamically at startup:
- Creates `products` tables (for variants, descriptions, attributes, pricing).
- Creates `transactions` or `checkouts` tables (for session states, line items, buyer, totals).
- Expected database files live in `./databases/products.db` and `./databases/transactions.db`.

---

## 4. Execution Parameters & Env Vars

Control Hono server behavior via system environment variables:

```bash
# Run server with development hot-reload
npm run dev

# Run in production with request signature enforcement enabled
REQUIRE_SIGNATURES=true \
ALLOW_INSECURE_PROFILE_URLS=false \
PORT=3000 \
npm start
```

### Environment Variables:
- `REQUIRE_SIGNATURES`: Restricts API endpoints to verified RFC 9421 signatures when `true`.
- `ALLOW_INSECURE_PROFILE_URLS`: Enables loopback/http profile resolution for local testing/CI if `true` (SSRF protections are disabled).
- `WEBHOOK_SIGNING_KEY`: Path to private PEM key (EC P-256 or Ed25519) to sign order event webhook deliveries.

---

## 5. Implementation Core Patterns

### 5.1 Route Validation with Zod
Hono uses Zod middleware for robust, schema-compliant JSON body parsing:

```typescript
import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { checkoutCreateSchema } from '../models/schemas';

const app = new Hono();

app.post('/checkout-sessions', zValidator('json', checkoutCreateSchema), async (c) => {
  const data = c.req.valid('json');
  const ucpAgent = c.req.header('UCP-Agent');
  const idempotencyKey = c.req.header('Idempotency-Key');

  // Core checkout business logic
  const checkoutSession = await checkoutService.create(data, {
    ucpAgent,
    idempotencyKey
  });

  return c.json(checkoutSession, 201);
});
```

Using standard Hono middleware ensures that all inputs are sanitized and validated against schemas defined in the UCP specifications.
