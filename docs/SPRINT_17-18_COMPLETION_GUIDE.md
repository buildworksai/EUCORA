# Sprint 17-18 Completion Guide

**SPDX-License-Identifier: Apache-2.0**

This guide provides step-by-step instructions to complete the remaining work for Sprint 17-18 (E17, E18, E21 agents).

---

## Current Status

- ✅ **Backend Implementation**: Complete (models, serializers, views, services, admin, URLs)
- ✅ **Frontend Implementation**: Complete (contracts, dashboards, routes, navigation)
- ✅ **Workflow Definitions**: Complete (9 workflows added to seed_alm_workflows.py)
- ✅ **Test Files**: Complete (test_models.py, test_api.py, test_services.py, test_correlation_isolation.py for each app)
- ✅ **TypeScript**: Zero errors (`npx tsc --noEmit`)
- ✅ **ESLint**: Zero warnings (`npm run lint`)
- ❌ **Test Coverage**: **NON-NEGOTIABLE** - Must execute and verify ≥90%
- ❌ **Migrations**: Need to generate and apply

---

## Step 1: Generate Migrations

### Option A: Using the Helper Script

```bash
./scripts/generate-migrations.sh
```

### Option B: Manual Generation

```bash
cd backend
python manage.py makemigrations secops_agent
python manage.py makemigrations sre_agent
python manage.py makemigrations kb_triage
```

### Step 1.1: Apply Migrations

```bash
python manage.py migrate
```

---

## Step 2: Seed Workflows

```bash
cd backend
python manage.py seed_alm_workflows
```

This will create 9 new workflow definitions:
- 3 for E17 SecOps Agent
- 3 for E18 SRE Agent
- 3 for E21 KB & Triage Agent

---

## Step 3: Run Tests with Coverage (NON-NEGOTIABLE)

### Option A: Using the Helper Script

```bash
./scripts/run-tests-coverage.sh
```

### Option B: Manual Execution

```bash
# Test SecOps Agent
pytest backend/apps/secops_agent/tests/ \
    --cov=backend/apps/secops_agent \
    --cov-report=term-missing \
    --cov-fail-under=90 \
    -v

# Test SRE Agent
pytest backend/apps/sre_agent/tests/ \
    --cov=backend/apps/sre_agent \
    --cov-report=term-missing \
    --cov-fail-under=90 \
    -v

# Test KB & Triage Agent
pytest backend/apps/kb_triage/tests/ \
    --cov=backend/apps/kb_triage \
    --cov-report=term-missing \
    --cov-fail-under=90 \
    -v
```

### Step 3.1: Verify Coverage

Each test run must show:
- **Coverage ≥90%** for the app
- All tests passing
- No critical failures

If coverage is below 90%, add additional tests to cover:
- Edge cases
- Error handling
- Service layer methods
- ViewSet custom actions
- Serializer validation

---

## Step 4: Update Tracker Status

Once tests pass with ≥90% coverage:

1. Update `docs/planning/PHASE-2-ENHANCEMENT-TRACKER.md`:
   - Change E17, E18, E21 status from "🟡 In Progress" to "🟢 Complete"
   - Update progress from 90% to 100%
   - Check the "≥90% test coverage" acceptance criterion

2. Update `reports/SPRINT_17-18_COMPLETION_SUMMARY.md`:
   - Mark test coverage as ✅ Complete
   - Update conclusion section

---

## Step 5: Verification Checklist

Before marking sprint complete, verify:

- [ ] Migrations generated and applied successfully
- [ ] All 9 workflows seeded successfully
- [ ] `pytest apps/secops_agent --cov --cov-fail-under=90` passes
- [ ] `pytest apps/sre_agent --cov --cov-fail-under=90` passes
- [ ] `pytest apps/kb_triage --cov --cov-fail-under=90` passes
- [ ] TypeScript compilation passes (`npx tsc --noEmit`)
- [ ] ESLint passes (`npm run lint`)
- [ ] All API endpoints accessible (test via Swagger UI at `/api/docs/`)
- [ ] Frontend dashboards load without errors
- [ ] Tracker updated to reflect completion

---

## Troubleshooting

### Migration Errors

If migrations fail:
1. Check for model field conflicts
2. Verify all dependencies are installed
3. Review migration files for syntax errors
4. Consider resetting migrations if in development: `python manage.py migrate secops_agent zero`

### Test Coverage Below 90%

If coverage is below 90%:
1. Review coverage report: `htmlcov/index.html`
2. Identify untested code paths
3. Add tests for:
   - Model methods and properties
   - Serializer custom fields
   - ViewSet custom actions
   - Service layer methods
   - Error handling paths

### Import Errors

If tests fail with import errors:
1. Verify all apps are in `INSTALLED_APPS` in `backend/config/settings/base.py`
2. Check Python path includes `backend/`
3. Verify all `__init__.py` files exist

---

## Next Steps (Post-Completion)

Once Sprint 17-18 is complete:

1. **Service Client Implementation**: Replace mock clients with real integrations
2. **Frontend Enhancements**: Add forms, detail views, charts
3. **Documentation**: Create API documentation and runbooks
4. **Performance Testing**: Load testing for high-volume scenarios
5. **Security Review**: Penetration testing and security audit

---

## Support

For issues or questions:
- Review `docs/planning/26-secops-agent.md`, `27-sre-agent.md`, `30-kb-triage-agent.md`
- Check existing agent implementations (E15, E16) for patterns
- Consult EUCORA standards in `.cursor/rules/eucora-standards.mdc`
