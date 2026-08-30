"""
Pytest configuration and global test fixtures for Autonomous DevOps Bomb Squad.
"""

import pytest

from src.mcp_servers.cache_cleaner_server import reset_cache_registry


@pytest.fixture(autouse=True)
def clean_cache_state():
    """Automatically reset the cache registry state before and after each test."""
    reset_cache_registry()
    yield
    reset_cache_registry()
