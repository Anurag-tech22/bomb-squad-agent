"""
Autonomous DevOps Bomb Squad - Cache Remediation MCP Server (Root Entrypoint)
"""

from src.mcp_servers.cache_cleaner_server import (
    inspect_cache_health_impl,
    dry_run_remediation_impl,
    execute_eviction_impl,
    MOCK_CACHE_REGISTRY,
)

try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("BombSquad-CacheCleaner")

    @mcp.tool()
    def inspect_cache_health():
        """Inspects cache cluster memory, fragmentation ratio, and flags leaked keys."""
        return inspect_cache_health_impl()

    @mcp.tool()
    def dry_run_remediation(target_pattern: str):
        """Executes a zero-impact dry run inside the Daytona Sandbox."""
        return dry_run_remediation_impl(target_pattern)

    @mcp.tool()
    def execute_eviction(target_pattern: str, approval_token: str, human_confirmed: bool):
        """Executes eviction only after explicit human sign-off."""
        return execute_eviction_impl(target_pattern, approval_token, human_confirmed)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    if __name__ == "__main__":
        print("FastMCP package not installed. Running diagnostic check directly:")
        print(inspect_cache_health_impl())
