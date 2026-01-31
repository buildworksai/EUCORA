# Database Migration Patterns

Complete guide to Django migrations with PostgreSQL.

---

## Critical Rules

| Rule | Consequence of Violation |
|------|-------------------------|
| NEVER modify existing migrations | Causes migration conflicts on production |
| Always specify dependencies | Migrations may run in wrong order |
| Test both forward and reverse | Rollback may fail in production |
| Use atomic operations | Partial migrations leave DB in bad state |

---

## Common Migration Operations

### Add Field

```python
# migrations/0002_add_risk_score.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="deployment",
            name="risk_score",
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=0.0,
                help_text="Calculated risk score (0-100)",
            ),
        ),
    ]
```

### Add Field with Default Calculation

```python
# migrations/0003_add_calculated_field.py
from django.db import migrations, models

def calculate_defaults(apps, schema_editor):
    """Forward migration: calculate values for existing rows."""
    Deployment = apps.get_model("deployments", "Deployment")
    for deployment in Deployment.objects.all():
        deployment.risk_score = 50.0  # Default value
        deployment.save(update_fields=["risk_score"])

def reverse_defaults(apps, schema_editor):
    """Reverse migration: no action needed (field will be removed)."""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0002_add_risk_score"),
    ]

    operations = [
        migrations.AddField(
            model_name="deployment",
            name="processed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.RunPython(calculate_defaults, reverse_defaults),
    ]
```

### Rename Field

```python
# migrations/0004_rename_field.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0003_add_calculated_field"),
    ]

    operations = [
        migrations.RenameField(
            model_name="deployment",
            old_name="processed_at",
            new_name="completed_at",
        ),
    ]
```

### Add Index

```python
# migrations/0005_add_indexes.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0004_rename_field"),
    ]

    operations = [
        # Simple index
        migrations.AddIndex(
            model_name="deployment",
            index=models.Index(
                fields=["status", "created_at"],
                name="depl_status_created_idx",
            ),
        ),

        # Partial index (PostgreSQL)
        migrations.AddIndex(
            model_name="deployment",
            index=models.Index(
                fields=["risk_score"],
                condition=models.Q(status="pending"),
                name="pending_risk_idx",
            ),
        ),
    ]
```

### Add Constraint

```python
# migrations/0006_add_constraints.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0005_add_indexes"),
    ]

    operations = [
        # Check constraint
        migrations.AddConstraint(
            model_name="deployment",
            constraint=models.CheckConstraint(
                check=models.Q(risk_score__gte=0) & models.Q(risk_score__lte=100),
                name="valid_risk_score_range",
            ),
        ),

        # Unique constraint
        migrations.AddConstraint(
            model_name="deployment",
            constraint=models.UniqueConstraint(
                fields=["application", "version", "target_ring"],
                name="unique_app_version_ring",
            ),
        ),
    ]
```

### Add Foreign Key

```python
# migrations/0007_add_foreign_key.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0006_add_constraints"),
        ("applications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="deployment",
            name="application",
            field=models.ForeignKey(
                to="applications.Application",
                on_delete=models.PROTECT,
                related_name="deployments",
                null=True,  # Allow null initially
            ),
        ),
    ]
```

---

## Data Migrations

### Migrate Data Between Fields

```python
# migrations/0008_migrate_data.py
from django.db import migrations

def migrate_forward(apps, schema_editor):
    """Move data from old field to new field."""
    Deployment = apps.get_model("deployments", "Deployment")

    for deployment in Deployment.objects.all():
        # Parse old_status into new status enum
        if deployment.old_status == "OK":
            deployment.status = "completed"
        elif deployment.old_status == "FAIL":
            deployment.status = "failed"
        else:
            deployment.status = "pending"
        deployment.save(update_fields=["status"])

def migrate_reverse(apps, schema_editor):
    """Reverse the data migration."""
    Deployment = apps.get_model("deployments", "Deployment")

    for deployment in Deployment.objects.all():
        if deployment.status == "completed":
            deployment.old_status = "OK"
        elif deployment.status == "failed":
            deployment.old_status = "FAIL"
        else:
            deployment.old_status = "PENDING"
        deployment.save(update_fields=["old_status"])

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0007_add_foreign_key"),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_reverse),
    ]
```

### Batch Processing for Large Tables

