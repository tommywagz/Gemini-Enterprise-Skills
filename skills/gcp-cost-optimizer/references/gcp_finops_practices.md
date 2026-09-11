# Google Cloud FinOps Practices

## Contents
- Where to source each inventory field
- Idle and over-provisioned Compute Engine
- Unattached disks and idle static IPs
- BigQuery: flat-rate/Editions slots vs. on-demand
- Cloud Run scaling economics
- Committed Use Discounts and Spot VMs (context for manual-review items)
- Anti-patterns: what NOT to recommend

This file grounds the rationale behind `assets/finops_checklist.json` and
`scripts/audit_gcp_costs.py`. Read it when a finding's one-line rationale
isn't enough to justify a recommendation to a workload owner, or when the
user asks "why would this save money" rather than just "what do I change."

## Where to source each inventory field

`scripts/audit_gcp_costs.py` expects the normalized inventory JSON described
in its own docstring, not a raw `gcloud` command's output. Typical mappings
from real data sources to that schema:

| Inventory field | Typical source |
|---|---|
| `compute_instances[].cpu_utilization_pct_p95` | Cloud Monitoring metric `compute.googleapis.com/instance/cpu/utilization`, or `gcloud recommender recommendations list --recommender=google.compute.instance.IdleResourceRecommender` (Recommender has already done the percentile math) |
| `persistent_disks[].attached_instances` | `gcloud compute disks list --format=json` — an empty `users` array on the raw command's output means unattached |
| `static_ips[].status` / `.users` | `gcloud compute addresses list --format=json` — `status: RESERVED` with an empty `users` array is the idle case |
| `bigquery_reservations[].avg_utilization_pct` | BigQuery reservation utilization chart in the console, or `INFORMATION_SCHEMA.JOBS_BY_PROJECT` slot-ms aggregated over the reservation's assigned projects |
| `bigquery_datasets[].long_term_storage_gb` | `bq show --format=json <dataset>` reports `numLongTermBytes` — convert bytes to GB |
| `cloud_run_services[].avg_requests_per_min` | Cloud Monitoring metric `run.googleapis.com/request_count`, averaged over the lookback window you care about (recommend at least 30 days to smooth out weekday/weekend cycles) |
| any `monthly_cost_usd` field | Cloud Billing export (BigQuery billing export table), filtered to the resource's labels/name — this is what turns a documented `waste_fraction` into an actual dollar estimate |

Prefer Recommender/Active Assist data over deriving your own thresholds from
raw metrics where available — Google's recommenders already apply
statistically sound lookback windows and percentile logic; a hand-rolled
"last 24 hours average" is a much noisier signal.

## Idle and over-provisioned Compute Engine

- A RUNNING instance billed 24/7 with p95 CPU utilization near zero over a
  meaningful lookback window (weeks, not hours — short windows catch
  legitimately bursty workloads mid-idle-period) is the single most common
  and easiest-to-fix waste pattern: dev/test boxes left running over a
  weekend, a proof-of-concept nobody tore down, a service migrated
  elsewhere but never decommissioned.
- The fix is rarely "just make it smaller" without data — recommend `gcloud
  recommender recommendations list
  --recommender=google.compute.instance.MachineTypeRecommender` for a
  rightsizing suggestion actually grounded in the instance's real usage
  history, not a guess.
- Instance schedules (start/stop on a cron-like schedule via
  `google_compute_resource_policy` with an `instance_schedule_policy`) are
  the correct fix for "only needed during business hours" workloads — much
  simpler and safer than manually stopping/starting instances.

## Unattached disks and idle static IPs

- These are the "set and forget" waste patterns: nobody actively decides to
  keep paying for them, they're just never cleaned up after the resource
  that used them was deleted, migrated, or replaced.
- A disk's `auto_delete` setting on the attaching instance controls whether
  deleting the instance also deletes the disk — many teams set this to
  `false` intentionally for data safety, then the "keep it around a bit
  longer just in case" disk quietly becomes permanent.
