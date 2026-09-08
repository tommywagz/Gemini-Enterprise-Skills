#!/usr/bin/env python3
"""Extract a host repository's real quality gates.

Scans a repo root for formatter/linter/type-checker configs, git hook
managers, CONTRIBUTING.md requirements and CI workflow `run:` commands, then
reconciles them into an ordered gate list with pinned tool versions.

The CI workflow is treated as the source of truth; config files are evidence.
Three conflict classes are reported:

  config_not_in_ci     a config file no CI job invokes (advisory only)
  ci_not_in_config     CI runs a tool with no config file (defaults apply)
  competing_formatters two formatters that will fight over the same files

Usage:
  extract_repo_rules.py <repo-root> [--json] [--target PATH]

Exit codes: 0 = scan completed, 2 = usage/path error.

Pure stdlib. YAML is parsed with a deliberately small line-oriented reader
(see _scan_workflow_text) so the script has no third-party dependency; it
extracts `run:` blocks and pinned versions, which is all Steps 1-2 need.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# --- Tool knowledge ----------------------------------------------------------
# config filenames -> tool name. A tool may have several possible configs.
CONFIG_FILES: dict[str, tuple[str, ...]] = {
    "eslint": (".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json",
               ".eslintrc.yml", ".eslintrc.yaml", "eslint.config.js",
               "eslint.config.mjs", "eslint.config.ts"),
    "prettier": (".prettierrc", ".prettierrc.json", ".prettierrc.yml",
                 ".prettierrc.yaml", ".prettierrc.js", "prettier.config.js"),
    "biome": ("biome.json", "biome.jsonc"),
    "ruff": ("ruff.toml", ".ruff.toml"),
    "black": (),          # configured only via pyproject
    "isort": (".isort.cfg",),
    "mypy": ("mypy.ini", ".mypy.ini"),
    "pyright": ("pyrightconfig.json",),
    "flake8": (".flake8", "setup.cfg"),
    "pylint": (".pylintrc", "pylintrc"),
    "typescript": ("tsconfig.json",),
    "golangci-lint": (".golangci.yml", ".golangci.yaml", ".golangci.toml"),
    "rustfmt": ("rustfmt.toml", ".rustfmt.toml"),
    "clippy": ("clippy.toml", ".clippy.toml"),
    "checkstyle": ("checkstyle.xml",),
    "spotless": (),       # configured in build.gradle / pom.xml
}

# Tools whose config lives inside a shared manifest, keyed by TOML/INI section.
PYPROJECT_SECTIONS = {
    "ruff": "[tool.ruff",
    "black": "[tool.black",
    "isort": "[tool.isort",
    "mypy": "[tool.mypy",
    "pytest": "[tool.pytest",
    "pyright": "[tool.pyright",
}

# Formatters that will fight if both are active on the same files.
COMPETING_FORMATTERS = [
    ({"prettier", "biome"}, "Prettier and Biome both format JS/TS"),
    ({"black", "ruff-format"}, "Black and `ruff format` both format Python"),
    ({"gofmt", "gofumpt"}, "gofmt and gofumpt disagree on some rewrites"),
    ({"rustfmt", "prettier"}, "only if Prettier is configured for .rs files"),
]

# Tool invocation patterns, matched against CI `run:` command text.
TOOL_PATTERNS: dict[str, re.Pattern[str]] = {
    "eslint": re.compile(r"\beslint\b"),
    "prettier": re.compile(r"\bprettier\b"),
    "biome": re.compile(r"\bbiome\b"),
    "ruff-format": re.compile(r"\bruff\s+format\b"),
    "ruff": re.compile(r"\bruff\b(?!\s+format)"),
    "black": re.compile(r"\bblack\b"),
    "isort": re.compile(r"\bisort\b"),
    "mypy": re.compile(r"\bmypy\b"),
    "pyright": re.compile(r"\bpyright\b"),
    "flake8": re.compile(r"\bflake8\b"),
    "pylint": re.compile(r"\bpylint\b"),
    "typescript": re.compile(r"\btsc\b"),
    "pytest": re.compile(r"\bpytest\b"),
    "jest": re.compile(r"\bjest\b"),
    "vitest": re.compile(r"\bvitest\b"),
    "node-test": re.compile(r"\bnode\s+--test\b"),
    "next-build": re.compile(r"\bnext\s+build\b"),
    "vite-build": re.compile(r"\bvite\s+build\b"),
    "golangci-lint": re.compile(r"\bgolangci-lint\b"),
    "gofmt": re.compile(r"\bgofmt\b"),
    "gofumpt": re.compile(r"\bgofumpt\b"),
    "go-test": re.compile(r"\bgo\s+test\b"),
    "cargo-fmt": re.compile(r"\bcargo\s+fmt\b"),
    "clippy": re.compile(r"\bcargo\s+clippy\b"),
    "cargo-test": re.compile(r"\bcargo\s+test\b"),
    "checkstyle": re.compile(r"\bcheckstyle\b"),
    "spotless": re.compile(r"\bspotless\w*\b"),
    "pre-commit": re.compile(r"\bpre-commit\b"),
}

HOOK_MANAGERS = {
    "pre-commit": ".pre-commit-config.yaml",
    "husky": ".husky",
    "lefthook": "lefthook.yml",
}

# Dependency installation is not a quality gate. Without this filter every
# `pip install ... pytest` line is misreported as a test gate.
INSTALL_NOISE = re.compile(
    r"^\s*(?:sudo\s+)?(?:"
    r"pip3?\s+install|python3?\s+-m\s+pip\s+install|uv\s+(?:pip\s+)?(?:install|sync)|"
    r"npm\s+(?:ci|install|i)\b|pnpm\s+(?:install|i)\b|yarn\s+(?:install)?\s*$|"
    r"poetry\s+install|apt-get|brew\s+install|go\s+install|cargo\s+install|"
    r"gem\s+install|curl\b|wget\b|actions/"
    r")",
    re.I,
)

# CI usually calls gates through a script alias rather than the tool directly.
# `npm run lint` must be resolved to what `lint` actually runs.
# Anchored to command position (start of line, or after a shell separator) so
# prose like `echo "npm publishes failed"` is not mistaken for an invocation.
SCRIPT_ALIAS = re.compile(
    r"(?:^|[;&|]|&&|\|\|)\s*(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?([a-zA-Z][\w:-]*)",
)
# `npm test` / `yarn test` are implicit aliases for the `test` script.
IMPLICIT_ALIASES = {"test", "start", "build", "lint", "format", "typecheck"}
# Package-manager subcommands that are never a script alias. Without this,
# `npm publish` and `npm pack` get reported as unresolvable gates.
PM_SUBCOMMANDS = {
    "publish", "pack", "version", "ci", "install", "i", "add", "remove",
    "audit", "exec", "dlx", "link", "login", "whoami", "config", "cache",
    "view", "info", "outdated", "update", "dedupe", "prune", "init", "create",
}

CI_GLOBS = (
    (".github/workflows", ("*.yml", "*.yaml")),
    (".", (".gitlab-ci.yml",)),
    (".circleci", ("config.yml",)),
)

# CONTRIBUTING.md requirements worth surfacing; a script cannot verify these.
CONTRIB_SIGNALS = {
    "conventional_commits": re.compile(
        r"conventional\s+commit|feat\(|fix\(|<type>\(<scope>\)", re.I),
    "dco_signoff": re.compile(r"signed-off-by|\bDCO\b|--signoff", re.I),
    "changelog_entry": re.compile(r"changelog|CHANGELOG\.md", re.I),
    "coverage_threshold": re.compile(r"coverage\s*(?:of|at|>=|:)?\s*\d{2,3}\s*%", re.I),
    "squash_required": re.compile(r"squash\s+(?:your\s+)?commits", re.I),
    "issue_before_pr": re.compile(r"open\s+an?\s+issue\s+(?:first|before)", re.I),
    "no_external_prs": re.compile(r"not\s+accepting\s+external\s+(?:pull\s+requests|contributions)", re.I),
}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _scan_workflow_text(text: str) -> tuple[list[str], dict[str, str]]:
    """Pull `run:` command lines and pinned versions out of a CI YAML file.

    Returns (commands, versions). Handles both inline `run: cmd` and block
    scalars (`run: |`), which is where multi-gate jobs actually live.
    """
    commands: list[str] = []
    versions: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        m = re.match(r"-?\s*run:\s*([|>][-+]?)?\s*(.*)$", stripped)
        if m:
            block, inline = m.group(1), m.group(2).strip()
            if block:  # block scalar: consume the more-indented lines below
                base = len(line) - len(line.lstrip())
                i += 1
                pending = ""
                while i < len(lines):
                    nxt = lines[i]
                    if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= base:
                        break
                    body = nxt.strip()
                    if body:
                        # Join `\` continuations, or a multi-line `pip install`
                        # loses its prefix and reads as a bare tool list.
                        if body.endswith("\\"):
                            pending += body[:-1].rstrip() + " "
                        else:
                            commands.append((pending + body).strip())
                            pending = ""
                    i += 1
                if pending:
                    commands.append(pending.strip())
                continue
            if inline:
                commands.append(inline)

        # Version pins: `node-version: 20`, `version: 0.6.9`, `uses: x@v1.2.3`
        vm = re.match(r"-?\s*([a-z-]*version):\s*['\"]?([^'\"\s]+)['\"]?\s*$", stripped)
        if vm:
            versions[vm.group(1)] = vm.group(2)
        um = re.match(r"-?\s*uses:\s*([^@\s]+)@([^\s]+)", stripped)
        if um:
            versions[f"uses:{um.group(1)}"] = um.group(2)
        i += 1
    return commands, versions


def load_script_aliases(root: Path) -> dict[str, str]:
    """Map script-alias name -> the command it actually runs.

    Sources: package.json `scripts`, and Makefile targets (best effort). CI
    almost never names the linter directly, so without this the gate list of a
    typical JS/TS repo comes back empty.
    """
    aliases: dict[str, str] = {}

    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(_read(pkg) or "{}")
        except json.JSONDecodeError:
            data = {}
        for name, cmd in (data.get("scripts") or {}).items():
            if isinstance(cmd, str):
                aliases[name] = cmd

    makefile = next((root / n for n in ("Makefile", "makefile") if (root / n).exists()), None)
    if makefile:
        current: str | None = None
        for line in _read(makefile).splitlines():
            tm = re.match(r"^([a-zA-Z][\w.-]*)\s*:(?!=)", line)
            if tm:
                current = tm.group(1)
                continue
            if current and line.startswith("\t"):
                body = line.lstrip("\t").lstrip("@-").strip()
                if body and current not in aliases:
                    aliases[current] = body
                current = None
    return aliases


def resolve_command(cmd: str, aliases: dict[str, str], depth: int = 0) -> list[str]:
    """Expand a CI command into itself plus any script aliases it invokes.

    Recurses one level deeper than the obvious case so that
    `npm run ci` -> `npm run lint && npm run test` -> `eslint .` resolves.
    """
    resolved = [cmd]
    if depth >= 3:
        return resolved
    for m in SCRIPT_ALIAS.finditer(cmd):
        name = m.group(1)
        if name in PM_SUBCOMMANDS:
            continue
        # `npm test` has no `run`, so the captured token may be the script.
        if name not in aliases and name in IMPLICIT_ALIASES:
            continue
        target = aliases.get(name)
        if target:
            resolved.extend(resolve_command(target, aliases, depth + 1))
    for part in re.split(r"&&|\|\||;", cmd):
        part = part.strip()
        if part and part != cmd and part in aliases:
            resolved.extend(resolve_command(aliases[part], aliases, depth + 1))
    return resolved


def _find_ci_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for subdir, patterns in CI_GLOBS:
        base = root / subdir
        if not base.is_dir():
            continue
        for pattern in patterns:
            found.extend(sorted(p for p in base.glob(pattern) if p.is_file()))
    return found


def detect_configs(root: Path) -> dict[str, list[str]]:
    """Map tool -> the config files present for it."""
    configs: dict[str, list[str]] = {}
    for tool, names in CONFIG_FILES.items():
        for name in names:
            path = root / name
            if path.exists():
                # setup.cfg only counts for flake8 if it declares the section
                if name == "setup.cfg" and "[flake8]" not in _read(path):
                    continue
                configs.setdefault(tool, []).append(name)

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = _read(pyproject)
        for tool, section in PYPROJECT_SECTIONS.items():
            if section in text:
                configs.setdefault(tool, []).append("pyproject.toml")
    return configs


def detect_hooks(root: Path) -> dict[str, str]:
    return {
        name: rel for name, rel in HOOK_MANAGERS.items()
        if (root / rel).exists()
    }


def extract_pinned_versions(root: Path, hooks: dict[str, str]) -> dict[str, dict[str, str]]:
    """Collect version pins with their source, most authoritative first."""
    pins: dict[str, dict[str, str]] = {}

    # 1. Lockfiles are the strongest signal that a resolution actually happened.
    for lock in ("package-lock.json", "uv.lock", "poetry.lock", "Cargo.lock",
                 "go.sum", "pnpm-lock.yaml", "yarn.lock"):
        if (root / lock).exists():
            pins.setdefault("_lockfiles", {})[lock] = "present"

    # 2. pre-commit `rev:` pins are exact and easy to read.
    pc = root / hooks.get("pre-commit", ".pre-commit-config.yaml")
    if pc.exists():
        text = _read(pc)
        repo_url = None
        for line in text.splitlines():
            s = line.strip()
            rm = re.match(r"-?\s*repo:\s*(\S+)", s)
            if rm:
                repo_url = rm.group(1).rstrip("/").split("/")[-1]
            vm = re.match(r"rev:\s*['\"]?([^'\"\s]+)", s)
            if vm and repo_url:
                pins.setdefault("pre_commit_rev", {})[repo_url] = vm.group(1)

    # 3. Manifest ranges are the weakest — a range is not a resolved version.
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(_read(pkg) or "{}")
        except json.JSONDecodeError:
            data = {}
        deps = {**data.get("devDependencies", {}), **data.get("dependencies", {})}
        for name, spec in deps.items():
            if any(t in name for t in ("eslint", "prettier", "biome", "typescript",
                                       "jest", "vitest")):
                pins.setdefault("manifest_range", {})[name] = spec
    return pins


def parse_contributing(root: Path) -> dict[str, Any]:
    for name in ("CONTRIBUTING.md", "CONTRIBUTING.rst", ".github/CONTRIBUTING.md"):
        path = root / name
        if path.exists():
            text = _read(path)
            return {
                "file": name,
                "signals": sorted(k for k, rx in CONTRIB_SIGNALS.items() if rx.search(text)),
            }
    return {"file": None, "signals": []}


def parse_ci(root: Path, aliases: dict[str, str]) -> dict[str, Any]:
    gates: list[dict[str, Any]] = []
    versions: dict[str, str] = {}
    unresolved: list[str] = []
    unmatched: list[str] = []

    for path in _find_ci_files(root):
        text = _read(path)
        commands, file_versions = _scan_workflow_text(text)
        versions.update(file_versions)

        # A job that only `uses:` an external action hides its gates elsewhere.
        if not commands and re.search(r"^\s*-?\s*uses:", text, re.M):
            for m in re.finditer(r"uses:\s*([^\s@]+@[^\s]+)", text):
                ref = m.group(1)
                if not ref.startswith("actions/"):
                    unresolved.append(f"{path.name}:{ref}")

        for cmd in commands:
            if INSTALL_NOISE.match(cmd):
                continue
            expansion = resolve_command(cmd, aliases)
            matched = sorted({
                t for text_ in expansion
                for t, rx in TOOL_PATTERNS.items() if rx.search(text_)
            })
            if matched:
                gate: dict[str, Any] = {
                    "file": str(path.relative_to(root)),
                    "command": cmd,
                    "tools": matched,
                }
                if len(expansion) > 1:
                    gate["resolved_via_alias"] = expansion[1:]
                gates.append(gate)
            else:
                alias_hit = SCRIPT_ALIAS.search(cmd)
                if alias_hit and alias_hit.group(1) not in PM_SUBCOMMANDS:
                    # An alias CI runs that we could not expand — a real blind
                    # spot, not silence. Surfaced so the report can flag it.
                    unmatched.append(f"{path.name}: {cmd}")

    return {
        "gates": gates,
        "versions": versions,
        "unresolved_external": sorted(set(unresolved)),
        "unresolved_aliases": sorted(set(unmatched)),
    }


def reconcile(configs: dict[str, list[str]], ci: dict[str, Any]) -> dict[str, Any]:
    """Produce the three conflict classes the SKILL.md workflow acts on."""
    ci_tools = {t for gate in ci["gates"] for t in gate["tools"]}
    config_tools = set(configs)

    # `ruff format` and `ruff` share one config file.
    if "ruff" in config_tools and "ruff-format" in ci_tools:
        config_tools.add("ruff-format")

    competing = []
    active = ci_tools | config_tools
    for pair, why in COMPETING_FORMATTERS:
        if pair <= active:
            competing.append({
                "tools": sorted(pair),
                "reason": why,
                "resolution": "keep whichever CI invokes; disable the other for the target path",
            })

    return {
        "config_not_in_ci": sorted(config_tools - ci_tools),
        "ci_not_in_config": sorted(ci_tools - config_tools),
        "competing_formatters": competing,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Extract a host repo's real quality gates.")
    ap.add_argument("repo_root", help="path to the host repository root")
    ap.add_argument("--json", action="store_true", help="emit JSON (default: text)")
    ap.add_argument("--target", help="target path being audited (recorded, not scanned)")
    args = ap.parse_args()

    root = Path(args.repo_root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    if not (root / ".git").exists():
        print(f"warning: {root} has no .git — is this the repo root?", file=sys.stderr)

    configs = detect_configs(root)
    hooks = detect_hooks(root)
    aliases = load_script_aliases(root)
    ci = parse_ci(root, aliases)
    report = {
        "repo_root": str(root),
        "target": args.target,
        "configs": configs,
        "hook_managers": hooks,
        "script_aliases": aliases,
        "contributing": parse_contributing(root),
        "ci_gates": ci["gates"],
        "ci_gate_count": len(ci["gates"]),
        "tool_versions": {
            "from_ci": ci["versions"],
            **extract_pinned_versions(root, hooks),
        },
        "unresolved_external_actions": ci["unresolved_external"],
        "unresolved_aliases": ci["unresolved_aliases"],
        "conflicts": reconcile(configs, ci),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"host repo: {root}")
    print(f"configs:   {', '.join(sorted(configs)) or 'none found'}")
    print(f"hooks:     {', '.join(sorted(hooks)) or 'none found'}")
    print(f"CI gates:  {len(ci['gates'])}")
    for gate in ci["gates"]:
        via = " (via alias)" if gate.get("resolved_via_alias") else ""
        print(f"  [{'+'.join(gate['tools'])}] {gate['command'][:76]}{via}")
    if ci["unresolved_aliases"]:
        print("\nunresolved aliases (CI runs these, tool unknown):")
        for entry in ci["unresolved_aliases"]:
            print(f"  {entry[:88]}")
    conflicts = report["conflicts"]
    if conflicts["config_not_in_ci"]:
        print(f"\nconfig_not_in_ci (advisory only): {', '.join(conflicts['config_not_in_ci'])}")
    if conflicts["ci_not_in_config"]:
        print(f"ci_not_in_config (tool defaults apply): {', '.join(conflicts['ci_not_in_config'])}")
    for c in conflicts["competing_formatters"]:
        print(f"competing_formatters: {' vs '.join(c['tools'])} — {c['reason']}")
    if report["unresolved_external_actions"]:
        print(f"UNRESOLVED_EXTERNAL: {', '.join(report['unresolved_external_actions'])}")
    if report["contributing"]["signals"]:
        print(f"\nCONTRIBUTING signals: {', '.join(report['contributing']['signals'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
