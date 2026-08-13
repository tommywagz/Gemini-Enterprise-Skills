# Security Review

## Contents
- Scope of concern
- Data classification
- Risk tiers
- Order of operations

## Scope of concern

Scope every skill for: misconfigurations that give the agent too much access
to the filesystem, exposure of sensitive data, and agent manipulation through
prompt injection (instructions hidden in bundled files that try to redirect
the agent's behavior).

## Data classification

Assign one label per skill, driven by the most sensitive data its bundled
files or instructions touch — this is what the production checklist's "Data
classification set correctly" box refers to:

| Label | Skill touches... |
|---|---|
| **Public** | No data beyond what's already public (docs, general code). |
| **Internal** | Internal repo/business context with no regulated or customer data. |
| **Confidential** | Customer PII, financial records, or internal secrets/credentials (even via env vars/IAM roles). |
| **Restricted** | Regulated data (health, payment card, government) or anything with a legal handling requirement. |

A skill that only *reads* sensitive data still inherits that data's
classification — classify by what it touches, not by what it writes.

## Risk tiers

| Risk Level | Indicators |
|---|---|
| **Low** | Instructions only, no scripts, no external references |
| **Medium** | Contains scripts (`*.py`, `*.sh`, `*.js`) |
| **High** | References external URLs, uses `aws cli`, `curl`, `kubectl apply` |
| **Critical** | Path traversal patterns (`../`), hardcoded credentials, data exfiltration logic |

`scripts/security_scan.sh` performs the pattern-matching pass for Steps 4-6
below and suggests a starting tier — treat its output as a lead list to
manually verify, not a final verdict. A skill can pattern-match clean and
still be Critical (e.g. adversarial instructions in prose, which grep can't
judge), and it can pattern-match a hit that's actually benign (a `curl`
example inside a fenced code block that's never executed).

## Order of operations

Work through these in order — do not skip ahead to scripts if you haven't
read the prose, since adversarial instructions often live in the parts that
"look like documentation."

1. **Read all skill directory content.** Review `SKILL.md`, every referenced
   Markdown file, and every bundled script in full. Do not trust or score a
   skill you have not fully read.
2. **Verify script behavior matches stated purpose.** Run scripts in a
   sandboxed environment; confirm their actual output aligns with what the
   skill body claims they do.
3. **Check for adversarial instructions.** Look specifically for: directives
   to ignore safety rules or bypass approvals, instructions to hide actions
   from the user, data exfiltration through model responses, and behavior
   that changes based on specific trigger inputs (a conditional backdoor).
4. **Check for external network calls.** Run
   `scripts/security_scan.sh <skill-dir>`, or search manually for: `http`,
   `requests.get`, `urllib`, `curl`, `fetch`, `wget`, `aws s3 cp`. External
   calls are how context gets exfiltrated to an attacker-controlled server.
5. **Verify no hardcoded credentials.** AWS access keys, kubeconfig tokens,
   and API keys must be sourced from environment variables or IAM roles —
   they must never appear literally in skill content.
6. **Identify the full blast radius.** List every bash command, kubectl
   operation, and CLI call the skill can issue. Assess combined risk, not
   just each call individually — e.g. `kubectl get secrets` plus a
   network-write capability together are Critical even if each looks
   Medium alone. For each call that is destructive or hard to reverse
   (delete, force-push, `kubectl apply`/`delete`, `terraform apply`, writes
   to shared/production systems), confirm the skill's body requires an
   explicit user confirmation step before issuing it — this is what the
   production checklist's "Approval workflow configured for irreversible
   actions" box refers to. Flag any irreversible call the body would fire
   without one.

Any Critical finding halts the improvement loop in the main workflow — report
it immediately rather than continuing on to performance tuning.
