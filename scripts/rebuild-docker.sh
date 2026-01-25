#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Docker Rebuild Script — Django 5.1.15 Migration Verification

set -e  # Exit on error

echo "========================================"
echo "EUCORA Docker Rebuild Script"
echo "========================================"
echo ""
echo "Purpose: Rebuild containers with Django 5.1.15 and verify migrations"
echo "Timeline: ~5-10 minutes"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

echo "Step 1/7: Stopping all containers..."
docker compose down

echo ""
echo "Step 2/7: Rebuilding web container (no cache)..."
docker compose build web --no-cache

echo ""
echo "Step 3/7: Rebuilding celery-worker container (no cache)..."
docker compose build celery-worker --no-cache

echo ""
echo "Step 4/7: Rebuilding celery-beat container (no cache)..."
docker compose build celery-beat --no-cache

echo ""
echo "Step 5/7: Starting all containers..."
docker compose up -d

echo ""
echo "Step 6/7: Waiting for containers to start (30 seconds)..."
sleep 30

echo ""
echo "Step 7/7: Verifying container status..."
docker compose ps

echo ""
echo "========================================"
echo "Verification Steps"
echo "========================================"
echo ""

echo "Checking Django version..."
docker compose exec -T web python -c "import django; print(f'Django version: {django.VERSION}')"

echo ""
echo "Checking django-celery-beat version..."
docker compose exec -T web python -c "import django_celery_beat; print(f'django-celery-beat version: {django_celery_beat.__version__}')"

echo ""
echo "Checking requests version..."
docker compose exec -T web python -c "import requests; print(f'requests version: {requests.__version__}')"

echo ""
echo "Running Django system check..."
docker compose exec -T web python manage.py check --deploy

echo ""
echo "Checking migration status..."
docker compose exec -T web python manage.py showmigrations | grep -E "(evidence_store|packaging_factory|cab_workflow)"

echo ""
echo "Testing health endpoint..."
curl -s http://localhost:8000/api/v1/health/liveness/ | python -m json.tool || echo "Health check failed"

echo ""
echo "========================================"
echo "Rebuild Complete!"
echo "========================================"
echo ""
echo "Expected Results:"
echo "  ✅ Django version: (5, 1, 15, 'final', 0)"
echo "  ✅ django-celery-beat version: 2.8.1"
echo "  ✅ requests version: 2.32.5"
echo "  ✅ System check: 0 errors"
echo "  ✅ All migrations: [X] (applied)"
echo "  ✅ Health check: 200 OK"
echo ""
echo "Next Steps:"
echo "  1. Review the output above"
echo "  2. If all ✅, run: docker compose logs web | tail -50"
echo "  3. If any errors, see: backend/reports/COMMIT-SUMMARY-2026-01-25.md"
echo ""
