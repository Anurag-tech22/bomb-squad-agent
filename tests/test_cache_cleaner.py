"""
Test suite for Cache Cleaner MCP Server & TrueForge Safety Gates.
Verified under Qodo code quality standards.
"""

import pytest
from src.mcp_servers.cache_cleaner_server import (
    inspect_cache_health_impl,
    dry_run_remediation_impl,
    execute_eviction_impl,
    MOCK_CACHE_REGISTRY,
)


def test_inspect_cache_health_detects_poison_keys():
    """Verify that cache inspection accurately detects memory load and poisoned keys."""
    res = inspect_cache_health_impl()
    assert res["status"] in ["CRITICAL", "HEALTHY"]
    assert "total_memory_used_mb" in res
    assert "suspect_keys" in res
    assert res["poisoned_keys_detected"] >= 2


def test_dry_run_remediation_protects_user_sessions():
    """Ensure dry-run isolates leaked keys and guarantees zero impact on active sessions."""
    res = dry_run_remediation_impl("leak:*")
    assert res["safety_check_passed"] is True
    assert res["active_sessions_impacted"] == 0
    assert res["matched_keys_count"] >= 2
    assert res["requires_hitl_approval"] is True
    assert res["approval_token"] == "TF-007-EVIC-REQ"


def test_dry_run_empty_pattern_rejected():
    """Ensure invalid patterns are handled safely."""
    res = dry_run_remediation_impl("")
    assert res["safety_check_passed"] is False
    assert "INVALID_PATTERN" in res["error"]


def test_execute_eviction_fails_without_human_confirmation():
    """HITL Gate Test: Ensure execution is rejected without human confirmation."""
    res = execute_eviction_impl(
        target_pattern="leak:*",
        approval_token="TF-007-EVIC-REQ",
        human_confirmed=False,
    )
    assert res["success"] is False
    assert res["code"] == "ERR_HITL_REQUIRED"


def test_execute_eviction_fails_with_invalid_token():
    """HITL Gate Test: Ensure execution is rejected if approval token is incorrect."""
    res = execute_eviction_impl(
        target_pattern="leak:*",
        approval_token="INVALID-TOKEN",
        human_confirmed=True,
    )
    assert res["success"] is False
    assert res["code"] == "ERR_INVALID_TOKEN"


def test_execute_eviction_successful_when_authorized():
    """Verify clean eviction and state resolution when authorized with valid token."""
    res = execute_eviction_impl(
        target_pattern="leak:*",
        approval_token="TF-007-EVIC-REQ",
        human_confirmed=True,
    )
    assert res["success"] is True
    assert res["remediation_status"] == "RESOLVED"
    assert res["linear_ticket_status"] == "CLOSED"
    assert "leak:deadlock_lock_4481" in res["evicted_keys"]
    
    # Active sessions must remain intact
    assert "session:user_101" in MOCK_CACHE_REGISTRY
    assert "session:user_102" in MOCK_CACHE_REGISTRY
