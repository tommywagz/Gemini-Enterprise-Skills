#!/usr/bin/env python3
"""Render a new Hono/ADK workspace. Python stdlib only; never installs or runs it.

Exit 0: rendered plan or generated workspace; exit 2: invalid input or I/O error.
The bundled schema describes workspace.json; validation here implements the
fixed generator contract, not a general-purpose JSON Schema interpreter.
"""
import argparse
import ast
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TOKEN = re.compile(r"@@([a-z_]+)@@")


def render(text, variables):
    def replace(match):
        key = match.group(1)
        if key not in variables:
            raise ValueError(f"unknown template variable: {key}")
        return str(variables[key])
    return TOKEN.sub(replace, text)


def relative_path(value):
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or "\\" in value
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError(f"unsafe relative path: {value}")
    return path


def plan(variables):
    manifest = json.loads((ASSETS / "scaffold_template_manifest.json").read_text())
    if manifest["manifest_version"] != "1.0.0" or set(manifest["variables"]) != set(variables):
        raise ValueError("unsupported manifest version or variables")
    files = {}
    for entry in manifest["files"]:
        path = str(relative_path(render(entry["path"], variables)))
        if path in files or path == "workspace.json":
            raise ValueError(f"duplicate/reserved output: {path}")
        if ("template" in entry) == ("content" in entry):
            raise ValueError("each entry needs exactly one template or content")
        if "template" in entry:
            source = (ASSETS / relative_path(entry["template"])).resolve()
            source.relative_to(ASSETS.resolve())
            text = source.read_text(encoding="utf-8")
        else:
            text = entry["content"]
        files[path] = render(text, variables)
    descriptor = {
        "schema_version": "1.0.0", **variables,
        "services": {"web": "apps/web", "agents": "apps/agents"},
        "files": sorted([*files, "workspace.json"]),
    }
    files["workspace.json"] = json.dumps(descriptor, indent=2) + "\n"
    for path, text in files.items():
        if path.endswith(".json"):
            json.loads(text)
        elif path.endswith(".py"):
            ast.parse(text, filename=path)
    return descriptor, files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new directory; parent must exist")
    parser.add_argument("--name", required=True, help="lowercase-hyphen workspace name")
    parser.add_argument("--agent-name", default="orchestrator")
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--web-port", type=int, default=3000)
    parser.add_argument("--adk-port", type=int, default=8000)
    parser.add_argument("--dry-run", action="store_true", help="validate and print plan; write nothing")
    args = parser.parse_args(argv)
    created = False
    target = None
    try:
        variables = {key: getattr(args, key) for key in
                     ("name", "agent_name", "model", "web_port", "adk_port")}
        patterns = {"name": (r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", 64),
                    "agent_name": (r"[a-z][a-z0-9_]*", 64),
                    "model": (r"[A-Za-z0-9][A-Za-z0-9._:/-]*", 128)}
        for key, (pattern, limit) in patterns.items():
            if len(variables[key]) > limit or not re.fullmatch(pattern, variables[key]):
                raise ValueError(f"invalid {key}")
        if args.agent_name in {"keyword", "google", "typing", "os", "json", "sys"}:
            raise ValueError("agent_name shadows a Python dependency")
        import keyword
        if keyword.iskeyword(args.agent_name):
            raise ValueError("agent_name must not be a Python keyword")
        if not all(1024 <= variables[key] <= 65535 for key in ("web_port", "adk_port")):
            raise ValueError("ports must be between 1024 and 65535")
        if args.web_port == args.adk_port:
            raise ValueError("web and ADK ports must differ")
        # Reject even dangling destination symlinks; never follow an existing target.
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("output already exists; choose a new directory")
        parent = args.output.parent.resolve(strict=True)
        if not parent.is_dir():
            raise ValueError("output parent must be a directory")
        target = parent / args.output.name
        descriptor, files = plan(variables)
        if not args.dry_run:
            target.mkdir()  # exclusive reservation: no exist_ok, no overwrite mode
            created = True
            for path, text in files.items():
                destination = target / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("x", encoding="utf-8") as stream:
                    stream.write(text)
        print(json.dumps({"mode": "dry-run" if args.dry_run else "generated",
                          "output": str(target), "workspace": descriptor}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        if created:
            shutil.rmtree(target)
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
