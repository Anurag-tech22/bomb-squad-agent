"""
Autonomous DevOps Bomb Squad — FastMCP Root Entry Point.

This module exposes the agent's three core MCP tools to the TrueForge agent
harness via the FastMCP protocol:

  - inspect_cache_health:   Zero-side-effect telemetry and health triage.
  - dry_run_remediation:    Blast-radius analysis inside the Daytona Sandbox.
  - execute_eviction:       Cryptographic HITL-gated state mutation.

Usage (within TrueForge trueforge.config.json):
    "command": "python",
    "args": ["-m", "cache_cleaner_server"]
"""

from __future__ import annotations

from typing import Any

from src.mcp_servers.cache_cleaner_server import (
    REQUIRED_APPROVAL_TOKEN,  # noqa: F401 – re-exported for harness config discovery
    dry_run_remediation_impl,
    execute_eviction_impl,
    inspect_cache_health_impl,
)

try:
    from mcp.server.fastmcp import FastMCP

    mcp: FastMCP = FastMCP("BombSquad-CacheCleaner")

    @mcp.tool()
    def inspect_cache_health() -> dict[str, Any]:
        """
        Perform read-only cluster telemetry triage.

        Scans all cache keys for memory fragmentation, OOM pressure, poison
        locks, and deadlocked TTL entries. This tool has zero side effects —
        it NEVER mutates registry state.

        Returns:
            CacheHealthReport dict: status, total_keys, suspect_keys,
            poisoned_keys_detected, fragmentation_ratio, recommended_action.
        """
        return inspect_cache_health_impl()

    @mcp.tool()
    def dry_run_remediation(target_pattern: str) -> dict[str, Any]:
        """
        Calculate blast radius and session impact inside an isolated Daytona Sandbox.

        Matches keys against the supplied glob pattern and computes:
        - Keys eligible for safe eviction
        - Active user sessions at risk (must be zero for safety gate to pass)
        - Estimated memory reclaimed in MB
        - Whether HITL operator approval is required

        This tool is fully read-only — no keys are evicted.

        Args:
            target_pattern: Redis-style glob pattern (e.g. 'leak:*', '*').

        Returns:
            DryRunResult dict: matched_keys_count, keys_to_evict,
            memory_reclaimed_mb, safety_check_passed, requires_hitl_approval.
        """
        return dry_run_remediation_impl(target_pattern)

    @mcp.tool()
    def execute_eviction(
        target_pattern: str,
        approval_token: str,
        human_confirmed: bool,
    ) -> dict[str, Any]:
        """
        Execute authorized cache eviction with cryptographic HITL validation.

        This is the ONLY state-mutating tool in the harness. Execution requires:
        1. human_confirmed=True (explicit operator sign-off via TrueForge UI)
        2. approval_token matching the operator-issued TF-007 token

        If either invariant fails, the tool returns an ABORTED/UNAUTHORIZED
        result with zero state mutation.

        Args:
            target_pattern:  Redis-style glob pattern to target (e.g. 'leak:*').
            approval_token:  Operator-issued authorization token (e.g. 'TF-007-EVIC-REQ').
            human_confirmed: Must be True for eviction to proceed.

        Returns:
            EvictionResult dict: success, evicted_keys, current_memory_mb,
            remediation_status, linear_ticket_status, notion_sync.
        """
        return execute_eviction_impl(target_pattern, approval_token, human_confirmed)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    if __name__ == "__main__":
        import json

        print("FastMCP not available — running standalone diagnostic:\n")
        result = inspect_cache_health_impl()
        print(json.dumps(result, indent=2, default=str))
