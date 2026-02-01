#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Docker Rebuild Script — Django 5.1.15 Migration Verification

set -euo pipefail

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Rebuild failed with exit code $exit_code" >&2
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT ERR

echo "========================================"
echo "EUCORA Docker Rebuild Script"
echo "========================================"
echo ""
echo "Purpose: Rebuild containers with Django 5.1.15 and verify migrations"
echo "Timeline: ~5-10 minutes"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Validate working directory
if [ ! -f "docker-compose.yml" ] && [ ! -f "docker-compose.dev.yml" ]; then
    echo "Error: Must be run from project root directory" >&2
    exit 1
fi

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo "Error: docker not found" >&2
    exit 1
fi

echo "Step 1/7: Stopping all containers..."
docker compose down || true

echo ""
echo "Step 2/7: Rebuilding web container (no cache)..."
timeout 600 docker compose build web --no-cache || exit 1

echo ""
echo "Step 3/7: Rebuilding celery-worker container (no cache)..."
timeout 600 docker compose build celery-worker --no-cache || exit 1

echo ""
echo "Step 4/7: Rebuilding celery-beat container (no cache)..."
timeout 600 docker compose build celery-beat --no-cache || exit 1

echo ""
echo "Step 5/7: Starting all containers..."
docker compose up -d || exit 1

echo ""
echo "Step 6/7: Waiting for containers to start..."
# Wait for containers to be healthy instead of fixed sleep
for i in {1..60}; do
    if timeout 5 curl -f http://localhost:8000/health/live > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo ""
echo "Step 7/7: Verifying container status..."
docker compose ps

echo ""
echo "========================================"
echo "Verification Steps"
echo "========================================"
echo ""

echo "Checking Django version..."
docker compose exec -T web python -c "import django; print(f'Django version: {django.VERSION}')" || exit 1

echo ""
echo "Checking django-celery-beat version..."
docker compose exec -T web python -c "import django_celery_beat; print(f'django-celery-beat version: {django_celery_beat.__version__}')" || exit 1

echo ""
echo "Checking requests version..."
docker compose exec -T web python -c "import requests; print(f'requests version: {requests.__version__}')" || exit 1

echo ""
echo "Running Django system check..."
docker compose exec -T web python manage.py check --deploy || exit 1

echo ""
echo "Checking migration status..."
docker compose exec -T web python manage.py showmigrations | grep -E "(evidence_store|packaging_factory|cab_workflow)" || exit 1

echo ""
echo "Testing health endpoint..."
timeout 10 curl -sf http://localhost:8000/api/v1/health/liveness/ | python -m json.tool || {
    echo "Health check failed" >&2
    exit 1
}

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
exit 0
