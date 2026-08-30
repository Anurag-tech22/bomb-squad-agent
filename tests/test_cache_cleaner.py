"""
Comprehensive Unit & Invariant Test Suite for Autonomous DevOps Bomb Squad Agent.
Adheres to Qodo AI and Google/NVIDIA code quality and testing standards.
"""

import threading
import pytest
from src.mcp_servers.cache_cleaner_server import (
    inspect_cache_health_impl,
    dry_run_remediation_impl,
    execute_eviction_impl,
    MOCK_CACHE_REGISTRY,
    REQUIRED_APPROVAL_TOKEN,
    CacheHealthStatus,
    KeyType,
)


class TestCacheInspection:
    """Test suite validating cache telemetry and health inspection invariants."""

    def test_inspect_cache_health_schema_and_metrics(self):
        """Verify that cache inspection returns compliant telemetry adhering to schema."""
        res = inspect_cache_health_impl()
        assert res["status"] in [CacheHealthStatus.CRITICAL.value, CacheHealthStatus.HEALTHY.value]
        assert "total_memory_used_mb" in res
        assert "suspect_keys" in res
        assert res["poisoned_keys_detected"] >= 2
        assert res["total_keys"] == len(MOCK_CACHE_REGISTRY)

    def test_inspect_cache_health_is_read_only(self):
        """Invariant-01: Ensure telemetry queries have zero side effects on state."""
        before_state = dict(MOCK_CACHE_REGISTRY)
        _ = inspect_cache_health_impl()
        assert MOCK_CACHE_REGISTRY == before_state


class TestSandboxDryRun:
    """Test suite validating Daytona Sandbox dry-run calculations & safety gates."""

    def test_dry_run_isolates_and_protects_user_sessions(self):
        """Invariant-03: Ensure dry run guarantees 0% collateral disruption to active sessions."""
        res = dry_run_remediation_impl("leak:*")
        assert res["safety_check_passed"] is True
        assert res["active_sessions_impacted"] == 0
        assert res["matched_keys_count"] >= 2
        assert res["requires_hitl_approval"] is True
        assert res["approval_token"] == REQUIRED_APPROVAL_TOKEN
        assert res["memory_reclaimed_mb"] > 0.0

    def test_dry_run_empty_pattern_rejected(self):
        """Ensure empty or whitespace-only patterns are rejected safely."""
        res = dry_run_remediation_impl("")
        assert res["safety_check_passed"] is False
        assert "INVALID_PATTERN" in res["error"]

    def test_dry_run_wildcard_session_collision_detection(self):
        """Ensure full wildcard pattern (*) properly flags active user session disruption."""
        res = dry_run_remediation_impl("*")
        assert res["active_sessions_impacted"] >= 3
        # Active sessions are detected and excluded from safe evict list
        for key in res["keys_to_evict"]:
            assert not key.startswith("session:")


class TestHITLApprovalGates:
    """Test suite validating cryptographic Human-in-the-Loop approval gate invariants."""

    def test_eviction_strictly_fails_without_human_confirmation(self):
        """Invariant-04: State mutation must fail deterministically if human_confirmed is False."""
        res = execute_eviction_impl(
            target_pattern="leak:*",
            approval_token=REQUIRED_APPROVAL_TOKEN,
            human_confirmed=False,
        )
        assert res["success"] is False
        assert res["code"] == "ERR_HITL_REQUIRED"
        assert res["remediation_status"] == "ABORTED"

    def test_eviction_strictly_fails_with_invalid_token(self):
        """Invariant-04: State mutation must fail if authorization token does not match."""
        res = execute_eviction_impl(
            target_pattern="leak:*",
            approval_token="MALICIOUS_OR_EXPIRED_TOKEN",
            human_confirmed=True,
        )
        assert res["success"] is False
        assert res["code"] == "ERR_INVALID_TOKEN"
        assert res["remediation_status"] == "UNAUTHORIZED"

    def test_eviction_executes_successfully_when_authorized(self):
        """Verify clean eviction and state reconciliation when authorized by operator."""
        res = execute_eviction_impl(
            target_pattern="leak:*",
            approval_token=REQUIRED_APPROVAL_TOKEN,
            human_confirmed=True,
        )
        assert res["success"] is True
        assert res["remediation_status"] == "RESOLVED"
        assert res["linear_ticket_status"] == "CLOSED"
        assert "leak:deadlock_lock_4481" in res["evicted_keys"]

        # Active user sessions must remain intact in the live registry
        assert "session:user_101" in MOCK_CACHE_REGISTRY
        assert "session:user_102" in MOCK_CACHE_REGISTRY
        assert "session:user_103" in MOCK_CACHE_REGISTRY


class TestConcurrencyAndThreadSafety:
    """Test suite validating thread-safe state access under concurrent operations."""

    def test_concurrent_inspection_and_dry_run(self):
        """Ensure simultaneous thread execution does not raise race conditions."""
        errors = []

        def worker():
            try:
                for _ in range(50):
                    inspect_cache_health_impl()
                    dry_run_remediation_impl("leak:*")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
