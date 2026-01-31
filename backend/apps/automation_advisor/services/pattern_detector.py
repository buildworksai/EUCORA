# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Pattern detection algorithms for automation opportunities.

Detects repetitive tasks, manual processes, and error-prone operations.
"""
from dataclasses import dataclass
from typing import Any

from apps.automation_advisor.models import TaskPattern


@dataclass
class PatternDetectionResult:
    """Result of pattern detection."""

    pattern_type: str
    name: str
    occurrence_count: int
    avg_duration_minutes: float
    error_rate: float
    evidence: dict[str, Any]


class PatternDetector:
    """Detects automation opportunity patterns."""

    def detect_repetitive_tasks(self, incidents: list[dict], threshold: int = 10) -> list[PatternDetectionResult]:
        """
        Detect tasks that occur repeatedly with similar characteristics.

        Args:
            incidents: List of incident dictionaries
            threshold: Minimum occurrence count

        Returns:
            List of detected patterns
        """
        patterns = []

        # Group by category and short description similarity
        grouped = {}
        for incident in incidents:
            category = incident.get("category", "Unknown")
            short_desc = incident.get("short_description", "")
            key = f"{category}::{short_desc[:50]}"

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(incident)

        # Filter by threshold
        for key, incident_list in grouped.items():
            if len(incident_list) >= threshold:
                category, desc = key.split("::", 1)
                avg_duration = self._calculate_avg_duration(incident_list)
                error_rate = self._calculate_error_rate(incident_list)

                patterns.append(
                    PatternDetectionResult(
                        pattern_type=TaskPattern.PatternType.REPETITIVE,
                        name=f"{category}: {desc}",
                        occurrence_count=len(incident_list),
                        avg_duration_minutes=avg_duration,
                        error_rate=error_rate,
                        evidence={"incidents": len(incident_list), "category": category},
                    )
                )

        return patterns

    def detect_manual_processes(self, tickets: list[dict]) -> list[PatternDetectionResult]:
        """
        Detect processes that require manual intervention.

        Args:
            tickets: List of ticket dictionaries

        Returns:
            List of detected patterns
        """
        patterns = []

        # Look for keywords indicating manual processes
        manual_keywords = ["manually", "hand-off", "wait for", "manual", "human intervention"]

        for ticket in tickets:
            description = ticket.get("description", "").lower()
            work_notes = ticket.get("work_notes", "").lower()

            for keyword in manual_keywords:
                if keyword in description or keyword in work_notes:
                    # Check for multiple reassignments (indicates hand-offs)
                    reassign_count = ticket.get("reassign_count", 0)
                    if reassign_count > 2:
                        patterns.append(
                            PatternDetectionResult(
                                pattern_type=TaskPattern.PatternType.MANUAL,
                                name=f"Manual process: {ticket.get('number', 'Unknown')}",
                                occurrence_count=1,
                                avg_duration_minutes=self._calculate_duration(ticket),
                                error_rate=0.0,
                                evidence={"reassign_count": reassign_count, "keyword": keyword},
                            )
                        )
                    break

        return patterns

    def detect_error_prone(self, changes: list[dict], deployments: list[dict]) -> list[PatternDetectionResult]:
        """
        Detect processes with high error rates.

        Args:
            changes: List of change request dictionaries
            deployments: List of deployment dictionaries

        Returns:
            List of detected patterns
        """
        patterns = []

        # Calculate failure rates by category
        change_failures = {}
        for change in changes:
            category = change.get("category", "Unknown")
            state = change.get("state", "")
            if state in ["failed", "rolled_back"]:
                if category not in change_failures:
                    change_failures[category] = {"total": 0, "failed": 0}
                change_failures[category]["total"] += 1
                change_failures[category]["failed"] += 1
            else:
                if category not in change_failures:
                    change_failures[category] = {"total": 0, "failed": 0}
                change_failures[category]["total"] += 1

        # Find categories with high error rates
        for category, stats in change_failures.items():
            if stats["total"] > 0:
                error_rate = stats["failed"] / stats["total"]
                if error_rate > 0.2:  # 20% error rate threshold
                    patterns.append(
                        PatternDetectionResult(
                            pattern_type=TaskPattern.PatternType.ERROR_PRONE,
                            name=f"Error-prone: {category}",
                            occurrence_count=stats["total"],
                            avg_duration_minutes=0.0,
                            error_rate=error_rate,
                            evidence={"category": category, "failure_count": stats["failed"]},
                        )
                    )

        return patterns

    def _calculate_avg_duration(self, incidents: list[dict]) -> float:
        """Calculate average duration from incidents."""
        durations = []
        for incident in incidents:
            duration = self._calculate_duration(incident)
            if duration > 0:
                durations.append(duration)
        return sum(durations) / len(durations) if durations else 0.0

    def _calculate_duration(self, item: dict) -> float:
        """Calculate duration in minutes from item."""
        opened = item.get("opened_at")
        closed = item.get("closed_at")
        if opened and closed:
            try:
                from datetime import datetime

                opened_dt = datetime.fromisoformat(str(opened).replace("Z", "+00:00"))
                closed_dt = datetime.fromisoformat(str(closed).replace("Z", "+00:00"))
                delta = closed_dt - opened_dt
                return delta.total_seconds() / 60
            except Exception:
                pass
        return 0.0

    def _calculate_error_rate(self, incidents: list[dict]) -> float:
        """Calculate error rate from incidents."""
        if not incidents:
            return 0.0
        error_count = sum(1 for i in incidents if i.get("state") in ["failed", "error"])
        return error_count / len(incidents)
