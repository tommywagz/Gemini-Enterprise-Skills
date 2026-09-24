# Empirical Performance Methodology

## Source

SPEC CPU 2017 Run and Reporting Rules:
https://www.spec.org/cpu2017/Docs/runrules.html

## Reproducible Observation

Treat a benchmark result as an observation under stated conditions. Capture CPU
and memory model, operating system, kernel, runtime/compiler and dependency
versions, power/performance settings, command line, configuration, data set,
network topology, clock source, warm-up method, sample count, and start/end
time. Identify uncontrolled load and any deviation from the baseline run.

Use representative workloads and preserve the unrounded raw measurements. Make
the percentile rule explicit: for sorted `n` samples, nearest-rank percentile
`p` is the value at zero-based index `ceil(p * n) - 1`, bounded to the sample
range. Report median and P90; label P99 inconclusive below 100 samples and
P99.99 inconclusive below 10,000 samples (fewer than one expected observation
in the respective tail). Record stronger project-specific adequacy rules when
they exist. The helper assumes millisecond samples; it reports transfer
throughput when `--payload-bytes` is provided, one measured transfer per sample.

## Workload Dimensions

Warm the service or runtime before timed trials, keeping warm-up samples out of
the result. Use repeated trials with the same request mix and controlled
concurrency. Test payload scaling with increasing byte sizes relevant to the
documented limit; for each size report payload bytes, samples, latency, and
throughput `payload_bytes / elapsed_seconds`.

For event streams, record arrivals in one monotonic-clock unit. Define an
interval as `arrival[i] - arrival[i-1]`; define jitter as the absolute interval
deviation from the median interval. Report average and maximum jitter alongside
the raw arrival timestamps.

Measure clean compilation after removing documented build outputs and incremental
compilation after a minimal source change. State exactly what was removed or
changed. Compare to a pre-existing requirement or recorded baseline, not a
generic performance number. If no threshold exists, report the observation
without a pass/fail claim.

## Result States

Use `pass` only when a named requirement or baseline gate is met. Use `fail`
when a valid measurement violates that gate. Use `skipped` when the applicable
operation cannot run. Use `inconclusive` when conditions, sample adequacy, or
measurement validity prevent a defensible comparison.
