# GCP Security Benchmarks & Private-by-Default Rules

## Contents
- CIS Google Cloud Platform Foundation Benchmark: structure and scope
- Storage: private-by-default rules
- Networking: private-by-default rules
- Compute & GKE hardening
- Cloud SQL hardening
- Logging & monitoring baseline
- Org policy constraints that make fixes durable
- Known limitations of scanning a single Terraform plan

This file grounds the CIS control numbers and rationale cited by
`assets/gcp_compliance_checklist.json` and `scripts/audit_tf_gcp.py`. Read it
when a finding's one-line rationale isn't enough context to explain a fix to
the user, or when the user asks "why does CIS care about this" rather than
just "how do I fix it."

## CIS Google Cloud Platform Foundation Benchmark: structure and scope

The CIS GCP Foundation Benchmark organizes controls into numbered sections
(section numbers below match the `cis_id` field in the checklist):

| Section | Area |
|---|---|
| 1.x | Identity and Access Management (IAM) |
| 2.x | Logging and Monitoring |
| 3.x | Networking |
| 4.x | Virtual Machines (Compute Engine) |
| 5.x | Storage (Cloud Storage, BigQuery) |
| 6.x | Cloud SQL |
| 7.x | Kubernetes Engine (GKE) |

The benchmark also splits controls into **Level 1** (baseline, no material
performance/cost tradeoff) and **Level 2** (defense-in-depth, may add latency
or operational overhead). Treat this repo's severities as a risk-based
re-ranking, not a literal restatement of CIS levels — a Level 2 control can
still be CRITICAL in this checklist if its absence is a common real-world
breach vector (e.g. public storage buckets).

