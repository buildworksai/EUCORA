# SecOps Agent Migrations

## Status

Migrations need to be generated. The models are defined in `models.py`.

## Generate Migrations

Run from project root:

```bash
./scripts/generate-migrations.sh
```

Or manually:

```bash
cd backend
python manage.py makemigrations secops_agent
python manage.py migrate
```

## Models Requiring Migrations

- VulnerabilityScanner
- Vulnerability
- VulnerabilityInstance (includes CorrelationIdModel)
- RemediationPlan (includes CorrelationIdModel)
- SIEMConnection
- SecurityAlert (includes CorrelationIdModel)
- ComplianceBaseline
- ComplianceCheck (includes CorrelationIdModel)

## Dependencies

- `apps.core.models` (TimeStampedModel, CorrelationIdModel)
- `apps.application_portfolio.models` (Application - optional FK)
