---
name: eucora-sprint-executor
description: Execute EUCORA Phase 2 enhancements (E1-E21) following CAB-approved governance. Use when implementing any enhancement, creating Django apps, React components, or running sprints. Triggers on mentions of E1-E21, sprint execution, or EUCORA development.
---

# EUCORA Sprint Executor

Execute Phase 2 enhancements with architectural rigor and quality gate enforcement.

## Quick Start

1. Read the spec: `docs/planning/{enhancement-number}-{name}.md`
2. Update tracker: `docs/planning/PHASE-2-ENHANCEMENT-TRACKER.md`
3. Follow the standard workflow below
4. Run quality checks before completion

## Enhancement Priority Order

| Order | Enhancement | Sprint | Dependencies |
|-------|-------------|--------|--------------|
| 1 | E3: RBAC | 1-2 | None |
| 2 | E2: Storage | 1-2 | None |
| 3 | E7: Vector Storage | 3-4 | None |
| 4 | E1: Document Management | 3-4 | E2, E7 |
| 5 | E8: AI Workflows | 5-6 | E3, E7 |
| 6 | E5: Application Policy | 7-8 | E3, E8 |
| 7 | E6: Application Stack | 7-8 | E3 |
| 8 | E4: 1E DEX | 9-10 | E3 |
| 9 | E9: PowerShell Audit | 9-10 | None |
| 10 | E10: CMDB Agent | 11-12 | E8 |
| 11 | E11: Change Comms | 11-12 | E8, E10 |
| 12 | E14: Discovery | 11-12 | E7, E8 |
| 13 | E12: Documentation | 13-14 | E1, E7, E8 |
| 14 | E13: Automation Advisor | 13-14 | E7, E8, E10 |
| 15 | E15: IAM Security | 13-14 | E3, E7, E8 |
| 16 | E16: Request Coord | 15-16 | E8, E10, E11 |
| 17 | E17: SecOps | 17-18 | E3, E7, E8, E15 |
| 18 | E18: SRE Agent | 17-18 | E3, E7, E8, E9 |
| 19 | E21: KB Triage | 17-18 | E1, E7, E8 |
| 20 | E19: SLA Governance | 19-20 | E3, E7, E8, E18 |
| 21 | E20: Planning Agent | 19-20 | E3, E7, E8, E14 |

## Spec Document Locations

| ID | Spec Path |
|----|-----------|
| E1 | docs/planning/10-document-management-rag.md |
| E2 | docs/planning/11-storage-configuration.md |
| E3 | docs/planning/12-comprehensive-rbac.md |
| E4 | docs/planning/13-1e-dex-integration.md |
| E5 | docs/planning/14-application-policy-ui.md |
| E6 | docs/planning/15-application-stack-ux.md |
| E7 | docs/planning/16-vector-storage-pgvector.md |
| E8 | docs/planning/17-ai-agent-workflows.md |
| E9 | docs/planning/18-powershell-production-audit.md |
| E10 | docs/planning/19-cmdb-integration-agent.md |
| E11 | docs/planning/20-change-communications-agent.md |
| E12 | docs/planning/21-documentation-agent.md |
| E13 | docs/planning/22-automation-advisor-agent.md |
| E14 | docs/planning/23-discovery-agent.md |
| E15 | docs/planning/24-iam-security-agent.md |
| E16 | docs/planning/25-request-coordination-agent.md |
| E17 | docs/planning/26-secops-agent.md |
| E18 | docs/planning/27-sre-agent.md |
| E19 | docs/planning/28-sla-governance-agent.md |
| E20 | docs/planning/29-planning-agent.md |
| E21 | docs/planning/30-kb-triage-agent.md |

## Standard Workflow

### Phase 1: Backend Implementation

```bash
# 1. Create Django app
cd backend
python manage.py startapp {app_name}
mv {app_name} apps/

# 2. Add to INSTALLED_APPS in config/settings/base.py
# 3. Create models with CorrelationIdModel mixin
# 4. Create and run migrations
python manage.py makemigrations {app_name}
python manage.py migrate

# 5. Create serializers, views, urls
# 6. Register in config/urls.py
```

### Phase 2: Frontend Implementation

```bash
# 1. Create domain directory
mkdir -p frontend/src/routes/{domain}

# 2. Create contracts.ts FIRST (types + endpoints)
# 3. Create page components
# 4. Create hooks for API calls
# 5. Add route to App.tsx
# 6. Add to Sidebar.tsx
```

### Phase 3: Testing

```bash
# Backend
cd backend
pytest apps/{app_name}/ --cov --cov-fail-under=90

# Frontend
cd frontend
npm run test -- --coverage
npm run lint
npx tsc --noEmit
```

### Phase 4: Update Tracker

Update `docs/planning/PHASE-2-ENHANCEMENT-TRACKER.md`:
- Mark tasks complete
- Update progress percentage
- Note any blockers

## Quality Gates (MANDATORY)

Before marking ANY enhancement complete:

```bash
# Backend checks
cd backend
pytest --cov --cov-fail-under=90
flake8 apps/
mypy apps/

# Frontend checks
cd frontend
npm run build          # Zero errors
npm run lint           # Zero warnings
npm run test           # All passing
npx tsc --noEmit       # Zero type errors
```

## Code Templates

### Django Model with Correlation ID

```python
from apps.core.models import TimeStampedModel, CorrelationIdModel

class MyModel(TimeStampedModel, CorrelationIdModel):
    """Model description."""
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='active')

    class Meta:
        ordering = ['-created_at']
```

### ViewSet with Correlation Filtering

```python
class MyViewSet(viewsets.ModelViewSet):
    serializer_class = MySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = MyModel.objects.all()
        correlation_id = self.request.query_params.get('correlation_id')
        if correlation_id:
            qs = qs.filter(correlation_id=correlation_id)
        return qs
```

### Frontend contracts.ts

```typescript
export interface MyEntity {
  id: string;
  correlation_id: string;
  name: string;
  status: string;
  created_at: string;
}

export const ENDPOINTS = {
  list: '/api/my-entity/',
  detail: (id: string) => `/api/my-entity/${id}/`,
  action: (id: string) => `/api/my-entity/${id}/action/`,
} as const;
```

### React Query Hook

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { MyEntity, ENDPOINTS } from './contracts';

export function useMyEntities() {
  return useQuery<MyEntity[]>({
    queryKey: ['my-entities'],
    queryFn: () => apiClient.get(ENDPOINTS.list).then(r => r.data),
  });
}
```

## Additional Resources

- [Enhancement Workflows](enhancement-workflows.md)
- [Code Templates](code-templates.md)
- [Commands Reference](commands.md)
