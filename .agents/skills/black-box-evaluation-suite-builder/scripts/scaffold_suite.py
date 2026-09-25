#!/usr/bin/env python3
"""Create isolated black-box evaluation planning files without overwriting data."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ASSETS = Path(__file__).resolve().parents[1] / "assets"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a black-box evaluation directory.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    destinations = {
        "coverage_matrix.json": ASSETS / "coverage_matrix_template.json",
        "evaluation_report.json": ASSETS / "evaluation_report_template.json",
    }
    # Check the whole destination set before writing anything on a repeat run.
    existing = [args.output / name for name in destinations if (args.output / name).exists()]
    if existing:
        print(f"refusing to overwrite {', '.join(map(str, existing))}", file=sys.stderr)
        return 2
    args.output.mkdir(parents=True, exist_ok=True)
    for name, source in destinations.items():
        destination = args.output / name
        shutil.copyfile(source, destination)
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
