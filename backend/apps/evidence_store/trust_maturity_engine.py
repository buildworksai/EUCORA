# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: Trust Maturity Engine

Progressive automation based on demonstrated control effectiveness.

Maturity Levels:
- Level 0: Baseline (100% CAB review) - Weeks 1-4
- Level 1: Cautious (Limited auto-approve) - Weeks 5-8
- Level 2: Moderate (Balanced) - Weeks 9-12
- Level 3: Mature (Evidence-based) - Month 4+
- Level 4: Optimized (Maximum automation) - Month 6+

Progression criteria:
- Incident rate below threshold
- P1/P2 incident count
- Weeks of clean operation
- Control effectiveness validation

Implementation Date: 2026-01-23
"""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.evidence_store.models_p5_5 import (
    DeploymentIncident,
    RiskModelVersion,
    TrustMaturityLevel,
    TrustMaturityProgress,
)

logger = logging.getLogger(__name__)


class TrustMaturityEngine:
    """
    Evaluate trust maturity progression and recommend level changes.

    Usage:
        engine = TrustMaturityEngine()
        result = engine.evaluate_maturity_progression(
            current_level='LEVEL_0_BASELINE',
            evaluation_period_weeks=4
        )

        if result['ready_to_progress']:
            # Activate next risk model version
            # Submit to CAB for approval
    """

    def __init__(self):
        self.evaluation_timestamp = timezone.now()

    def evaluate_maturity_progression(self, current_level: str, evaluation_period_weeks: int = 4) -> Dict[str, Any]:
        """
        Evaluate whether criteria are met to progress to next maturity level.

        Args:
            current_level: Current maturity level (e.g., 'LEVEL_0_BASELINE')
            evaluation_period_weeks: How many weeks to analyze (default: 4)

        Returns:
            dict with:
            - ready_to_progress: bool
            - next_level: str (if ready)
            - blocking_criteria: list (if not ready)
            - incident_analysis: dict
            - recommendation: str
        """
        # Get evaluation period
        eval_end = self.evaluation_timestamp
        eval_start = eval_end - timedelta(weeks=evaluation_period_weeks)

        # Get next maturity level
        try:
            next_level_obj = self._get_next_level(current_level)
        except ValueError as e:
            return {"ready_to_progress": False, "error": str(e), "recommendation": "Already at maximum maturity level"}

        # Gather deployment and incident data
        incident_data = self._analyze_incidents(eval_start, eval_end)

        # Evaluate criteria
        criteria_results = self._evaluate_criteria(next_level_obj, incident_data, evaluation_period_weeks)

        # Determine if ready to progress
        ready = all(c["met"] for c in criteria_results)

        # Compile result
        result = {
            "ready_to_progress": ready,
            "current_level": current_level,
            "next_level": next_level_obj.level if ready else None,
            "evaluation_period": {
                "start": eval_start.isoformat(),
                "end": eval_end.isoformat(),
                "weeks": evaluation_period_weeks,
            },
            "incident_analysis": incident_data,
            "criteria_evaluation": criteria_results,
            "blocking_criteria": [c["criterion"] for c in criteria_results if not c["met"]],
        }

        # Add recommendation
        if ready:
            result["recommendation"] = self._generate_progression_recommendation(next_level_obj, incident_data)
            result["new_risk_model_version"] = next_level_obj.risk_model_version
            result["new_thresholds"] = next_level_obj.auto_approve_thresholds
        else:
            result["recommendation"] = self._generate_improvement_recommendation(criteria_results, incident_data)

        # Record evaluation
        self._record_evaluation(result, current_level, next_level_obj if ready else None)

        return result

    def _get_next_level(self, current_level: str) -> TrustMaturityLevel:
        """Get next maturity level definition."""
        level_order = [
            "LEVEL_0_BASELINE",
            "LEVEL_1_CAUTIOUS",
            "LEVEL_2_MODERATE",
            "LEVEL_3_MATURE",
            "LEVEL_4_OPTIMIZED",
        ]

        try:
            current_index = level_order.index(current_level)
        except ValueError:
            raise ValueError(f"Unknown maturity level: {current_level}")

        if current_index >= len(level_order) - 1:
            raise ValueError(f"Already at maximum maturity level: {current_level}")

        next_level_name = level_order[current_index + 1]

        try:
            return TrustMaturityLevel.objects.get(level=next_level_name)
        except TrustMaturityLevel.DoesNotExist:
            raise ValueError(f"Maturity level {next_level_name} not configured in database")

    def _analyze_incidents(self, start_date, end_date) -> Dict[str, Any]:
        """
        Analyze incidents in evaluation period.

        Returns deployment counts, incident counts by severity, incident rate.
        """
        incidents = DeploymentIncident.objects.filter(incident_date__gte=start_date, incident_date__lt=end_date)

        total_incidents = incidents.count()

        # Incidents by severity
        p1_count = incidents.filter(severity="P1").count()
        p2_count = incidents.filter(severity="P2").count()
        p3_count = incidents.filter(severity="P3").count()
        p4_count = incidents.filter(severity="P4").count()

        # Auto-approved incidents
        auto_approved_incidents = incidents.filter(was_auto_approved=True).count()
        cab_reviewed_incidents = incidents.filter(was_auto_approved=False).count()

        # Estimate total deployments (from unique deployment_intent_ids in incidents + successful deployments)
        # For greenfield: use a placeholder or track separately
        # TODO: Add DeploymentExecution model to track all deployment attempts
        total_deployments = self._estimate_total_deployments(start_date, end_date)

        # Calculate incident rate
        incident_rate = Decimal(total_incidents) / Decimal(total_deployments) if total_deployments > 0 else Decimal(0)

        return {
            "total_deployments": total_deployments,
            "total_incidents": total_incidents,
            "incident_rate": float(incident_rate),
            "incident_rate_percentage": float(incident_rate * 100),
            "p1_incidents": p1_count,
            "p2_incidents": p2_count,
            "p3_incidents": p3_count,
            "p4_incidents": p4_count,
            "auto_approved_incidents": auto_approved_incidents,
            "cab_reviewed_incidents": cab_reviewed_incidents,
            "high_severity_incidents": p1_count + p2_count,
        }

    def _estimate_total_deployments(self, start_date, end_date) -> int:
        """
        Estimate total deployments in period.

        Greenfield assumption: 100 deployments/week (from requirements)
        Future: Query actual deployment execution records
        """
        weeks = (end_date - start_date).days / 7
        estimated_deployments = int(weeks * 100)  # 100 deployments/week capacity

        logger.info(f"Estimated {estimated_deployments} deployments over {weeks:.1f} weeks " f"(100/week assumption)")

        return estimated_deployments

    def _evaluate_criteria(
        self, next_level: TrustMaturityLevel, incident_data: Dict[str, Any], evaluation_period_weeks: int
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all criteria for progressing to next level.

        Returns list of criteria with met/not met status.
        """
        results = []

        # Criterion 1: Weeks required
        results.append(
            {
                "criterion": "Minimum weeks at current level",
                "required": next_level.weeks_required,
                "actual": evaluation_period_weeks,
                "met": evaluation_period_weeks >= next_level.weeks_required,
            }
        )

        # Criterion 2: Incident rate
        actual_rate = Decimal(str(incident_data["incident_rate"]))
        results.append(
            {
                "criterion": "Maximum incident rate",
                "required": f"{float(next_level.max_incident_rate) * 100:.2f}%",
                "actual": f"{incident_data['incident_rate_percentage']:.2f}%",
                "met": actual_rate <= next_level.max_incident_rate,
            }
        )

        # Criterion 3: P1 incidents
        results.append(
            {
                "criterion": "Maximum P1 incidents",
                "required": next_level.max_p1_incidents,
                "actual": incident_data["p1_incidents"],
                "met": incident_data["p1_incidents"] <= next_level.max_p1_incidents,
            }
        )

        # Criterion 4: P2 incidents
        results.append(
            {
                "criterion": "Maximum P2 incidents",
                "required": next_level.max_p2_incidents,
                "actual": incident_data["p2_incidents"],
                "met": incident_data["p2_incidents"] <= next_level.max_p2_incidents,
            }
        )

        return results

    def _generate_progression_recommendation(
        self, next_level: TrustMaturityLevel, incident_data: Dict[str, Any]
    ) -> str:
        """Generate recommendation for progression."""
        return (
            f"✅ READY TO PROGRESS to {next_level.get_level_display()}\n\n"
            f"All criteria met:\n"
            f"- Incident rate: {incident_data['incident_rate_percentage']:.2f}%\n"
            f"- P1 incidents: {incident_data['p1_incidents']}\n"
            f"- P2 incidents: {incident_data['p2_incidents']}\n"
            f"- Total deployments: {incident_data['total_deployments']}\n\n"
            f"Recommended Action:\n"
            f"1. Submit progression to CAB for approval\n"
            f"2. Activate Risk Model v{next_level.risk_model_version}\n"
            f"3. New auto-approve thresholds: {next_level.auto_approve_thresholds}\n"
            f"4. Continue monitoring for {next_level.weeks_required} weeks before next evaluation"
        )

    def _generate_improvement_recommendation(
        self, criteria_results: List[Dict[str, Any]], incident_data: Dict[str, Any]
    ) -> str:
        """Generate recommendation for improvement."""
        blocking = [c for c in criteria_results if not c["met"]]

        rec = "❌ NOT READY TO PROGRESS\n\nBlocking criteria:\n"
        for criterion in blocking:
            rec += f"- {criterion['criterion']}: Required {criterion['required']}, Actual {criterion['actual']}\n"

        rec += "\nRecommended Actions:\n"

        # Specific recommendations based on blocking criteria
        if incident_data["p1_incidents"] > 0:
            rec += "- Conduct P1 incident root cause analysis\n"
            rec += "- Implement preventative controls based on findings\n"

        if incident_data["incident_rate_percentage"] > 1.0:
            rec += "- Review deployment quality gates\n"
            rec += "- Improve pre-deployment testing\n"
            rec += "- Enhance risk factor scoring\n"

        if incident_data["auto_approved_incidents"] > 0:
            rec += f"- {incident_data['auto_approved_incidents']} incidents from auto-approved deployments\n"
            rec += "- Consider tightening auto-approve thresholds\n"

        rec += "- Continue current maturity level until criteria met\n"

        return rec

    def _record_evaluation(
        self, result: Dict[str, Any], current_level: str, next_level: Optional[TrustMaturityLevel]
    ) -> TrustMaturityProgress:
        """Record maturity evaluation to database."""
        incident_data = result["incident_analysis"]
        eval_period = result["evaluation_period"]

        status = "CRITERIA_MET" if result["ready_to_progress"] else "CRITERIA_NOT_MET"

        progress = TrustMaturityProgress.objects.create(
            evaluation_date=self.evaluation_timestamp,
            current_level=current_level,
            next_level=next_level.level if next_level else "",
            evaluation_period_start=eval_period["start"],
            evaluation_period_end=eval_period["end"],
            deployments_total=incident_data["total_deployments"],
            incidents_total=incident_data["total_incidents"],
            incident_rate=Decimal(str(incident_data["incident_rate"])),
            p1_incidents=incident_data["p1_incidents"],
            p2_incidents=incident_data["p2_incidents"],
            p3_incidents=incident_data["p3_incidents"],
            p4_incidents=incident_data["p4_incidents"],
            auto_approved_deployments=0,  # TODO: Track from deployment execution
            auto_approved_incidents=incident_data["auto_approved_incidents"],
            status=status,
            decision_notes=result["recommendation"],
            blocking_criteria=result["blocking_criteria"],
            requires_cab_approval=result["ready_to_progress"],
        )

        logger.info(
            f"Recorded maturity evaluation: {current_level} → "
            f"{next_level.level if next_level else 'N/A'} - Status: {status}"
        )

        return progress

    def get_current_maturity_status(self) -> Dict[str, Any]:
        """
        Get current maturity level and status.

        Returns active risk model version and current level.
        """
        try:
            active_model = RiskModelVersion.get_active_version()

            # Infer current level from active model mode
            mode_to_level = {
                "GREENFIELD_CONSERVATIVE": "LEVEL_0_BASELINE",
                "CAUTIOUS": "LEVEL_1_CAUTIOUS",
                "MODERATE": "LEVEL_2_MODERATE",
                "MATURE": "LEVEL_3_MATURE",
                "OPTIMIZED": "LEVEL_4_OPTIMIZED",
            }

            current_level = mode_to_level.get(active_model.mode, "LEVEL_0_BASELINE")

            # Get latest evaluation
            latest_eval = (
                TrustMaturityProgress.objects.filter(current_level=current_level).order_by("-evaluation_date").first()
            )

            return {
                "current_level": current_level,
                "risk_model_version": active_model.version,
                "risk_model_mode": active_model.mode,
                "auto_approve_thresholds": active_model.auto_approve_thresholds,
                "latest_evaluation": (
                    {
                        "date": latest_eval.evaluation_date.isoformat() if latest_eval else None,
                        "status": latest_eval.status if latest_eval else None,
                        "incident_rate": float(latest_eval.incident_rate) if latest_eval else None,
                    }
                    if latest_eval
                    else None
                ),
            }
        except ValueError:
            return {
                "current_level": "NOT_CONFIGURED",
                "error": "No active risk model version",
            }
