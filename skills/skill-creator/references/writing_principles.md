# Skill Body Writing Principles & Bundling Rules

## Contents
- Writing principles
- Freedom-level table
- How to bundle resources (decision table)
- Bundling decision tree (scripts vs. references vs. assets)
- Anti-patterns to avoid in the skill itself

## Writing principles

- **Be specific, not general.** Instead of "check the pod status," write "run
  `kubectl describe pod [pod-name] -n [namespace]` and look for the
  `Last State`, `Exit Code`, and `Events` sections — these three fields
  contain 90% of failure information."
- **Make decisions explicit.** Agents follow instructions literally. If there
  are branches, state them. If required input is missing, default sensibly
  and confirm with the user before proceeding — don't guess silently.
- **Include anti-patterns.** Tell the agent what NOT to do, and why, so it
  doesn't reach for the obvious-but-wrong shortcut under pressure.
- **Embed domain knowledge.** This is the key differentiator between a skill
  and a table of contents. Distinguish adjacent failure modes / cases
  explicitly and say how handling differs between them.
- **Keep steps atomic.** Each step should produce one verifiable intermediate
  result. This makes the skill easier to test and easier for an agent to
  self-correct mid-workflow.
- **Be concise.** The context window is a shared resource. Challenge every
  paragraph: "does this justify its token cost?" Prefer one concrete example
  over a page of prose.
- **Avoid redundancy.** Information lives in SKILL.md *or* a reference file —
  never both. If it belongs in references, leave a pointer in SKILL.md, not a
  copy.
- **Don't over-document.** Skills are for agents, not humans. Do not add a
  README.md, INSTALLATION_GUIDE.md, or CHANGELOG.md inside the skill folder.
  If a human needs it, it doesn't belong in the skill directory.

## Freedom-level table

Not every step deserves the same level of prescription — match it to how
fragile or reversible the operation is.

| Freedom level | When to use | Example |
|---|---|---|
| **High** (text instructions) | Multiple valid approaches exist | General guidance |
| **Medium** (pseudocode / parameterized) | A preferred pattern exists, some variation OK | Templated workflows |
| **Low** (specific scripts, exact steps) | Operations are fragile or irreversible | Production deploys, config changes |

## How to bundle resources

Run each candidate piece of content through this table before deciding where
it lives:

| Question | Action |
|---|---|
| Is code being regenerated repeatedly in conversations? | Add to `scripts/` |
| Is there documentation too large for the skill body? | Add to `references/` |
| Does the skill output require a template or static file? | Add to `assets/` |
| Does the agent need to *read and reason about* the content? | `references/` |
| Does the agent need to *execute* the content deterministically? | `scripts/` |
| Does the agent need to *produce* or *copy* the content? | `assets/` |

The first three rows classify by content type (code / docs / output file);
the last three classify by what the agent *does* with it (reason about it /
run it / hand it out unread). If a piece of content answers "yes" to more
than one row, split it: e.g. a large lookup table the agent both reasons
about *and* copies into output belongs in `references/` for the reasoning
step, with a trimmed-down copy in `assets/` for the output step — don't force
one file to serve both.

## Bundling decision tree

```
SKILL.md body (active context, ≤5000 tokens)
     |
     +-- "run scripts/X.sh"      --> scripts/      (executed, NOT loaded into context)
     |
     +-- "read references/X.md" --> references/    (loaded into context on demand)
     |
     +-- "use assets/X"          --> assets/        (used in output, never loaded)
```

- **`scripts/`** — executable code for tasks needing deterministic
  reliability, or that would otherwise be regenerated (and drift) each
  conversation. Tell the agent exactly when and how to invoke it, and what
  output format to expect back, e.g.: *"run `scripts/collect_pod_state.sh
  [namespace] [pod-name]` — it writes structured JSON to
  `/tmp/pod_state_[timestamp].json`; parse that for Steps 1-3 instead of
  running kubectl commands individually. If kubectl access is unavailable,
  fall back to the manual commands in Steps 1-3."*
- **`references/`** — documentation to load into context only when the body
  needs deeper detail: schemas, API docs, compliance policy, decision trees,
  lookup tables too large for the 5000-token body budget. Add a table of
  contents to the top of any reference file over 100 lines so the agent can
  decide whether to load the whole file or jump to a section.
- **`assets/`** — files used *in the output*, never read into context:
  templates, boilerplate configs, large lookup tables, binaries. The agent
  copies or fills these in without needing to understand their internal
  contents.

Bundle a reference only when: the info is needed for accurate decisions, it's
too large for the body (roughly >5000 tokens), or it's a policy/table that
changes independently of the skill's logic. Otherwise, put it in the body.

## Anti-patterns to avoid when writing a skill

- Don't write a description with vague verbs ("handles X issues") — it will
  either never trigger or trigger on everything.
- Don't duplicate reference content into the body "just in case" — it burns
  the always-loaded budget for nothing.
- Don't create empty `scripts/`, `references/`, or `assets/` folders when a
  skill has no bundled content of that type — omit the folder entirely.
- Don't invent API/CLI details from memory when the user has supplied source
  docs or URLs — ground the skill in what was actually provided, and note
  where a claim could not be verified.
