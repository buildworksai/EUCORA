#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
#
# Docker deployment script for E8: AI Agent Workflows
# This script rebuilds containers and verifies deployment

set -e

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
    echo -e "${RED}Error: docker-compose not found${NC}"
    exit 1
fi

COMPOSE_FILE="docker-compose.dev.yml"

echo ""
echo -e "${YELLOW}Step 1: Rebuilding backend container with new dependencies...${NC}"
docker-compose -f "$COMPOSE_FILE" build eucora-api

echo ""
echo -e "${YELLOW}Step 2: Restarting API container (migrations and seeding run automatically)...${NC}"
docker-compose -f "$COMPOSE_FILE" restart eucora-api

echo ""
echo -e "${YELLOW}Step 3: Waiting for container to be ready...${NC}"
sleep 5

echo ""
echo -e "${YELLOW}Step 4: Verifying workflows seeded...${NC}"
WORKFLOW_COUNT=$(docker-compose -f "$COMPOSE_FILE" exec -T eucora-api python manage.py shell -c "
from apps.ai_agents.workflows.models import WorkflowDefinition
print(WorkflowDefinition.objects.count())
" 2>/dev/null | tail -1)

if [ "$WORKFLOW_COUNT" -ge 6 ]; then
    echo -e "${GREEN}✓ Workflows seeded successfully: $WORKFLOW_COUNT workflows${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Expected 6 workflows, found $WORKFLOW_COUNT${NC}"
    echo "  Running seed_workflows manually..."
    docker-compose -f "$COMPOSE_FILE" exec -T eucora-api python manage.py seed_workflows
fi

echo ""
echo -e "${YELLOW}Step 5: Testing API endpoint...${NC}"
if curl -s http://localhost:8000/api/v1/ai/workflows/ > /dev/null; then
    echo -e "${GREEN}✓ Workflows API endpoint responding${NC}"
else
    echo -e "${RED}✗ Workflows API endpoint not responding${NC}"
    echo "  Check container logs: docker-compose -f $COMPOSE_FILE logs eucora-api"
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
echo "View logs: docker-compose -f $COMPOSE_FILE logs -f eucora-api"
