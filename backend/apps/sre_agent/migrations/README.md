# SRE Agent Migrations

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
python manage.py makemigrations sre_agent
python manage.py migrate
```

## Models Requiring Migrations

- MonitoringPlatform
- HealthEndpoint
- HealthCheckResult
- SLODefinition
- SLOMetric
- SelfHealingRule
- SelfHealingExecution (includes CorrelationIdModel)
- Runbook
- RunbookExecution (includes CorrelationIdModel)

## Dependencies

- `apps.core.models` (TimeStampedModel, CorrelationIdModel)
