# Workload Identity Federation Instead Of Downloadable Keys

Federation exchanges an external identity assertion for short-lived Google
credentials; it avoids a long-lived service-account key stored in CI. Build a
Workload Identity Pool and OIDC/SAML provider, restrict issuer/audience and
attribute mapping, then bind only approved principal attributes to service
account impersonation (`roles/iam.workloadIdentityUser`). For GKE, use GKE
Workload Identity to bind a Kubernetes service account to a Google service
account, and separately apply namespace RBAC.

Migration order: inventory key users; create restricted federation in a
non-production project; test token exchange and required API calls; deploy
with monitoring; retain a time-limited rollback; then disable/delete the old
user-managed key through the authorized key-rotation process. Never copy a
private key into Terraform, source control, logs, or ticket comments.
