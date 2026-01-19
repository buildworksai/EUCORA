#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Script to check demo data status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔍 EUCORA Demo Data Status Check"
echo "=================================="
echo ""

# Check if we're in Docker or local environment
if [ -f /.dockerenv ] || [ -n "$DOCKER_CONTAINER" ]; then
    PYTHON_CMD="python"
    MANAGE_PY="manage.py"
else
    PYTHON_CMD="python3"
    MANAGE_PY="$BACKEND_DIR/manage.py"
    
    if [ -d "$BACKEND_DIR/venv" ]; then
        source "$BACKEND_DIR/venv/bin/activate"
    elif [ -d "$PROJECT_ROOT/venv" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
fi

cd "$BACKEND_DIR"

# Check if Django is available
if ! $PYTHON_CMD -c "import django" 2>/dev/null; then
    echo "❌ Error: Django is not installed"
    echo "   Use Docker: docker-compose exec eucora-api python manage.py shell"
    exit 1
fi

echo "📊 Checking demo data status..."
echo ""

$PYTHON_CMD "$MANAGE_PY" shell << 'EOF'
from apps.core.demo_data import demo_data_stats
from apps.core.utils import get_demo_mode_enabled

stats = demo_data_stats()
demo_mode = get_demo_mode_enabled()

print("Demo Mode Enabled:", demo_mode)
print("")
print("Demo Data Counts:")
print(f"  Assets: {stats['assets']:,}")
print(f"  Applications: {stats['applications']:,}")
print(f"  Deployments: {stats['deployments']:,}")
print(f"  Ring Deployments: {stats['ring_deployments']:,}")
print(f"  CAB Approvals: {stats['cab_approvals']:,}")
print(f"  Evidence Packs: {stats['evidence_packs']:,}")
print(f"  Events: {stats['events']:,}")
print(f"  Users: {stats['users']:,}")
print("")

total = sum(stats.values())
if total == 0:
    print("⚠️  WARNING: No demo data found!")
    print("   Run: ./scripts/utilities/seed-demo-data.sh")
elif not demo_mode:
    print("⚠️  WARNING: Demo mode is disabled!")
    print("   Enable it via admin page or run:")
    print("   python manage.py shell -c \"from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True)\"")
else:
    print("✅ Demo data is available and demo mode is enabled")
EOF
