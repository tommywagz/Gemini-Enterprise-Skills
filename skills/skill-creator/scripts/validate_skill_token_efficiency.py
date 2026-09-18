#!/usr/bin/env python3
"""Report token-efficiency guardrails for skill packages.

Checks all skills/<name>/SKILL.md files for description size, active-body word
budget, unreferenced markdown resources, and exact duplicated paragraphs
between a SKILL.md body and its references.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
DESCRIPTION_LIMIT = 1024
BODY_WORD_LIMIT = 6250  # Conservative word approximation of 5,000 tokens.


def frontmatter_and_body(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    _, frontmatter, body = text.split("---\n", 2)
    return frontmatter, body


def description_length(frontmatter: str) -> int:
    folded = re.search(r"^description:\s*>[-+]?\n((?:^[ \t]+.*\n?)*)", frontmatter, re.M)
    if folded:
        return len(" ".join(line.strip() for line in folded.group(1).splitlines()))
    inline = re.search(r"^description:\s*(.+)$", frontmatter, re.M)
    return len(inline.group(1).strip()) if inline else 0


def paragraphs(text: str) -> set[str]:
    blocks = re.split(r"\n\s*\n", text)
    return {
        re.sub(r"\s+", " ", block).strip()
        for block in blocks
        if len(re.sub(r"\s+", " ", block).strip()) >= 100
    }


def main() -> int:
    errors: list[str] = []
    for skill_file in sorted(SKILLS.glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        frontmatter, body = frontmatter_and_body(text)
        description_chars = description_length(frontmatter)
        body_words = len(re.findall(r"\b\w+[\w'-]*\b", body))
        print(f"{skill_file.relative_to(ROOT)}: description={description_chars} chars, body={body_words} words")
        if description_chars == 0:
            errors.append(f"{skill_file}: missing description")
        elif description_chars > DESCRIPTION_LIMIT:
            errors.append(f"{skill_file}: description exceeds {DESCRIPTION_LIMIT} characters")
        if body_words > BODY_WORD_LIMIT:
            errors.append(f"{skill_file}: body exceeds {BODY_WORD_LIMIT} words")

        for resource_dir in ("references", "scripts", "assets"):
            resource_root = skill_file.parent / resource_dir
            resource_paths = sorted(path for path in resource_root.rglob("*") if path.is_file()) if resource_root.is_dir() else []
            for resource in resource_paths:
                relative = resource.relative_to(skill_file.parent).as_posix()
                if relative not in body:
                    errors.append(f"{skill_file}: unreferenced resource {relative}")
                if resource_dir != "references" or resource.suffix != ".md":
                    continue
                duplicate = paragraphs(body) & paragraphs(resource.read_text(encoding="utf-8"))
                if duplicate:
                    errors.append(f"{skill_file}: duplicated paragraph with {relative}")

    if errors:
        print("\nFAIL", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("\nPASS: token-efficiency checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