```python
# migrations/0009_batch_update.py
from django.db import migrations

def batch_update(apps, schema_editor):
    """Update large table in batches to avoid locking."""
    Deployment = apps.get_model("deployments", "Deployment")

    batch_size = 1000
    batch = []

    # Use iterator() to avoid loading all records into memory
    for deployment in Deployment.objects.all().iterator():
        deployment.processed = True
        batch.append(deployment)

        if len(batch) >= batch_size:
            Deployment.objects.bulk_update(batch, ["processed"])
            batch = []

    # Process remaining records
    if batch:
        Deployment.objects.bulk_update(batch, ["processed"])

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0008_migrate_data"),
    ]

    operations = [
        migrations.RunPython(batch_update, migrations.RunPython.noop),
    ]
```

---

## PostgreSQL-Specific Migrations

### Enable Extension

```python
# migrations/0001_enable_pgvector.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
    ]
```

### Create Vector Column and Index

```python
# migrations/0002_add_vector_column.py
from django.db import migrations
from pgvector.django import VectorField, HnswIndex

class Migration(migrations.Migration):
    dependencies = [
        ("knowledge", "0001_enable_pgvector"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgevector",
            name="embedding",
            field=VectorField(dimensions=1536, null=True),
        ),
        migrations.AddIndex(
            model_name="knowledgevector",
            index=HnswIndex(
                name="knowledge_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
```

### Raw SQL for Complex Operations

```python
# migrations/0010_create_materialized_view.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0009_batch_update"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE MATERIALIZED VIEW deployment_stats AS
                SELECT
                    application_id,
                    COUNT(*) as total_deployments,
                    AVG(risk_score) as avg_risk_score,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
                FROM deployments_deployment
                GROUP BY application_id;

                CREATE UNIQUE INDEX deployment_stats_app_idx
                ON deployment_stats(application_id);
            """,
            reverse_sql="""
                DROP MATERIALIZED VIEW IF EXISTS deployment_stats;
            """,
        ),
    ]
```

---

## Migration Commands

### Development Workflow

```bash
# Create migration after model changes
python manage.py makemigrations app_name

# Show migration SQL (for review)
python manage.py sqlmigrate app_name 0002

# Apply all pending migrations
python manage.py migrate

# Apply specific migration
python manage.py migrate app_name 0002

# Check for missing migrations
python manage.py makemigrations --check

# Show migration status
python manage.py showmigrations
```

### Troubleshooting

```bash
# Fake a migration (mark as applied without running)
python manage.py migrate app_name 0002 --fake

# Reverse to previous migration
python manage.py migrate app_name 0001

# Reverse all migrations for an app
python manage.py migrate app_name zero

# Squash migrations (combine multiple into one)
python manage.py squashmigrations app_name 0001 0010
```

---

## Migration Testing Checklist

```
☐ Migration creates correctly: makemigrations --check
☐ SQL looks correct: sqlmigrate app_name XXXX
☐ Forward migration works: migrate
☐ Reverse migration works: migrate app_name previous
☐ Indexes created correctly: \d+ table_name in psql
☐ Constraints active: Check via pg_constraint
☐ No data loss in forward/reverse cycle
☐ Performance acceptable for large tables
```

---

## Common Pitfalls

### ❌ Modifying Existing Migration

```python
# NEVER do this after migration is applied to production
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name="deployment",
            name="risk_score",
            field=models.DecimalField(max_digits=10, decimal_places=4),  # Changed!
        ),
    ]
```

### ✅ Create New Migration Instead

```python
# Create a new migration to alter the field
class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0002_add_risk_score"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deployment",
            name="risk_score",
            field=models.DecimalField(max_digits=10, decimal_places=4),
        ),
    ]
```

### ❌ Missing Reverse Migration

```python
# This will fail on migrate --reverse
migrations.RunPython(migrate_forward)  # No reverse function!
```

### ✅ Always Provide Reverse

```python
# Always provide reverse function
migrations.RunPython(migrate_forward, migrate_reverse)

# Or explicitly mark as non-reversible
migrations.RunPython(migrate_forward, migrations.RunPython.noop)
```

### ❌ Long-Running Migration Blocking Table

```python
# This locks the table for the entire update
def update_all(apps, schema_editor):
    Model = apps.get_model("app", "Model")
    for obj in Model.objects.all():  # May be millions
        obj.field = calculate(obj)
        obj.save()
```

### ✅ Batch Updates to Reduce Locking

```python
# Process in batches
def update_all(apps, schema_editor):
    Model = apps.get_model("app", "Model")
    batch_size = 1000

    # Use iterator() to avoid loading all into memory
    queryset = Model.objects.all().iterator()
    batch = []

    for obj in queryset:
        obj.field = calculate(obj)
        batch.append(obj)

        if len(batch) >= batch_size:
            Model.objects.bulk_update(batch, ["field"])
            batch = []

    if batch:
        Model.objects.bulk_update(batch, ["field"])
```
