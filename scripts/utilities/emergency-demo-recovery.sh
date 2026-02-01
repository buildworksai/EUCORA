#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Emergency Demo Recovery Script
# Use this when demos break during customer presentations

set -euo pipefail

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Emergency recovery failed with exit code $exit_code" >&2
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "🚨 EMERGENCY DEMO RECOVERY"
echo "=========================="
echo ""

# Validate paths
if [ ! -d "${BACKEND_DIR}" ]; then
    echo "Error: Backend directory not found: ${BACKEND_DIR}" >&2
    exit 1
fi

# Check if we're in Docker or local environment
if [ -f /.dockerenv ] || [ -n "${DOCKER_CONTAINER:-}" ]; then
    PYTHON_CMD="python"
    MANAGE_PY="manage.py"
    echo "📦 Running in Docker container"
else
    PYTHON_CMD="python3"
    MANAGE_PY="${BACKEND_DIR}/manage.py"
    echo "💻 Running in local environment"

    if [ -d "${BACKEND_DIR}/venv" ]; then
        source "${BACKEND_DIR}/venv/bin/activate"
    elif [ -d "${PROJECT_ROOT}/venv" ]; then
        source "${PROJECT_ROOT}/venv/bin/activate"
    fi
fi

cd "${BACKEND_DIR}"

# Validate manage.py exists
if [ ! -f "${MANAGE_PY}" ]; then
    echo "Error: manage.py not found at ${MANAGE_PY}" >&2
    exit 1
fi

# Check if Django is available
if ! "${PYTHON_CMD}" -c "import django" 2>/dev/null; then
    echo "❌ Error: Django is not installed" >&2
    echo "   Use Docker: docker-compose exec eucora-api bash -c 'python manage.py shell'" >&2
    exit 1
fi

echo ""
echo "Step 1: Checking database connection..."
if ! timeout 30 "${PYTHON_CMD}" -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.db import connection
connection.ensure_connection()
print('✅ Database connected')
" 2>&1; then
    echo "❌ Database connection failed!" >&2
    exit 1
fi

echo ""
echo "Step 2: Checking demo data status..."
timeout 60 "${PYTHON_CMD}" "${MANAGE_PY}" shell << 'EOF'
import sys
from apps.core.demo_data import demo_data_stats
from apps.core.utils import get_demo_mode_enabled

try:
    stats = demo_data_stats()
    total = sum(stats.values())
    demo_mode = get_demo_mode_enabled()

    print(f"Demo Mode: {'✅ ENABLED' if demo_mode else '❌ DISABLED'}")
    print(f"Total Demo Items: {total:,}")
    print(f"  Assets: {stats['assets']:,}")
    print(f"  Applications: {stats['applications']:,}")
    print(f"  Deployments: {stats['deployments']:,}")
    print(f"  Events: {stats['events']:,}")

    if total == 0:
        print("\n⚠️  NO DEMO DATA FOUND - Will seed minimum dataset")
        sys.exit(1)
    elif not demo_mode:
        print("\n⚠️  DEMO MODE DISABLED - Will enable")
        sys.exit(2)
    else:
        print("\n✅ Demo data exists and demo mode is enabled")
        sys.exit(0)
except Exception as e:
    print(f"❌ Error checking status: {e}")
    sys.exit(3)
EOF

EXIT_CODE=$?

if [ ${EXIT_CODE} -eq 1 ]; then
    echo ""
    echo "Step 3: Seeding minimum demo data (fast recovery)..."
    timeout 300 "${PYTHON_CMD}" "${MANAGE_PY}" seed_demo_data \
        --assets 100 \
        --applications 10 \
        --deployments 20 \
        --users 5 \
        --events 100 \
        --batch-size 50 \
        || {
            echo "❌ Seeding failed, trying smaller batch..." >&2
            timeout 300 "${PYTHON_CMD}" "${MANAGE_PY}" seed_demo_data \
                --assets 50 \
                --applications 5 \
                --deployments 10 \
                --users 3 \
                --events 50 \
                --batch-size 25 \
                || echo "⚠️  Seeding partially failed, but continuing..." >&2
        }
elif [ ${EXIT_CODE} -eq 2 ]; then
    echo ""
    echo "Step 3: Enabling demo mode..."
    timeout 30 "${PYTHON_CMD}" "${MANAGE_PY}" shell -c "
from apps.core.utils import set_demo_mode_enabled
set_demo_mode_enabled(True)
print('✅ Demo mode enabled')
" || echo "⚠️  Failed to enable demo mode" >&2
fi

echo ""
echo "Step 4: Final verification..."
timeout 60 "${PYTHON_CMD}" "${MANAGE_PY}" shell << 'EOF'
from apps.core.demo_data import demo_data_stats
from apps.core.utils import get_demo_mode_enabled

stats = demo_data_stats()
demo_mode = get_demo_mode_enabled()
total = sum(stats.values())

print(f"Demo Mode: {'✅ ENABLED' if demo_mode else '❌ DISABLED'}")
print(f"Total Demo Items: {total:,}")

if demo_mode and total > 0:
    print("\n✅ RECOVERY SUCCESSFUL - System ready for demo")
    print(f"   Assets: {stats['assets']:,}")
    print(f"   Applications: {stats['applications']:,}")
    print(f"   Deployments: {stats['deployments']:,}")
else:
    print("\n⚠️  PARTIAL RECOVERY - Some issues remain")
    if not demo_mode:
        print("   - Demo mode is still disabled")
    if total == 0:
        print("   - No demo data found")
EOF

echo ""
echo "=========================="
echo "Recovery complete!"
echo ""
echo "Next steps:"
echo "  1. Check health: curl http://localhost:8000/health/demo-ready"
echo "  2. Access admin: http://localhost:5173/admin/demo-data"
echo "  3. If issues persist, check logs: docker-compose logs eucora-api"
exit 0
