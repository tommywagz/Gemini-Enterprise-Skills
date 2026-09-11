# GCP Machine Types, Storage Tiers, and Pricing Models (Conceptual Reference)

## Contents
- Why this file has no $/unit numbers
- Compute Engine machine type families
- Discount mechanisms compared
- Persistent disk types
- BigQuery pricing models
- Cloud Run billing dimensions

## Why this file has no $/unit numbers

GCP pricing changes over time and varies by region, committed term, and
negotiated discounts (enterprise agreements, reseller pricing). Hardcoding a
`$/vCPU-hour` or `$/GB-month` figure here would go stale and could actively
mislead a savings estimate. Instead:

- `scripts/audit_gcp_costs.py` only computes a dollar estimate when the
  inventory input itself supplies `monthly_cost_usd` (sourced from the
  user's actual Cloud Billing export), multiplied by a checklist-documented
  `waste_fraction` — an estimate derived from the user's own real spend, not
  a lookup table here.
- For an authoritative current rate, use the [Google Cloud Pricing
  Calculator](https://cloud.google.com/products/calculator) or the Cloud
  Billing Catalog API — never state a specific current price to a user from
  memory.

This file instead covers the *mechanics* each pricing model uses, which is
stable even as the numbers change, so a recommendation can be explained
correctly regardless of current rates.

## Compute Engine machine type families

| Family | Optimized for | Notes |
|---|---|---|
| E2 | Cost | Shared-core options available for very light workloads; no sustained-use discount needed since it already prices near the sustained-use-discounted rate of other families |
| N2 / N2D | General purpose | Broadest general-purpose choice; N2D runs on AMD, typically priced slightly lower than N2 for similar performance |
| C2 / C3 | Compute-optimized | Highest per-core performance; not the right fix for an "idle" finding — idle instances need scheduling or downsizing, not a faster machine type |
| M2 / M3 | Memory-optimized | Very large RAM; check for over-provisioning if `cpu_utilization_pct_p95` is low but memory pressure is the actual reason for the machine type |
| A2 / A3 | Accelerator-optimized (GPU) | Rightsizing here means matching GPU count/type to the actual model workload, not general CPU rightsizing logic |

A `MachineTypeRecommender` suggestion from Recommender already accounts for
family-appropriate sizing — prefer it over manually picking a different
family based on this table alone.

## Discount mechanisms compared

| Mechanism | Commitment | Discount applies to | Risk if wrong |
|---|---|---|---|
| Sustained Use Discount | None — automatic | Certain machine types, scales with % of month instance ran | None — it's automatic, not a decision point for this skill |
| Committed Use Discount (resource-based) | 1 or 3 years, specific machine family + region | That specific resource shape | Paying for committed capacity you stop using before the term ends |
| Committed Use Discount (Flexible / spend-based) | 1 or 3 years, a spend commitment | Any eligible compute spend across a broader scope | Less risky than resource-based CUDs but still a multi-year spend floor |
| Spot VM discount | None — per-instance choice, can be preempted anytime | The specific Spot-provisioned instance | Workload interruption; wrong choice for stateful/latency-sensitive services |

`GCP-COST-CUD-001` in the checklist is deliberately `automated: false`
because choosing *which* commitment mechanism and size is a multi-month
trend decision, not something a point-in-time inventory can respond to
safely — see `references/gcp_finops_practices.md` for the recommended
data-driven path (Recommender's `UsageCommitmentRecommender`).

## Persistent disk types

| Type | Typical use case | Relative cost |
|---|---|---|
| pd-standard | Sequential-access, low-IOPS workloads (backups, batch) | Lowest |
| pd-balanced | General-purpose default for most VMs | Low-medium |
| pd-ssd | High-IOPS random-access workloads (databases) | Medium-high |
| pd-extreme | Very high, provisioned-IOPS workloads | Highest, IOPS provisioned separately from size |
| Hyperdisk (Balanced/Extreme/Throughput) | Newer generation, independently provisioned capacity/IOPS/throughput | Varies — check current docs, this family is still expanding |

`GCP-COST-DISK-002` treats pd-ssd as advisory-only precisely because some
workloads (transactional databases, workloads with real random-write IOPS
needs) genuinely need it — the checklist's `waste_fraction` for this rule is
intentionally the lowest of the automated checks, reflecting lower
confidence.

## BigQuery pricing models

| Model | Billed on | Best fit |
|---|---|---|
| On-demand | Bytes scanned per query | Unpredictable, bursty, or low-volume analytics |
| Flat-rate (legacy) / Editions (Standard, Enterprise, Enterprise Plus) | Committed or autoscaling slot capacity | Sustained, predictable heavy query volume |
| Storage: active | Bytes stored, tables modified in the last 90 days | N/A — automatic, not a plan choice |
| Storage: long-term | Bytes stored, tables untouched 90+ days | Automatic discount vs. active rate — the real lever is expiration, not storage class, per `GCP-COST-BQ-002` |

Editions reservations also support autoscaling (baseline + autoscale slots),
which can reduce the under-utilization problem `GCP-COST-BQ-001` flags by
letting capacity shrink during off-peak hours automatically — worth
mentioning as an alternative to a flat resize when discussing that finding
with a user.

## Cloud Run billing dimensions

Cloud Run (and Cloud Run functions on the 2nd-gen execution environment)
bills primarily on:

- **CPU and memory allocated per instance**, for the time an instance is
  active (or continuously, if `cpu_idle` / "CPU always allocated" is
  configured instead of the request-based default).
- **Number of instances kept warm** (`min_instances`), each billed as if
  actively running regardless of request volume — this is the dimension
  `GCP-COST-RUN-001` targets.
- **Requests served**, a much smaller per-request fee on top of the above.

`concurrency` doesn't change the per-instance bill directly — it changes how
many requests share one billed instance's CPU/memory, which is why a
mismatched `concurrency = 1` on a multi-vCPU instance (`GCP-COST-RUN-002`)
is wasted *capacity*, not a separate line item.
