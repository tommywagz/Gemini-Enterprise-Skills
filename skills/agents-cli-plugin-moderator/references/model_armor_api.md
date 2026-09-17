# Google Cloud Model Armor REST API Reference

## Contents
- Endpoints and service hosts
- Methods: sanitizeUserPrompt / sanitizeModelResponse
- Template resource path
- Request schemas
- Response schema: SanitizationResult
- Confidence levels and filter categories
- Enforcement types
- IAM

Source: Google Cloud Model Armor documentation (`docs.cloud.google.com/model-armor/...`,
fetched 2026-09-16). Note the live docs host has **no** `/docs/` path segment —
`cloud.google.com/model-armor/docs/...` 404s; use `docs.cloud.google.com/model-armor/...`.

## Endpoints and service hosts

| Purpose | Host |
|---|---|
| Template CRUD, floor settings | `https://modelarmor.googleapis.com` (global) |
| `sanitizeUserPrompt` / `sanitizeModelResponse` | `https://modelarmor.{LOCATION}.rep.googleapis.com` (**regional required**) |

Calling a sanitize method against the global host instead of the regional
`.rep.googleapis.com` host fails outright — this is a common integration
mistake. OAuth scope: `https://www.googleapis.com/auth/cloud-platform`.

## Methods

Both live under `projects.locations.templates`:

| Method | HTTP | Path |
|---|---|---|
| `sanitizeUserPrompt` | `POST` | `.../v1/projects/{PROJECT_ID}/locations/{LOCATION}/templates/{TEMPLATE_ID}:sanitizeUserPrompt` |
| `sanitizeModelResponse` | `POST` | `.../v1/{name=projects/*/locations/*/templates/*}:sanitizeModelResponse` |

## Template resource path

```
projects/{PROJECT_ID}/locations/{LOCATION}/templates/{TEMPLATE_ID}
```

Best practice: maintain **two separate templates** — one for
`sanitizeUserPrompt` tuned for prompt injection/jailbreak and malicious
uploads, one for `sanitizeModelResponse` tuned for PII/SDP leakage, off-brand
content, and malicious URLs. Sharing one template across both defeats
independent threshold tuning and traceability.

## Request schemas

`sanitizeUserPrompt`:
```json
{ "userPromptData": { "text": "TEST_PROMPT" } }
```
- `userPromptData`: a `DataItem`. `.text` (string) for plain text, or
  `.byteItem = { "byteDataType": "IMAGE", "byteData": "<base64>" }` for
  image screening (preview; JPEG/PNG/BMP only, <=4MB, one image/request).
- Optional: `multiLanguageDetectionMetadata`, `enableMultiLanguageDetection`
  (bool), `streamingMode` (enum, for the streaming variant).
- **Only include the latest user turn** — never concatenate conversation
  history or include the system prompt; history dilutes the injection
  signal and inflates token cost.

`sanitizeModelResponse`:
```json
{
  "modelResponseData": { "text": "..." },
  "userPrompt": "string",
  "multiLanguageDetectionMetadata": { "...": "..." },
  "streamingMode": "..."
}
```
`modelResponseData` is required; `userPrompt` (the originating user prompt)
is optional context that can improve topicality/off-brand detection.

## Response schema: `SanitizationResult`

Both methods return:
```json
{ "sanitizationResult": { /* SanitizationResult, below */ } }
```

