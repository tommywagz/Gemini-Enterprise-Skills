# GKE Artifact Registry Image-Pull Triage

For `ErrImagePull`/`ImagePullBackOff`, preserve the pod event first. Check
the `LOCATION-docker.pkg.dev/PROJECT/REPOSITORY/IMAGE:TAG` path/tag/digest,
then node service-account access to Artifact Registry Reader
(`roles/artifactregistry.reader`) in the image-hosting project. Cross-project
pulls need the grant in that hosting project.

Workload Identity governs workload API calls after start; it does not alone
replace node pull authorization. For `imagePullSecrets`, check only the
reference/name/namespace: never decode, log, or paste contents. `manifest
unknown` is a name/tag problem; `denied`/`unauthorized` is auth; timeout/DNS
events are networking, not IAM. Never embed registry passwords in manifests.
