#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Script to seed demo data for EUCORA

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🌱 EUCORA Demo Data Seeding Script"
echo "===================================="
echo ""

# Check if we're in Docker or local environment
if [ -f /.dockerenv ] || [ -n "$DOCKER_CONTAINER" ]; then
    echo "📦 Running in Docker container"
    PYTHON_CMD="python"
    MANAGE_PY="manage.py"
else
    echo "💻 Running in local environment"
    PYTHON_CMD="python3"
    MANAGE_PY="$BACKEND_DIR/manage.py"

    # Check if virtual environment exists
    if [ -d "$BACKEND_DIR/venv" ]; then
        echo "🔧 Activating virtual environment..."
        source "$BACKEND_DIR/venv/bin/activate"
    elif [ -d "$PROJECT_ROOT/venv" ]; then
        echo "🔧 Activating virtual environment..."
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
fi

cd "$BACKEND_DIR"

# Check if Django is available
if ! $PYTHON_CMD -c "import django" 2>/dev/null; then
    echo "❌ Error: Django is not installed or not in PYTHONPATH"
    echo "   Please install dependencies: pip install -r requirements.txt"
    echo "   Or use Docker: docker-compose exec eucora-api python manage.py seed_demo_data"
    exit 1
fi

# Default values (small dataset for development)
ASSETS=${ASSETS:-100}
APPLICATIONS=${APPLICATIONS:-10}
DEPLOYMENTS=${DEPLOYMENTS:-20}
USERS=${USERS:-5}
EVENTS=${EVENTS:-100}
BATCH_SIZE=${BATCH_SIZE:-50}
CLEAR_EXISTING=${CLEAR_EXISTING:-true}

echo "📊 Seeding configuration:"
echo "   Assets: $ASSETS"
echo "   Applications: $APPLICATIONS"
echo "   Deployments: $DEPLOYMENTS"
echo "   Users: $USERS"
echo "   Events: $EVENTS"
echo "   Batch Size: $BATCH_SIZE"
echo "   Clear Existing: $CLEAR_EXISTING"
echo ""

# Run the seed command
echo "🚀 Starting demo data seeding..."
$PYTHON_CMD "$MANAGE_PY" seed_demo_data \
    --assets "$ASSETS" \
    --applications "$APPLICATIONS" \
    --deployments "$DEPLOYMENTS" \
    --users "$USERS" \
    --events "$EVENTS" \
    --batch-size "$BATCH_SIZE" \
    $([ "$CLEAR_EXISTING" = "true" ] && echo "--clear-existing") \
    || {
        echo "❌ Error seeding demo data"
        exit 1
    }

echo ""
echo "✅ Demo data seeding completed!"
echo ""
echo "🔧 Enabling demo mode..."
$PYTHON_CMD "$MANAGE_PY" shell -c "
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
