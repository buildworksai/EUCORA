# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for SecOps Agent.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    ComplianceBaseline,
    ComplianceCheck,
    RemediationPlan,
    SecurityAlert,
    SIEMConnection,
    Vulnerability,
    VulnerabilityInstance,
    VulnerabilityScanner,
)
from .serializers import (
    ComplianceBaselineSerializer,
    ComplianceCheckSerializer,
    RemediationPlanSerializer,
    SecurityAlertSerializer,
    SIEMConnectionSerializer,
    VulnerabilityInstanceSerializer,
    VulnerabilityScannerSerializer,
    VulnerabilitySerializer,
)
from .services.compliance_checker import ComplianceChecker
from .services.remediation_service import RemediationService
from .services.siem_client import get_siem_client
from .services.vulnerability_scanner import get_scanner_client

logger = logging.getLogger(__name__)


class VulnerabilityScannerViewSet(viewsets.ModelViewSet):
    """ViewSet for vulnerability scanners."""

    queryset = VulnerabilityScanner.objects.all()
    serializer_class = VulnerabilityScannerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by scanner_type and is_active if provided."""
        queryset = VulnerabilityScanner.objects.all()
        scanner_type = self.request.query_params.get("scanner_type")
        if scanner_type:
            queryset = queryset.filter(scanner_type=scanner_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def sync(self, request: Request, pk=None) -> Response:
        """Sync vulnerabilities from scanner."""
        scanner = self.get_object()
        client = get_scanner_client(scanner)

        try:
            vulnerabilities_data = client.sync_vulnerabilities()
            synced_count = 0

            for vuln_data in vulnerabilities_data:
                instances_data = vuln_data.pop("instances", [])
                vulnerability, _ = Vulnerability.objects.update_or_create(
                    cve_id=vuln_data["cve_id"],
                    defaults={
                        "title": vuln_data["title"],
                        "description": vuln_data["description"],
                        "severity": vuln_data["severity"],
                        "cvss_score": vuln_data.get("cvss_score"),
                        "cvss_vector": vuln_data.get("cvss_vector"),
                        "exploitability_score": vuln_data.get("exploitability_score"),
                        "published_date": vuln_data["published_date"],
                        "modified_date": vuln_data.get("modified_date", vuln_data["published_date"]),
                        "references": vuln_data.get("references", []),
                        "affected_products": vuln_data.get("affected_products", []),
                    },
                )

                for inst_data in instances_data:
                    VulnerabilityInstance.objects.update_or_create(
                        vulnerability=vulnerability,
                        asset_id=inst_data["asset_id"],
                        scanner=scanner,
                        defaults={
                            "asset_name": inst_data["asset_name"],
                            "detected_at": inst_data["detected_at"],
                            "status": VulnerabilityInstance.Status.OPEN,
                        },
                    )
                    synced_count += 1

            scanner.last_sync = timezone.now()
            scanner.save()

            return Response({"synced": synced_count, "vulnerabilities": len(vulnerabilities_data)})
        except Exception as e:
            logger.error(f"Failed to sync vulnerabilities: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test scanner connection."""
        scanner = self.get_object()
        client = get_scanner_client(scanner)

        try:
            success = client.test_connection()
            return Response({"success": success})
        except Exception as e:
            logger.error(f"Failed to test connection: {e}")
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VulnerabilityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for vulnerabilities."""

    queryset = Vulnerability.objects.all()
    serializer_class = VulnerabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by severity, cve_id, or search."""
        queryset = Vulnerability.objects.all()
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        cve_id = self.request.query_params.get("cve_id")
        if cve_id:
            queryset = queryset.filter(cve_id__icontains=cve_id)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset.order_by("-cvss_score", "-published_date")

    @action(detail=True, methods=["get"])
    def instances(self, request: Request, pk=None) -> Response:
        """Get instances of this vulnerability."""
        vulnerability = self.get_object()
        instances = vulnerability.instances.all()
        serializer = VulnerabilityInstanceSerializer(instances, many=True)
        return Response(serializer.data)


