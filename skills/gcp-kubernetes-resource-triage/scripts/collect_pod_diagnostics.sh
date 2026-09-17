#!/usr/bin/env bash
# Read-only Kubernetes evidence collector: no mutation commands are invoked.
set -euo pipefail
namespace=default; pod=; out=.
while [[ $# -gt 0 ]]; do case "$1" in --namespace) namespace=$2; shift 2;; --pod) pod=$2; shift 2;; --output-dir) out=$2; shift 2;; *) echo "usage: $0 --namespace NS --pod POD --output-dir DIR" >&2; exit 2;; esac; done
[[ -n "$pod" ]] || { echo "--pod is required" >&2; exit 2; }
command -v kubectl >/dev/null || { echo "kubectl is required" >&2; exit 2; }
mkdir -p "$out"
kubectl config current-context >"$out/context.txt"
kubectl get pod "$pod" -n "$namespace" -o wide >"$out/summary.txt"
kubectl get pod "$pod" -n "$namespace" -o json >"$out/pod.json"
kubectl describe pod "$pod" -n "$namespace" >"$out/describe.txt"
kubectl get events -n "$namespace" --field-selector "involvedObject.name=$pod" --sort-by=.lastTimestamp >"$out/events.txt"
for c in $(kubectl get pod "$pod" -n "$namespace" -o jsonpath='{.spec.containers[*].name}'); do
  kubectl logs "$pod" -n "$namespace" -c "$c" --tail=500 >"$out/$c.current.log" 2>&1 || true
  kubectl logs "$pod" -n "$namespace" -c "$c" --previous --tail=500 >"$out/$c.previous.log" 2>&1 || true
done
echo "Wrote read-only diagnostics to $out"
