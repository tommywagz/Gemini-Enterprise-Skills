---
name: black-box-evaluation-suite-builder
description: "Builds executable black-box evaluation suites from a repository's documented interfaces, startup commands, and public behavior. TRIGGER when users request end-to-end, integration, acceptance, deployment, lifecycle, shutdown, latency, compilation, data-transfer, or agent-capability evaluations; including requests to scaffold an executable test suite. DO NOT TRIGGER for isolated white-box unit tests, implementation-level code review, or reviewing an existing test report without creating or changing a suite."
version: 1.0.0
author: Actual Agentic Solutions
tags: [black-box, integration-testing, acceptance-testing, performance, agents]
license: Apache-2.0
compatibility: "Repository-local test framework; Python 3.9+ for bundled helpers"
metadata: {}
---

# Black-Box Evaluation Suite Builder

## Overview

Create a runnable suite that judges only observable contracts at public
boundaries. Success is an isolated suite and report that distinguish a product
failure from an unavailable dependency or invalid test environment.

## Prerequisites

- The repository is available locally, including its documented commands.
- A safe local, disposable, or approved sandbox target is available for any
  stateful or externally connected interface.
- Do not put production credentials, personal data, or destructive production
  endpoints in fixtures, commands, or reports.

## Workflow

### 1. Inspect Before Designing

Read the repository's README, contribution docs, manifests, CI files, compose
or deployment files, API/CLI documentation, examples, and existing test
commands. Record components, supported features, public interfaces, startup
and health signals, configuration, dependencies, build/compile paths, and
shutdown procedures. Record assumptions and mark each inaccessible component
as skipped with its blocker; do not invent a substitute contract.

Choose assertions from an external consumer's view: process exit/status,
network response, CLI output, generated artifact, persisted state, log health
signal, or final UI state. Do not make private functions, internal tables, or
implementation call ordering the oracle.

### 2. Create the Evaluation Contract

Run `scripts/scaffold_suite.py --output <evaluation-dir>` to copy the initial
matrix and report records from `assets/coverage_matrix_template.json` and
`assets/evaluation_report_template.json`. Populate one matrix row for every
applicable component-feature pair across deployment, normal use, failure or
recovery, and shutdown. Read `references/black_box_test_design.md` when
selecting partitions, boundaries, decisions, and states.

Include positive, negative, malformed-input, permission, dependency-failure,
and repeated-run cases when the interface makes them relevant. Give each test
its own namespace, ports, temp path, database/schema, and cleanup action.
Assert setup separately from product behavior so a missing runtime, denied
credential, or unavailable service is reported as skipped or inconclusive,
not as a product regression.

### 3. Implement Lifecycle Cases

Use the repository's existing framework and commands when practical. Otherwise
add the smallest conventional black-box harness that runs public commands or
talks to published endpoints. Test startup or deployment, readiness, a normal
consumer flow, invalid and unauthorized paths, dependency loss and documented
recovery, repeated invocation, graceful shutdown, and restart/terminal-state
behavior where supported.

Make cleanup idempotent and run it on both pass and failure. Never exercise a
production deployment merely to test failure or shutdown. If a required
dependency cannot be isolated, write a reproducible mock, container, or
approved sandbox fixture; otherwise skip the case with evidence of the block.

### 4. Add Empirical Performance Cases When Measurable

Read `references/performance_methodology.md` before timing requests, transfers,
builds, or compilation. Write the hardware, OS/runtime/tool versions,
configuration, workload, warm-up, sample count, clock, raw samples, and
percentile method into the report. Establish pass thresholds from an existing
project requirement or a recorded baseline; never invent a universal latency
target.

Separate clean and incremental builds when compilation exists. Measure payload
scaling at increasing byte sizes and report latency plus throughput. For streams,
define jitter as the absolute deviation of each interarrival interval from the
median interarrival interval, then report average and maximum jitter. Run:

```text
scripts/measure_samples.py --samples latency-ms.json --arrival-times arrival-ms.json --output metrics.json
```

The helper retains raw samples and calculates nearest-rank percentiles. It marks
tail percentiles below the documented sample adequacy as inconclusive rather
than overstating a small sample.

### 5. Evaluate Agent Products by Outcomes

Only if the target includes an AI agent, read
`references/agent_capability_scenarios.md`. Build local or approved-sandbox
scenarios with a verifiable final state, valid tool/API actions, bounded turns,
and recovery after a controlled tool error or natural-language correction.
Adapt issue-resolution, multi-step/multimodal, constrained interaction,
UI-final-state, API discovery, and recovery patterns to the product. Score task
completion, safety-valid actions, recovery, and user-facing clarity, not an
exact hidden reasoning trace or prescribed action sequence.

### 6. Execute and Report

Run the documented setup, test, and cleanup commands from a clean fixture at
least twice when repeatability applies. Produce a report from
`assets/evaluation_report_template.json` with test IDs traced to matrix IDs.
Classify each result as `pass`, `fail`, `skipped`, or `inconclusive`; include
commands, evidence, environment differences, raw measurements, and untested
features. A failing assertion is `fail`; an unmet prerequisite is normally
`skipped`; insufficient data or an invalid measurement is `inconclusive`.

## Examples

### HTTP Service

Input: "Build an end-to-end suite for this API, including restart and latency."

Expected behavior: inspect the documented server command and `/health` route,
isolate a test database, test valid/invalid/unauthorized requests and restart,
measure a baseline-backed request workload, and report lifecycle coverage plus
raw latency data.

### Tool-Using Agent

Input: "Evaluate whether this agent can resolve a local fixture issue and recover
from a failed tool call."

Expected behavior: use a sandbox repository and fake tool, assert the fixed
artifact and valid calls, inject one deterministic error, accept alternate valid
paths, and report completion and recovery separately.

## Error Handling

- No documented public interface: report the gap and ask for the intended
  consumer contract rather than test internals.
- Startup cannot reach readiness: capture public diagnostics, clean up, and
  classify environment failures separately from failed product assertions.
- Flaky timing data: preserve all samples, repeat the controlled run, and mark
  a result inconclusive if conditions cannot be controlled.
- Destructive, costly, or remote operation: stop until a safe sandbox and
  explicit scope are provided.

## Reference Files

- **references/black_box_test_design.md**: partitions, boundaries, decision
  tables, state transitions, and lifecycle matrix examples.
- **references/performance_methodology.md**: reproducible timing, percentile,
  throughput, jitter, baseline, and compilation guidance.
- **references/agent_capability_scenarios.md**: outcome-based agent scenarios
  derived from the named benchmark families.
- **scripts/scaffold_suite.py**: creates an isolated matrix/report scaffold.
- **scripts/measure_samples.py**: emits reproducible latency, jitter, and
  payload metrics from JSON measurements.
- **assets/coverage_matrix_template.json**: initial machine-readable coverage
  matrix.
- **assets/evaluation_report_template.json**: initial machine-readable report.

## Output Format

Return the repository inspection summary and assumptions; matrix path and case
counts; exact runnable setup/test/cleanup commands; pass/fail/skipped/
inconclusive totals; performance method and raw-data paths; and every untested
component or feature with its reason.
