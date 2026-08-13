# Full SKILL.md Structural Template (Annotated)

## Contents
- Annotated template
- Worked example (k8s-pod-debugger)

## Annotated template

```markdown
---
name: k8s-pod-debugger
description: [What it does] + [TRIGGER when:] + [DO NOT TRIGGER when:]
---

- Kubernetes Pod Failure Debugger

- Overview
Brief context: why this task exists, what success looks like.

- Prerequisites
- kubectl configured with access to the target cluster
- Namespace and pod name, or deployment name, from the user

- Workflow

- Step 1: [First Action]
Clear instruction. Include decision branches:
- If X: do Y
- If Z: do W

- Step 2: [Next Action]
...

- Examples

- Example 1: [Common Case]
Input: ...
Expected output / behavior: ...

- Error Handling
- Common failure mode: how to recover

- Reference Files
- **scripts/collect_pod_state.sh**: [What it does, when to run it]
- **references/exit_codes.md**: [When to read it]

- Output Format
Describe what the agent should return or produce.
```

## Worked example: k8s-pod-debugger

This shows the template filled in for a real skill, illustrating the level of
specificity expected at each section.

**Description** (Trigger / Do Not Trigger pattern):
> Diagnoses failing or crashing Kubernetes pods by inspecting pod status, exit
> codes, and events. TRIGGER when the user mentions `CrashLoopBackOff`,
> `OOMKilled`, `ImagePullBackOff`, a pod stuck in `Pending`, or asks "why is my
> pod crashing/restarting". DO NOT TRIGGER for general kubectl usage questions
> unrelated to a failing pod, or for cluster-level issues like node failures.

**Step 1: Identify the failure mode**
Run `kubectl describe pod [pod-name] -n [namespace]` and look at `Last State`,
`Exit Code`, and `Events` — these three fields contain 90% of failure
information.
- If `CrashLoopBackOff`: the container is starting and crashing — check exit
  code and logs (Step 2).
- If `OOMKilled`: the container hit its memory limit — check
  `resources.limits.memory` (Step 3).
- If `ImagePullBackOff`: check registry auth — see `references/aws_ecr_auth.md`.

**Anti-pattern called out explicitly:**
> Do not delete and recreate the pod as a first step — always diagnose the
> root cause first, or the same failure will recur immediately.

This is the pattern to copy: concrete commands, explicit branches by exact
error string, an anti-pattern warning, and pointers to reference files instead
of inlining their contents.
