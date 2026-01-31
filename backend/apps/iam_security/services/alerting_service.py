# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Alerting service for security anomalies.

Sends alerts via email, Teams, and ServiceNow.
"""
import logging

from apps.iam_security.models import AnomalyDetection, SecurityAlert

logger = logging.getLogger(__name__)


class AlertingService:
    """Service for sending security alerts."""

    def send_alert(self, anomaly: AnomalyDetection, channel: str, recipients: list[str]) -> SecurityAlert:
        """
        Send security alert.

        Args:
            anomaly: Anomaly detection instance
            channel: Alert channel (email, teams, servicenow)
            recipients: List of recipient addresses/IDs

        Returns:
            Created SecurityAlert instance
        """
        subject = f"Security Alert: {anomaly.anomaly_type} - {anomaly.user_principal}"
        body = self._generate_alert_body(anomaly)

        alert = SecurityAlert.objects.create(
            anomaly=anomaly,
            channel=channel,
            recipients=recipients,
            subject=subject,
            body=body,
            sent_at=anomaly.created_at,
        )

        # Send via channel (simplified - would integrate with actual services)
        try:
            if channel == SecurityAlert.Channel.EMAIL:
                self._send_email(recipients, subject, body)
            elif channel == SecurityAlert.Channel.TEAMS:
                self._send_teams(recipients, subject, body)
            elif channel == SecurityAlert.Channel.SERVICENOW:
                self._send_servicenow(recipients, subject, body)

            alert.status = SecurityAlert.Status.DELIVERED
            alert.save()
        except Exception as e:  # noqa: F841
            logger.exception(f"Error sending alert via {channel}")
            alert.status = SecurityAlert.Status.FAILED
            alert.save()

        return alert

    def _generate_alert_body(self, anomaly: AnomalyDetection) -> str:
        """Generate alert body content."""
        return f"""
Security Anomaly Detected

Type: {anomaly.anomaly_type}
Severity: {anomaly.severity}
User: {anomaly.user_principal}
Description: {anomaly.description}

Evidence: {anomaly.evidence}

Detection Rule: {anomaly.detection_rule}

Please investigate this anomaly immediately.
"""

    def _send_email(self, recipients: list[str], subject: str, body: str) -> None:
        """Send email alert (placeholder)."""
        logger.info(f"Sending email to {recipients}: {subject}")

    def _send_teams(self, recipients: list[str], subject: str, body: str) -> None:
        """Send Teams alert (placeholder)."""
        logger.info(f"Sending Teams message to {recipients}: {subject}")

    def _send_servicenow(self, recipients: list[str], subject: str, body: str) -> None:
        """Send ServiceNow incident (placeholder)."""
        logger.info(f"Creating ServiceNow incident: {subject}")
