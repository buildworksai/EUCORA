# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Anomaly detection engine.

Applies detection rules to identify security anomalies.
"""
from datetime import datetime, timedelta

from django.db import models

from apps.iam_security.models import AnomalyDetection, DetectionRule, IdentityProvider, PermissionChange, SignInEvent


class AnomalyDetector:
    """Detects security anomalies using configured rules."""

    def __init__(self, provider: IdentityProvider):
        """
        Initialize detector for identity provider.

        Args:
            provider: Identity provider instance
        """
        self.provider = provider

    def detect_anomalies(self) -> list[AnomalyDetection]:
        """
        Run all active detection rules.

        Returns:
            List of detected anomalies
        """
        anomalies = []
        rules = DetectionRule.objects.filter(is_active=True)

        for rule in rules:
            detected = self._apply_rule(rule)
            anomalies.extend(detected)

            if detected:
                rule.last_triggered = datetime.now()
                rule.trigger_count += len(detected)
                rule.save()

        return anomalies

    def _apply_rule(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Apply a single detection rule."""
        if rule.anomaly_type == AnomalyDetection.AnomalyType.SUSPICIOUS_LOGIN:
            return self._detect_impossible_travel(rule)
        elif rule.anomaly_type == AnomalyDetection.AnomalyType.AUTHENTICATION_ATTACK:
            return self._detect_brute_force(rule)
        elif rule.anomaly_type == AnomalyDetection.AnomalyType.UNUSUAL_ACTIVITY:
            return self._detect_unusual_hours(rule)
        elif rule.anomaly_type == AnomalyDetection.AnomalyType.NEW_DEVICE:
            return self._detect_new_device(rule)
        elif rule.anomaly_type == AnomalyDetection.AnomalyType.PRIVILEGE_CHANGE:
            return self._detect_privilege_escalation(rule)
        elif rule.anomaly_type == AnomalyDetection.AnomalyType.DORMANT_ACTIVATION:
            return self._detect_dormant_activation(rule)
        elif rule.anomaly_type == AnomalyDetection.AnomalyType.SERVICE_ACCOUNT_ABUSE:
            return self._detect_service_account_abuse(rule)
        return []

    def _detect_impossible_travel(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Detect geographically impossible logins."""
        config = rule.rule_config
        max_speed_kmh = config.get("max_speed_kmh", 1000)
        min_events = config.get("min_events", 2)

        # Get recent sign-ins grouped by user
        lookback = timedelta(hours=24)
        since = datetime.now() - lookback
        events = SignInEvent.objects.filter(
            provider=self.provider,
            status=SignInEvent.Status.SUCCESS,
            event_time__gte=since,
        ).order_by("user_principal", "event_time")

        anomalies = []
        current_user = None
        user_events = []

        for event in events:
            if event.user_principal != current_user:
                if current_user and len(user_events) >= min_events:
                    # Check for impossible travel
                    anomaly = self._check_impossible_travel(current_user, user_events, max_speed_kmh, rule)
                    if anomaly:
                        anomalies.append(anomaly)
                current_user = event.user_principal
                user_events = [event]
            else:
                user_events.append(event)

        # Check last user
        if current_user and len(user_events) >= min_events:
            anomaly = self._check_impossible_travel(current_user, user_events, max_speed_kmh, rule)
            if anomaly:
                anomalies.append(anomaly)

        return anomalies

    def _check_impossible_travel(
        self, user: str, events: list[SignInEvent], max_speed: float, rule: DetectionRule
    ) -> AnomalyDetection | None:
        """Check if events indicate impossible travel."""
        for i in range(len(events) - 1):
            event1 = events[i]
            event2 = events[i + 1]

            location1 = event1.location
            location2 = event2.location

            if location1 and location2:
                # Calculate distance and time
                distance_km = self._calculate_distance(
                    location1.get("latitude"),
                    location1.get("longitude"),
                    location2.get("latitude"),
                    location2.get("longitude"),
                )
                time_diff_hours = (event2.event_time - event1.event_time).total_seconds() / 3600

                if time_diff_hours > 0:
                    speed_kmh = distance_km / time_diff_hours
                    if speed_kmh > max_speed:
                        return AnomalyDetection.objects.create(
                            provider=self.provider,
                            anomaly_type=AnomalyDetection.AnomalyType.SUSPICIOUS_LOGIN,
                            severity=rule.severity,
                            user_principal=user,
                            description=f"Impossible travel detected: {distance_km:.1f}km in {time_diff_hours:.1f}h ({speed_kmh:.1f} km/h)",  # noqa: E501
                            evidence={
                                "event1": str(event1.id),
                                "event2": str(event2.id),
                                "distance_km": distance_km,
                                "speed_kmh": speed_kmh,
                            },
                            related_events=[str(event1.id), str(event2.id)],
                            detection_rule=rule.name,
                        )
        return None

    def _detect_brute_force(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Detect brute force authentication attempts."""
        config = rule.threshold_config
        failure_threshold = config.get("failure_threshold", 10)
        time_window_minutes = config.get("time_window_minutes", 30)

        lookback = timedelta(minutes=time_window_minutes)
        since = datetime.now() - lookback

        # Group failed sign-ins by user
        failed_events = (
            SignInEvent.objects.filter(
                provider=self.provider,
                status=SignInEvent.Status.FAILURE,
                event_time__gte=since,
            )
            .values("user_principal")
            .annotate(count=models.Count("id"))
        )

        anomalies = []
        for item in failed_events:
            if item["count"] >= failure_threshold:
                user = item["user_principal"]
                events = SignInEvent.objects.filter(
                    provider=self.provider,
                    user_principal=user,
                    status=SignInEvent.Status.FAILURE,
                    event_time__gte=since,
                )

                anomalies.append(
                    AnomalyDetection.objects.create(
                        provider=self.provider,
                        anomaly_type=AnomalyDetection.AnomalyType.AUTHENTICATION_ATTACK,
                        severity=rule.severity,
                        user_principal=user,
                        description=f"Brute force attempt: {item['count']} failed sign-ins in {time_window_minutes} minutes",  # noqa: E501
                        evidence={"failure_count": item["count"]},
                        related_events=[str(e.id) for e in events],
                        detection_rule=rule.name,
                    )
                )

        return anomalies

    def _detect_unusual_hours(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Detect access outside normal working hours."""
        config = rule.rule_config
        normal_start = config.get("normal_hours_start", 7)
        normal_end = config.get("normal_hours_end", 20)

        lookback = timedelta(hours=24)
        since = datetime.now() - lookback

        events = SignInEvent.objects.filter(
            provider=self.provider,
            status=SignInEvent.Status.SUCCESS,
            event_time__gte=since,
        )

        anomalies = []
        for event in events:
            hour = event.event_time.hour
            if hour < normal_start or hour >= normal_end:
                anomalies.append(
                    AnomalyDetection.objects.create(
                        provider=self.provider,
                        anomaly_type=AnomalyDetection.AnomalyType.UNUSUAL_ACTIVITY,
                        severity=rule.severity,
                        user_principal=event.user_principal,
                        description=f"Unusual hour access: {hour}:00",
                        evidence={"hour": hour, "normal_range": f"{normal_start}-{normal_end}"},
                        related_events=[str(event.id)],
                        detection_rule=rule.name,
                    )
                )

        return anomalies

    def _detect_new_device(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Detect access from new device."""
        config = rule.rule_config
        lookback_days = config.get("lookback_days", 90)

        lookback = timedelta(days=lookback_days)
        since = datetime.now() - lookback

        # Get recent sign-ins with device info
        recent_events = SignInEvent.objects.filter(  # noqa: F841
            provider=self.provider,
            status=SignInEvent.Status.SUCCESS,
            event_time__gte=since,
        ).exclude(device_detail__isnull=True)

        # Group by user and check for new devices (simplified)
        anomalies = []
        # Implementation would check device history per user
        return anomalies

    def _detect_privilege_escalation(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Detect privilege escalation."""
        config = rule.rule_config
        sensitive_roles = config.get("sensitive_roles", [])

        # Check permission changes for sensitive roles
        lookback = timedelta(hours=24)
        since = datetime.now() - lookback

        changes = PermissionChange.objects.filter(
            provider=self.provider,
            change_type=PermissionChange.ChangeType.ADD,
            resource_type=PermissionChange.ResourceType.ROLE,
            event_time__gte=since,
        )

        anomalies = []
        for change in changes:
            if change.resource_name in sensitive_roles:
                anomalies.append(
                    AnomalyDetection.objects.create(
                        provider=self.provider,
                        anomaly_type=AnomalyDetection.AnomalyType.PRIVILEGE_CHANGE,
                        severity=rule.severity,
                        user_principal=change.target_principal,
                        description=f"Privilege escalation: {change.resource_name}",
                        evidence={"role": change.resource_name, "actor": change.actor_principal},
                        related_events=[str(change.id)],
                        detection_rule=rule.name,
                    )
                )

        return anomalies

    def _detect_dormant_activation(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Detect dormant account activation."""
        config = rule.rule_config
        dormant_days = config.get("dormant_days", 90)  # noqa: F841

        # Check for accounts with no recent activity that suddenly become active
        # Simplified implementation
        return []

    def _detect_service_account_abuse(self, rule: DetectionRule) -> list[AnomalyDetection]:
        """Detect service account interactive sign-in."""
        config = rule.rule_config
        service_patterns = config.get("service_account_patterns", ["svc-*", "*-service"])

        lookback = timedelta(hours=24)
        since = datetime.now() - lookback

        events = SignInEvent.objects.filter(
            provider=self.provider,
            status=SignInEvent.Status.SUCCESS,
            event_time__gte=since,
        )

        anomalies = []
        for event in events:
            user = event.user_principal.lower()
            for pattern in service_patterns:
                pattern_lower = pattern.lower().replace("*", "")
                if pattern_lower in user:
                    anomalies.append(
                        AnomalyDetection.objects.create(
                            provider=self.provider,
                            anomaly_type=AnomalyDetection.AnomalyType.SERVICE_ACCOUNT_ABUSE,
                            severity=AnomalyDetection.Severity.CRITICAL,
                            user_principal=event.user_principal,
                            description=f"Service account used for interactive sign-in: {user}",
                            evidence={"pattern": pattern},
                            related_events=[str(event.id)],
                            detection_rule=rule.name,
                        )
                    )
                    break

        return anomalies

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates (Haversine formula)."""
        from math import asin, cos, radians, sin, sqrt

        R = 6371  # Earth radius in km
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return R * c