CIS re-numbers and revises controls between benchmark versions (v1.x, v2.0,
v3.0). Before quoting a control number to a user as authoritative, note the
benchmark version this checklist was grounded in
(`assets/gcp_compliance_checklist.json`'s `grounded_in` field) and suggest
they cross-check against the current PDF from the CIS website if precision
matters for a compliance audit trail.

## Storage: private-by-default rules

- **Public Access Prevention** (`public_access_prevention = "enforced"` on
  `google_storage_bucket`): the single strongest control — it makes public
  IAM bindings/ACLs *unenforceable* regardless of what gets added later, at
  the bucket level, independent of any single IAM binding audit catching the
  next mistake.
- **Uniform bucket-level access** (`uniform_bucket_level_access = true`):
  disables legacy per-object ACLs so the bucket's IAM policy is the *only*
  authorization surface. Without it, an object-level ACL can grant access
  that never shows up in a `google_storage_bucket_iam_*` resource at all —
  meaning Terraform-only scanning can miss a public object even when the
  bucket's own IAM policy looks clean.
- `allUsers` grants access to anyone on the internet, unauthenticated.
  `allAuthenticatedUsers` grants access to any Google account holder
  worldwide, not just principals in your organization — treat both as
  equally CRITICAL; `allAuthenticatedUsers` is not "internal."

## Networking: private-by-default rules

- Default-deny is the correct baseline: every ingress rule should be a
  narrow allow-list, not a broad allow with narrow exceptions.
- `0.0.0.0/0` in `source_ranges` matches every IPv4 address on the internet.
  There is no "just for now" safe use of it on an ingress rule for a
  management port (22, 3389) or an unrestricted protocol/port rule.
- Prefer **Identity-Aware Proxy (IAP) TCP forwarding** for SSH/RDP access
  instead of a public firewall rule: it moves authentication to Google's
  identity layer and narrows the only valid source range to
  `35.235.240.0/20` (Google's IAP range), regardless of where the admin is
  connecting from.
- **VPC Flow Logs** (a `log_config` block on `google_compute_subnetwork`)
  are the forensic baseline for any network-layer incident review — absence
  isn't just a hardening gap, it is a future investigation with no network
  evidence.

## Compute & GKE hardening

- Compute instances: disable serial port access
  (`metadata["serial-port-enable"] = "false"`, the default) unless a specific
  incident requires interactive console debugging, and re-disable it
  afterward.
- GKE legacy ABAC (`enable_legacy_abac`) predates Kubernetes RBAC and cannot
  express least-privilege access to cluster resources — there is no valid
  reason to re-enable it on a modern cluster.
- **Private clusters** (`private_cluster_config.enable_private_nodes = true`)
  remove external IPs from nodes entirely; combine with
  `master_authorized_networks_config` to also restrict who can reach the
  control plane's public endpoint (or disable the public endpoint outright
  with `enable_private_endpoint = true` for the strictest posture).
- **Kubernetes Network Policy** (`network_policy.enabled = true`, with a
  provider like Calico or GKE Dataplane V2) is the pod-to-pod equivalent of a
  VPC firewall — without it, one compromised pod can reach every other pod
  in the cluster.

## Cloud SQL hardening

- Prefer **no public IP** (`ipv4_enabled = false`) with a private VPC peering
  connection, or the Cloud SQL Auth Proxy, over relying solely on
  `authorized_networks` allow-lists on a public IP.
- `require_ssl = true` (or the newer `ssl_mode` setting on providers that
  support it) is necessary even on a private-IP instance — private routing
  keeps traffic off the public internet, but does not encrypt it in transit
  by itself.
- Automated backups (`backup_configuration.enabled = true`) plus
  `point_in_time_recovery_enabled = true` are the only recovery path for
  ransomware, accidental `DROP TABLE`, or a bad migration that isn't caught
  immediately.

## Logging & monitoring baseline

- Cloud Audit Logs (Admin Activity logs are always on and cannot be
  disabled; Data Access logs must be explicitly enabled per-service via
  `google_project_iam_audit_config`) are the record of *who did what*, which
  is what most incident reviews and compliance audits actually need.
- A **log sink** (`google_logging_project_sink`) routed to a separate,
  access-restricted project or bucket protects the log trail itself from
  deletion by whoever is being investigated — logs that live only in the
  project being compromised are not a reliable record.
- This checklist marks audit-logging and org-policy controls
  `automated: false` (see `assets/gcp_compliance_checklist.json`) because
  verifying them correctly requires organization- or folder-level context a
  single project's Terraform plan does not contain — flag them for manual
  review rather than silently passing or guessing.

## Org policy constraints that make fixes durable

A resource-level fix (e.g. `public_access_prevention = "enforced"` on one
bucket) only protects that one resource. An **organization policy
constraint** enforced at the folder or org level makes the secure state the
*default* for every future resource, so the next engineer's mistake never
ships:

| Constraint | Effect |
|---|---|
| `constraints/storage.publicAccessPrevention` | Forces public access prevention on every bucket in scope |
| `constraints/compute.vmExternalIpAccess` | Blocks external IPs on Compute instances except an explicit allow-list |
| `constraints/iam.disableServiceAccountKeyCreation` | Blocks creation of new user-managed service account keys |
| `constraints/iam.disableServiceAccountKeyUpload` | Blocks uploading external public keys for a service account |
| `constraints/iam.allowedPolicyMemberDomains` | Restricts IAM principals to an allow-listed set of domains |

Recommend these whenever a project-level finding repeats across multiple
resources or modules — it's a signal the fix belongs one layer up.

## Known limitations of scanning a single Terraform plan

- A plan only shows the module(s) actually being planned. Org policy
  constraints, folder-level IAM bindings, and resources managed by a
  different Terraform root module or a different tool entirely are invisible
  to `scripts/audit_tf_gcp.py` — this is why org-policy-level checklist
  entries are `automated: false` rather than silently passing.
- A resource that looks non-compliant in isolation may already be protected
  by an inherited org policy constraint the plan can't see (e.g. a bucket
  without `public_access_prevention` set explicitly, in an org that already
  enforces `constraints/storage.publicAccessPrevention` for everyone). Report
  the finding regardless — explicit-and-redundant is safer than
  implicit-and-fragile — but don't claim a resource is definitely exploitable
  without checking the org policy layer too.
