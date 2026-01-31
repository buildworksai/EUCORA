#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Generate migrations for new Django apps
# Usage: ./scripts/generate-migrations.sh

set -e

cd "$(dirname "$0")/.."

echo "Generating migrations for new Django apps..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Generate migrations for each app
echo "Generating migrations for secops_agent..."
python backend/manage.py makemigrations secops_agent

echo "Generating migrations for sre_agent..."
python backend/manage.py makemigrations sre_agent

echo "Generating migrations for kb_triage..."
python backend/manage.py makemigrations kb_triage

echo ""
echo "Migrations generated successfully!"
echo "Next step: Run 'python backend/manage.py migrate' to apply migrations"
