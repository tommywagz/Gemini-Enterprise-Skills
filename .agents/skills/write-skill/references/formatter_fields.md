# Frontmatter Fields & Description Checklist

## Contents
- Field reference table
- Description checklist (Trigger / Do Not Trigger pattern)
- Token budget by component

## Field reference table

| Field | Required | Value |
|---|---|---|
| `name` | Yes | Lowercase letters, numbers, hyphens only. Max 64 characters. Must match the skill's folder name. |
| `description` | Yes | When and why to use this skill. Max 1024 characters. This is the routing trigger — see checklist below. |
| `version` | No | Semantic versioning (`major.minor.patch`) for lifecycle management. |
| `author` | No | Searchable attribution for skill registries. |
| `tags` | No | Searchable categories for skill registries. |
| `tools` | No | Pre-approved tool allow-list (enforced in enterprise runtimes). |
| `license` | No | License applied to the skill. Default to the repo's license if unspecified. |
| `compatibility` | No | Environment requirements (e.g. "Claude Code", "Claude Agent SDK", specific runtimes). |
| `metadata` | No | Arbitrary key-value pairs for custom properties. |

## Description checklist (Trigger / Do Not Trigger pattern)

The `description` is always loaded at startup — it is the *only* signal the
routing model sees before deciding to activate the skill. A vague description
causes both false negatives (skill never fires) and false positives (skill
fires on unrelated requests). Every description must satisfy all six:

1. One sentence summary of the skill's purpose.
2. At least 2-3 concrete TRIGGER conditions using specific technical terms
   users will actually say or type (error messages, CLI verbs, file types,
   service names) — not paraphrased categories.
3. At least 1-2 DO NOT TRIGGER conditions covering the most common misfire
   scenarios (the adjacent task someone might confuse this skill for).
4. No ambiguous verbs ("handle", "do", "deal with") — use specific actions
   ("debug", "diagnose", "deploy", "scaffold", "validate").
5. Mention key error messages, CLI tools, or service names agents can
   pattern-match on.
6. Under 150 words total, under 1024 characters.

Bad: *"Helps with Kubernetes issues."*
Good: *"Diagnoses failing pods. TRIGGER when the user mentions
`CrashLoopBackOff`, `OOMKilled`, or asks why a pod keeps restarting. DO NOT
TRIGGER for node-level or networking issues."*

## Token budget by component

| Component | Budget | Loaded when |
|---|---|---|
| `description` | ≤1024 chars (~250 tokens) | Always, at agent startup |
| `SKILL.md` body | ≤5000 tokens | On activation, when description matches |
| `references/*` | Variable, on demand | When the SKILL.md body explicitly points to it |
| `scripts/*` | Not loaded — executed | When the SKILL.md body invokes it |
| `assets/*` | Never loaded into context | Used directly in output |

Challenge every paragraph in SKILL.md against this budget: if it's reference
material rather than an active instruction, it belongs in `references/`, with
a pointer left in its place — not duplicated in both.
