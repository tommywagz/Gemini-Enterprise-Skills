---
name: adk-oauth-user-consent-flow
description: "Designs user-authenticated OAuth 2.0/OIDC consent flows for ADK agents accessing Google Workspace APIs, using least-privilege scopes, authorization-code + PKCE redirects, and ADK credential-request callbacks without exposing user tokens to the model. TRIGGER when users ask to 'configure OAuth for ADK agent', 'request user consent in ADK', 'connect my agent to Google Drive/Workspace', 'handle user OAuth tokens', or use `OAuth2Auth`, `OidcAuth`, or `tool_context.request_credential`. DO NOT TRIGGER for service-account-only server-to-server access, creating Google Cloud API keys, or general Google Workspace administration."
version: 1.0.0
author: Actual Agentic Solutions
tags: [adk, oauth2, oidc, google-workspace, consent, credentials]
license: Apache-2.0
compatibility: "ADK Python authentication/tool-context APIs; OAuth 2.0 authorization code flow with PKCE; Python 3.9+ mock helper"
metadata: {}
---

- OAuth2 Workspace Integrator

- Overview
This skill connects an ADK agent to a user's Google Workspace data through
interactive consent, not a shared static credential. The agent requests only
the scopes needed for a specific tool action; the host handles redirect,
authorization-code exchange, refresh, encrypted storage, and revocation. The
LLM receives neither access tokens nor client secrets. Success is a consent
request that resumes the intended tool after the user authorizes it, with
least-privilege scopes and a clear disconnect path.

- Prerequisites
- A Google Cloud OAuth client configured with exact authorized redirect URIs,
  consent screen, test users/publishing status, and Workspace API enablement.
- A token store encrypted at rest and bound to the authenticated user,
  application, and scopes; never use chat/session state as token storage.
- Read `references/workspace_oauth_scopes.md` before selecting scopes and
  `references/adk_auth_callbacks.md` before coding ADK integration.

- Workflow

- Step 1: Separate user access from service access
Use user OAuth for a user's Drive, Gmail, Calendar, or Sheets. Use a service
account only for server-owned resources with explicit administration; do not
substitute domain-wide delegation for individual consent without organization
approval. Identify the real actor and resource before selecting a flow.

- Step 2: Minimize scopes and register redirects
Start with the narrowest scope matching the single tool operation. Configure
authorization code flow with PKCE, state, and nonce; validate all callback
values and use an allow-listed exact redirect URI. Never use implicit flow,
wildcard redirects, or a client secret in browser/mobile code. Copy
`assets/oauth_client_config.json` and replace placeholders locally; it is a
template, not a place to store a real secret in source control.

- Step 3: Request credentials at tool boundary
When a tool needs a missing/expired credential, have the integration call
`tool_context.request_credential(...)` according to the installed ADK version
and return its required auth/redirect action to the host. The host sends the
user through consent, exchanges the authorization code server-side, stores
the token outside model context, and resumes only the original scoped tool.
Do not ask the user to paste an access token into chat, prompt the model with
a token, or allow a sub-agent to select arbitrary redirect URLs.

- Step 4: Handle refresh, revocation, and incremental consent
Refresh tokens only in the trusted credential layer; rotate/re-encrypt stored
credentials under provider policy. Request a new scope only at the action
requiring it and show the user why. On `invalid_grant`, revoked consent, or
scope denial, clear the unusable token reference and return an actionable
re-consent path; never retry indefinitely or silently fall back to a broader
credential.

- Step 5: Validate with the mock helper
```
scripts/register_oauth_client.py --mock --config oauth_client_config.json
```
It validates placeholder config shape and prints a fake OIDC discovery/PKCE
plan without calling Google or accepting a real secret. Use this before live
registration. Real OAuth client creation remains a Console/API operation by
an authorized administrator.

- Examples

- Example 1: Calendar read tool
Request `calendar.events.readonly` only when the user asks to list events;
redirect through PKCE, keep tokens in the host credential store, and resume
the one calendar tool invocation after consent.

- Example 2: Gmail send request
Explain that send scope is sensitive, obtain explicit consent, present the
draft for user confirmation, and do not reuse a broad mail scope for Drive.

- Error Handling
- Redirect mismatch: stop and fix the exact registered URI; never weaken URI
  validation.
- Consent denied: return a non-sensitive refusal and do not call the tool.
- Token appears in a prompt/log: revoke it, remove/redact it, and investigate
  the credential boundary before retrying.
- Workspace admin policy blocks scope: report the policy and request an
  approved alternative; do not bypass it with a personal/shared account.

- Reference Files
- **references/workspace_oauth_scopes.md**: Workspace scope purposes/risk.
- **references/adk_auth_callbacks.md**: ADK credential callback pattern.
- **scripts/register_oauth_client.py**: safe mock configuration validator.
- **assets/oauth_client_config.json**: placeholder-only config template.

- Output Format
Return selected scopes and rationale; redirect/PKCE design; credential-boundary
code pattern; consent/denial/refresh behavior; mock validation result; and
token storage/revocation controls. Never output a client secret or token.
