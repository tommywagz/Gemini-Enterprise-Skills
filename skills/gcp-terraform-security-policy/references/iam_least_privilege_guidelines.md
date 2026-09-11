# GCP IAM Least-Privilege Guidelines

## Contents
- Role types: primitive vs. predefined vs. custom
- Choosing a predefined role instead of a primitive role
- Service account best practices
- Workload Identity vs. service account keys
- IAM Recommender and safe role tightening
- Deny policies (blocklisting on top of an allow model)

Read this file when a finding is `GCP-IAM-001` (primitive role) or
`GCP-IAM-002` (service account key), or when the user asks for IAM-specific
guidance beyond "remove the broad grant" — it supplies the *replacement*
role or pattern, not just the problem.

## Role types: primitive vs. predefined vs. custom

| Type | Example | Scope | Use when |
|---|---|---|---|
| Primitive | `roles/owner`, `roles/editor`, `roles/viewer` | Every service in the project, undifferentiated | Almost never in production — these predate IAM's fine-grained model |
| Predefined | `roles/storage.objectViewer`, `roles/cloudsql.client` | One service, curated permission set maintained by Google | Default choice — matches most real job functions |
| Custom | `roles/myorg.deployPipeline` | Exact permission list you define | Only when no predefined role's permission set fits (fewer surprises, but you own the maintenance burden as the API evolves) |

`roles/editor` in particular is a common trap: it looks like "read plus
some writes" but actually grants create/update/delete across nearly every
GCP service in the project, including the ability to modify network and
storage configuration outside the principal's actual job.

## Choosing a predefined role instead of a primitive role

When a scan flags `roles/owner` or `roles/editor` on a member, ask what that
member actually needs to do, then map it to the narrowest predefined role
covering just that:

| Actual need | Predefined role (not primitive) |
|---|---|
| Read/write objects in a specific bucket | `roles/storage.objectAdmin` (bucket-scoped IAM binding, not project-scoped) |
| Deploy Cloud Run/Functions revisions | `roles/run.developer` / `roles/cloudfunctions.developer` |
| Query BigQuery datasets | `roles/bigquery.dataViewer` + `roles/bigquery.jobUser` |
| Connect to Cloud SQL | `roles/cloudsql.client` |
| Manage a GKE cluster's workloads (not the cluster itself) | `roles/container.developer` |
| CI/CD service account deploying infra | A custom role scoped to the exact `resourcemanager`/`compute`/`iam` permissions the pipeline calls, not `roles/editor` |

Prefer granting the role at the narrowest resource scope available (bucket,
dataset, instance) over project scope whenever the IAM surface supports it —
a `google_storage_bucket_iam_member` on one bucket is strictly safer than a
`google_project_iam_member` with a storage role, even predefined.

## Service account best practices

- Never grant a service account a primitive role, for the same reasons as a
  human principal — service accounts are usually *more* exposed (embedded in
  running workloads) and *less* monitored (no MFA, no session review) than
  human logins.
- Avoid the **default Compute Engine service account**
  (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) for anything
  beyond throwaway experiments — it is granted `roles/editor` by default in
  older projects and is shared across every VM in the project unless
  explicitly overridden per-instance.
- One service account per workload/function, scoped to only the permissions
  that workload needs — not one shared service account across a whole
  project's automation.

## Workload Identity vs. service account keys

`GCP-IAM-002` flags any `google_service_account_key` resource because
user-managed keys are long-lived, downloadable secrets with no built-in
expiry:

- **On GKE**: use **Workload Identity** — bind a Kubernetes service account
  to a GCP service account (`roles/iam.workloadIdentityUser`) so pods
  authenticate as the GCP service account with short-lived, automatically
  rotated credentials and no key material ever touching disk or a Secret.
- **On GCE/Cloud Run/Cloud Functions**: attach the service account directly
  to the resource (`service_account_email` / `service_account` block) —
  the metadata server issues short-lived tokens automatically; no key
  needed.
- **Outside GCP** (other clouds, on-prem, CI runners): use **Workload
  Identity Federation** to exchange an external identity token (AWS IAM role,
  GitHub Actions OIDC token, etc.) for short-lived GCP credentials, instead
  of downloading and storing a service account key as a CI secret.
- If a key is truly unavoidable (a legacy on-prem system with no federation
  support), require `constraints/iam.disableServiceAccountKeyCreation` at the
  org level with an explicit, documented, time-boxed exception, and rotate it
  on a schedule short enough that a leaked-and-undetected key has a bounded
  blast radius.

## IAM Recommender and safe role tightening

Before manually guessing a narrower role, check whether **IAM Recommender**
already has a data-driven suggestion: it observes 90 days of actual
permission usage per principal and proposes the smallest predefined or
custom role that covers what was actually used. Cross-check any Recommender
suggestion against expected *future* usage (a role that's unused today may
still be needed for a quarterly job) before applying it — Recommender only
sees the past.

## Deny policies (blocklisting on top of an allow model)

IAM Deny policies let you explicitly block specific permissions for specific
principals regardless of what any allow binding grants elsewhere — useful as
a backstop when you cannot immediately clean up every over-broad allow
binding (e.g. a legacy `roles/editor` grant you're migrating off of over
several sprints). A deny policy is a mitigation for the transition period,
not a substitute for actually narrowing the underlying role grant flagged by
`GCP-IAM-001`.
