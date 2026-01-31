# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Escalation Engine.

Evaluates escalation rules and triggers actions.
"""
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.db import models
from django.utils import timezone

from ..models import EscalationEvent, EscalationRule, RequestStatusUpdate, TrackedRequest
from .sla_tracker import SLATracker

logger = logging.getLogger(__name__)


class EscalationEngine:
    """
    Evaluates escalation rules and triggers actions.

    Responsibilities:
    - Evaluate rules against requests
    - Trigger escalation events
    - Execute escalation actions
    """

    def __init__(self):
        """Initialize escalation engine."""
        self.sla_tracker = SLATracker()

    def evaluate_rules(self, request: TrackedRequest) -> List[EscalationRule]:
        """
        Evaluate all active escalation rules for a request.

        Args:
            request: TrackedRequest instance

        Returns:
            List of matching EscalationRule instances
        """
        matching_rules = []

        # Get active rules (optionally filtered by request type)
        rules = EscalationRule.objects.filter(is_active=True).filter(
            models.Q(request_type__isnull=True) | models.Q(request_type=request.request_type)
        )

        for rule in rules:
            if self._rule_matches(request, rule):
                matching_rules.append(rule)

        return matching_rules

    def _rule_matches(self, request: TrackedRequest, rule: EscalationRule) -> bool:
        """
        Check if a rule matches a request.

        Args:
            request: TrackedRequest instance
            rule: EscalationRule instance

        Returns:
            True if rule matches
        """
        trigger_type = rule.trigger_type
        config = rule.trigger_config

        if trigger_type == EscalationRule.TriggerType.SLA_WARNING:
            status, needs_action = self.sla_tracker.check_sla_status(request)
            hours_before = config.get("hours_before_breach", 4)
            if status == "warning":
                if request.sla_due:
                    hours_remaining = (request.sla_due - timezone.now()).total_seconds() / 3600
                    return hours_remaining <= hours_before
            return False

        elif trigger_type == EscalationRule.TriggerType.SLA_BREACH:
            status, needs_action = self.sla_tracker.check_sla_status(request)
            return status == "breached"

        elif trigger_type == EscalationRule.TriggerType.BLOCKED:
            blocked_days = config.get("blocked_days", 2)
            if request.blocked_reason:
                threshold = timezone.now() - timedelta(days=blocked_days)
                return request.last_updated <= threshold
            return False

        elif trigger_type == EscalationRule.TriggerType.REASSIGNMENT:
            reassignment_count = config.get("reassignment_count", 3)
            time_window_hours = config.get("time_window_hours", 48)
            threshold = timezone.now() - timedelta(hours=time_window_hours)

            # Count reassignments in time window
            status_updates = RequestStatusUpdate.objects.filter(
                request=request,
                created_at__gte=threshold,
            ).exclude(old_status=request.status)

            # Check if assignment_group changed multiple times
            groups_seen = set()
            for update in status_updates:
                # This is simplified - in reality would track assignment_group changes
                groups_seen.add(update.old_status)

            return len(groups_seen) >= reassignment_count

        return False

    def trigger_escalation(
        self,
        request: TrackedRequest,
        rule: EscalationRule,
        trigger_reason: str,
    ) -> EscalationEvent:
        """
        Trigger an escalation for a request.

        Args:
            request: TrackedRequest instance
            rule: EscalationRule instance
            trigger_reason: Reason for escalation

        Returns:
            EscalationEvent instance
        """
        # Increment escalation level
        request.is_escalated = True
        request.escalation_level += 1
        request.save()

        # Execute actions
        actions_taken = []
        for action in rule.escalation_actions:
            result = self._execute_action(request, action)
            actions_taken.append({"action": action, "result": result})

        # Create escalation event
        escalation_event = EscalationEvent.objects.create(
            request=request,
            rule=rule,
            trigger_reason=trigger_reason,
            escalation_level=request.escalation_level,
            actions_taken=actions_taken,
        )

        logger.info(f"Escalated request {request.servicenow_number} to level {request.escalation_level}")

        return escalation_event

    def _execute_action(self, request: TrackedRequest, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single escalation action.

        Args:
            request: TrackedRequest instance
            action: Action definition dict

        Returns:
            Result dict
        """
        action_type = action.get("type")

        if action_type == "notify":
            recipients = action.get("recipients", [])
            # This would trigger notification service
            return {"type": "notify", "recipients": recipients, "status": "queued"}

        elif action_type == "update_priority":
            new_priority = action.get("new_priority")
            request.priority = new_priority
            request.save()
            return {"type": "update_priority", "new_priority": new_priority, "status": "completed"}

        elif action_type == "escalate":
            level = action.get("level", 1)
            request.escalation_level = max(request.escalation_level, level)
            request.is_escalated = True
            request.save()
            return {"type": "escalate", "level": level, "status": "completed"}

        elif action_type == "add_work_note":
            note = action.get("note", "")
            # This would add a work note to ServiceNow
            return {"type": "add_work_note", "note": note, "status": "queued"}

        return {"type": action_type, "status": "unknown"}
