# EUCORA
### End-User Computing Orchestration & Reliability Architecture
**by BuildWorks.AI**

![EUCORA Logo](./EUCORA-logo2.png)

---

## Overview

**EUCORA** (End-User Computing Orchestration & Reliability Architecture) is an enterprise-grade platform engineering solution designed to bring strict control plane discipline to endpoint management. It serves as a unified orchestration layer focusing on policy, evidence, and reliability across heterogeneous execution planes (Intune, Jamf, SCCM, Landscape, Ansible).

**Build by BuildWorks.AI**

## Features

- **Thin Control Plane**: separate policy intents from execution details.
- **Evidence-First Governance**: CAB-ready evidence packs (hashes, signatures, SBOMs) for every change.
- **Ring-Based Rollouts**: Deterministic promotion gates (Canary → Pilot → Global).
- **Hybrid Distribution**: Intelligent content handling for Online, Intermittent, and Air-gapped sites.
- **Drift Detection**: Automated reconciliation loops to enforce desired state.

## Architecture

EUCORA enforces a strict governance model designed for high-compliance environments.
See [docs/architecture/architecture-overview.md](docs/architecture/architecture-overview.md) for the authoritative design.

## Getting Started

### Prerequisites

- Docker
- Python 3.10+ / PowerShell 7+ (depending on module)
- Pre-commit (for development)

### Installation

```bash
git clone https://github.com/buildworksai/EUCORA.git
cd EUCORA

# Install pre-commit hooks (for developers)
pwsh -File scripts/utilities/Install-PreCommitHooks.ps1
```

### For Developers

See [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md) for complete development environment setup including:
- Pre-commit hooks configuration
- SPDX compliance checks
- PowerShell linting with PSScriptAnalyzer
- CI/CD workflow details

## Contributing

We welcome contributions that adhere to our strict architectural and quality standards.
Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before submitting a Pull Request.

## License

EUCORA is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---
*Build by BuildWorks.AI*
