# Tech Stack Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview

This document defines the **authoritative** technology stack for the Enterprise Endpoint Application Packaging & Deployment Factory (EUCORA). All technologies **not listed** are **banned** unless formally approved via Architecture Change Proposal (ACP).

**Design Principle**: "Standard, proven, enterprise-grade tech only. Minimize fragmentation, maximize interoperability."

---

## EUCORA-13001 Backend Stack (Control Plane)

### Core Framework
- **Framework**: Django 5.0.x + Django REST Framework 3.15.x
- **Language**: Python 3.12.x
- **ASGI Server**: Uvicorn 0.30.x (for async support where needed)
- **Database**: PostgreSQL 17.x (Alpine) — Primary system of record
- **ORM**: Django ORM (migrations-based schema evolution)
- **Caching**: Redis 7.x (Alpine) — Session store and caching layer

### Authentication & Authorization
- **Authentication Method**: Session-based (Django sessions) with Entra ID OAuth2 integration
- **Session Storage**: Redis (region-local, ephemeral)
- **MFA**: django-otp 1.3.0 + django-otp-totp 1.1.2 (TOTP only, RFC 6238)
- **Authorization**: Policy Engine (custom ABAC implementation) + Django permissions

**FORBIDDEN**:
- ❌ JWT tokens for web sessions (use session-based auth only)
- ❌ Custom authentication backends without ACP approval
- ❌ Storing authorization decisions in Redis (policy engine only)

### API Framework
- **REST API**: Django REST Framework 3.15.x
- **API Documentation**: drf-spectacular 0.27.2 (OpenAPI/Swagger generation)
- **CORS**: django-cors-headers 4.3.1
- **API Standards**: RESTful, versioned via URL path (`/api/v1/`)

### Testing & Quality
- **Testing Framework**: pytest-django 4.8.0, pytest 8.3.5
- **Coverage**: pytest-cov 6.1.1 (≥90% enforced)
- **Mocking**: pytest-mock (built-in)
- **Integration**: Django test client (built-in)
- **Code Quality**: 
  - Black 25.1.0 (formatting)
  - Flake8 7.2.0 (linting, --max-warnings 0)
  - django-stubs 5.0.2 (mypy type stubs)

### Background Tasks & Scheduling
- **Task Queue**: Celery 5.3.x
- **Message Broker**: Redis 7.x (shared with caching layer)
- **Scheduler**: Celery Beat (for periodic tasks)

### Observability
- **Logging**: structlog (structured JSON logging)
- **SIEM Integration**: Azure Log Analytics (custom Data Collector API client)
- **Metrics**: Prometheus client (custom exporter)
- **Tracing**: OpenTelemetry (optional for Phase 8+)

---

## EUCORA-13002 Frontend Stack (Web Control Plane UI)

### Core Framework
- **Build Tool**: Vite 5.1.4
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.3.3 (Strict mode)
- **Routing**: React Router DOM 6.22.0

**FORBIDDEN**:
- ❌ Next.js (not approved for EUCORA)
- ❌ Node.js backend services (use Django only)
- ❌ Server-Side Rendering (SSR) — SPA architecture only

### Styling & UI Components
- **Styling**: Tailwind CSS 3.4.17 + Tailwind CSS Animate 1.0.7
- **Component Library**: 
  - Radix UI (headless accessible components)
  - shadcn/ui (component patterns built on Radix)
- **Icons**: Lucide React 0.454.0
- **Theming**: Custom CSS variables + Tailwind config

**Design Requirements**:
- ✅ Premium glassmorphism aesthetic (defined in branding.md)
- ✅ Dark mode support (system preference detection)
- ✅ Micro-animations for interactions
- ✅ WCAG 2.1 AA accessibility compliance

### State Management
- **Client State**: Zustand (pinned exact via package.json)
- **Server State**: TanStack Query (React Query, pinned exact)

**FORBIDDEN**:
- ❌ Redux / Redux Toolkit / redux-saga / redux-thunk
- ❌ MobX
- ❌ Jotai / Recoil (use Zustand for client state)

### Forms & Validation
- **Forms**: React Hook Form 7.54.1
- **Validation**: Zod 3.24.1
- **Resolvers**: Hookform Resolvers 3.9.1

### Authentication (Frontend)
- **Microsoft Authentication**: MSAL-React 3.x (Entra ID integration)
- **Session Management**: Server-side sessions (no JWTs in localStorage)

### Specialized Libraries
- **Workflows/Diagrams**: ReactFlow (@xyflow/react 12.6.0)
- **Drag & Drop**: React Beautiful DnD 13.1.1
- **Charts**: Recharts 2.15.0
- **Markdown**: React Markdown 10.1.0 + Remark GFM 4.0.1
- **Code Highlighting**: React Syntax Highlighter 15.6.1
- **Notifications**: Sonner 1.7.1
- **Date Handling**: date-fns 2.28.0 + React Day Picker 8.10.1
- **Animations**: Framer Motion (optional, pinned exact)

