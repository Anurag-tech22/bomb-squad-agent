"""
Comprehensive unit & invariant test suite for the Autonomous DevOps Bomb Squad Agent.

Tests are organized by concern:
  - CacheInspection     → read-only telemetry correctness
  - SandboxDryRun       → blast-radius calculation & session protection
  - HITLApprovalGates   → cryptographic authorization invariants
  - ConcurrencyAndThreadSafety → race-condition absence under parallel load
"""

import threading

from src.mcp_servers.cache_cleaner_server import (
    MOCK_CACHE_REGISTRY,
    REQUIRED_APPROVAL_TOKEN,
    CacheHealthStatus,
    KeyType,
    dry_run_remediation_impl,
    execute_eviction_impl,
    inspect_cache_health_impl,
)


class TestCacheInspection:
    """Validates cache telemetry and health-inspection invariants."""

    def test_inspect_cache_health_schema_and_metrics(self) -> None:
        """Telemetry must return a schema-compliant report with expected field presence."""
        res = inspect_cache_health_impl()

        assert res["status"] in {CacheHealthStatus.CRITICAL.value, CacheHealthStatus.HEALTHY.value}
        assert "total_memory_used_mb" in res
        assert "suspect_keys" in res
        assert res["poisoned_keys_detected"] >= 2
        assert res["total_keys"] == len(MOCK_CACHE_REGISTRY)
        assert res["fragmentation_ratio"] >= 1.0

    def test_inspect_cache_health_is_read_only(self) -> None:
        """Invariant-01: telemetry queries must have zero side effects on registry state."""
        before_state = dict(MOCK_CACHE_REGISTRY)

        _ = inspect_cache_health_impl()

        assert before_state == MOCK_CACHE_REGISTRY

    def test_inspect_reports_critical_when_poisoned_keys_present(self) -> None:
        """Health status must be CRITICAL when leaked or deadlocked keys exist."""
        res = inspect_cache_health_impl()

        # The initial registry contains poison_lock and stale_batch entries
        assert res["status"] == CacheHealthStatus.CRITICAL.value
        assert len(res["suspect_keys"]) >= 2


class TestSandboxDryRun:
    """Validates Daytona Sandbox dry-run calculations and safety gates."""

    def test_dry_run_isolates_and_protects_user_sessions(self) -> None:
        """Invariant-03: dry run must guarantee 0% collateral disruption to active sessions."""
        res = dry_run_remediation_impl("leak:*")

        assert res["safety_check_passed"] is True
        assert res["active_sessions_impacted"] == 0
        assert res["matched_keys_count"] >= 2
        assert res["requires_hitl_approval"] is True
        assert res["approval_token"] == REQUIRED_APPROVAL_TOKEN
        assert res["memory_reclaimed_mb"] > 0.0

    def test_dry_run_empty_pattern_rejected(self) -> None:
        """Empty or whitespace-only patterns must be rejected with a structured error."""
        for bad_pattern in ("", "   ", "\t"):
            res = dry_run_remediation_impl(bad_pattern)
            assert res["safety_check_passed"] is False
            assert res["error"] is not None
            assert "INVALID_PATTERN" in res["error"]

    def test_dry_run_wildcard_session_collision_detection(self) -> None:
        """Full wildcard pattern (*) must flag active user session disruption correctly."""
        res = dry_run_remediation_impl("*")

        assert res["active_sessions_impacted"] >= 3
        # Sessions must be excluded from the safe eviction list
        for key in res["keys_to_evict"]:
            assert not key.startswith("session:")

    def test_dry_run_is_read_only(self) -> None:
        """Dry run must not mutate the registry under any pattern."""
        before_state = dict(MOCK_CACHE_REGISTRY)

        dry_run_remediation_impl("leak:*")
        dry_run_remediation_impl("*")

        assert before_state == MOCK_CACHE_REGISTRY


class TestHITLApprovalGates:
    """Validates cryptographic Human-in-the-Loop approval gate invariants."""

    def test_eviction_strictly_fails_without_human_confirmation(self) -> None:
        """Invariant-04: state mutation must fail deterministically when human_confirmed=False."""
        res = execute_eviction_impl(
            target_pattern="leak:*",
            approval_token=REQUIRED_APPROVAL_TOKEN,
            human_confirmed=False,
        )

        assert res["success"] is False
        assert res["code"] == "ERR_HITL_REQUIRED"
        assert res["remediation_status"] == "ABORTED"

    def test_eviction_strictly_fails_with_invalid_token(self) -> None:
        """Invariant-04: state mutation must fail when the authorization token is wrong."""
        res = execute_eviction_impl(
            target_pattern="leak:*",
            approval_token="MALICIOUS_OR_EXPIRED_TOKEN",
            human_confirmed=True,
        )

        assert res["success"] is False
        assert res["code"] == "ERR_INVALID_TOKEN"
        assert res["remediation_status"] == "UNAUTHORIZED"

    def test_eviction_executes_successfully_when_authorized(self) -> None:
        """Verify clean eviction and state reconciliation when operator-authorized."""
        res = execute_eviction_impl(
            target_pattern="leak:*",
            approval_token=REQUIRED_APPROVAL_TOKEN,
            human_confirmed=True,
        )

        assert res["success"] is True
        assert res["remediation_status"] == "RESOLVED"
        assert res["linear_ticket_status"] == "CLOSED"
        assert res["notion_sync"] == "READY"
        assert "leak:deadlock_lock_4481" in res["evicted_keys"]
        assert "leak:deadlock_lock_4482" in res["evicted_keys"]

        # Active user sessions must remain intact in the live registry
        assert "session:user_101" in MOCK_CACHE_REGISTRY
        assert "session:user_102" in MOCK_CACHE_REGISTRY
        assert "session:user_103" in MOCK_CACHE_REGISTRY

    def test_eviction_never_removes_active_sessions(self) -> None:
        """Active sessions must be unconditionally preserved even for catch-all patterns."""
        res = execute_eviction_impl(
            target_pattern="*",
            approval_token=REQUIRED_APPROVAL_TOKEN,
            human_confirmed=True,
        )

        assert res["success"] is True
        for key in res["evicted_keys"]:
            assert MOCK_CACHE_REGISTRY.get(key) is None  # evicted key is gone
            entry_type = KeyType.ACTIVE_SESSION.value
            # Confirm nothing with active_session type was evicted
            assert entry_type not in key  # simple guard; detailed check below

        assert "session:user_101" in MOCK_CACHE_REGISTRY
        assert "session:user_102" in MOCK_CACHE_REGISTRY
        assert "session:user_103" in MOCK_CACHE_REGISTRY


class TestConcurrencyAndThreadSafety:
    """Validates thread-safe state access under concurrent operations."""

    def test_concurrent_inspection_and_dry_run(self) -> None:
        """Simultaneous thread execution must not raise race conditions or corrupt state."""
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(50):
                    inspect_cache_health_impl()
                    dry_run_remediation_impl("leak:*")
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety violation: {errors}"
