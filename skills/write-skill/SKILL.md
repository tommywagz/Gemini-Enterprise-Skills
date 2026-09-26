---
name: write-skill
description: >-
  Creates or restructures an Agent Skill package with SKILL.md, scripts,
  references, and assets. TRIGGER for "create/write/scaffold a skill", a
  SKILL.md, or fixing a skill's description, token budget, or layout. DO NOT
  TRIGGER for ordinary documentation, general code, evaluating/testing/scoring
  skills (route to evaluate-skill), or searching external registries like
  GitHub or Composio to find existing skills (route to find-skill).
version: 1.1.0
author: Actual Agentic Solutions
tags: [skill-authoring, meta, agent-skills, scaffolding]
license: Apache-2.0
compatibility: Claude Code, Claude Agent SDK
metadata:
  category: meta-skill
---

# Write Skill

Create or update a concise, well-routed Agent Skill grounded in supplied
source material.

## Inputs

- Goal, trigger and do-not-trigger cases, source material, and any reusable
  scripts, references, or templates.
- Required tools, license, and runtime. If unspecified, use the host license
  and minimum necessary tools, and disclose those defaults.

## Workflow

1. Confirm scope. For a vague new skill, ask for trigger boundaries before
   writing. For an existing package, inspect its files before changing them.
2. Choose a lowercase-hyphen name matching the directory. Read
   `references/formatter_fields.md` when drafting or auditing frontmatter;
   preserve concrete trigger terms and do-not-trigger cases.
3. Route content deliberately. Keep active decisions in `SKILL.md`, reusable
   deterministic work in `scripts/`, on-demand reasoning material in
   `references/`, and output-only material in `assets/`. Read
   `references/writing_principles.md` when the split or instruction freedom is
   unclear. Do not duplicate content across them or create empty folders.
4. For a new directory, run
   `scripts/scaffold_skill.sh <skill-name> [output-dir] [components]`.
   It refuses existing directories; ask the user before any overwrite.
5. Write or revise the active body: prerequisites, ordered decision path,
   safety gates, script invocations, conditional reference pointers, and
   output contract. Read `references/full_template.md` only when selecting a
   structure or drafting a new skill.
6. Validate name/directory match, description routing quality, no empty
   bundled folders, executable referenced scripts, and a body below roughly
   5,000 tokens. Move detail to a referenced file instead of deleting safety
   guidance.

| Condition | Action |
| --- | --- |
| Missing domain source for fragile specifics | Mark the gap and ask for documentation; do not invent it. |
| Description exceeds budget | Remove redundant trigger prose before anti-triggers. |
| Existing target directory | Stop and request overwrite approval. |
| Referenced resource unavailable | Name it and pause; do not fabricate it. |
| Request asks to score, benchmark, or evaluate an existing skill | Delegate to `evaluate-skill`; do not use `write-skill`. |
| Request asks to search external registries or find existing skills | Delegate to `find-skill`; do not use `write-skill`. |

## Compact cases

- New Terraform review skill with supplied policy → scaffold → place the
  policy in references and the decision path in `SKILL.md`.
- Existing directory without overwrite approval → report the conflict → stop.

## Resources

- `scripts/scaffold_skill.sh`: creates new package skeletons (step 4).
- `references/formatter_fields.md`: frontmatter and budget checks (step 2).
- `references/writing_principles.md`: bundling and instruction guidance (step 3).
- `references/full_template.md`: structural template (step 5).
- `assets/skill_template.md`: scaffold starter content (used by the script).

## Output

Return the changed folder tree, relevant `SKILL.md` content or diff, and the
description/token-budget validation result with any defaults called out.
