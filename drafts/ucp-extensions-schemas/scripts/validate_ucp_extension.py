#!/usr/bin/env python3
"""UCP Extension Schema and Manifest Validator.

Validates JSON Schema syntax (Draft 2020-12), date-based versioning (YYYY-MM-DD),
reverse-domain namespace authority binding, and instance payload compliance.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import jsonschema
    from jsonschema.validators import Draft202012Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

DATE_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


def validate_date_version(version: str) -> tuple[bool, str]:
    """Validate ISO 8601 calendar date version YYYY-MM-DD."""
    if not isinstance(version, str) or not DATE_REGEX.match(version):
        return False, f"Version '{version}' is not in valid YYYY-MM-DD format"
    try:
        datetime.date.fromisoformat(version)
    except ValueError as e:
        return False, f"Version '{version}' is an invalid calendar date: {e}"
    return True, "Valid date version"


def extract_authority_prefix(url_str: str) -> tuple[str | None, str]:
    """Parse URL and reverse host labels into authority prefix (e.g. ucp.dev -> dev.ucp)."""
    try:
        parsed = urlparse(url_str)
    except Exception as e:
        return None, f"Failed to parse URL '{url_str}': {e}"

    if parsed.scheme.lower() != "https":
        return None, f"Schema URL must use HTTPS scheme, got '{parsed.scheme}'"

    if parsed.username or parsed.password:
        return None, "Schema URL must not contain user credentials"

    host = parsed.hostname
    if not host:
        return None, "Schema URL does not have a valid hostname"

    labels = host.lower().split(".")
    if len(labels) < 2:
        return None, f"Hostname '{host}' must have at least two domain labels"

    reversed_prefix = ".".join(reversed(labels))
    return reversed_prefix, f"Derived authority prefix: {reversed_prefix}"


def validate_authority_binding(namespace: str, schema_url: str) -> tuple[bool, str]:
    """Verify that namespace leading labels align with reversed schema URL host labels."""
    reversed_prefix, msg = extract_authority_prefix(schema_url)
    if not reversed_prefix:
        return False, msg

    # Allow exact match or hierarchical match (namespace starts with authority_prefix + '.')
    # Also handle standard subdomains where base domain is registered (e.g. schemas.example.com -> com.example)
    if namespace == reversed_prefix or namespace.startswith(reversed_prefix + "."):
        return True, f"Namespace '{namespace}' matches authority '{reversed_prefix}'"

    # Check root domain match (e.g. com.example for schemas.example.com)
    root_prefix_parts = reversed_prefix.split(".")
    # if reversed_prefix is com.example.schemas, root prefix is com.example
    if len(root_prefix_parts) > 2:
        root_prefix = ".".join(root_prefix_parts[:2])
        if namespace == root_prefix or namespace.startswith(root_prefix + "."):
            return True, f"Namespace '{namespace}' matches root authority '{root_prefix}'"

    return False, f"Authority mismatch: namespace '{namespace}' does not align with host authority '{reversed_prefix}'"


def validate_schema_file(path: Path, check_authority: bool = True) -> list[str]:
    """Validate a single UCP extension schema file."""
    errors: list[str] = []
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"{path}: JSON parse error: {e}"]

    if not isinstance(content, dict):
        return [f"{path}: Schema root must be a JSON object"]

    # Check $schema
    schema_dialect = content.get("$schema")
    if not schema_dialect or "json-schema.org" not in schema_dialect:
        errors.append(f"{path}: Missing or invalid $schema dialect header")

    # Check $id
    schema_id = content.get("$id")
    if not schema_id:
        errors.append(f"{path}: Missing $id URI")

    # Check UCP metadata
    ucp_meta = content.get("ucp")
    if not ucp_meta or not isinstance(ucp_meta, dict):
        errors.append(f"{path}: Missing top-level 'ucp' metadata object")
    else:
        version = ucp_meta.get("version")
        ok, msg = validate_date_version(version)
        if not ok:
            errors.append(f"{path}: {msg}")

        namespace = ucp_meta.get("namespace")
        if not namespace or not isinstance(namespace, str):
            errors.append(f"{path}: Missing or invalid ucp.namespace")
        elif check_authority and schema_id:
            ok, msg = validate_authority_binding(namespace, schema_id)
            if not ok:
                errors.append(f"{path}: {msg}")

        extends = ucp_meta.get("extends")
        if not extends or not isinstance(extends, str):
            errors.append(f"{path}: Missing or invalid ucp.extends target")

    # Check JSON Schema validity using jsonschema
    if HAS_JSONSCHEMA:
        try:
            Draft202012Validator.check_schema(content)
        except jsonschema.exceptions.SchemaError as e:
            errors.append(f"{path}: JSON Schema Draft 2020-12 validation error: {e.message}")
        except Exception as e:
            errors.append(f"{path}: Unexpected schema validation error: {e}")

    return errors


def validate_instance_file(schema_path: Path, data_path: Path) -> list[str]:
    """Validate an instance document against the given schema."""
    errors: list[str] = []
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        instance = json.loads(data_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"File read/parse error: {e}"]

    if HAS_JSONSCHEMA:
        try:
            validator = Draft202012Validator(schema)
            for err in sorted(validator.iter_errors(instance), key=lambda e: e.path):
                loc = ".".join(str(p) for p in err.path) or "root"
                errors.append(f"Instance validation failure at '{loc}': {err.message}")
        except Exception as e:
            errors.append(f"Instance validation execution error: {e}")
    else:
        errors.append("jsonschema library is required for instance evaluation")

    return errors


def validate_discovery_manifest(path: Path) -> list[str]:
    """Validate discovery manifest structure, version formats, and capability authority."""
    errors: list[str] = []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"{path}: JSON parse error: {e}"]

    ucp = doc.get("ucp") if isinstance(doc, dict) and "ucp" in doc else doc
    if not isinstance(ucp, dict):
        return [f"{path}: Manifest missing 'ucp' container"]

    proto_ver = ucp.get("version")
    ok, msg = validate_date_version(proto_ver)
    if not ok:
        errors.append(f"{path}: Protocol version error: {msg}")

    capabilities = ucp.get("capabilities", {})
    if isinstance(capabilities, dict):
        cap_items = capabilities.items()
    elif isinstance(capabilities, list):
        cap_items = [(f"item_{i}", item) for i, item in enumerate(capabilities)]
    else:
        return [f"{path}: 'capabilities' must be a dict or list"]

    for cap_name, entries in cap_items:
        entry_list = entries if isinstance(entries, list) else [entries]
        for entry in entry_list:
            if not isinstance(entry, dict):
                continue
            ver = entry.get("version")
            if ver:
                ok, msg = validate_date_version(ver)
                if not ok:
                    errors.append(f"{path}: Capability '{cap_name}' version error: {msg}")
            schema_url = entry.get("schema")
            if schema_url and not cap_name.startswith("item_"):
                ok, msg = validate_authority_binding(cap_name, schema_url)
                if not ok:
                    errors.append(f"{path}: Capability '{cap_name}': {msg}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UCP Extension Schemas and Manifests")
    parser.add_argument("--schema", type=Path, help="Path to extension JSON schema file")
    parser.add_argument("--dir", type=Path, help="Directory containing extension schemas to validate")
    parser.add_argument("--data", type=Path, help="Instance payload to validate against --schema")
    parser.add_argument("--manifest", type=Path, help="Path to discovery profile manifest")
    parser.add_argument("--no-authority", action="store_true", help="Skip reverse-domain authority binding checks")
    args = parser.parse_args()

    check_auth = not args.no_authority
    all_errors: list[str] = []
    checked_count = 0

    if args.schema:
        print(f"Validating schema: {args.schema}")
        errs = validate_schema_file(args.schema, check_authority=check_auth)
        all_errors.extend(errs)
        checked_count += 1

        if args.data:
            print(f"Validating payload: {args.data} against {args.schema}")
            instance_errs = validate_instance_file(args.schema, args.data)
            all_errors.extend(instance_errs)
            checked_count += 1

    if args.dir:
        for json_path in sorted(args.dir.glob("**/*.json")):
            print(f"Validating schema: {json_path}")
            errs = validate_schema_file(json_path, check_authority=check_auth)
            all_errors.extend(errs)
            checked_count += 1

    if args.manifest:
        print(f"Validating discovery manifest: {args.manifest}")
        errs = validate_discovery_manifest(args.manifest)
        all_errors.extend(errs)
        checked_count += 1

    if checked_count == 0:
        parser.print_help()
        return 1

    if all_errors:
        print(f"\nFAILED with {len(all_errors)} error(s):", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"\nSUCCESS: All {checked_count} target(s) passed validation cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
