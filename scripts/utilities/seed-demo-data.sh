#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Script to seed demo data for EUCORA

set -euo pipefail

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Demo data seeding failed with exit code $exit_code" >&2
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "🌱 EUCORA Demo Data Seeding Script"
echo "===================================="
echo ""

# Validate paths
if [ ! -d "${BACKEND_DIR}" ]; then
    echo "Error: Backend directory not found: ${BACKEND_DIR}" >&2
    exit 1
fi

# Check if we're in Docker or local environment
if [ -f /.dockerenv ] || [ -n "${DOCKER_CONTAINER:-}" ]; then
    echo "📦 Running in Docker container"
    PYTHON_CMD="python"
    MANAGE_PY="manage.py"
else
    echo "💻 Running in local environment"
    PYTHON_CMD="python3"
    MANAGE_PY="${BACKEND_DIR}/manage.py"

    # Check if virtual environment exists
    if [ -d "${BACKEND_DIR}/venv" ]; then
        echo "🔧 Activating virtual environment..."
        source "${BACKEND_DIR}/venv/bin/activate"
    elif [ -d "${PROJECT_ROOT}/venv" ]; then
        echo "🔧 Activating virtual environment..."
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
    echo "❌ Error: Django is not installed or not in PYTHONPATH" >&2
    echo "   Please install dependencies: pip install -r requirements.txt" >&2
    echo "   Or use Docker: docker-compose exec eucora-api python manage.py seed_demo_data" >&2
    exit 1
fi

# Default values (small dataset for development)
ASSETS="${ASSETS:-100}"
APPLICATIONS="${APPLICATIONS:-10}"
DEPLOYMENTS="${DEPLOYMENTS:-20}"
USERS="${USERS:-5}"
EVENTS="${EVENTS:-100}"
BATCH_SIZE="${BATCH_SIZE:-50}"
CLEAR_EXISTING="${CLEAR_EXISTING:-true}"

echo "📊 Seeding configuration:"
echo "   Assets: ${ASSETS}"
echo "   Applications: ${APPLICATIONS}"
echo "   Deployments: ${DEPLOYMENTS}"
echo "   Users: ${USERS}"
echo "   Events: ${EVENTS}"
echo "   Batch Size: ${BATCH_SIZE}"
echo "   Clear Existing: ${CLEAR_EXISTING}"
echo ""

# Run the seed command with timeout
echo "🚀 Starting demo data seeding..."
timeout 600 "${PYTHON_CMD}" "${MANAGE_PY}" seed_demo_data \
    --assets "${ASSETS}" \
    --applications "${APPLICATIONS}" \
    --deployments "${DEPLOYMENTS}" \
    --users "${USERS}" \
    --events "${EVENTS}" \
    --batch-size "${BATCH_SIZE}" \
    $([ "${CLEAR_EXISTING}" = "true" ] && echo "--clear-existing") \
    || {
        echo "❌ Error seeding demo data" >&2
        exit 1
    }

echo ""
echo "✅ Demo data seeding completed!"
echo ""
echo "🔧 Enabling demo mode..."
"${PYTHON_CMD}" "${MANAGE_PY}" shell -c "
from apps.core.utils import set_demo_mode_enabled
set_demo_mode_enabled(True)
print('Demo mode enabled')
" || echo "⚠️  Warning: Could not enable demo mode (may already be enabled)"

echo ""
echo "✨ Done! Demo data is now available."
echo ""
echo "📝 Next steps:"
echo "   1. Access the admin demo data page: http://localhost:5173/admin/demo-data"
echo "   2. Verify demo data stats are showing non-zero counts"
echo "   3. Ensure demo mode is enabled (toggle in admin page)"
exit 0
