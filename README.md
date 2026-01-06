<p align="center">
  <img src="./EUCORA-logo.png" alt="EUCORA Logo" width="400">
</p>

<h1 align="center">EUCORA</h1>
<h3 align="center">End-User Computing Orchestration & Reliability Architecture</h3>

<p align="center">
  <strong>Enterprise-Grade Endpoint Application Packaging & Deployment Factory</strong>
</p>

<p align="center">
  <em>Built by <a href="https://buildworks.ai">BuildWorks.AI</a></em>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#key-capabilities">Capabilities</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#documentation">Documentation</a>
</p>

---

## Overview

**EUCORA** is a platform engineering solution that brings strict control plane discipline to enterprise endpoint management. It serves as a unified orchestration layer for policy, evidence, and reliability across heterogeneous execution planes including **Intune**, **Jamf**, **SCCM**, **Landscape**, and **Ansible**.

### The Problem We Solve

Managing 50,000+ endpoints across acquisitions with 5,000+ applications creates unacceptable risk in:
- **Security**: Privilege sprawl, unverified software, weak auditability
- **Operations**: Configuration drift, inconsistent deployment outcomes
- **Governance**: CAB evidence gaps, non-deterministic approvals

### Our Approach

EUCORA implements a **thin Control Plane** that standardizes the enterprise application lifecycle without replacing existing MDM infrastructure. The platform decides **what** should happen; existing tools execute **how** it happens.

---

## Key Capabilities

| Capability | Description |
|------------|-------------|
| **🎯 Thin Control Plane** | Separates policy intents from execution details across all platforms |
| **📋 Evidence-First Governance** | CAB-ready evidence packs with hashes, signatures, SBOMs for every change |
| **🔄 Ring-Based Rollouts** | Deterministic promotion gates (Lab → Canary → Pilot → Department → Global) |
| **🌐 Hybrid Distribution** | Intelligent content handling for Online, Intermittent, and Air-gapped sites |
| **🔍 Drift Detection** | Continuous reconciliation loops enforcing desired state |
| **⚖️ Risk Scoring** | Deterministic risk assessment with versioned scoring rubrics |
| **🤖 AI Agent Hub** | Intelligent automation assistants for packaging and deployment workflows |

---

## Architecture

```
                   ┌──────────────────────────────────────────────┐
                   │                  Control Plane               │
                   │ Policy + Orchestration + Evidence (Thin)     │
                   └───────────────┬──────────────────────────────┘
                                   │
                   ┌───────────────▼──────────────────────────────┐
                   │        Packaging & Publishing Factory         │
                   │ Build → Sign/Notarize → SBOM/Vuln → Test      │
                   └───────────────┬──────────────────────────────┘
                                   │
          ┌────────────────────────▼────────────────────────┐
          │                 Execution Planes                 │
          │ Intune | Jamf | SCCM | Landscape | Ansible       │
          └───────────────┬──────────────────────────────────┘
                          │
          ┌───────────────▼──────────────────────────────────┐
          │                  Endpoint Devices                 │
          │ Windows | macOS | Ubuntu | iOS/iPadOS | Android   │
          └──────────────────────────────────────────────────┘
```

### Core Principles

1. **Determinism** — No "AI-driven deployments"; all approvals and gates are explainable
2. **Separation of Duties** — Packaging ≠ Publishing ≠ Approval
3. **Idempotency** — Every deployment action can be retried safely
4. **Reconciliation over Hope** — Continuous desired-vs-actual drift detection
5. **Evidence-First Governance** — CAB decisions include standardized evidence packs
6. **Offline is First-Class** — Explicit distribution strategy per site class

---

## Platform Support

| Platform | Primary | Secondary | Notes |
|----------|---------|-----------|-------|
| Windows | Intune | SCCM | Legacy OS / constrained sites |
| macOS | Intune | Jamf | Jamf where deeper controls required |
| Ubuntu/Linux | Landscape / Ansible | Agent fallback | Signed APT repo as standard |
| iOS/iPadOS | Intune | — | ABM + ADE |
| Android | Intune | — | Android Enterprise |

---

## Technology Stack

### Backend
- **Django 5.x** with Django REST Framework
- **PostgreSQL** for system-of-record data
- **Redis** for caching and task queues
- **Celery** for async task processing

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** with shadcn/ui components
- **TanStack Query** for server state management

### Infrastructure
- **Docker** for containerization
- **Pre-commit hooks** for quality gates

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for backend development)
- Node.js 18+ (for frontend development)
- PowerShell 7+ (for CLI tooling)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/buildworksai/EUCORA.git
cd EUCORA

# Start development environment
docker compose -f docker-compose.dev.yml up -d

# Install pre-commit hooks (required for development)
pip install pre-commit && pre-commit install
```

### Development Setup

See [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md) for complete development environment configuration including:
- Pre-commit hooks and quality gates
- SPDX compliance checks
- Backend and frontend development workflows
- CI/CD integration details

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture/architecture-overview.md) | System-of-record for architectural decisions |
| [Control Plane Design](docs/architecture/control-plane-design.md) | Control Plane component specifications |
| [Risk Model](docs/architecture/risk-model.md) | Risk scoring formula, factors, and rubrics |
| [Ring Model](docs/architecture/ring-model.md) | Ring-based rollout and promotion gates |
| [CAB Workflow](docs/architecture/cab-workflow.md) | Change Advisory Board approval process |
| [Development Setup](docs/DEVELOPMENT_SETUP.md) | Developer onboarding guide |

### Runbooks

- [Incident Response](docs/runbooks/incident-response.md)
- [Rollback Execution](docs/runbooks/rollback-execution.md)
- [CAB Submission](docs/runbooks/cab-submission.md)

---

## Project Structure

```
EUCORA/
├── backend/           # Django REST API
│   ├── apps/          # Django applications
│   │   ├── ai_agents/         # AI automation assistants
│   │   ├── authentication/    # Entra ID integration
│   │   ├── cab_workflow/      # CAB approval workflows
│   │   ├── connectors/        # Execution plane adapters
│   │   ├── deployment_intents/# Deployment orchestration
│   │   ├── event_store/       # Immutable audit trail
│   │   ├── evidence_store/    # Evidence pack storage
│   │   ├── policy_engine/     # Risk scoring & policy
│   │   └── telemetry/         # Metrics & reporting
│   └── config/        # Django configuration
├── frontend/          # React SPA
│   └── src/
│       ├── components/    # UI components
│       ├── routes/        # Page components
│       └── lib/           # Utilities & stores
├── scripts/           # Automation tooling
│   ├── cli/           # dapctl CLI
│   ├── connectors/    # Connector scripts
│   └── packaging-factory/
├── docs/              # Documentation
│   ├── architecture/  # Architecture specs
│   ├── infrastructure/# Infrastructure docs
│   ├── modules/       # Per-platform specs
│   └── runbooks/      # Operational runbooks
└── reports/           # Implementation reports
```

---

## Contributing

We welcome contributions that adhere to our strict architectural and quality standards.

Please read:
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guidelines
- [AGENTS.md](AGENTS.md) — Specialized agent instructions
- [CLAUDE.md](CLAUDE.md) — Architecture and governance rules

### Quality Standards

- ≥90% test coverage enforced by CI
- Pre-commit hooks mandatory (zero bypasses)
- Type safety with zero new errors beyond baseline
- CAB evidence packs for all high-risk changes

---

## License

EUCORA is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ by <a href="https://buildworks.ai">BuildWorks.AI</a></strong>
</p>

<p align="center">
  <sub>Technical correctness and governance compliance are non-negotiable.</sub>
</p>
