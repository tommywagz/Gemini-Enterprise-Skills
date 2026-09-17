---
name: gcp-kubernetes-resource-triage
description: "Diagnoses failing GKE/Kubernetes workloads from read-only pod status, events, logs, container exit codes, resource settings, and Artifact Registry image-pull signals; produces reviewable remediation patch manifests without applying them. TRIGGER when users mention `CrashLoopBackOff`, `OOMKilled`, `ImagePullBackOff`, `ErrImagePull`, `CreateContainerConfigError`, a pod stuck `Pending`, or ask why a Kubernetes/GKE deployment is crashing or restarting. DO NOT TRIGGER for deploying a new Kubernetes app, modifying a healthy workload, cluster-node/network outages, or running destructive `kubectl` recovery commands."
version: 1.0.0
author: Actual Agentic Solutions
tags: [gke, kubernetes, kubectl, diagnostics, crashloopbackoff, remediation]
license: Apache-2.0
compatibility: "kubectl with read-only get/describe/log permissions to the target GKE cluster; Bash 4+"
metadata: {}
---

- GKE Workload Debugger

- Overview
This skill diagnoses a workload before attempting recovery. It collects only
read-only evidence, distinguishes image/startup/resource/scheduling failures,
and produces a targeted YAML patch for human review. It never deletes pods,
rolls a deployment, patches a live cluster, or retries blindly.

- Prerequisites
- Cluster context, namespace, and pod name (or label selector/deployment).
  Confirm context with `kubectl config current-context`.
- Read-only RBAC for pods, events, ReplicaSets, and logs. Never request
  `cluster-admin` merely to diagnose a failure.
- Run `scripts/collect_pod_diagnostics.sh`; it permits only `kubectl get`,
   `describe`, and `logs` commands.
- **Data classification: Confidential.** Pod specifications, events, and logs
  can contain customer data or secrets; store the evidence bundle locally and
  redact it before sharing.

- Workflow

- Step 1: Collect an evidence bundle
```
scripts/collect_pod_diagnostics.sh --namespace NAMESPACE --pod POD --output-dir ./pod-diagnostics
```
Review `summary.txt`, `describe.txt`, `events.txt`, and current/previous
container logs. Treat logs and pod specs as confidential. Do not run
`kubectl delete pod`, `rollout restart`, or `apply` while collecting evidence.

- Step 2: Classify the primary state
- `CrashLoopBackOff`: inspect `Last State`, exit code, termination message,
  and current plus `--previous` logs.
- `OOMKilled` / exit `137`: read `references/kubernetes_exit_codes.md`, then
  compare resource limits/requests with usage; a SIGKILL alone is not proof
  that raising a limit is safe.
- `ImagePullBackOff` / `ErrImagePull`: preserve the exact event and read
  `references/gke_registry_auth.md`; never print/decode image pull secrets.
- `Pending`: inspect `FailedScheduling`, PVC, CPU/memory, taints, affinity,
  and quota. A container that was never scheduled did not crash.
- `CreateContainerConfigError`: look for missing ConfigMap, Secret, service
  account, volume, or invalid environment reference.

- Step 3: Locate desired state and draft the smallest fix
Find the owning Deployment, Job, StatefulSet, or ReplicaSet from pod owner
references. Patch that owner, never the ephemeral pod. Copy the closest shape
from `assets/remediation_patch_template.yaml`; change only a confirmed field.
For registry auth provide IAM/binding checks, not a plaintext credential.
Never apply the draft: return it as review-only with evidence and rollback.

- Step 4: Report confidence
Return classification, exact event/exit evidence, ranked root-cause hypotheses,
review-only patch, risk/rollback, and a human verification command. Where
multiple causes remain, name the observation that distinguishes them.

- Examples

- Example 1: `OOMKilled` restart
Collect previous logs and describe/events, identify exit 137, compare
resources, and draft only the owner `resources.limits.memory` field when
evidence supports it. Warn that capacity/quota still need review.

- Example 2: Artifact Registry pull failure
For `ImagePullBackOff` after a migration, verify the event, image path/tag,
and node identity access; return non-secret IAM guidance rather than adding a
registry password to YAML.

- Error Handling
- Context mismatch: stop before collection and ask for intended cluster.
- RBAC `Forbidden`: record the denied read and request least-privilege access.
- No logs because container never started: rely on events/container state.
- Multiple containers: identify the named failing container; do not attribute
   a sidecar failure to the application.
- A referenced diagnostic guide is unavailable: do not guess an exit-code or
  registry-auth remedy. Return the collected evidence and request the matching
  versioned documentation.

- Reference Files
- **references/kubernetes_exit_codes.md**: terminated-container interpretation.
- **references/gke_registry_auth.md**: Artifact Registry/IAM pull diagnostics.
- **scripts/collect_pod_diagnostics.sh**: read-only evidence collection.
- **assets/remediation_patch_template.yaml**: review-only owner patch shapes.

- Output Format
Return classification; evidence; root-cause confidence; review-only patch;
risks/rollback; and the next human verification step.