class VulnerabilityInstanceViewSet(viewsets.ModelViewSet):
    """ViewSet for vulnerability instances."""

    queryset = VulnerabilityInstance.objects.select_related("vulnerability", "scanner", "application")
    serializer_class = VulnerabilityInstanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, status, asset_id, or vulnerability."""
        queryset = VulnerabilityInstance.objects.select_related("vulnerability", "scanner", "application")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        vulnerability_id = self.request.query_params.get("vulnerability_id")
        if vulnerability_id:
            queryset = queryset.filter(vulnerability_id=vulnerability_id)
        return queryset.order_by("-detected_at")

    @action(detail=True, methods=["post"])
    def remediate(self, request: Request, pk=None) -> Response:
        """Mark instance as remediated."""
        instance = self.get_object()
        instance.status = VulnerabilityInstance.Status.REMEDIATED
        instance.remediated_at = timezone.now()
        instance.remediation_notes = request.data.get("notes", "")
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def accept_risk(self, request: Request, pk=None) -> Response:
        """Accept risk for this instance."""
        instance = self.get_object()
        instance.status = VulnerabilityInstance.Status.ACCEPTED
        instance.remediation_notes = request.data.get("notes", "")
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def false_positive(self, request: Request, pk=None) -> Response:
        """Mark instance as false positive."""
        instance = self.get_object()
        instance.status = VulnerabilityInstance.Status.FALSE_POSITIVE
        instance.remediation_notes = request.data.get("notes", "")
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class RemediationPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for remediation plans."""

    queryset = RemediationPlan.objects.select_related("vulnerability", "approved_by")
    serializer_class = RemediationPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, status, risk_level, or vulnerability."""
        queryset = RemediationPlan.objects.select_related("vulnerability", "approved_by")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        risk_level = self.request.query_params.get("risk_level")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        vulnerability_id = self.request.query_params.get("vulnerability_id")
        if vulnerability_id:
            queryset = queryset.filter(vulnerability_id=vulnerability_id)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve remediation plan."""
        plan = self.get_object()
        if plan.status != RemediationPlan.Status.PENDING_APPROVAL:
            return Response({"error": "Plan is not pending approval"}, status=status.HTTP_400_BAD_REQUEST)

        plan.status = RemediationPlan.Status.APPROVED
        plan.approved_by = request.user
        plan.approved_at = timezone.now()
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def execute(self, request: Request, pk=None) -> Response:
        """Execute remediation plan."""
        plan = self.get_object()
        if plan.status != RemediationPlan.Status.APPROVED:
            return Response({"error": "Plan must be approved first"}, status=status.HTTP_400_BAD_REQUEST)

        plan.status = RemediationPlan.Status.EXECUTING
        plan.executed_at = timezone.now()
        plan.save()

        # TODO: Execute actual remediation steps
        # For now, mark as completed
        plan.status = RemediationPlan.Status.COMPLETED
        plan.completed_at = timezone.now()
        plan.save()

        # Update affected instances
        for instance in plan.affected_instances.all():
            instance.status = VulnerabilityInstance.Status.REMEDIATED
            instance.remediated_at = timezone.now()
            instance.save()

        serializer = self.get_serializer(plan)
        return Response(serializer.data)


