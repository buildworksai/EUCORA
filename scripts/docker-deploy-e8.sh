#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Docker deployment script for E8: AI Agent Workflows
# This script rebuilds containers and verifies deployment

set -euo pipefail

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}Error: Deployment failed with exit code $exit_code${NC}" >&2
    fi
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT ERR

echo "=========================================="
echo "E8: AI Agent Workflows - Docker Deployment"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found${NC}" >&2
    exit 1
fi

COMPOSE_FILE="docker-compose.dev.yml"

echo ""
echo -e "${YELLOW}Step 1: Rebuilding backend container with new dependencies...${NC}"
timeout 600 docker-compose -f "${COMPOSE_FILE}" build eucora-api || exit 1

echo ""
echo -e "${YELLOW}Step 2: Restarting API container (migrations and seeding run automatically)...${NC}"
docker-compose -f "${COMPOSE_FILE}" restart eucora-api || exit 1

echo ""
echo -e "${YELLOW}Step 3: Waiting for container to be ready...${NC}"
# Wait for container to be healthy instead of fixed sleep
for i in {1..30}; do
    if docker-compose -f "${COMPOSE_FILE}" ps eucora-api | grep -q "Up"; then
        sleep 2
        if timeout 5 curl -f http://localhost:8000/health/live > /dev/null 2>&1; then
            break
        fi
    fi
    sleep 1
done

echo ""
echo -e "${YELLOW}Step 4: Verifying workflows seeded...${NC}"
WORKFLOW_COUNT=$(docker-compose -f "${COMPOSE_FILE}" exec -T eucora-api python manage.py shell -c "
from apps.ai_agents.workflows.models import WorkflowDefinition
print(WorkflowDefinition.objects.count())
" 2>/dev/null | tail -1 || echo "0")

if [ "${WORKFLOW_COUNT}" -ge 6 ]; then
    echo -e "${GREEN}✓ Workflows seeded successfully: ${WORKFLOW_COUNT} workflows${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Expected 6 workflows, found ${WORKFLOW_COUNT}${NC}"
    echo "  Running seed_workflows manually..."
    docker-compose -f "${COMPOSE_FILE}" exec -T eucora-api python manage.py seed_workflows || exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Testing API endpoint...${NC}"
if timeout 10 curl -sf http://localhost:8000/api/v1/ai/workflows/ > /dev/null; then
    echo -e "${GREEN}✓ Workflows API endpoint responding${NC}"
else
    echo -e "${RED}✗ Workflows API endpoint not responding${NC}"
    echo "  Check container logs: docker-compose -f ${COMPOSE_FILE} logs eucora-api"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Access frontend: http://localhost:5173"
echo "  2. Navigate to AI Agent Hub"
echo "  3. Click 'Workflows' tab"
echo "  4. Start a workflow to test"
echo ""
echo "View logs: docker-compose -f ${COMPOSE_FILE} logs -f eucora-api"
exit 0
