# Sample Knowledge Base — Mock Terminology & Preference Dictionary

A worked example of the kind of facts worth seeding into Memory Bank before
an agent's first real conversation, split by the managed topic each fact
would naturally fall under (see `references/vertex_memory_bank_api.md` for
what each topic means). Copy the relevant entries into a JSON file matching
`assets/memory_bank_schema.json` and run `scripts/preload_memory.py
--facts-file <your-file>.json` to seed them — do not paste this Markdown
file directly into the script, it only accepts the JSON shape.

## User preferences (`USER_PREFERENCES`)

- I prefer concise answers — no more than three sentences unless I ask for
  detail.
- I want code examples in Python by default unless I name another language.
- I prefer the model to flag uncertainty explicitly rather than guessing
  confidently.

## User personal info (`USER_PERSONAL_INFO`)

- I work as a platform engineer on the Payments team.
- I'm based in the US/Eastern timezone.
- My team's on-call rotation starts every Monday.

## Explicit instructions (`EXPLICIT_INSTRUCTIONS`)

- Remember that I primarily use Terraform for infrastructure, not Pulumi or
  CloudFormation.
- Always ask before suggesting a database schema migration — I want to
  review the plan first.

## Team terminology glossary (custom topic example: `team_glossary`)

A **custom** topic (unlike the four examples above, which are managed
topics Memory Bank recognizes out of the box) needs a `label` and
`description` configured on the Memory Bank instance itself — see
`references/vertex_memory_bank_api.md`'s custom topic section before
seeding facts meant for a topic like this one:

- "PR-gate" refers to our internal term for the required-checks CI job that
  blocks merge until security scan, lint, and unit tests all pass.
- "The vault" is our team's nickname for the internal secrets-management
  service (not HashiCorp Vault — a common point of confusion for new
  hires).
- A "cold deploy" means deploying to production without first soaking the
  build in staging for 24 hours — reserved for security patches only.

## Turning this into a seed file

Each bullet above becomes one entry in the JSON array
`scripts/preload_memory.py --facts-file` expects. For example, the first
two "User preferences" bullets become:

```json
[
  {
    "fact": "I prefer concise answers — no more than three sentences unless I ask for detail.",
    "scope": {"user_id": "REPLACE_WITH_REAL_USER_ID"},
    "topic": "USER_PREFERENCES"
  },
  {
    "fact": "I want code examples in Python by default unless I name another language.",
    "scope": {"user_id": "REPLACE_WITH_REAL_USER_ID"},
    "topic": "USER_PREFERENCES"
  }
]
```

Do not seed real user data this way without the user's knowledge — this
file is a *pattern* to copy for legitimate onboarding/preference capture
flows (e.g. a settings form the user filled out themselves), not a template
for silently recording things a user never agreed to have remembered.