### Testing & Quality
- **Unit Testing**: Vitest (pinned exact)
- **Component Testing**: React Testing Library
- **E2E Testing**: Playwright (pinned exact)
- **Linting**: ESLint 9.34.0 (--max-warnings 0)
- **Formatting**: Prettier (pinned exact)

---

## EUCORA-13003 Automation & Execution Plane (PowerShell)

### Core Language
- **PowerShell**: 7.4.x (PowerShell Core)
- **Module Standards**: Comment-based help mandatory (.SYNOPSIS, .DESCRIPTION, .PARAMETER, .EXAMPLE)

### Connector Scripts
- **Intune**: Microsoft.Graph PowerShell SDK 2.x
- **Jamf**: Native REST API calls via Invoke-RestMethod
- **SCCM**: ConfigurationManager PowerShell module
- **Landscape**: Landscape CLI / API client
- **Ansible**: AWX/Tower API via Invoke-RestMethod

### Testing
- **Framework**: Pester 5.x
- **Coverage**: ≥90% enforced per script
- **Static Analysis**: PSScriptAnalyzer (ZERO errors, ZERO warnings)

### Packaging Tools
- **Windows**: 
  - PSADT (PowerShell App Deployment Toolkit) 3.9.x
  - Intune Content Prep Tool (intunewin)
- **macOS**: pkgbuild, productsign, notarytool
- **Linux**: dpkg-deb, APT repository signing

---

## EUCORA-13004 Infrastructure & DevOps

### Containerization
- **Runtime**: Docker 24.x + Docker Compose 2.x
- **Base Images**:
  - Python: python:3.12-alpine (pinned via get_python_image())
  - PostgreSQL: postgres:17-alpine (pinned via get_postgres_image())
  - Redis: redis:7-alpine (pinned via get_redis_image())
  - Node: node:18.19.1-alpine (frontend build only)

### Databases
- **Primary**: PostgreSQL 17.x (tenant-scoped, append-only event store)
- **Session Store**: Redis 7.x (ephemeral, region-local)

**FORBIDDEN**:
- ❌ SQLite for production (dev/testing only)
- ❌ NoSQL databases without ACP approval
- ❌ Storing authorization policies in Redis (PostgreSQL only)

### Object Storage
- **Standard**: MinIO (S3-compatible) for artifact/evidence storage
- **Azure Blob Storage**: For long-term archive (with WORM policy)

### API Gateway (Optional)
- **Gateway**: Kong 3.4 (Alpine, pinned via get_kong_image())
- **Usage**: OPTIONAL edge gateway for staging/production profiles
- **Disabled By Default**: Not required in local development or Phase 1-7

**Kong MUST NOT**:
- ❌ Perform authentication (Django owns this)
- ❌ Perform authorization (Policy Engine owns this)
- ❌ Issue sessions (saraise-auth owns this)

### Search (Future)
- **Search Engine**: OpenSearch 2.11.1 (Elasticsearch-compatible, Apache 2.0 licensed)
- **Vector Storage**: PostgreSQL + pgvector (unless ACP approves dedicated vector DB)

**FORBIDDEN**:
- ❌ Elasticsearch (use OpenSearch for Apache 2.0 licensing)

### Monitoring & Observability
- **Metrics**: Prometheus (pinned exact via get_prometheus_image())
- **Dashboards**: Grafana 10.2.0
- **Logging**: Loki 2.9.0 (optional)
- **SIEM**: Azure Sentinel (Log Analytics workspace)

### Development Tools
- **Email Testing**: MailHog (pinned exact via get_mailhog_image())
- **Secrets Management**: Azure Key Vault (production) + Vault (dev, pinned via get_vault_image())

### CI/CD
- **Version Control**: Git
- **CI Platform**: GitHub Actions (or enterprise-approved CI/CD)
- **Pre-Commit**: pre-commit framework (mandatory, see .pre-commit-config.yaml)

---

## EUCORA-13005 Service-to-Stack Mapping (Authoritative)

| Service | Stack | Purpose |
|---|---|---|
| **Control Plane API** | Django + DRF | REST API, authentication, orchestration |
| **Policy Engine** | Python (Django app) | ABAC evaluation, risk scoring |
| **CAB Workflow** | Django + Celery | Approval workflows, evidence validation |
| **Evidence Store** | Django + MinIO | Immutable artifact/evidence storage |
| **Event Store** | PostgreSQL (append-only) | Audit trail, correlation tracking |
| **Orchestrator** | Django + Celery | Deployment intent state machine |
| **Connectors** | PowerShell 7.x | Execution plane integration (Intune/Jamf/SCCM/Landscape/Ansible) |
| **Web UI** | Vite + React + TypeScript | Admin console, CAB portal, dashboards |
| **Background Workers** | Celery | Async tasks, scheduled jobs, reconciliation loops |

