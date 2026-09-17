# Predefined Role Mapping

| Broad role / need | Prefer | Scope |
|---|---|---|
| `roles/editor` object read/write | `roles/storage.objectAdmin` | Bucket where possible |
| GCS read only | `roles/storage.objectViewer` | Bucket/project |
| Compute instance operations | `roles/compute.instanceAdmin.v1` plus only required service-account-user permission | Project/resource |
| Cloud SQL application connection | `roles/cloudsql.client` | Project holding the instance |
| GKE workload read operations | `roles/container.viewer` plus Kubernetes RBAC | Project plus namespace RBAC |
| Artifact pull/push | `roles/artifactregistry.reader` / `roles/artifactregistry.writer` | Repository |

Predefined roles change over time; verify their current permissions before a
production migration. Use custom roles only for demonstrated gaps, avoid
wildcards, version them, and review at least annually. Preserve Google-managed
service-agent roles unless the owning service documents their replacement.
