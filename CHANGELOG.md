# Changelog

All notable changes to **EUCORA** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial codebase import and rebranding to EUCORA.
- Established `EUCORA` branding and identity by BuildWorks.AI.
- Added Control Plane and Execution Plane architecture documentation.
- Integrated `AGENTS.md` and `CLAUDE.md` for governance.
- Setup Apache 2.0 License and Contributing guidelines.
- Implemented SPDX license headers across all PowerShell files (60 files).
- Added pre-commit hooks for code quality enforcement.
- Created GitHub Actions workflows for CI/CD.
- Generated image assets (favicon, logos) from EUCORA branding.

### Changed
- Refactored repository structure to align with BuildWorks.AI governance model.
- Updated architecture documentation with EUCORA branding.

### Removed
- **Remote-Exec/** folder - Violated Control Plane architecture (direct endpoint connectivity forbidden).
- **Templates/** folder - Legacy PSADT approach incompatible with thin control plane model.

---
*Build by BuildWorks.AI*
