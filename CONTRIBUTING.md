# Contributing to Autonomous DevOps Bomb Squad 💣🛡️

Thank you for your interest in contributing to the Autonomous DevOps Bomb Squad Agent! We welcome contributions from developers, researchers, and site reliability engineers.

---

## 📋 Development Workflow

All contributions must follow our zero-trust engineering standards:

1. **Fork and Branch:** Create a feature branch matching `feat/<feature-name>` or `fix/<bug-name>`.
2. **Local Validation:** Run unit tests and syntax checks:
   ```bash
   pytest tests/ -v
   python -m py_compile src/mcp_servers/cache_cleaner_server.py
   ```
3. **Qodo Code Review Requirement:** Every Pull Request must be audited and approved by **Qodo AI**. Ensure all high-severity findings are resolved before merging.
4. **Safety Directives:** Ensure modifications to `agent_policy.txt` or `agent_instructions.txt` preserve our Human-in-the-Loop (HITL) gate invariants.

---

## 🧪 Testing Guidelines

* **Unit Tests:** Located in `tests/test_cache_cleaner.py`.
* **Invariant Tests:** Every new MCP tool must have associated test cases verifying that unauthenticated or unconfirmed execution is strictly rejected.

---

## ⚖️ Code of Conduct

Please adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all community interactions.
