#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Run tests with coverage for E17, E18, E21 agents
# Usage: ./scripts/run-tests-coverage.sh

set -e

cd "$(dirname "$0")/.."

echo "Running tests with coverage for Sprint 17-18 agents..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests for each app with coverage
echo "Testing secops_agent..."
pytest backend/apps/secops_agent/tests/ \
    --cov=backend/apps/secops_agent \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/secops_agent \
    --cov-fail-under=90 \
    -v

echo ""
echo "Testing sre_agent..."
pytest backend/apps/sre_agent/tests/ \
    --cov=backend/apps/sre_agent \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/sre_agent \
    --cov-fail-under=90 \
    -v

echo ""
echo "Testing kb_triage..."
pytest backend/apps/kb_triage/tests/ \
    --cov=backend/apps/kb_triage \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/kb_triage \
    --cov-fail-under=90 \
    -v

echo ""
echo "All tests completed!"
echo "Coverage reports available in htmlcov/ directory"
