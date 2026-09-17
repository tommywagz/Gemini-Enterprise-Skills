---
name: gcp-iam-privilege-audit
description: "Audits Google Cloud IAM bindings and service-account key exposure, interprets IAM Recommender evidence, and proposes reviewable least-privilege predefined/custom roles or Workload Identity Federation migration without changing access. TRIGGER when users ask to 'audit GCP IAM permissions', 'harden service account keys', 'implement least-privilege roles', 'configure Workload Identity', 'rightsize project-level editor bindings', or review IAM Recommender output. DO NOT TRIGGER for granting new broad production access, rotating secrets without an IAM audit objective, or AWS/Azure IAM reviews."
version: 1.0.0
author: Actual Agentic Solutions
tags: [gcp, iam, least-privilege, recommender, workload-identity, terraform]
license: Apache-2.0
compatibility: "Python 3.9+ for scripts/get_iam_recommendations.py; optional Application Default Credentials and Recommender IAM read permission for live API mode"
metadata: {}
---

- IAM Least-Privilege Hardener

- Overview
This skill turns broad Google Cloud IAM into reviewable, evidence-backed
recommendations. It inventories bindings and service-account keys, reads IAM
Recommender observations where authorized, maps actual job needs to narrower
roles, and proposes Terraform only. It never applies a policy, deletes a key,
or removes `roles/owner`/`roles/editor` automatically: these changes can
break workloads, emergency access, or organization controls.

- Prerequisites
- Authorized project/folder scope, principal/binding inventory, and a change
  owner who can validate required permissions before removal.
- Optional Application Default Credentials for live Recommender read mode;
  otherwise use the script's built-in mock or a reviewed response fixture.
- Treat policy exports, service-account email addresses, and recommender
  evidence as confidential. Never place private keys or tokens in reports.

- Workflow

- Step 1: Establish scope and collect read-only evidence
List project-level and inherited bindings, service accounts, user-managed
keys (metadata only), and workload identity usage. Define a rollback owner
and observation window before proposing any change. Do not infer unused from
absence in one short log window.

- Step 2: Obtain recommendation evidence
Run a safe local schema check/mock:
```
scripts/get_iam_recommendations.py --mock --project PROJECT_ID
```
For a live read, use an OAuth bearer token supplied through stdin (never an
argument or committed file):
```
printf '%s' "$ACCESS_TOKEN" | scripts/get_iam_recommendations.py --project PROJECT_ID --token-stdin
```
The script calls only the Recommender REST list endpoint and redacts token
handling from output. A `SUCCEEDED` recommendation is evidence to review, not
authorization to change a binding.

- Step 3: Map job intent to minimum role
Read `references/predefined_roles_map.md`. Replace primitive roles with the
narrowest predefined role that covers the confirmed action; use a custom role
only when no predefined role fits, with explicit included permissions and an
owner/review date. Review service agents separately: do not remove roles
granted to Google-managed service accounts merely because their use is opaque.

- Step 4: Prefer federation over downloadable keys
For external CI/CD, GKE, or on-premises identity, read
`references/workload_identity_setup.md` and design Workload Identity
Federation or GKE Workload Identity. Inventory and disable user-managed keys
only after the federated path has passed a non-production proof and a rollback
window exists. Never export, decode, or log a service-account private key.

- Step 5: Produce a review-only Terraform plan
Copy the appropriate blocks from
`assets/least_privilege_terraform_templates.tf`, replace placeholders, and
show the old binding, proposed binding, evidence, affected workload, rollback,
and test. Do not run `terraform apply` or `gcloud projects set-iam-policy`.

- Examples

- Example 1: Project Editor right-sizing
For a CI service account with `roles/editor`, inspect its proven deployment
actions and Recommender evidence, then propose only needed deploy/artifact
roles plus scoped resource bindings. Preserve break-glass access until the
owner approves and validates a staged rollout.

- Example 2: Static key hardening
For a GitHub pipeline with a downloaded key, map GitHub OIDC attributes to a
Workload Identity pool/provider and service-account impersonation binding.
Do not revoke the existing key until the new authentication is verified.

- Error Handling
- Recommender returns `403`: report the missing read permission and use mock
  mode; never ask for `Owner` as a diagnostic shortcut.
- No recommendation returned: it is not proof the binding is safe; document
  missing usage evidence and retain it pending owner review.
- A narrow role breaks a staged test: restore the prior approved binding,
  capture the missing permission, and revise the proposal; do not add
  `roles/editor` back as the default fix.

- Reference Files
- **references/predefined_roles_map.md**: role replacement map and cautions.
- **references/workload_identity_setup.md**: federation migration sequence.
- **scripts/get_iam_recommendations.py**: mock or read-only REST API client.
- **assets/least_privilege_terraform_templates.tf**: review-only HCL blocks.

- Output Format
Return scoped inventory; evidence; proposed role/federation change; Terraform
snippet; validation/rollback plan; and residual risks. Mark all changes
review-only until an authorized human approves them.