class SIEMConnectionViewSet(viewsets.ModelViewSet):
    """ViewSet for SIEM connections."""

    queryset = SIEMConnection.objects.all()
    serializer_class = SIEMConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by siem_type and is_active if provided."""
        queryset = SIEMConnection.objects.all()
        siem_type = self.request.query_params.get("siem_type")
        if siem_type:
            queryset = queryset.filter(siem_type=siem_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test SIEM connection."""
        connection = self.get_object()
        client = get_siem_client(connection)

        try:
            success = client.test_connection()
            return Response({"success": success})
        except Exception as e:
            logger.error(f"Failed to test connection: {e}")
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def sync_alerts(self, request: Request, pk=None) -> Response:
        """Sync alerts from SIEM."""
        connection = self.get_object()
        client = get_siem_client(connection)

        since = request.data.get("since")
        if since:
            since = datetime.fromisoformat(since.replace("Z", "+00:00"))

        try:
            alerts_data = client.sync_alerts(since=since)
            synced_count = 0

            for alert_data in alerts_data:
                SecurityAlert.objects.update_or_create(
                    siem=connection,
                    alert_id=alert_data["alert_id"],
                    defaults={
                        "title": alert_data["title"],
                        "severity": alert_data["severity"],
                        "description": alert_data["description"],
                        "source": alert_data["source"],
                        "affected_assets": alert_data.get("affected_assets", []),
                        "alert_time": alert_data["alert_time"],
                        "status": SecurityAlert.Status.NEW,
                    },
                )
                synced_count += 1

            return Response({"synced": synced_count})
        except Exception as e:
            logger.error(f"Failed to sync alerts: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SecurityAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for security alerts."""

    queryset = SecurityAlert.objects.select_related("siem", "remediation_plan")
    serializer_class = SecurityAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, status, severity, or siem."""
        queryset = SecurityAlert.objects.select_related("siem", "remediation_plan")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        siem_id = self.request.query_params.get("siem_id")
        if siem_id:
            queryset = queryset.filter(siem_id=siem_id)
        return queryset.order_by("-alert_time")

    @action(detail=True, methods=["post"])
    def correlate(self, request: Request, pk=None) -> Response:
        """Correlate alert with vulnerabilities."""
        alert = self.get_object()
        vulnerability_ids = request.data.get("vulnerability_ids", [])

        vulnerabilities = Vulnerability.objects.filter(id__in=vulnerability_ids)
        alert.related_vulnerabilities.set(vulnerabilities)

        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def create_incident(self, request: Request, pk=None) -> Response:
        """Create incident from alert."""
        alert = self.get_object()
        # TODO: Create incident in ServiceNow or other ITSM system
        alert.status = SecurityAlert.Status.INVESTIGATING
        alert.save()
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


class ComplianceBaselineViewSet(viewsets.ModelViewSet):
    """ViewSet for compliance baselines."""

    queryset = ComplianceBaseline.objects.all()
    serializer_class = ComplianceBaselineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by framework and is_active if provided."""
        queryset = ComplianceBaseline.objects.all()
        framework = self.request.query_params.get("framework")
        if framework:
            queryset = queryset.filter(framework=framework)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")


class ComplianceCheckViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for compliance checks."""

    queryset = ComplianceCheck.objects.select_related("baseline")
    serializer_class = ComplianceCheckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, baseline, or asset_id."""
        queryset = ComplianceCheck.objects.select_related("baseline")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        baseline_id = self.request.query_params.get("baseline_id")
        if baseline_id:
            queryset = queryset.filter(baseline_id=baseline_id)
        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        return queryset.order_by("-check_time")

    @action(detail=False, methods=["post"])
    def run_check(self, request: Request) -> Response:
        """Run compliance check for asset."""
        baseline_id = request.data.get("baseline_id")
        asset_id = request.data.get("asset_id")
        asset_config = request.data.get("asset_config", {})

        if not baseline_id or not asset_id:
            return Response({"error": "baseline_id and asset_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            baseline = ComplianceBaseline.objects.get(id=baseline_id)
        except ComplianceBaseline.DoesNotExist:
            return Response({"error": "Baseline not found"}, status=status.HTTP_404_NOT_FOUND)

        checker = ComplianceChecker(baseline)
        results = checker.check_asset(asset_id, asset_config)

        check = ComplianceCheck.objects.create(
            baseline=baseline,
            asset_id=asset_id,
            overall_score=results["overall_score"],
            passed_controls=results["passed_controls"],
            failed_controls=results["failed_controls"],
            control_results=results["control_results"],
        )

        serializer = self.get_serializer(check)
        return Response(serializer.data)


class SecOpsReportsViewSet(viewsets.ViewSet):
    """ViewSet for SecOps reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request: Request) -> Response:
        """Get SecOps summary statistics."""
        critical_vulns = VulnerabilityInstance.objects.filter(
            vulnerability__severity="critical", status=VulnerabilityInstance.Status.OPEN
        ).count()
        high_vulns = VulnerabilityInstance.objects.filter(
            vulnerability__severity="high", status=VulnerabilityInstance.Status.OPEN
        ).count()
        medium_vulns = VulnerabilityInstance.objects.filter(
            vulnerability__severity="medium", status=VulnerabilityInstance.Status.OPEN
        ).count()

        pending_plans = RemediationPlan.objects.filter(status=RemediationPlan.Status.PENDING_APPROVAL).count()
        executing_plans = RemediationPlan.objects.filter(status=RemediationPlan.Status.EXECUTING).count()

        critical_alerts = SecurityAlert.objects.filter(severity="critical", status=SecurityAlert.Status.NEW).count()
        high_alerts = SecurityAlert.objects.filter(severity="high", status=SecurityAlert.Status.NEW).count()

        return Response(
            {
                "critical_vulnerabilities": critical_vulns,
                "high_vulnerabilities": high_vulns,
                "medium_vulnerabilities": medium_vulns,
                "pending_remediation_plans": pending_plans,
                "executing_remediation_plans": executing_plans,
                "critical_alerts": critical_alerts,
                "high_alerts": high_alerts,
            }
        )

    @action(detail=False, methods=["get"])
    def risk_trend(self, request: Request) -> Response:
        """Get risk trend over time."""
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        # Group by date
        trends = []
        for i in range(days):
            date = since + timedelta(days=i)
            count = VulnerabilityInstance.objects.filter(
                detected_at__date=date.date(), status=VulnerabilityInstance.Status.OPEN
            ).count()
            trends.append({"date": date.date().isoformat(), "count": count})

        return Response({"trends": trends})

    @action(detail=False, methods=["get"])
    def compliance_status(self, request: Request) -> Response:
        """Get compliance status by framework."""
        baselines = ComplianceBaseline.objects.filter(is_active=True)

        status_data = []
        for baseline in baselines:
            recent_checks = baseline.checks.order_by("-check_time")[:10]
            avg_score = sum(check.overall_score for check in recent_checks) / len(recent_checks) if recent_checks else 0

            status_data.append(
                {
                    "baseline_id": str(baseline.id),
                    "framework": baseline.framework,
                    "name": baseline.name,
                    "average_score": round(avg_score, 2),
                    "check_count": len(recent_checks),
                }
            )

        return Response({"compliance_status": status_data})
