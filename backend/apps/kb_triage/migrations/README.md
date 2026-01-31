# KB & Triage Agent Migrations

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
python manage.py makemigrations kb_triage
python manage.py migrate
```

## Models Requiring Migrations

- KnowledgeSource
- KnowledgeArticle (includes embedding field for pgvector/E7)
- TriageRequest (includes CorrelationIdModel)
- TriageSuggestion
- ResolutionStep
- IncidentPattern (includes CorrelationIdModel)
- TriageFeedback

## Dependencies

- `apps.core.models` (TimeStampedModel, CorrelationIdModel)
- `pgvector` extension (for KnowledgeArticle.embedding field)

## Note

The `KnowledgeArticle.embedding` field uses pgvector. Ensure pgvector extension is installed:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
