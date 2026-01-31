# Agent Skills

Reusable agent expertise and knowledge patterns for the EUCORA platform.

---

## Available Skills

### Backend & Development

#### [backend-development](./backend-development/)
**Type:** Knowledge
**Purpose:** Full-stack backend development with Python, Django, PostgreSQL, migrations, PowerShell automation, and RAG/vector storage patterns
**Topics:** Python, Django, PostgreSQL, Migrations, PowerShell, RAG, pgvector
**Status:** ✅ Working

#### [react-best-practices](./react-best-practices/)
**Type:** Knowledge
**Purpose:** React + TypeScript development patterns for EUCORA frontend (contracts.ts, TanStack Query, Zustand, shadcn/ui)
**Topics:** React, TypeScript, TanStack Query, Zustand, shadcn/ui
**Status:** ✅ Working

#### [testing-patterns](./testing-patterns/)
**Type:** Knowledge
**Purpose:** Testing strategies for ≥90% coverage enforcement, idempotency tests, rollback tests, correlation ID isolation
**Topics:** pytest, Vitest, Pester, coverage, quality gates
**Status:** ✅ Working

---

### DevOps & Infrastructure

#### [devops-cicd](./devops-cicd/)
**Type:** Knowledge
**Purpose:** DevOps and CI/CD patterns including GitHub Actions workflows, Docker Compose orchestration, and quality gates
**Topics:** GitHub Actions, Docker, Docker Compose, pre-commit, quality gates
**Status:** ✅ Working

#### [kubernetes-patterns](./kubernetes-patterns/)
**Type:** Knowledge
**Purpose:** Kubernetes deployment patterns including Deployments, Services, ConfigMaps, Secrets, Ingress, and Helm
**Topics:** Kubernetes, Helm, Ingress, ConfigMaps, Secrets, health probes
**Status:** ✅ Working

#### [observability-stack](./observability-stack/)
**Type:** Knowledge
**Purpose:** Observability patterns including Prometheus metrics, Grafana dashboards, alerting rules, and structured logging
**Topics:** Prometheus, Grafana, metrics, alerting, structured logging, SIEM
**Status:** ✅ Working

#### [secrets-management](./secrets-management/)
**Type:** Knowledge
**Purpose:** Secrets management using Azure Key Vault, HashiCorp Vault, rotation policies, and External Secrets Operator
**Topics:** Azure Key Vault, Vault, secrets rotation, External Secrets Operator
**Status:** ✅ Working

---

### Governance & Workflow

#### [cab-workflow](./cab-workflow/)
**Type:** Knowledge
**Purpose:** CAB (Change Advisory Board) workflow patterns including evidence pack generation, risk scoring, and approval workflows
**Topics:** CAB approval, evidence packs, risk scoring, ring gates, exceptions
**Status:** ✅ Working

#### [security-audit](./security-audit/)
**Type:** Knowledge
**Purpose:** Security review checklist for CAB-compliant applications (session auth, SBOM, correlation IDs, SoD)
**Topics:** Security, SBOM, vulnerability scanning, SoD, audit trail
**Status:** ✅ Working

---

### Integrations & Connectors

#### [connector-development](./connector-development/)
**Type:** Knowledge
**Purpose:** Execution plane connector patterns for Intune, Jamf Pro, SCCM, Landscape, and Ansible integration
**Topics:** Intune, Jamf, SCCM, Landscape, Ansible, idempotency, retry logic
**Status:** ✅ Working

#### [servicenow-integration](./servicenow-integration/)
**Type:** Knowledge
**Purpose:** ServiceNow integration for CMDB sync, ITSM workflows, change request management, and CAB approval integration
**Topics:** ServiceNow, CMDB, ITSM, Change Management, Incidents
**Status:** ✅ Working

#### [one-e-dex-integration](./one-e-dex-integration/)
**Type:** Knowledge
**Purpose:** 1E DEX Platform (TeamViewer DEX) integration for Digital Employee Experience metrics and Green IT tracking
**Topics:** 1E DEX, boot time, user sentiment, carbon footprint, Green IT
**Status:** ✅ Working

---

## Skills by Category

| Category | Skills |
|----------|--------|
| **Frontend** | react-best-practices |
| **Backend** | backend-development, testing-patterns |
| **DevOps** | devops-cicd, kubernetes-patterns, observability-stack, secrets-management |
| **Governance** | cab-workflow, security-audit |
| **Integrations** | connector-development, servicenow-integration, one-e-dex-integration |

---

## Adding New Skills

1. Create a subdirectory: `.agents/skills/my-skill/`
2. Add `skill.md` with frontmatter:
   ```markdown
   ---
   name: my-skill
   description: What this skill provides and when to use it
   status: ✅ Working
   last-validated: 2026-01-30
   ---

   # My Skill

   Content here...
   ```
3. Update this README
4. Follow the patterns in existing skills

---

## Skill Structure Best Practices

- **Keep SKILL.md under 500 lines** — Use progressive disclosure
- **Include Quick Reference tables** — Easy lookup for common patterns
- **Add Anti-Patterns section** — What to avoid
- **Include Checklists** — Actionable validation steps
- **Link to reference files** — For detailed documentation

---

**Powered by [BuildWorks.AI](https://buildworks.ai)** — Enterprise AI • Open Source First
