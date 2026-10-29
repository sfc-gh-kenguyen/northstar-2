#!/usr/bin/env python3
"""Lightweight stress test for Northstar Streamlit Community Cloud mirrors.

Simulates many independent browser sessions by opening each mirror URL with a
fresh HTTP client (follows redirects). This does not fully reproduce Streamlit
WebSocket reruns, but it does stress initial session setup and catches mirrors
that fail, time out, or hit resource limits under concurrent load.

Usage:
  python scripts/load_test_mirrors.py
  python scripts/load_test_mirrors.py --users-per-mirror 30 --rounds 2
  python scripts/load_test_mirrors.py --urls https://northstar3.streamlit.app
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Iterable

import requests

DEFAULT_MIRRORS = (
    "https://northstar.streamlit.app",
    "https://northstar2.streamlit.app",
    "https://northstar3.streamlit.app",
    "https://northstar4.streamlit.app",
    "https://northstar5.streamlit.app",
    "https://northstar6.streamlit.app",
)

FAIL_PATTERNS = (
    "resource limits",
    "gone over its resource",
    "something went wrong",
    "unable to load",
    "502 bad gateway",
    "503 service unavailable",
)


@dataclass
class RequestResult:
    mirror: str
    ok: bool
    status_code: int | None
    elapsed_sec: float
    error: str | None = None
    hint: str | None = None


@dataclass
class MirrorSummary:
    mirror: str
    total: int = 0
    ok: int = 0
    failed: int = 0
    latencies_sec: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def record(self, result: RequestResult) -> None:
        self.total += 1
        if result.ok:
            self.ok += 1
            self.latencies_sec.append(result.elapsed_sec)
        else:
            self.failed += 1
            msg = result.error or result.hint or f"HTTP {result.status_code}"
            self.errors.append(msg)


def _one_request(mirror: str, timeout: float) -> RequestResult:
    started = time.perf_counter()
    try:
        with requests.Session() as session:
            session.headers.update(
                {
                    "User-Agent": (
                        "NorthstarLoadTest/1.0 (+https://github.com/sfc-gh-kenguyen/northstar)"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                }
            )
            resp = session.get(mirror, timeout=timeout, allow_redirects=True)
            elapsed = time.perf_counter() - started
            body_lower = (resp.text or "").lower()
            hint = next((p for p in FAIL_PATTERNS if p in body_lower), None)
            ok = resp.status_code == 200 and hint is None
            return RequestResult(
                mirror=mirror,
                ok=ok,
                status_code=resp.status_code,
                elapsed_sec=elapsed,
                hint=hint,
            )
    except requests.RequestException as exc:
        return RequestResult(
            mirror=mirror,
            ok=False,
            status_code=None,
            elapsed_sec=time.perf_counter() - started,
            error=str(exc),
        )


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[idx]


def _run_round(
    mirrors: Iterable[str],
    users_per_mirror: int,
    timeout: float,
    workers: int,
) -> list[RequestResult]:
    jobs = [m for m in mirrors for _ in range(users_per_mirror)]
    results: list[RequestResult] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one_request, mirror, timeout) for mirror in jobs]
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def _summarize(results: list[RequestResult]) -> dict[str, MirrorSummary]:
    out: dict[str, MirrorSummary] = {}
    for result in results:
        summary = out.setdefault(result.mirror, MirrorSummary(mirror=result.mirror))
        summary.record(result)
    return out


def _print_summary(label: str, summaries: dict[str, MirrorSummary]) -> None:
    print(f"\n=== {label} ===")
    for mirror in sorted(summaries):
        s = summaries[mirror]
        lat = s.latencies_sec
        print(f"\n{mirror}")
        print(f"  requests: {s.total}  ok: {s.ok}  failed: {s.failed}")
        if lat:
            print(
                f"  latency (ok): min {min(lat):.2f}s  p50 {_percentile(lat, 50):.2f}s  "
                f"p95 {_percentile(lat, 95):.2f}s  max {max(lat):.2f}s"
            )
        if s.errors:
            unique = sorted(set(s.errors))
            shown = unique[:5]
            print(f"  errors: {', '.join(shown)}")
            if len(unique) > 5:
                print(f"  ... and {len(unique) - 5} more")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stress-test Northstar Streamlit mirrors.")
    parser.add_argument(
        "--urls",
        nargs="+",
        default=list(DEFAULT_MIRRORS),
        help="Mirror base URLs to test (default: all four Northstar mirrors).",
    )
    parser.add_argument(
        "--users-per-mirror",
        type=int,
        default=20,
        help="Concurrent fresh sessions per mirror per round (default: 20).",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="How many back-to-back rounds to run (default: 1).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Thread pool size (default: users_per_mirror * number of mirrors).",
    )
    args = parser.parse_args(argv)

    mirrors = list(args.urls)
    workers = args.workers or max(1, args.users_per_mirror * len(mirrors))
    total_requests = args.users_per_mirror * len(mirrors) * args.rounds

    print("Northstar mirror load test")
    print(f"  mirrors: {len(mirrors)}")
    print(f"  users per mirror per round: {args.users_per_mirror}")
    print(f"  rounds: {args.rounds}")
    print(f"  total requests: {total_requests}")
    print(f"  workers: {workers}")
    print(f"  timeout: {args.timeout}s")
    print("\nNote: this tests initial page load, not Streamlit widget reruns.")

    all_results: list[RequestResult] = []
    for round_idx in range(1, args.rounds + 1):
        print(f"\nStarting round {round_idx}/{args.rounds}...")
        started = time.perf_counter()
        round_results = _run_round(mirrors, args.users_per_mirror, args.timeout, workers)
        elapsed = time.perf_counter() - started
        all_results.extend(round_results)
        _print_summary(f"Round {round_idx} ({elapsed:.1f}s wall)", _summarize(round_results))

    overall = _summarize(all_results)
    _print_summary("Overall", overall)

    total_ok = sum(s.ok for s in overall.values())
    total_failed = sum(s.failed for s in overall.values())
    print(f"\nDone: {total_ok} ok, {total_failed} failed out of {total_requests} requests.")
    if total_failed:
        print("Some mirrors struggled under this load. Consider lowering per-mirror traffic at the event.")
        return 1
    print("All mirrors returned HTTP 200 with no obvious resource-limit page text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
