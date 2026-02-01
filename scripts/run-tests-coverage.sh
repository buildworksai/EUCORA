#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Run tests with coverage for E17, E18, E21 agents
# Usage: ./scripts/run-tests-coverage.sh

set -euo pipefail

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Script failed with exit code $exit_code" >&2
    fi
    # Cleanup test artifacts if needed
    if [ -d "htmlcov" ]; then
        echo "Coverage reports available in htmlcov/ directory"
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT ERR

cd "$(dirname "$0")/.."

# Validate working directory
if [ ! -d "backend" ]; then
    echo "Error: Must be run from project root directory" >&2
    exit 1
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not found. Please install pytest." >&2
    exit 1
fi

echo "Running tests with coverage for Sprint 17-18 agents..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests for each app with coverage and timeout
echo "Testing secops_agent..."
timeout 300 pytest backend/apps/secops_agent/tests/ \
    --cov=backend/apps/secops_agent \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/secops_agent \
    --cov-fail-under=90 \
    -v || exit 1

echo ""
echo "Testing sre_agent..."
timeout 300 pytest backend/apps/sre_agent/tests/ \
    --cov=backend/apps/sre_agent \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/sre_agent \
    --cov-fail-under=90 \
    -v || exit 1

echo ""
echo "Testing kb_triage..."
timeout 300 pytest backend/apps/kb_triage/tests/ \
    --cov=backend/apps/kb_triage \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/kb_triage \
    --cov-fail-under=90 \
    -v || exit 1

echo ""
echo "All tests completed!"
echo "Coverage reports available in htmlcov/ directory"
exit 0
