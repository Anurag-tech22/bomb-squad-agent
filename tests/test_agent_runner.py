"""
Unit tests for TrueForge Agent Harness Runtime Engine (src/agent_runner.py).
"""

from __future__ import annotations

import pytest

from src.agent_runner import TrueForgeHarnessRuntime, main


class TestAgentRunner:
    """Test suite for TrueForge harness lifecycle and runtime execution."""

    def test_runtime_initialization(self) -> None:
        """Verify runtime initialization loads config and generates session ID."""
        runtime = TrueForgeHarnessRuntime()
        assert runtime.config is not None
        assert runtime.session_id.startswith("TF-SESSION-")

    def test_full_incident_remediation_lifecycle_success(self) -> None:
        """Verify successful end-to-end 5-phase incident remediation."""
        runtime = TrueForgeHarnessRuntime()
        res = runtime.run_incident_remediation_lifecycle(
            target_pattern="leak:*",
            simulate_human_approval=True,
        )
        assert res["success"] is True
        assert "session_id" in res
        assert res["eviction"]["success"] is True
        assert res["eviction"]["remediation_status"] == "RESOLVED"

    def test_incident_lifecycle_hitl_rejection(self) -> None:
        """Verify lifecycle halts when human approval is rejected."""
        runtime = TrueForgeHarnessRuntime()
        res = runtime.run_incident_remediation_lifecycle(
            target_pattern="leak:*",
            simulate_human_approval=False,
        )
        assert res["success"] is False
        assert res["phase"] == "hitl_gate"
        assert res["result"]["remediation_status"] == "ABORTED"

    def test_incident_lifecycle_invalid_pattern(self) -> None:
        """Verify lifecycle aborts when dry-run fails safety checks on empty pattern."""
        runtime = TrueForgeHarnessRuntime()
        res = runtime.run_incident_remediation_lifecycle(
            target_pattern="",
            simulate_human_approval=True,
        )
        assert res["success"] is False
        assert res["phase"] == "dry_run"

    def test_main_cli_entry_point(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify main() CLI returns exit code 0 on success."""
        exit_code = main()
        assert exit_code == 0
