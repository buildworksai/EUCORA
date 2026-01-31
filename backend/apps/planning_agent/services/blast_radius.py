# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Blast Radius Calculator.

Calculates blast radius and impact for deployments.
"""
import logging
from typing import Dict, List

from apps.planning_agent.models import BlastRadiusAnalysis, DeploymentPlan, RingDevice

logger = logging.getLogger(__name__)


class BlastRadiusCalculator:
    """Calculate blast radius for deployments."""

    def calculate_blast_radius(self, plan: DeploymentPlan) -> BlastRadiusAnalysis:
        """
        Calculate blast radius for a deployment plan.

        Args:
            plan: Deployment plan

        Returns:
            BlastRadiusAnalysis record
        """
        # Gather all devices across rings
        all_devices = []
        for ring in plan.rings.all():
            all_devices.extend(ring.devices.all())

        # Calculate metrics
        total_users = len(set(d.user_principal for d in all_devices if d.user_principal))
        vip_users = len([d for d in all_devices if d.criticality == RingDevice.Criticality.VIP])
        departments = self._extract_departments(all_devices)
        regions = self._extract_regions(all_devices)
        critical_systems = self._identify_critical_systems(all_devices)

        # Calculate productivity impact score
        productivity_impact = self._calculate_productivity_impact(total_users, vip_users, len(all_devices))

        # Generate recommendations
        recommendations = self._generate_recommendations(total_users, vip_users, len(departments), productivity_impact)

        # Create or update analysis
        analysis, _ = BlastRadiusAnalysis.objects.update_or_create(
            plan=plan,
            defaults={
                "total_users_affected": total_users,
                "vip_users_affected": vip_users,
                "departments_affected": departments,
                "regions_affected": regions,
                "critical_systems_affected": critical_systems,
                "productivity_impact_score": productivity_impact,
                "recommendations": recommendations,
            },
        )

        return analysis

    def _extract_departments(self, devices: List[RingDevice]) -> List[str]:
        """Extract unique departments from devices."""
        # TODO: Extract from user profiles or device metadata
        return ["Engineering", "Sales", "Support", "Operations"]

    def _extract_regions(self, devices: List[RingDevice]) -> List[str]:
        """Extract unique regions from devices."""
        # TODO: Extract from device metadata
        return ["US-East", "US-West", "EU-Central"]

    def _identify_critical_systems(self, devices: List[RingDevice]) -> List[str]:
        """Identify critical systems affected."""
        # TODO: Identify based on device roles or applications
        return []

    def _calculate_productivity_impact(self, total_users: int, vip_users: int, device_count: int) -> float:
        """
        Calculate productivity impact score (0-100).

        Higher score = higher impact.
        """
        base_score = min(100.0, (device_count / 1000.0) * 50.0)  # Base on device count
        vip_penalty = vip_users * 10.0  # VIP users add to impact
        return min(100.0, base_score + vip_penalty)

    def _generate_recommendations(
        self, total_users: int, vip_users: int, department_count: int, impact_score: float
    ) -> List[str]:
        """Generate recommendations based on blast radius."""
        recommendations = []

        if impact_score > 70:
            recommendations.append("Consider phased rollout with extended pause points")
        if vip_users > 10:
            recommendations.append("Notify VIP users in advance")
        if department_count > 5:
            recommendations.append("Coordinate with department heads")
        if total_users > 500:
            recommendations.append("Schedule during maintenance window")

        return recommendations


def calculate_blast_radius(plan: DeploymentPlan) -> BlastRadiusAnalysis:
    """
    Calculate blast radius.

    Args:
        plan: Deployment plan

    Returns:
        Blast radius analysis
    """
    calculator = BlastRadiusCalculator()
    return calculator.calculate_blast_radius(plan)
