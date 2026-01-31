# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Notification Service for Request Coordination.

Handles sending notifications via Email, Teams, Slack, and ServiceNow.
Reuses pattern from change_communications but adapted for requests.
"""
import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from ..models import CommunicationTemplate, RequestCommunication, RequestStakeholder, TrackedRequest

logger = logging.getLogger(__name__)


class RequestNotificationService:
    """
    Sends notifications for request events.

    Supports:
    - Email (SMTP)
    - Microsoft Teams (Webhook)
    - Slack (Webhook)
    - ServiceNow (API)
    """

    def __init__(self):
        """Initialize notification service."""

    def send_notification(
        self,
        request: TrackedRequest,
        communication_type: str,
        template: Optional[CommunicationTemplate] = None,
        recipients: Optional[List[str]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> RequestCommunication:
        """
        Send notification for a request event.

        Args:
            request: TrackedRequest instance
            communication_type: Type of communication (status_update, sla_warning, etc.)
            template: Communication template (auto-select if not provided)
            recipients: List of email addresses (auto-select stakeholders if not provided)
            extra_context: Additional context for template

        Returns:
            RequestCommunication instance
        """
        # Get template if not provided
        if not template:
            # Try to find template for this communication type
            templates = CommunicationTemplate.objects.filter(
                communication_type=communication_type,
                is_active=True,
            )
            template = templates.first()

        # Get recipients if not provided
        if not recipients:
            stakeholders = RequestStakeholder.objects.filter(request=request)
            recipients = [s.email for s in stakeholders]

        # Build context
        context = self._build_context(request, extra_context)

        # Render template
        if template:
            subject = self._render_template(template.subject_template, context)
            body = self._render_template(template.body_template, context)
            channel = template.channel
        else:
            # Fallback if no template
            subject = f"Request Update: {request.servicenow_number}"
            body = f"Request {request.servicenow_number} - {request.short_description}\n\nStatus: {request.status}"
            channel = RequestCommunication.Channel.EMAIL

        # Create communication record
        communication = RequestCommunication.objects.create(
            request=request,
            communication_type=communication_type,
            channel=channel,
            subject=subject,
            body=body,
            recipients=recipients,
            status=RequestCommunication.Status.PENDING,
        )

        # Send via appropriate channel
        try:
            if channel == RequestCommunication.Channel.EMAIL:
                self._send_email(communication)
            elif channel == RequestCommunication.Channel.TEAMS:
                self._send_teams(communication)
            elif channel == RequestCommunication.Channel.SLACK:
                self._send_slack(communication)
            elif channel == RequestCommunication.Channel.SERVICENOW:
                self._send_servicenow(communication)

            communication.status = RequestCommunication.Status.SENT
            communication.sent_at = timezone.now()
            communication.save()

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            communication.status = RequestCommunication.Status.FAILED
            communication.error_message = str(e)
            communication.save()

        return communication

    def _build_context(self, request: TrackedRequest, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build template context from request."""
        from datetime import timedelta

        context = {
            "request_number": request.servicenow_number,
            "short_description": request.short_description,
            "requestor_name": request.requestor_name,
            "requestor_email": request.requestor_email,
            "assigned_to": request.assigned_to or "Unassigned",
            "assignment_group": request.assignment_group or "Unassigned",
            "status": request.get_status_display(),
            "priority": request.get_priority_display(),
            "sla_due": request.sla_due.isoformat() if request.sla_due else None,
        }

        if request.sla_due:
            time_remaining = request.sla_due - timezone.now()
            context["time_remaining"] = str(time_remaining)
            context["time_remaining_hours"] = int(time_remaining.total_seconds() / 3600)

        if extra:
            context.update(extra)

        return context

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render template with variable substitution."""
        result = template
        for key, value in context.items():
            placeholder = "${" + key + "}"
            if value is not None:
                result = result.replace(placeholder, str(value))
            else:
                result = result.replace(placeholder, "")
        return result

    def _send_email(self, communication: RequestCommunication) -> None:
        """Send email notification."""
        send_mail(
            subject=communication.subject,
            message=communication.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=communication.recipients,
            fail_silently=False,
        )

    def _send_teams(self, communication: RequestCommunication) -> None:
        """Send Teams notification (placeholder - would need webhook config)."""
        logger.info(f"Teams notification: {communication.subject}")

    def _send_slack(self, communication: RequestCommunication) -> None:
        """Send Slack notification (placeholder - would need webhook config)."""
        logger.info(f"Slack notification: {communication.subject}")

    def _send_servicenow(self, communication: RequestCommunication) -> None:
        """Send ServiceNow notification (placeholder)."""
        logger.info(f"ServiceNow notification: {communication.subject}")