```json
{
  "filterMatchState": "MATCH_FOUND | NO_MATCH_FOUND | FILTER_MATCH_STATE_UNSPECIFIED",
  "filterResults": {
    "csam": { "csamFilterFilterResult": { "executionState": "...", "matchState": "..." } },
    "malicious_uris": { "maliciousUriFilterResult": {
        "executionState": "...", "matchState": "...", "maliciousUriMatchedItems": [ "..." ] } },
    "rai": { "raiFilterResult": {
        "executionState": "...", "matchState": "...",
        "raiFilterTypeResults": {
          "sexually_explicit": {"matchState": "..."},
          "hate_speech": {"matchState": "..."},
          "harassment": {"matchState": "..."},
          "dangerous": {"matchState": "..."},
          "violence": {"matchState": "..."},
          "sexually_suggestive": {"matchState": "..."}
        } } },
    "pi_and_jailbreak": { "piAndJailbreakFilterResult": {
        "executionState": "...", "matchState": "...", "confidenceLevel": "..." } },
    "sdp": { "sdpFilterResult": {
        "inspectResult": { "executionState": "...", "matchState": "...",
          "findings": [ {"infoType": "...", "likelihood": "...", "location": {"...": "..."}} ] }
        /* or deidentifyResult / redactResult, depending on SDP mode */
    } },
    "virusScanFilterResult": { "executionState": "...", "matchState": "...",
      "scannedContentType": "...", "virusDetails": [ "..." ] }
  },
  "invocationResult": "SUCCESS | PARTIAL | FAILURE | INVOCATION_RESULT_UNSPECIFIED",
  "sanitizationMetadata": { "errorCode": "...", "errorMessage": "...", "filterVersionConfig": {} }
}
```

### How to read a verdict, in order of granularity

1. **Top-level gate**: `filterMatchState == "MATCH_FOUND"` -> at least one
   configured filter was violated -> BLOCK signal. `"NO_MATCH_FOUND"` -> ALLOW.
2. **Per-filter**: iterate `filterResults` keys (`csam`, `malicious_uris`,
   `rai`, `pi_and_jailbreak`, `sdp`); each nested `*FilterResult.matchState`
   is the same enum — use it to distinguish *why* (e.g. "RAI dangerous
   content" vs "SDP found a credit card").
3. **Execution health (separate axis from the verdict)**:
   `filterResults.*.executionState` is `EXECUTION_SUCCESS` or
   `EXECUTION_SKIPPED` per filter. `sanitizationResult.invocationResult` is
   the aggregate: `SUCCESS` (all filters ran), `PARTIAL` (some
   skipped/failed), `FAILURE` (all skipped/failed). Treat `FAILURE` as a
   **fail-open vs. fail-closed policy decision**, not as an implicit
   `NO_MATCH_FOUND` pass.
4. **SDP specifics**: `sdpFilterResult.inspectResult.findings[].infoType` +
   `.likelihood` (`VERY_UNLIKELY`..`VERY_LIKELY`) gives the exact PII
   category and confidence — use this for a dedicated exfiltration
   log/alert path distinct from generic content-safety blocks.

## Confidence levels (prompt injection/jailbreak + responsible-AI filters only)

| Level | Detection probability | False-positive risk | Recommended use |
|---|---|---|---|
| `HIGH` | Only near-certain violations | Very low | Production, uninterrupted UX priority |
| `MEDIUM_AND_ABOVE` | Balanced | Moderate | Standard enterprise default |
| `LOW_AND_ABOVE` | Any indication | High | Use cautiously; only for prompt-injection/jailbreak where missing a true positive is worse than a false positive |

Sensitive Data Protection (SDP) confidence works differently (`likelihood`
per finding, not a single template-level threshold) — see the SDP specifics
note above.

## Enforcement types

| Mode | Behavior |
|---|---|
| `Inspect only` | Logs the verdict to Cloud Logging; does not stop the request/response. Requires Cloud Logging enabled to be useful. Use to baseline false-positive rate before blocking. |
| `Inspect and block` | Actively denies on a `MATCH_FOUND` verdict. The calling application/plugin (the Policy Enforcement Point) is responsible for actually stopping the request — Model Armor only returns the verdict. |

Best practice: **start every new integration in `Inspect only`**, then
switch to `Inspect and block` once thresholds are validated against real
traffic.

## IAM

- Predefined roles: `roles/modelarmor.user` (call sanitize methods),
  `roles/modelarmor.viewer` (view templates).
- Confirmed permission: `modelarmor.templates.useToSanitizeModelResponse`
  (required for `sanitizeModelResponse`). The symmetric
  `sanitizeUserPrompt` permission was not independently verified in the
  fetched docs — confirm the exact string in the IAM console before citing
  it verbatim in a compliance document.
