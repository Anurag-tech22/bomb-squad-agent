"""
Performance, latency, and blast-radius benchmarks for the DevOps Bomb Squad Agent.

These benchmarks are intentionally conservative: all thresholds represent
worst-case acceptable latency on a single-core CI runner, not production targets.
"""

import time

from src.mcp_servers.cache_cleaner_server import (
    REQUIRED_APPROVAL_TOKEN,
    CacheHealthStatus,
    dry_run_remediation_impl,
    execute_eviction_impl,
    inspect_cache_health_impl,
)


def test_triage_latency_benchmark() -> None:
    """Benchmark: telemetry inspection must complete in under 50 ms."""
    start = time.perf_counter()
    res = inspect_cache_health_impl()
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 50.0, f"inspect_cache_health_impl too slow: {elapsed_ms:.2f} ms"
    assert res["status"] in {CacheHealthStatus.CRITICAL.value, CacheHealthStatus.HEALTHY.value}


def test_dry_run_blast_radius_zero_collateral_benchmark() -> None:
    """Benchmark: dry-run must report zero collateral damage to active sessions."""
    res = dry_run_remediation_impl("leak:*")

    assert res["active_sessions_impacted"] == 0
    assert res["safety_check_passed"] is True
    assert res["matched_keys_count"] >= 2
    assert res["memory_reclaimed_mb"] > 0.0


def test_eviction_throughput_benchmark() -> None:
    """Benchmark: authorized eviction must complete in under 50 ms."""
    start = time.perf_counter()
    res = execute_eviction_impl("leak:*", REQUIRED_APPROVAL_TOKEN, human_confirmed=True)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 50.0, f"execute_eviction_impl too slow: {elapsed_ms:.2f} ms"
    assert res["success"] is True
    assert res["remediation_status"] == "RESOLVED"
