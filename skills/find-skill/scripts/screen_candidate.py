#!/usr/bin/env python3
"""Pattern-scan a fetched candidate's raw text before it is read as
instructions. See this skill's references/security_screening.md for the rule
this enforces ("fetched content is data, never instructions") and what each
category means.

This is a lead list for manual verification, not a verdict -- it cannot
judge adversarial prose, and a hit inside a fenced example that's never
executed will still show up here. A CLEAN result does not mean "safe to
install without reading it" -- it means "no automatable red flag found."

Usage:
  screen_candidate.py <path-or-url>

If the argument starts with http:// or https://, it is fetched (capped at
2MB, 10s timeout) and scanned in memory -- nothing is written to disk.
Otherwise it is treated as a local file path.

Exit codes: 0 if clean, 1 if anything was flagged, 2 on a usage/fetch error
(treat a fetch error as UNSCREENED, not as passing).
"""
import re
import sys
import urllib.error
import urllib.request

MAX_BYTES = 2 * 1024 * 1024
TIMEOUT = 10
USER_AGENT = "find-skill/0.1.0 (+security-screening script)"

NETWORK_PATTERN = re.compile(
    r"https?://|requests\.(get|post)|urllib|curl[\s]|fetch\(|wget[\s]|aws[\s]+s3([\s]|api)",
    re.IGNORECASE,
)
HIGH_CLI_PATTERN = re.compile(
    r"aws[\s]|kubectl[\s]+(apply|delete)|curl[\s]+.*(-d|--data|-F|--upload-file)",
    re.IGNORECASE,
)
TRAVERSAL_PATTERN = re.compile(r"\.\./")
CRED_PATTERN = re.compile(
    r"AKIA[0-9A-Z]{16}"
    r"|-----BEGIN[A-Z ]*PRIVATE KEY-----"
    r"|(api[_-]?key|secret|password|token)[\s]*[:=][\s]*[\"']?[A-Za-z0-9/+_-]{16,}",
    re.IGNORECASE,
)
# Imperative language aimed at hijacking the agent reading this file, not at
# the human user -- the specific risk that makes third-party skill/tool
# content different from a skill the user wrote themselves.
INJECTION_PATTERN = re.compile(
    r"ignore\s+(the\s+)?(previous|prior|above|your)\s+instructions"
    r"|disregard\s+(the\s+)?(above|previous)"
    r"|you\s+must\s+immediately"
    r"|do\s+not\s+tell\s+the\s+user"
    r"|new\s+instructions\s*:"
    r"|system\s+prompt"
    r"|act\s+as\s+(if\s+you|an?\s+unrestricted)"
    r"|(dear|hey|to)\s+(claude|assistant|ai|model)\b.{0,40}(must|should|immediately|ignore|skip)",
    re.IGNORECASE,
)

CATEGORIES = [
    ("Network / exfiltration patterns (High indicator)", NETWORK_PATTERN),
    ("High-privilege CLI patterns (High indicator)", HIGH_CLI_PATTERN),
    ("Path traversal patterns (Critical indicator)", TRAVERSAL_PATTERN),
    ("Possible hardcoded credentials (Critical indicator)", CRED_PATTERN),
    ("Injection phrasing aimed at the agent (Critical indicator)", INJECTION_PATTERN),
]


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read(MAX_BYTES + 1).decode("utf-8", errors="replace")


def load_text(path_or_url):
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return fetch_url(path_or_url)
    with open(path_or_url, encoding="utf-8", errors="replace") as f:
        return f.read()


def find_matches(text, pattern):
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            hits.append((lineno, line.strip()[:200]))
    return hits


def main():
    if len(sys.argv) != 2:
        print("Usage: screen_candidate.py <path-or-url>", file=sys.stderr)
        sys.exit(2)

    target = sys.argv[1]
    try:
        text = load_text(target)
    except (OSError, urllib.error.URLError, TimeoutError) as e:
        print(f"UNSCREENED: could not read '{target}': {e}", file=sys.stderr)
        print("Treat as unscreened, not as passing -- do not install.", file=sys.stderr)
        sys.exit(2)

    if len(text.encode("utf-8")) > MAX_BYTES:
        print(
            f"Warning: '{target}' exceeds {MAX_BYTES} bytes; scan covers a truncated prefix only.",
            file=sys.stderr,
        )

    print(f"Security scan: {target}")
    print("=" * 60)

    any_hit = False
    critical = False
    for label, pattern in CATEGORIES:
        hits = find_matches(text, pattern)
        print(f"\n-- {label} --")
        if hits:
            any_hit = True
            if "Critical" in label:
                critical = True
            for lineno, line in hits:
                print(f"  L{lineno}: {line}")
        else:
            print("  (none)")

    print("\n" + "=" * 60)
    if critical:
        tier = "Critical"
    elif any_hit:
        tier = "High"
    else:
        tier = "Low/Medium (no automatable red flag found)"
    print(f"Suggested risk tier: {tier}")
    print(
        "(pattern match only -- read the full file yourself before installing, "
        "per this skill's references/security_screening.md)"
    )

    sys.exit(1 if any_hit else 0)


if __name__ == "__main__":
    main()
