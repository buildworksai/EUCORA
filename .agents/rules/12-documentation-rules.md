# Documentation Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Prescribe documentation structure, versioning, cross-references, ADRs, and API spec requirements.
**Design Principle**: "Documentation must reflect CAB-ready discipline; use established folder hierarchy."

## Rules
1. Folder structure: architecture docs under `docs/architecture/`, infrastructure under `docs/infrastructure/`, connectors under `docs/modules/`, runbooks under `docs/runbooks/`, agent rules under `.agents/rules/`.
2. Header requirements: every doc must state `# Title`, `Version`, `Status`, `Last Updated` with semantic versioning (e.g., v1.0).
3. Cross references: include markdown links to at least two related docs (e.g., architecture overview, risk model).
4. ADR requirements: create ADRs for new architectural decisions (format: `docs/architecture/adr/00X-description.md`).
5. API documentation: provide OpenAPI/Swagger spec files under `docs/api/` when APIs are exposed.

## Enforcement Examples
- ✅ Example command to generate doc skeleton: `./scripts/generate-doc.sh docs/architecture/control-plane-design.md` ensures structure with header.
- ✅ SARAISE principle: short enforcement statements, include ✅/❌ examples per rule.
- ❌ Creating docs at repo root or forgetting `Last Updated` field results in review rejection.

## Related Documentation
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)
- [Risk Model](../docs/architecture/risk-model.md)

---

**Documentation Rules v1.0 — Design**