- Static IPs are billed while **reserved but unattached** specifically —
  Google's pricing model is structured to discourage exactly this waste
  pattern, so an idle reservation found during an audit is almost always an
  oversight, not an intentional cost.

## BigQuery: flat-rate/Editions slots vs. on-demand

- **On-demand** pricing bills per TB of data scanned by each query — good
  for unpredictable/bursty analytics workloads, bad (expensive) for
  sustained heavy query volume.
- **Flat-rate / Editions reservations** bill for committed slot capacity
  regardless of usage — good for sustained heavy query volume at a
  predictable cost, bad (wasteful) if the commitment is sized well above
  actual sustained usage.
- The break-even point depends entirely on query volume and data scanned,
  which is exactly why `GCP-COST-BQ-001` only fires on **sustained**
  low utilization (the checklist default threshold is 30% averaged over 30
  days) rather than a single low-usage day — reservations naturally have
  slack during off-peak hours by design.
- Dataset storage: BigQuery automatically discounts storage for tables
  unmodified for 90+ days (long-term storage rate) — the real waste in
  `GCP-COST-BQ-002` isn't the storage class, it's data with **no expiration
  policy at all**, silently growing forever in datasets that were only ever
  meant to hold recent data (staging, logs, scratch tables).

## Cloud Run scaling economics

- `min_instances > 0` is a deliberate cost-for-latency trade: it keeps that
  many instances warm continuously, billed whether or not they're serving
  traffic, specifically to avoid cold-start latency on the next request.
  That trade only pays for itself if the service actually receives enough
  traffic (or has a strict-enough latency SLA) to justify it.
- `concurrency` controls how many requests one instance serves
  simultaneously, sharing that instance's allocated CPU/memory. Leaving
  `concurrency = 1` on a multi-vCPU instance means the extra vCPU is
  provisioned (and billed) but structurally idle unless the handler itself
  spawns worker threads to use it — this is very often just the Cloud Run
  default carried over unexamined, not a deliberate choice.

## Committed Use Discounts and Spot VMs (context for manual-review items)

- **Committed Use Discounts (CUDs)**: discount steady-state compute spend in
  exchange for a 1- or 3-year commitment (resource-based, tied to a specific
  machine family/region, or the more flexible spend-based Flexible CUDs).
  Sizing a commitment requires a stable historical usage trend — this is
  why `GCP-COST-CUD-001` is `automated: false` in the checklist: a
  point-in-time inventory snapshot cannot show 6-12 months of trend on its
  own. Point the user at `gcloud recommender recommendations list
  --recommender=google.compute.commitment.UsageCommitmentRecommender`, which
  is already trend-aware, instead of sizing a commitment off this script's
  output alone.
- **Spot VMs**: discounted heavily off on-demand price in exchange for
  possible preemption with short notice. Genuinely fault-tolerant, batch, or
  stateless-and-restartable workloads are excellent candidates; anything
  stateful or latency-sensitive is not, regardless of how much a label
  suggests otherwise — `GCP-COST-COMPUTE-002` treats a `batch`/
  `fault-tolerant`-looking label as a signal to *investigate*, never as
  sufficient confirmation on its own to migrate.

## Anti-patterns: what NOT to recommend

- Don't recommend stopping, deleting, or resizing anything based on a single
  point-in-time snapshot without a documented lookback window — a workload
  idle for one hour during a holiday is not the same finding as one idle for
  30 sustained days.
- Don't quote a specific dollar savings figure that wasn't computed from a
  `monthly_cost_usd` value actually present in the inventory input — see the
  script's own guardrail against fabricating prices.
- Don't suggest Spot VMs, aggressive `min_instances` reduction, or disk
  deletion as a default action — every one of these requires the workload
  owner's confirmation that the specific tradeoff (preemption risk, cold
  starts, data loss) is acceptable for that specific resource.
