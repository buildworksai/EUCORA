# Contributing to EUCORA

Thank you for your interest in contributing to **EUCORA** (End-User Computing Orchestration & Reliability Architecture).

**BuildWorks.AI** enforces strict architectural and quality standards to ensure enterprise-grade reliability. Please review this document carefully before submitting changes.

## Code of Conduct

All contributors are expected to adhere to our Code of Conduct and treat others with respect and professionalism.

## Governance & Architecture

Before writing code, you **MUST** read:
1.  **[AGENTS.md](AGENTS.md)**: Role definitions and specialized agent instructions.
2.  **[CLAUDE.md](CLAUDE.md)**: Non-negotiable global rules, architecture principles, and quality gates.

Key Principles:
- **Thin Control Plane**: Policy/Orchestration/Evidence only.
- **Evidence-First**: All changes require audit trails and evidence packs.
- **Idempotency**: All operations must be retryable.
- **Pre-Commit**: Zero tolerance for linter warnings or type errors.

## Development Workflow

1.  **Fork and Clone**: Fork the repository and clone it locally.
2.  **Branching**: Create a feature branch (`feature/description`) or fix branch (`fix/issue-id`).
3.  **Pre-Commit Hooks**: Ensure pre-commit hooks are installed and passing.
    ```bash
    pip install pre-commit
    pre-commit install
    ```
4.  **Commits**: Use conventional commits (e.g., `feat: add new connector`, `fix: resolve race condition`).
5.  **Pull Requests**:
    - Link to related issues.
    - Provide a clear description of changes.
    - confirm that all quality gates passed.

## Pull Request Process

1.  All PRs must pass CI/CD checks (linting, tests, build).
2.  Significant architectural changes require an **ADR** (Architecture Decision Record).
3.  High-risk changes (per Risk Model) may require simulated CAB approval in the test environment.
4.  Maintainers will review your code against `CLAUDE.md` standards.

## Legal

By contributing to EUCORA, you agree that your contributions will be licensed under the project's **Apache License 2.0**.

---
*Build by BuildWorks.AI*
