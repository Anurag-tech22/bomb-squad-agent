"""
DevOps Bomb Squad - Zero-Trust Autonomous Incident Remediation Agent.

Main CLI entry point for TrueForge Agent Harness execution.
"""

from __future__ import annotations

import sys

from src.agent_runner import main

if __name__ == "__main__":
    sys.exit(main())
