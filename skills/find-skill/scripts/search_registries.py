#!/usr/bin/env python3
"""Query external skill/tool/MCP-server indexes for candidates.

Returns METADATA ONLY (name, source, tier, url, one-line description) as
JSON on stdout -- never a candidate's full instructional body. Fetching and
reading a specific candidate's actual content is a separate, later step
(screen_candidate.py), so unscreened third-party text never lands directly
in an agent's context as a side effect of searching.

Sources (see this skill's references/source_allowlist.md for the tier rationale):
  local  VoltAgent/awesome-agent-skills README (Tier 2, community-curated)
  mcp    official MCP registry API (Tier 1), falling back to
         wong2/awesome-mcp-servers README (Tier 2) if the API call fails
  sdk    Composio catalog (Tier 1) -- only queried if COMPOSIO_API_KEY is
         set; LangChain has no dynamic search API, see the reference doc.

Tier 3 sources (mcpservers.org, github.com/hoodini/ai-agents-skills) are
intentionally NOT queried here -- they require manual, user-confirmed
lookup per the source allowlist.

Usage:
  search_registries.py "<query>" [--sources local,mcp,sdk] [--limit N]

Exit codes: 0 on completion (even if individual sources failed -- check the
"errors" key in the output); 1 only for a usage error.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "find-skill/0.1.0 (+registry-search script)"
TIMEOUT = 10

VOLTAGENT_README = (
    "https://raw.githubusercontent.com/VoltAgent/awesome-agent-skills/main/README.md"
)
WONG2_README = (
    "https://raw.githubusercontent.com/wong2/awesome-mcp-servers/main/README.md"
)
MCP_REGISTRY_API = "https://registry.modelcontextprotocol.io/v0/servers"
COMPOSIO_TOOLKITS_API = "https://backend.composio.dev/api/v3/toolkits"

# Matches "- **[Name](url)** - description" list items used by both the
# VoltAgent and wong2 awesome-lists (verified against both READMEs).
AWESOME_LIST_ITEM = re.compile(r"^-\s+\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s+-\s+(.*)$")


def http_get(url, headers=None):
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def matches_query(text, keywords):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def parse_awesome_list(markdown_text, keywords, limit, source, tier):
    results = []
    for line in markdown_text.splitlines():
        m = AWESOME_LIST_ITEM.match(line.strip())
        if not m:
            continue
        name, url, description = m.groups()
        if matches_query(f"{name} {description}", keywords):
            results.append(
                {
                    "name": name,
                    "url": url,
                    "description": description.strip(),
                    "source": source,
                    "tier": tier,
                }
            )
        if len(results) >= limit:
            break
    return results


def search_local_index(keywords, limit):
    try:
        text = http_get(VOLTAGENT_README)
    except (urllib.error.URLError, TimeoutError) as e:
        return [], f"local index (VoltAgent/awesome-agent-skills) unreachable: {e}"
    return (
        parse_awesome_list(
            text, keywords, limit, "VoltAgent/awesome-agent-skills", 2
        ),
        None,
    )


def search_mcp_index(keywords, limit):
    query = " ".join(keywords)
    url = f"{MCP_REGISTRY_API}?{urllib.parse.urlencode({'search': query})}"
    try:
        text = http_get(url)
        data = json.loads(text)
        results = []
        for entry in data.get("servers", []):
            server = entry.get("server", {})
            name = server.get("name", "")
            description = server.get("description", "")
            repo = server.get("repository", {}).get("url", "")
            remotes = server.get("remotes", [])
            candidate_url = repo or (remotes[0]["url"] if remotes else "")
            results.append(
                {
                    "name": name,
                    "url": candidate_url,
                    "description": description,
                    "source": "registry.modelcontextprotocol.io",
                    "tier": 1,
                }
            )
            if len(results) >= limit:
                break
        return results, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        # Fall back to the community-curated MCP list per the allowlist.
        try:
            fallback_text = http_get(WONG2_README)
        except (urllib.error.URLError, TimeoutError) as e2:
            return [], (
                f"MCP registry API failed ({e}) and fallback "
                f"wong2/awesome-mcp-servers also unreachable: {e2}"
            )
        return (
            parse_awesome_list(
                fallback_text, keywords, limit, "wong2/awesome-mcp-servers", 2
            ),
            f"MCP registry API failed ({e}); used wong2/awesome-mcp-servers fallback",
        )


def search_sdk_index(keywords, limit):
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        return [], (
            "COMPOSIO_API_KEY not set -- skipped the Managed SDK Index. "
            "Look up integrations manually at https://composio.dev/tools "
            "and screen any code sample before use."
        )
    query = " ".join(keywords)
    url = f"{COMPOSIO_TOOLKITS_API}?{urllib.parse.urlencode({'search': query})}"
    try:
        text = http_get(url, headers={"x-api-key": api_key})
        data = json.loads(text)
        results = []
        items = data.get("items", data.get("data", []))
        for item in items[:limit]:
            results.append(
                {
                    "name": item.get("name", item.get("slug", "")),
                    "url": item.get("url", f"https://composio.dev/tools/{item.get('slug', '')}"),
                    "description": item.get("description", ""),
                    "source": "composio.dev",
                    "tier": 1,
                }
            )
        return results, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return [], (
            f"Composio API call failed ({e}) -- endpoint or auth scheme may "
            "have changed since this script was written. Check "
            "https://composio.dev/tools manually."
        )


def main():
    args = sys.argv[1:]
    if not args:
        print(
            'Usage: search_registries.py "<query>" [--sources local,mcp,sdk] [--limit N]',
            file=sys.stderr,
        )
        sys.exit(1)

    query = args[0]
    sources = ["local", "mcp", "sdk"]
    limit = 5

    i = 1
    while i < len(args):
        if args[i] == "--sources" and i + 1 < len(args):
            sources = [s.strip() for s in args[i + 1].split(",") if s.strip()]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            print(f"Unrecognized argument: {args[i]}", file=sys.stderr)
            sys.exit(1)

    keywords = query.split()
    all_results = []
    errors = []

    if "local" in sources:
        results, error = search_local_index(keywords, limit)
        all_results.extend(results)
        if error:
            errors.append(error)

    if "mcp" in sources:
        results, error = search_mcp_index(keywords, limit)
        all_results.extend(results)
        if error:
            errors.append(error)

    if "sdk" in sources:
        results, error = search_sdk_index(keywords, limit)
        all_results.extend(results)
        if error:
            errors.append(error)

    print(
        json.dumps(
            {"query": query, "results": all_results, "errors": errors},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
