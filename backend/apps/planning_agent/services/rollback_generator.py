# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Rollback Plan Generator.

Generates rollback plans for deployments.
"""
import logging
from typing import List

from apps.planning_agent.models import DeploymentPlan, RollbackPlan

logger = logging.getLogger(__name__)


class RollbackPlanGenerator:
    """Generate rollback plans."""

    def generate_rollback_plan(self, plan: DeploymentPlan) -> RollbackPlan:
        """
        Generate rollback plan for deployment.

        Args:
            plan: Deployment plan

        Returns:
            RollbackPlan record
        """
        # Define trigger conditions
        trigger_conditions = [
            "Success rate drops below threshold",
            "Critical errors detected",
            "User complaints exceed threshold",
            "Performance degradation detected",
        ]

        # Generate rollback steps (reverse order of rings)
        rollback_steps = []
        for ring in plan.rings.all().order_by("-ring_number"):
            rollback_steps.append(
                {
                    "ring": ring.ring_name,
                    "action": f"Rollback {ring.device_count} devices in {ring.ring_name}",
                    "estimated_minutes": max(5, ring.device_count // 10),
                }
            )

        # Estimate total duration
        estimated_duration = sum(step["estimated_minutes"] for step in rollback_steps)

        # Determine if CAB approval required
        requires_cab_approval = plan.overall_risk_score > 50 or len(plan.rings.all()) > 3

        # Create or update rollback plan
        rollback, _ = RollbackPlan.objects.update_or_create(
            deployment_plan=plan,
            defaults={
                "trigger_conditions": trigger_conditions,
                "rollback_steps": rollback_steps,
                "estimated_duration_minutes": estimated_duration,
                "requires_cab_approval": requires_cab_approval,
            },
        )

        return rollback


def generate_rollback_plan(plan: DeploymentPlan) -> RollbackPlan:
    """
    Generate rollback plan.

    Args:
        plan: Deployment plan

    Returns:
        Rollback plan
    """
    generator = RollbackPlanGenerator()
    return generator.generate_rollback_plan(plan)