---

## EUCORA-13006 Banned Technologies (by Exclusion)

Any technology **not listed** above is **banned** unless formally approved via Architecture Change Proposal (ACP).

### Specifically Banned

**Backend**:
- ❌ Node.js backend frameworks (Express, Fastify, Koa) — use Django
- ❌ FastAPI — use Django + DRF
- ❌ Flask — use Django
- ❌ SQLAlchemy — use Django ORM
- ❌ Alembic — use Django migrations
- ❌ Prisma — use Django ORM
- ❌ JWT tokens for web sessions — use session-based auth
- ❌ Custom authentication without ACP approval

**Frontend**:
- ❌ Next.js — not approved for EUCORA
- ❌ Redux / Redux Toolkit / redux-saga — use Zustand
- ❌ Vue.js / Svelte / Angular — use React
- ❌ tRPC — use DRF APIs
- ❌ Apollo GraphQL — REST APIs only unless ACP approved

**Databases**:
- ❌ MongoDB / DynamoDB — use PostgreSQL
- ❌ ClickHouse — use PostgreSQL + OpenSearch
- ❌ Elasticsearch — use OpenSearch (Apache 2.0)
- ❌ Cassandra / ScyllaDB — use PostgreSQL

**Infrastructure**:
- ❌ Kubernetes (unless enterprise standard) — use Docker Compose for dev/staging
- ❌ Terraform (unless enterprise standard) — document infrastructure-as-code separately

---

## EUCORA-13007 AI/Agent Stack (Phase 4+ Only, Optional)

**Hard Rule**: AI dependencies are **forbidden** in Phase 1-3 unless the phase plan explicitly enables them.

### Agent Development (Phase 4+, Reference Only)
- **LLM SDK**: OpenAI SDK (pinned exact via central registry)
- **Agent Framework**: LangGraph / CrewAI patterns
- **Structured Outputs**: instructor (pinned exact)
- **Type Safety**: pydantic-ai (pinned exact)
- **Workflow Engine**: temporalio (pinned exact, saga pattern)

### Governance & Quality (Phase 4+, Reference Only)
- **Output Validation**: guardrails-ai (pinned exact)
- **RAG Metrics**: ragas (pinned exact)
- **Tracing**: langsmith (pinned exact)

### Cost Optimization (Phase 4+, Reference Only)
- **LLM Gateway**: portkey-ai (pinned exact, caching/fallbacks/cost tracking)
- **Prompt Optimization**: dspy-ai (pinned exact)

**Vector Storage**: PostgreSQL + pgvector (unless ACP approves dedicated vector DB)

---

## EUCORA-13008 Migration & Exceptions

Any deviation from this tech stack requires:
1. **Rationale**: Why is the deviation necessary?
2. **Risk Assessment**: Security, maintenance, architectural impact
3. **Architecture Change Proposal (ACP)**: Formal approval from Platform Admin + CAB
4. **Cross-Reference**: Link to this rule ID (EUCORA-13008) in PR description

---

## EUCORA-13009 Accessibility & Branding Guardrails

- ✅ Use semantic colors from `.agents/rules/branding.md` (no hardcoded hex in components)
- ✅ Enforce keyboard/ARIA patterns for Radix UI components
- ✅ Follow EUCORA brand colors defined in Tailwind config (deepBlue, teal, gold, green)
- ✅ Dark mode toggle with system preference detection
- ✅ WCAG 2.1 AA compliance for all UI elements

---

## EUCORA-13010 Version Pinning Strategy

- **Backend**: Pin major.minor versions, allow patch updates (`Django~=5.0.0`)
- **Frontend**: Pin exact versions for state management and routing (`"zustand": "4.5.2"`)
- **Infrastructure**: Pin exact Docker image tags via helper functions (`get_postgres_image()`)
- **AI/Agent**: Pin exact versions via central registry (Phase 4+ only)

**Rationale**: Balance stability (major/minor pins) with security patches (allow patch updates).

---

## Related Documentation

- [AGENTS.md](../../AGENTS.md) — Agent roles and responsibilities
- [CLAUDE.md](../../CLAUDE.md) — Architectural principles and anti-patterns
- [.agents/rules/branding.md](./branding.md) — Branding and visual identity
- [docs/planning/phase-8-backend-implementation-prompt.md](../../docs/planning/phase-8-backend-implementation-prompt.md) — Backend (Django) implementation
- [docs/planning/phase-9-frontend-implementation-prompt.md](../../docs/planning/phase-9-frontend-implementation-prompt.md) — Frontend (React) implementation

---

**Tech Stack Rules v1.0 — Design**
