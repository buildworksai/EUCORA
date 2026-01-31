# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Notification Service for Change Communications.

Handles sending notifications via Email, Teams, Slack, and ServiceNow.
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from ..models import ChangeAuditEvent, ChangeRecord, Communication, CommunicationTemplate, StakeholderGroup
from .template_renderer import RenderedTemplate, TemplateRenderer

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of sending a notification."""

    success: bool
    communication_id: str
    channel: str
    recipients: List[str]
    error_message: Optional[str] = None


class NotificationService:
    """
    Sends notifications through various channels.

    Supports:
    - Email (SMTP)
    - Microsoft Teams (Webhook)
    - Slack (Webhook)
    - ServiceNow (API)
    """

    def __init__(self):
        """Initialize notification service."""
        self.renderer = TemplateRenderer()

    async def send_notification(
        self,
        change_record: ChangeRecord,
        event_type: str,
        stakeholder_groups: Optional[List[StakeholderGroup]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> List[NotificationResult]:
        """
        Send notification for a change event.

        Args:
            change_record: The change record
            event_type: Type of event (scheduled, started, completed, etc.)
            stakeholder_groups: Groups to notify (auto-select if not provided)
            extra_context: Additional context for template

        Returns:
            List of notification results
        """
        results = []

        # Build context
        context = self.renderer.build_context(change_record, extra_context)

        # Get stakeholder groups if not provided
        if not stakeholder_groups:
            stakeholder_groups = await self._get_applicable_groups(change_record)

        for group in stakeholder_groups:
            # Get template for this event and channel
            template = await self._get_template(event_type, group.notification_channel)

            if not template:
                logger.warning(f"No template for {event_type}/{group.notification_channel}")
                continue

            # Render template
            rendered = self.renderer.render(template, context)

            # Create communication record
            communication = await Communication.objects.acreate(
                change_record=change_record,
                template=template,
                stakeholder_group=group,
                channel=group.notification_channel,
                subject=rendered.subject,
                body=rendered.body,
                recipients=self._get_recipients(group),
                status=Communication.Status.PENDING,
            )

            # Send via appropriate channel
            try:
                _result = await self._send_via_channel(  # noqa: F841
                    group.notification_channel,
                    group.channel_config,
                    rendered,
                    self._get_recipients(group),
                )

                communication.status = Communication.Status.SENT
                communication.sent_at = timezone.now()
                await communication.asave()

                # Create audit event
                await ChangeAuditEvent.objects.acreate(
                    change_record=change_record,
                    event_type=ChangeAuditEvent.EventType.NOTIFICATION_SENT,
                    description=f"Sent {event_type} notification to {group.name}",
                    metadata={
                        "channel": group.notification_channel,
                        "recipients": self._get_recipients(group)[:5],  # First 5
                    },
                )

                results.append(
                    NotificationResult(
                        success=True,
                        communication_id=str(communication.id),
                        channel=group.notification_channel,
                        recipients=self._get_recipients(group),
                    )
                )

            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
                communication.status = Communication.Status.FAILED
                communication.error_message = str(e)
                await communication.asave()

                results.append(
                    NotificationResult(
                        success=False,
                        communication_id=str(communication.id),
                        channel=group.notification_channel,
                        recipients=self._get_recipients(group),
                        error_message=str(e),
                    )
                )

        return results

    async def _get_applicable_groups(
        self,
        change_record: ChangeRecord,
    ) -> List[StakeholderGroup]:
        """Get stakeholder groups applicable for this change."""
        groups = []
        async for group in StakeholderGroup.objects.filter(is_active=True):
            # Check scope filters
            if self._matches_scope(group, change_record):
                groups.append(group)
        return groups

    def _matches_scope(
        self,
        group: StakeholderGroup,
        change_record: ChangeRecord,
    ) -> bool:
        """Check if change record matches group's scope filters."""
        filters = group.scope_filters

        if not filters:
            return True

        # Check various filters
        if "change_types" in filters:
            if change_record.change_type not in filters["change_types"]:
                return False

        if "risk_levels" in filters:
            if change_record.risk_level not in filters["risk_levels"]:
                return False

        return True

    async def _get_template(
        self,
        event_type: str,
        channel: str,
    ) -> Optional[CommunicationTemplate]:
        """Get template for event type and channel."""
        return await CommunicationTemplate.objects.filter(
            event_type=event_type,
            channel=channel,
            is_active=True,
        ).afirst()

    def _get_recipients(self, group: StakeholderGroup) -> List[str]:
        """Get recipients from group configuration."""
        config = group.channel_config

        if group.notification_channel == "email":
            return config.get("email_addresses", [])
        elif group.notification_channel == "teams":
            return [config.get("webhook_url", "")]
        elif group.notification_channel == "slack":
            return [config.get("webhook_url", "")]

        return []

    async def _send_via_channel(
        self,
        channel: str,
        config: Dict[str, Any],
        rendered: RenderedTemplate,
        recipients: List[str],
    ) -> bool:
        """Send notification via specific channel."""
        if channel == "email":
            return await self._send_email(config, rendered, recipients)
        elif channel == "teams":
            return await self._send_teams(config, rendered)
        elif channel == "slack":
            return await self._send_slack(config, rendered)
        elif channel == "servicenow":
            return await self._send_servicenow(config, rendered)
        else:
            raise ValueError(f"Unknown channel: {channel}")

    async def _send_email(
        self,
        config: Dict[str, Any],
        rendered: RenderedTemplate,
        recipients: List[str],
    ) -> bool:
        """Send email notification."""
        if not recipients:
            raise ValueError("No email recipients configured")

        # In production, use async email sending
        # For now, use Django's send_mail
        from_email = config.get("from_email", settings.DEFAULT_FROM_EMAIL)

        try:
            send_mail(
                subject=rendered.subject,
                message=rendered.body,
                from_email=from_email,
                recipient_list=recipients,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            raise

    async def _send_teams(
        self,
        config: Dict[str, Any],
        rendered: RenderedTemplate,
    ) -> bool:
        """Send Microsoft Teams notification via webhook."""
        import httpx

        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Teams webhook URL not configured")

        # Teams Adaptive Card format
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": rendered.subject,
            "sections": [
                {
                    "activityTitle": rendered.subject,
                    "text": rendered.body,
                    "markdown": True,
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()

        return True

    async def _send_slack(
        self,
        config: Dict[str, Any],
        rendered: RenderedTemplate,
    ) -> bool:
        """Send Slack notification via webhook."""
        import httpx

        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Slack webhook URL not configured")

        payload = {
            "text": f"*{rendered.subject}*\n\n{rendered.body}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()

        return True

    async def _send_servicenow(
        self,
        config: Dict[str, Any],
        rendered: RenderedTemplate,
    ) -> bool:
        """Send ServiceNow notification."""
        # This would integrate with ServiceNow's notification API
        # For now, just log it
        logger.info(f"ServiceNow notification: {rendered.subject}")
        return True

    async def retry_failed(self, communication_id: str) -> NotificationResult:
        """Retry a failed communication."""
        communication = await Communication.objects.select_related("change_record", "stakeholder_group").aget(
            id=communication_id
        )

        if communication.status != Communication.Status.FAILED:
            raise ValueError(f"Communication is not in failed state: {communication.status}")

        communication.retry_count += 1
        rendered = RenderedTemplate(
            subject=communication.subject,
            body=communication.body,
            variables_used=[],
        )

        try:
            await self._send_via_channel(
                communication.channel,
                communication.stakeholder_group.channel_config if communication.stakeholder_group else {},
                rendered,
                communication.recipients,
            )

            communication.status = Communication.Status.SENT
            communication.sent_at = timezone.now()
            communication.error_message = ""
            await communication.asave()

            return NotificationResult(
                success=True,
                communication_id=str(communication.id),
                channel=communication.channel,
                recipients=communication.recipients,
            )

        except Exception as e:
            communication.error_message = str(e)
            await communication.asave()

            return NotificationResult(
                success=False,
                communication_id=str(communication.id),
                channel=communication.channel,
                recipients=communication.recipients,
                error_message=str(e),
            )
