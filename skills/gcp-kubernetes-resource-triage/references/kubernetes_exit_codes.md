# Kubernetes Container Exit Codes

| Signal | Meaning | Triage |
|---|---|---|
| `0` | Process exited normally | A Deployment may still be misconfigured for a long-running process. |
| `1` | Generic application failure | Use termination message and previous logs. |
| `126` / `127` | Not executable / command missing | Check image entrypoint, PATH, permissions, and architecture. |
| `137` | SIGKILL (128+9) | Often `OOMKilled`; confirm pod reason before changing memory. |
| `139` | SIGSEGV (128+11) | Preserve crash/log evidence and image version. |
| `143` | SIGTERM (128+15) | Often rollout/eviction; inspect events. |

Kubernetes reasons (`OOMKilled`, `Error`, `Completed`) are more reliable than
an exit code alone. `ImagePullBackOff` occurs before a container starts and
does not map to an application exit code.
