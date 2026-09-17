# ADK Credential Callback Pattern

Use ADK's tool context credential request at the point a tool actually needs
access. In Python, tool functions receive a `tool_context`; call the installed
ADK version's `tool_context.request_credential(...)` with a developer-owned
auth configuration and requested scopes. The returned credential/auth action
is handled by the trusted host, which drives the redirect and later supplies a
credential reference for the same user/tool action.

The exact `request_credential` argument and return types vary by ADK release;
inspect the version-pinned API reference rather than copying an unverified
signature. The invariant is fixed: dynamic redirect URI/state/PKCE validation,
code exchange, refresh, token encryption, and credential lookup happen outside
LLM context. `OidcAuth`/`OAuth2Auth` configuration must use an allow-listed
issuer and exact redirect URI; never let model-produced text select either.
