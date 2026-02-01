#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Generate migrations for new Django apps
# Usage: ./scripts/generate-migrations.sh

set -euo pipefail

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Migration generation failed with exit code $exit_code" >&2
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT ERR

cd "$(dirname "$0")/.."

# Validate working directory
if [ ! -d "backend" ] || [ ! -f "backend/manage.py" ]; then
    echo "Error: Must be run from project root directory with backend/manage.py present" >&2
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: python not found. Please install Python." >&2
    exit 1
fi

# Check if Django manage.py exists and is executable
if [ ! -x "backend/manage.py" ]; then
    echo "Error: backend/manage.py not found or not executable" >&2
    exit 1
fi

# Validate migrations directory is writable
if [ ! -w "backend" ]; then
    echo "Error: backend directory is not writable" >&2
    exit 1
fi

echo "Generating migrations for new Django apps..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Generate migrations for each app with timeout
echo "Generating migrations for secops_agent..."
timeout 60 python backend/manage.py makemigrations secops_agent || exit 1

echo "Generating migrations for sre_agent..."
timeout 60 python backend/manage.py makemigrations sre_agent || exit 1

echo "Generating migrations for kb_triage..."
timeout 60 python backend/manage.py makemigrations kb_triage || exit 1

echo ""
echo "Migrations generated successfully!"
echo "Next step: Run 'python backend/manage.py migrate' to apply migrations"
exit 0
