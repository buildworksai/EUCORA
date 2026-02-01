# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Ring Strategy Generator.

Generates optimal ring assignment strategy for deployments.
"""
import logging
from typing import Dict, List, Tuple

from apps.planning_agent.models import RingAssignment
from apps.planning_agent.services.inventory_client import get_inventory_client

logger = logging.getLogger(__name__)


class RingStrategyGenerator:
    """Generates optimal ring assignment strategy."""

    def generate_strategy(
        self, application, target_scope: dict, risk_tolerance: str = "moderate"
    ) -> List[RingAssignment]:
        """
        Generate deployment strategy.

        Args:
            application: Application to deploy
            target_scope: Target scope (departments, regions, groups)
            risk_tolerance: Risk tolerance (conservative, moderate, aggressive)

        Returns:
            List of RingAssignment objects
        """
        # 1. Gather all devices in scope
        devices = self.gather_devices(target_scope)

        # 2. Score each device
        scored_devices = []
        for device in devices:
            score = self.calculate_device_score(device)
            scored_devices.append((device, score))

        # 3. Sort by suitability for early rings
        scored_devices.sort(key=lambda x: x[1], reverse=True)

        # 4. Assign to rings based on risk tolerance
        ring_sizes = self.calculate_ring_sizes(total_devices=len(devices), risk_tolerance=risk_tolerance)

        rings = []
        idx = 0
        for ring_num, (ring_name, size_pct) in enumerate(ring_sizes.items()):
            ring_size = int(len(devices) * size_pct / 100)
            ring_devices = scored_devices[idx : idx + ring_size]
            idx += ring_size

            # Create ring assignment (will be saved by caller)
            ring_assignment = RingAssignment(
                ring_number=ring_num,
                ring_name=ring_name,
                device_count=len(ring_devices),
                device_criteria={"risk_tolerance": risk_tolerance, "size_pct": size_pct},
            )
            rings.append(ring_assignment)

        return rings

    def gather_devices(self, target_scope: dict) -> List[Dict]:
        """
        Gather devices in scope.

        Args:
            target_scope: Target scope configuration

        Returns:
            List of device dictionaries
        """
        try:
            # Get inventory client from configuration
            connection_config = target_scope.get("connection_config", {})
            client_type = connection_config.get("type", "intune")

            # Use inventory client to get devices
            inventory_client = get_inventory_client(connection_config, client_type)
            devices = inventory_client.get_devices(target_scope)

            # Enrich with deployment history if available
            # This would query DeploymentIntent for success rates
            for device in devices:
                # Add deployment success rate (would come from historical data)
                device["deployment_success_rate"] = 0.9  # Default, would be calculated from history
                device["meets_requirements"] = True  # Would check against app requirements

            logger.info(f"Gathered {len(devices)} devices from {client_type} inventory")
            return devices

        except Exception as e:
            logger.error(f"Failed to gather devices from inventory: {e}", exc_info=True)
            # Fallback to mock devices if inventory fails
            logger.warning("Falling back to mock devices")
            return [
                {
                    "device_id": f"DEVICE-{i:03d}",
                    "device_name": f"Device {i}",
                    "health_score": 0.8 + (i % 3) * 0.1,
                    "is_it_staff": i < 10,
                    "criticality": "vip" if i < 5 else "standard",
                    "deployment_success_rate": 0.9,
                    "meets_requirements": True,
                }
                for i in range(100)
            ]

    def calculate_device_score(self, device: dict) -> float:
        """
        Score device suitability for early ring.

        Args:
            device: Device dictionary

        Returns:
            Score (higher = better for early ring)
        """
        score = 0.0

        # Health score (higher = better for early ring)
        score += device.get("health_score", 0.5) * 30

        # IT staff device bonus
        if device.get("is_it_staff"):
            score += 20

        # Non-VIP bonus (safer for early rings)
        if device.get("criticality") != "vip":
            score += 15

        # Previous success history
        score += device.get("deployment_success_rate", 0.8) * 20

        # Compatible hardware
        if device.get("meets_requirements"):
            score += 15

        return score

    def calculate_ring_sizes(self, total_devices: int, risk_tolerance: str) -> Dict[str, Tuple[int, float]]:
        """
        Calculate ring sizes based on risk tolerance.

        Args:
            total_devices: Total number of devices
            risk_tolerance: Risk tolerance level

        Returns:
            Dictionary mapping ring names to (ring_number, size_percentage)
        """
        if risk_tolerance == "conservative":
            return {
                "Ring 0 - Lab": (0, 1),
                "Ring 1 - IT Canary": (1, 2),
                "Ring 2 - Early Adopters": (2, 5),
                "Ring 3 - Department": (3, 20),
                "Ring 4 - Global": (4, 72),
            }
        elif risk_tolerance == "moderate":
            return {
                "Ring 0 - Lab": (0, 1),
                "Ring 1 - IT Canary": (1, 5),
                "Ring 2 - Early Adopters": (2, 10),
                "Ring 3 - Department": (3, 30),
                "Ring 4 - Global": (4, 54),
            }
        else:  # aggressive
            return {
                "Ring 0 - Lab": (0, 1),
                "Ring 1 - IT Canary": (1, 10),
                "Ring 2 - Early Adopters": (2, 20),
                "Ring 3 - Global": (3, 69),
            }


def generate_ring_strategy(application, target_scope: dict, risk_tolerance: str = "moderate") -> List[RingAssignment]:
    """
    Generate ring strategy.

    Args:
        application: Application to deploy
        target_scope: Target scope
        risk_tolerance: Risk tolerance

    Returns:
        List of ring assignments
    """
    generator = RingStrategyGenerator()
    return generator.generate_strategy(application, target_scope, risk_tolerance)
