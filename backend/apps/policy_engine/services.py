# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine services for risk scoring.
"""
import logging
from typing import Dict

from .models import RiskAssessment, RiskModel

logger = logging.getLogger(__name__)


def calculate_risk_score(evidence_pack: Dict, correlation_id: str) -> Dict:
    """
    Calculate risk score from evidence pack using active risk model.

    Args:
        evidence_pack: Evidence pack data with all required fields
        correlation_id: Deployment intent correlation ID

    Returns:
        {
            'risk_score': int (0-100),
            'factor_scores': dict,
            'requires_cab_approval': bool,
            'model_version': str,
        }

    Raises:
        ValueError: If no active risk model found
    """
    risk_model = RiskModel.objects.filter(is_active=True).first()
    if not risk_model:
        raise ValueError("No active risk model found")

    factor_scores = {}
    weighted_sum = 0.0

    for factor in risk_model.factors:
        name = factor["name"]
        weight = factor["weight"]
        rubric = factor.get("rubric", {})

        # Evaluate factor score (0.0 - 1.0) based on evidence pack
        normalized_score = _evaluate_factor(name, evidence_pack, rubric)
        factor_scores[name] = normalized_score

        weighted_sum += weight * normalized_score

    # Clamp to 0-100
    risk_score = int(max(0, min(100, weighted_sum * 100)))

    # Create risk assessment record
    assessment = RiskAssessment.objects.create(
        deployment_intent_id=correlation_id,
        risk_model_version=risk_model.version,
        risk_score=risk_score,
        factor_scores=factor_scores,
        requires_cab_approval=risk_score > risk_model.threshold,
    )

    logger.info(
        f"Risk assessment completed: {correlation_id} - Score: {risk_score}",
        extra={"correlation_id": correlation_id, "risk_score": risk_score},
    )

    return {
        "risk_score": risk_score,
        "factor_scores": factor_scores,
        "requires_cab_approval": risk_score > risk_model.threshold,
        "model_version": risk_model.version,
    }


def _evaluate_factor(factor_name: str, evidence_pack: Dict, rubric: Dict) -> float:
    """
    Evaluate a single risk factor.

    Args:
        factor_name: Name of the factor (e.g., 'Privilege Elevation')
        evidence_pack: Complete evidence pack data
        rubric: Scoring rubric for this factor

    Returns:
        Normalized score (0.0 - 1.0)
    """
    # Factor 1: Privilege Elevation
    if factor_name == "Privilege Elevation":
        if evidence_pack.get("requires_admin"):
            return 1.0
        elif evidence_pack.get("requests_elevation"):
            return 0.5
        else:
            return 0.0

    # Factor 2: Blast Radius
    elif factor_name == "Blast Radius":
        ring = evidence_pack.get("target_ring", "lab").lower()
        ring_scores = {
            "lab": 0.0,
            "canary": 0.2,
            "pilot": 0.4,
            "department": 0.7,
            "global": 1.0,
        }
        return ring_scores.get(ring, 0.5)

    # Factor 3: Rollback Complexity
    elif factor_name == "Rollback Complexity":
        has_rollback_plan = evidence_pack.get("has_rollback_plan", False)
        rollback_tested = evidence_pack.get("rollback_tested", False)
        if has_rollback_plan and rollback_tested:
            return 0.0
        elif has_rollback_plan:
            return 0.5
        else:
            return 1.0

    # Factor 4: Vulnerability Severity
    elif factor_name == "Vulnerability Severity":
        vuln_scan = evidence_pack.get("vulnerability_scan_results", {})
        critical_count = vuln_scan.get("critical", 0)
        high_count = vuln_scan.get("high", 0)

        if critical_count > 0:
            return 1.0
        elif high_count > 0:
            return 0.7
        elif vuln_scan.get("medium", 0) > 0:
            return 0.3
        else:
            return 0.0

    # Factor 5: Compliance Impact
    elif factor_name == "Compliance Impact":
        compliance_tags = evidence_pack.get("compliance_tags", [])
        if "sox" in compliance_tags or "hipaa" in compliance_tags:
            return 1.0
        elif "pci" in compliance_tags:
            return 0.7
        elif compliance_tags:
            return 0.3
        else:
            return 0.0

    # Factor 6: Deployment Frequency
    elif factor_name == "Deployment Frequency":
        from datetime import timedelta

        from django.utils import timezone

        from apps.event_store.models import DeploymentEvent

        # Query deployment frequency for this app in last 30 days
        app_name = evidence_pack.get("app_name", "")
        thirty_days_ago = timezone.now() - timedelta(days=30)

        deployment_count = DeploymentEvent.objects.filter(
            event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            event_data__app_name=app_name,
            created_at__gte=thirty_days_ago,
        ).count()

        # Risk scoring: More frequent deployments = lower risk (better tested)
        # 0 deployments = 1.0 (high risk, untested)
        # 1-2 deployments = 0.7 (medium-high risk)
        # 3-5 deployments = 0.4 (medium risk)
        # 6-10 deployments = 0.2 (low-medium risk)
        # 10+ deployments = 0.0 (low risk, well-tested)
        if deployment_count == 0:
            return 1.0
        elif deployment_count <= 2:
            return 0.7
        elif deployment_count <= 5:
            return 0.4
        elif deployment_count <= 10:
            return 0.2
        else:
            return 0.0

    # Factor 7: Evidence Completeness
    elif factor_name == "Evidence Completeness":
        required_fields = ["artifact_hash", "sbom_data", "vulnerability_scan_results", "rollback_plan"]
        missing_fields = [f for f in required_fields if not evidence_pack.get(f)]
        completeness = 1.0 - (len(missing_fields) / len(required_fields))
        return 1.0 - completeness  # Invert: more complete = lower risk

    # Factor 8: Historical Success Rate
    elif factor_name == "Historical Success Rate":
        from datetime import timedelta

        from django.utils import timezone

        from apps.event_store.models import DeploymentEvent

        # Query historical success rate for this app in last 90 days
        app_name = evidence_pack.get("app_name", "")
        ninety_days_ago = timezone.now() - timedelta(days=90)

        # Count completed deployments
        completed_count = DeploymentEvent.objects.filter(
            event_type=DeploymentEvent.EventType.DEPLOYMENT_COMPLETED,
            event_data__app_name=app_name,
            created_at__gte=ninety_days_ago,
        ).count()

        # Count failed deployments
        failed_count = DeploymentEvent.objects.filter(
            event_type=DeploymentEvent.EventType.DEPLOYMENT_FAILED,
            event_data__app_name=app_name,
            created_at__gte=ninety_days_ago,
        ).count()

        total_count = completed_count + failed_count

        if total_count == 0:
            # No historical data = medium risk
            return 0.5

        success_rate = completed_count / total_count

        # Risk scoring: Higher success rate = lower risk
        # 100% success = 0.0 (low risk)
        # 90-99% success = 0.1 (low-medium risk)
        # 75-89% success = 0.3 (medium risk)
        # 50-74% success = 0.6 (medium-high risk)
        # <50% success = 1.0 (high risk)
        if success_rate >= 0.99:
            return 0.0
        elif success_rate >= 0.90:
            return 0.1
        elif success_rate >= 0.75:
            return 0.3
        elif success_rate >= 0.50:
            return 0.6
        else:
            return 1.0

    # Default: medium risk
    else:
        logger.warning(f"Unknown risk factor: {factor_name}")
        return 0.5
