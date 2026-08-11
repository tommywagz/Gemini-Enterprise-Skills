---
name: write-skill
description: >-
  Creates, formats, and scaffolds new Agent Skills using the standard
  SKILL.md + scripts/ + references/ + assets/ architecture. TRIGGER when the
  user asks to "create a skill", "write a skill", "make an agent skill",
  "package this as a skill/SKILL.md", "scaffold a skill folder", wants a
  Trigger/Do-Not-Trigger description written, or wants a workflow, runbook,
  API doc, or set of scripts turned into a reusable Claude Code or Claude
  Agent SDK skill. Also trigger to audit, restructure, or fix an existing
  skill's SKILL.md format, description, token budget, or folder layout. DO
  NOT TRIGGER for general documentation requests with no skill-authoring
  intent (e.g. writing a README or product doc), or for simply
  invoking/running an already-installed skill rather than authoring one.
version: 1.0.0
author: Actual Agentic Solutions
tags: [skill-authoring, meta, agent-skills, scaffolding]
license: Apache-2.0
compatibility: Claude Code, Claude Agent SDK
metadata:
  category: meta-skill
---

- Write Skill

- Overview
Turns a task, workflow, or set of source material (docs, URLs, existing
scripts, output templates) into a well-formed Agent Skill: a folder with a
`SKILL.md` (required) plus optional `scripts/`, `references/`, and `assets/`
subfolders. The description below is the routing trigger for *this* skill;
the body teaches you to write that same kind of trigger for the skill you
create.

- Prerequisites
- The task or goal the new skill should accomplish.
- Any source material the user has: reference docs, URLs, example scripts,
  output templates, existing partial skills. Ground the new skill in these —
  do not invent API/CLI specifics from memory when better sources exist.
- Any constraints: required tool allow-list, license, target runtime
  (Claude Code, Claude Agent SDK, enterprise registry).
If the goal is vague ("make me a skill for X"), ask what triggers it and what
it should NOT fire on before writing anything — a skill built on a guessed
scope will misfire in both directions.

- Workflow

- Step 1: Gather inputs
Confirm: the goal, trigger phrases vs. do-not-trigger cases, source material
to ground the skill in, and any scripts/assets to wrap. If the user hasn't
specified license/tools/compatibility, default to the host repo's license and
the minimal tool set the workflow actually needs, and state the defaults you
chose rather than silently assuming them.

- Step 2: Name and describe
Choose a `name` in lowercase-hyphen-only form that matches the skill's folder
name. Draft the `description` using the Trigger/Do-Not-Trigger checklist —
see `references/formatter_fields.md` for the full field table and the six-
point checklist (concrete trigger terms, 1-2 do-not-trigger cases, no
ambiguous verbs, under 150 words / 1024 characters).

- Step 3: Decide what goes where
Apply the bundling decision tree in `references/writing_principles.md`:
active instructions stay in the SKILL.md body; deterministic/repeatable code
goes in `scripts/`; on-demand documentation goes in `references/`; output
templates and binaries go in `assets/`. Only create the subfolders you will
actually populate — never leave an empty `scripts/`, `references/`, or
`assets/` in the delivered skill.

- Step 4: Scaffold the folder
Run `scripts/scaffold_skill.sh <skill-name> [output-dir] [components]` to
create the skeleton and a starter `SKILL.md` from `assets/skill_template.md`
in one pass. Pass a `components` list (e.g. `references,scripts`) to skip
folders decided against in Step 3. If the target folder already exists, the
script refuses to overwrite it — resolve that with the user before retrying.

- Step 5: Write the SKILL.md body
Follow the annotated template and worked example in
`references/full_template.md`: Overview, Prerequisites, Workflow (atomic
steps with explicit branches and named anti-patterns), Examples, Error
Handling, Reference Files, Output Format. Match each step's prescriptiveness
to how fragile the operation is, per the freedom-level table in
`references/writing_principles.md` — high freedom for steps with several
valid approaches, low freedom (exact commands) for fragile or irreversible
ones.

- Step 6: Populate bundled files
Write the `references/`, `scripts/`, and `assets/` content, grounded in the
source material gathered in Step 1. Add a table of contents to any reference
file over 100 lines. Never duplicate content between the body and a
reference file — leave a pointer in the body instead.

- Step 7: Validate before delivering
Check: `name` is lowercase-hyphen and matches the folder; `description`
passes all six checklist points; the SKILL.md body stays under ~5000 tokens;
no unused empty folders; every script referenced in the body is executable
and invoked with the exact command shown. Report the final folder tree.

- Examples

- Example 1: New skill from a stated goal
Input: "I want a skill that reviews Terraform plans for drift before apply."
Expected output / behavior: propose `name: terraform-drift-review`, draft a
description with triggers on `terraform plan`, `terraform apply`, "drift" and
a do-not-trigger for general Terraform authoring help; ask whether the user
has an existing drift policy doc or script to ground Step 6 in before
writing placeholder content.

- Example 2: Fixing an existing skill
Input: "This skill's description never fires — can you fix it?"
Expected output / behavior: audit the existing `description` against the
six-point checklist in `references/formatter_fields.md`, point out which
items fail (usually missing concrete trigger terms or no do-not-trigger
case), and rewrite it in place — no folder restructure needed unless asked.

- Error Handling
- Goal or scope is unclear: ask clarifying questions before scaffolding;
  don't guess a broad description "to be safe" — over-broad descriptions
  cause false-positive triggers.
- Description exceeds 150 words / 1024 characters: cut redundant trigger
  phrasing before cutting do-not-trigger cases — false positives are usually
  more disruptive than a missed activation.
- SKILL.md body threatens to exceed ~5000 tokens: move detail into
  `references/` rather than trimming the domain knowledge that makes the
  skill useful.
- No source material provided for a skill needing specific API/CLI details:
  do not fabricate plausible-sounding specifics — mark the gap as TODO in
  the output and ask the user for docs or a link.
- Target skill folder already exists: stop and confirm with the user before
  any overwrite; `scripts/scaffold_skill.sh` already refuses this by default.

- Reference Files
- **scripts/scaffold_skill.sh**: creates `<skill-name>/SKILL.md` (from the
  asset template) plus the chosen subfolders in one command. Run it in
  Step 4 instead of creating files by hand.
- **references/full_template.md**: the annotated SKILL.md structure plus a
  fully worked example — read before writing the body in Step 5.
- **references/formatter_fields.md**: full frontmatter field table and the
  six-point description checklist — read in Step 2.
- **references/writing_principles.md**: body-writing principles, the
  freedom-level table, and the scripts/references/assets bundling decision
  tree — read in Steps 3 and 5.
- **assets/skill_template.md**: blank starter SKILL.md with placeholder
  sections, filled in automatically by the scaffold script.

- Output Format
Return the created folder tree, the full `SKILL.md` content, and a short
confirmation that the description and token-budget checks from Step 7
passed. If any input was defaulted rather than user-specified (license,
tools, missing source material), call that out explicitly.
