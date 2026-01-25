# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Generation Service for P5.1
Collects and generates evidence packages for CAB decision-making.
"""
import json
from decimal import Decimal

from django.utils import timezone

from .models import EvidencePackage, RiskFactor, RiskScoreBreakdown


class EvidenceGenerationService:
    """
    Service for collecting and generating evidence packages.
    Implements P5.1: Evidence Pack Generation Engine.

    Formula: risk_score = clamp(0..100, Σ(weight_i * normalized_factor_i))
    """

    @staticmethod
    def generate_evidence_package(
        deployment_intent_id: str,
        correlation_id: str,
        artifact_info: dict = None,
        test_results: dict = None,
        scan_results: dict = None,
        deployment_plan: dict = None,
        rollback_plan: dict = None,
        created_by: str = "system",
    ) -> EvidencePackage:
        """
        Generate a complete evidence package for CAB decision-making.

        Args:
            deployment_intent_id: ID of deployment intent
            correlation_id: Unique identifier for audit trail
            artifact_info: Hash, signature, SBOM of artifacts
            test_results: Test coverage, results summary
            scan_results: Vulnerability scan results
            deployment_plan: How deployment will proceed
            rollback_plan: Rollback strategy (plane-specific)
            created_by: User or system creating this package

        Returns:
            EvidencePackage: Immutable evidence record with risk score

        Raises:
            ValueError: If correlation_id already exists or required fields missing
        """

        # Check for duplicate
        if EvidencePackage.objects.filter(correlation_id=correlation_id).exists():
            raise ValueError(f"Evidence package with correlation_id {correlation_id} already exists")

        # Collect all evidence
        evidence_data = {
            "artifacts": artifact_info or {},
            "test_results": test_results or {},
            "scan_results": scan_results or {},
            "deployment_plan": deployment_plan or {},
            "rollback_plan": rollback_plan or {},
            "collected_at": timezone.now().isoformat(),
        }

        # Compute risk score
        risk_score, risk_factors = EvidenceGenerationService._compute_risk_score(evidence_data)

        # Check completeness
        completeness_check = EvidenceGenerationService._check_completeness(evidence_data)
        is_complete = all(completeness_check.values())

        # Create evidence package (SHA-256 hash computed automatically on save)
        package = EvidencePackage.objects.create(
            deployment_intent_id=deployment_intent_id,
            correlation_id=correlation_id,
            evidence_data=evidence_data,
            risk_score=risk_score,
            risk_factors=risk_factors,
            is_complete=is_complete,
            completeness_check=completeness_check,
            created_by=created_by,
        )

        # Create risk breakdown for transparency
        RiskScoreBreakdown.objects.create(
            evidence_package=package,
            correlation_id=correlation_id,
            factors_evaluated=risk_factors,
            created_by=created_by,
        )

        return package

    @staticmethod
    def _compute_risk_score(evidence_data: dict) -> tuple:
        """
        Compute risk score from evidence using risk model v1.0.

        Formula: clamp(0..100, Σ(weight_i * normalized_factor_i))

        Returns:
            (risk_score: Decimal, risk_factors: dict with all factor details)
        """
        risk_factors = {}
        weighted_sum = Decimal("0.0")
        total_weight = Decimal("0.0")

        # Get risk factors from database (v1.0)
        factors = RiskFactor.objects.filter(model_version="1.0").all()

        if not factors.exists():
            # If no factors configured, return neutral score
            return Decimal("50.0"), risk_factors

        for factor in factors:
            # Evaluate factor based on evidence
            normalized_value = EvidenceGenerationService._evaluate_factor(
                factor.factor_type, evidence_data, factor.rubric
            )

            weight = Decimal(str(factor.weight))
            weighted_contribution = weight * normalized_value
            weighted_sum += weighted_contribution
            total_weight += weight

            risk_factors[factor.factor_type] = {
                "name": factor.name,
                "value": float(normalized_value),
                "weight": float(weight),
                "contribution": float(weighted_contribution),
            }

        # Clamp to [0, 100]
        if total_weight > 0:
            raw_score = (weighted_sum / total_weight) * Decimal("100")
            risk_score = (
                Decimal("100.0")
                if raw_score > Decimal("100")
                else (Decimal("0.0") if raw_score < Decimal("0") else raw_score)
            )
        else:
            risk_score = Decimal("50.0")

        return round(risk_score, 2), risk_factors

    @staticmethod
    def _evaluate_factor(factor_type: str, evidence: dict, rubric: dict) -> Decimal:
        """
        Evaluate a single risk factor based on evidence and rubric.

        Implements rubric-based evaluation with factor-specific logic.
        Returns normalized value [0-100] as Decimal.

        Rubric format example (for coverage):
            {'>90%': 0, '80-90%': 10, '<80%': 30}

        Factor-specific implementations:
        - coverage: Parses test_results.coverage_percent against rubric
        - security: Counts critical/high issues from scan_results
        - testing: Evaluates manual_test_status presence
        - rollback: Checks rollback_plan completeness
        - scope: Counts affected_components in deployment_plan
        """
        score = Decimal("50.0")  # Default neutral score

        try:
            if not rubric:
                return score

            if factor_type == "coverage":
                # Evaluate test coverage percentage
                coverage = evidence.get("test_results", {}).get("coverage_percent")
                if coverage is not None:
                    coverage_val = float(coverage)
                    # Match against rubric thresholds
                    for threshold, points in rubric.items():
                        if ">90" in threshold and coverage_val > 90:
                            score = Decimal(str(points))
                            break
                        elif "80-90" in threshold and 80 <= coverage_val <= 90:
                            score = Decimal(str(points))
                            break
                        elif "<80" in threshold and coverage_val < 80:
                            score = Decimal(str(points))
                            break

            elif factor_type == "security":
                # Count critical/high vulnerabilities
                scan_results = evidence.get("scan_results", {})
                critical_count = len(scan_results.get("critical", []))
                high_count = len(scan_results.get("high", []))

                # Rubric: number of issues mapped to risk score
                total_issues = critical_count + high_count
                for threshold, points in rubric.items():
                    try:
                        threshold_val = int(threshold.strip("><="))
                        if ">" in threshold and total_issues > threshold_val:
                            score = Decimal(str(points))
                            break
                        elif "=" in threshold and total_issues == threshold_val:
                            score = Decimal(str(points))
                            break
                        elif "<" in threshold and total_issues < threshold_val:
                            score = Decimal(str(points))
                            break
                    except (ValueError, IndexError):
                        pass

            elif factor_type == "testing":
                # Evaluate presence of manual testing
                manual_test_status = evidence.get("test_results", {}).get("manual_test_status")
                if manual_test_status:
                    if manual_test_status == "completed":
                        score = Decimal(rubric.get("completed", "10"))
                    elif manual_test_status == "in_progress":
                        score = Decimal(rubric.get("in_progress", "30"))
                    else:
                        score = Decimal(rubric.get("not_started", "50"))
                else:
                    score = Decimal(rubric.get("not_started", "50"))

            elif factor_type == "rollback":
                # Check rollback plan completeness
                rollback_plan = evidence.get("rollback_plan", {})
                has_plan = bool(rollback_plan and len(str(rollback_plan)) > 10)

                if has_plan:
                    score = Decimal(rubric.get("validated", "10"))
                else:
                    score = Decimal(rubric.get("missing", "50"))

            elif factor_type == "scope":
                # Count affected components
                deployment_plan = evidence.get("deployment_plan", {})
                affected_components = deployment_plan.get("affected_components", [])
                count = len(affected_components) if isinstance(affected_components, list) else 1

                # Rubric: component count thresholds
                for threshold, points in rubric.items():
                    try:
                        threshold_val = int(threshold.strip("><"))
                        if ">" in threshold and count > threshold_val:
                            score = Decimal(str(points))
                            break
                        elif "<" in threshold and count < threshold_val:
                            score = Decimal(str(points))
                            break
                        elif "=" in threshold and count == threshold_val:
                            score = Decimal(str(points))
                            break
                    except (ValueError, IndexError):
                        pass

            # Clamp to [0, 100]
            return Decimal("100.0") if score > Decimal("100") else (Decimal("0.0") if score < Decimal("0") else score)

        except Exception:
            # If evaluation fails, return neutral score
            return Decimal("50.0")

    @staticmethod
    def _check_completeness(evidence_data: dict) -> dict:
        """
        Check if all required evidence fields are present.

        Returns:
            dict with boolean status for each required field
        """
        required_fields = [
            "artifacts",
            "test_results",
            "scan_results",
            "deployment_plan",
            "rollback_plan",
        ]

        completeness = {}
        for field in required_fields:
            # A field is complete if it exists and is not empty
            completeness[field] = bool(evidence_data.get(field) and len(str(evidence_data.get(field))) > 2)

        return completeness

    @staticmethod
    def verify_package_immutability(package: EvidencePackage) -> dict:
        """
        Verify evidence package hasn't been tampered with.

        Returns:
            dict with verification status and details
        """
        is_valid = package.verify_immutability()

        return {
            "is_valid": is_valid,
            "package_id": str(package.id),
            "correlation_id": package.correlation_id,
            "original_hash": package.content_hash,
            "message": (
                "Evidence package hash verification passed"
                if is_valid
                else "Hash mismatch - evidence may have been modified"
            ),
        }

    @staticmethod
    def list_evidence_for_deployment(deployment_intent_id: str):
        """
        List all evidence packages for a deployment.

        Returns:
            QuerySet of EvidencePackage ordered by created_at descending
        """
        return EvidencePackage.objects.filter(deployment_intent_id=deployment_intent_id).order_by("-created_at")
