# Source Allowlist & Trust Tiers

## Contents
- Why source tiering exists
- Tier definitions
- Source-by-source assignment
- Handling sources not on this list

## Why source tiering exists
The instructions this skill is built from say: "Only look through reputable
sources even if some of the ones that I recommended are actually unsafe and
I didn't know." A source being named as a candidate does not make it
reputable. This file applies independent judgment to every named source once,
so that judgment doesn't have to be re-derived — or skipped under time
pressure — on every search.

## Tier definitions

| Tier | Meaning | Automated query in `search_registries.py`? | Install without extra confirmation? |
|---|---|---|---|
| 1 — Official | Run by the protocol/project maintainers or an established vendor with a documented API | Yes | Yes, after Step 4 screening still passes |
| 2 — Community-curated | A maintained aggregator/"awesome list" with a visible contribution process, but individual entries are third-party and unvetted by the aggregator itself | Yes | Yes, after Step 4 screening still passes |
| 3 — Unverified / single-maintainer | No visible moderation process, or a personal repository with no organizational backing | No — manual lookup only, gated behind explicit user opt-in | No — requires explicit user confirmation in Step 3, in addition to Step 4 screening |

## Source-by-source assignment

| Source | Tier | Why |
|---|---|---|
| `registry.modelcontextprotocol.io` | 1 | Official MCP registry. Verified: `GET /v0/servers?search=<query>` returns structured `{"servers":[{"server": {"name","description","repository","remotes"}}]}` JSON — no auth required for read access. |
| `github.com/modelcontextprotocol/servers` | 1 | Official reference-server org under the `modelcontextprotocol` GitHub organization. |
| `composio.dev` / `backend.composio.dev` | 1 | Established commercial vendor with a versioned, authenticated API (`/api/v3/...`; the older `/api/v1/apps` is retired). Still third-party *code* once installed — screen exactly like any other candidate. |
| `github.com/VoltAgent/awesome-agent-skills` | 2 | Actively maintained "awesome list" with a `CONTRIBUTING.md` and visible history. Verified structure: a single `README.md` of `- **[name](url)** - description` entries grouped by publisher, no `SKILL.md` files hosted in-repo. Entries link out (many via `officialskills.sh`) to third-party sources VoltAgent has not itself security-reviewed. |
| `github.com/wong2/awesome-mcp-servers` | 2 | Same pattern as above — community-curated list of `- **[name](url)** - description` entries, each pointing to a third-party server repo. |
| `mcpservers.org` | 3 | Third-party directory site; ownership and moderation process are not verifiable from the site alone. |
| `github.com/hoodini/ai-agents-skills` | 3 | Single-maintainer personal repository, not an official or widely-recognized index. |
| LangChain tool docs (`python.langchain.com`) | N/A | No dynamic search API for this purpose — treat as a documentation lookup via `WebFetch`, not an automated registry query. Any code sample pulled from there is still third-party content and needs Step 4 screening before use. |

## Handling sources not on this list
If the user names a source not in this table, do not default it to Tier 1.
Apply the same test used to build this table:
1. Is it run by the protocol/project maintainers, or an established vendor
   with a documented API? → Tier 1.
2. Is it a maintained aggregator with a visible contribution/moderation
   process? → Tier 2.
3. Anything else — including a source recommended without independent
   verification — defaults to Tier 3 until shown otherwise.
