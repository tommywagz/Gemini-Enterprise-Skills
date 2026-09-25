#!/usr/bin/env python3
"""Calculate reproducible percentile and jitter summaries from JSON arrays."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median


def read_numbers(path: Path) -> list[float]:
    values = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(values, list) or not values:
        raise ValueError(f"{path} must contain a non-empty JSON array")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError(f"{path} must contain only numbers")
    numbers = [float(value) for value in values]
    if any(not math.isfinite(value) for value in numbers):
        raise ValueError(f"{path} must contain only finite numbers")
    return numbers


def nearest_rank(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize latency and optional stream arrivals.")
    parser.add_argument("--samples", required=True, type=Path, help="JSON array of latency values")
    parser.add_argument("--arrival-times", type=Path, help="JSON array of monotonic arrival times")
    parser.add_argument("--payload-bytes", type=int, help="Bytes transferred per sample; samples must be positive milliseconds")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    samples = read_numbers(args.samples)
    if any(sample < 0 for sample in samples):
        raise ValueError("latency samples must be non-negative")
    if args.payload_bytes is not None and (args.payload_bytes <= 0 or any(sample <= 0 for sample in samples)):
        raise ValueError("payload bytes and transfer latencies must be positive")
    result: dict[str, object] = {
        "percentile_method": "nearest-rank: sorted[ceil(p*n)-1], zero-based",
        "raw_samples": samples,
        "sample_count": len(samples),
        "latency": {
            "median": median(samples),
            "p90": nearest_rank(samples, 0.90),
            "p99": nearest_rank(samples, 0.99),
            "p99_99": nearest_rank(samples, 0.9999),
            "p99_status": "inconclusive" if len(samples) < 100 else "reported",
            "p99_99_status": "inconclusive" if len(samples) < 10000 else "reported",
        },
    }
    if args.payload_bytes is not None:
        throughput = [args.payload_bytes * 1000 / sample for sample in samples]
        result["transfer"] = {
            "payload_bytes": args.payload_bytes,
            "method": "payload bytes divided by each measured transfer latency in seconds",
            "raw_bytes_per_second": throughput,
            "median_bytes_per_second": median(throughput),
        }
    if args.arrival_times:
        arrivals = read_numbers(args.arrival_times)
        if len(arrivals) < 2:
            raise ValueError("arrival times require at least two values")
        intervals = [later - earlier for earlier, later in zip(arrivals, arrivals[1:])]
        if any(interval <= 0 for interval in intervals):
            raise ValueError("arrival times must be strictly increasing")
        baseline = median(intervals)
        jitter = [abs(interval - baseline) for interval in intervals]
        result["jitter"] = {
            "definition": "absolute deviation from median interarrival interval",
            "raw_arrival_times": arrivals,
            "median_interarrival": baseline,
            "average": sum(jitter) / len(jitter),
            "maximum": max(jitter),
        }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
