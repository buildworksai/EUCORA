# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Recommendation engine for automation opportunities.

Generates ranked recommendations with implementation approaches.
"""
from typing import Any

from apps.automation_advisor.models import TaskPattern
from apps.automation_advisor.services.pattern_detector import PatternDetectionResult
from apps.automation_advisor.services.roi_calculator import ROICalculator


class RecommendationEngine:
    """Generates automation recommendations."""

    def __init__(self, roi_calculator: ROICalculator | None = None):
        """
        Initialize recommendation engine.

        Args:
            roi_calculator: ROI calculator instance
        """
        self.roi_calculator = roi_calculator or ROICalculator()

    def generate_recommendations(self, patterns: list[PatternDetectionResult]) -> list[dict[str, Any]]:
        """
        Generate ranked automation recommendations.

        Args:
            patterns: List of detected patterns

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        for pattern in patterns:
            # Estimate complexity based on pattern type
            complexity = self._estimate_complexity(pattern)

            # Calculate annual occurrences (extrapolate from detected)
            annual_occurrences = pattern.occurrence_count * 12  # Rough estimate

            # Calculate time saved (assume 50% reduction for automation)
            time_saved_per_occurrence = (pattern.avg_duration_minutes / 60) * 0.5

            # Calculate scores
            scores = self.roi_calculator.calculate_automation_score(
                frequency=annual_occurrences,
                time_per_occurrence=time_saved_per_occurrence,
                error_rate=pattern.error_rate,
                complexity=complexity,
            )

            # Calculate ROI
            roi = self.roi_calculator.calculate_roi(
                annual_occurrences=annual_occurrences,
                time_saved_per_occurrence=time_saved_per_occurrence,
                complexity=complexity,
            )

            # Generate recommendation
            recommendation = {
                "pattern": pattern,
                "title": f"Automate: {pattern.name}",
                "description": self._generate_description(pattern),
                "current_process": self._describe_current_process(pattern),
                "proposed_automation": self._propose_automation(pattern, complexity),
                "scores": scores,
                "roi": roi,
                "complexity": complexity,
            }

            recommendations.append(recommendation)

        # Sort by overall score (descending)
        recommendations.sort(key=lambda x: x["scores"]["overall_score"], reverse=True)

        return recommendations

    def _estimate_complexity(self, pattern: PatternDetectionResult) -> str:
        """Estimate automation complexity."""
        if pattern.pattern_type == TaskPattern.PatternType.REPETITIVE:
            return "low"
        elif pattern.pattern_type == TaskPattern.PatternType.MANUAL:
            return "medium"
        else:  # ERROR_PRONE
            return "high"

    def _generate_description(self, pattern: PatternDetectionResult) -> str:
        """Generate description for recommendation."""
        return (
            f"This {pattern.pattern_type} pattern occurs {pattern.occurrence_count} times "
            f"with an average duration of {pattern.avg_duration_minutes:.1f} minutes "
            f"and an error rate of {pattern.error_rate * 100:.1f}%."
        )

    def _describe_current_process(self, pattern: PatternDetectionResult) -> str:
        """Describe current manual process."""
        if pattern.pattern_type == TaskPattern.PatternType.MANUAL:
            return "Requires manual intervention and multiple hand-offs between teams."
        elif pattern.pattern_type == TaskPattern.PatternType.ERROR_PRONE:
            return "High error rate indicates process inconsistencies and manual errors."
        else:
            return "Repetitive task performed manually with similar steps each time."

    def _propose_automation(self, pattern: PatternDetectionResult, complexity: str) -> str:
        """Propose automation approach."""
        if complexity == "low":
            return (
                "Implement script-based automation with scheduled execution. "
                "Low complexity allows for quick implementation."
            )
        elif complexity == "medium":
            return (
                "Develop workflow automation with approval gates. "
                "Medium complexity requires integration with existing systems."
            )
        else:
            return (
                "Design comprehensive automation solution with error handling and monitoring. "
                "High complexity requires careful planning and testing."
            )
