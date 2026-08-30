"""
Unit tests validating TrueForge harness manifest and safety configuration.
"""

from __future__ import annotations

import json
from pathlib import Path


class TestTrueForgeConfiguration:
    """Test suite validating trueforge.config.json and safety policies."""

    def test_config_manifest_structure(self) -> None:
        """Ensure trueforge.config.json is valid and contains required sections."""
        config_path = Path("trueforge.config.json")
        assert config_path.exists(), "trueforge.config.json must exist at project root"

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["version"] == "1.0.0"
        assert "agent" in data
        assert "sandbox" in data
        assert "mcp_servers" in data
        assert "safety_gates" in data

    def test_safety_gates_enforcement_rules(self) -> None:
        """Validate safety gates mandate HITL approval for dangerous operations."""
        with open("trueforge.config.json", encoding="utf-8") as f:
            data = json.load(f)

        hitl_config = data["safety_gates"]["human_in_the_loop"]
        assert "execute_eviction" in hitl_config["enforce_on_tools"]
        assert hitl_config["approval_token_prefix"] == "TF-007"
        assert hitl_config["require_ui_diff_preview"] is True

    def test_instructions_and_policy_files_exist(self) -> None:
        """Ensure referenced instructions and policy files exist and are populated."""
        instructions_path = Path("agent_instructions.txt")
        policy_path = Path("agent_policy.txt")

        assert instructions_path.exists()
        assert policy_path.exists()
        assert len(instructions_path.read_text(encoding="utf-8").strip()) > 50
        assert len(policy_path.read_text(encoding="utf-8").strip()) > 50
