# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Discovery Agent.
"""
import logging

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    DiscoveredApplication,
    DiscoveryReport,
    DiscoveryRun,
    DiscoverySource,
    LicenseGap,
    NormalizedApplication,
    PatchGap,
)
from .serializers import (
    DiscoveredApplicationSerializer,
    DiscoveryReportSerializer,
    DiscoveryRunSerializer,
    DiscoveryRunStartSerializer,
    DiscoverySourceSerializer,
    GapResolveSerializer,
    GenerateReportSerializer,
    LicenseGapSerializer,
    MergeApplicationsSerializer,
    NormalizedApplicationDetailSerializer,
    NormalizedApplicationSerializer,
    PatchGapSerializer,
)

logger = logging.getLogger(__name__)


class DiscoverySourceViewSet(viewsets.ModelViewSet):
    """ViewSet for discovery sources."""

    queryset = DiscoverySource.objects.all()
    serializer_class = DiscoverySourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by source type if provided."""
        queryset = DiscoverySource.objects.all()
        source_type = self.request.query_params.get("source_type")
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        return queryset.order_by("name")

    @action(detail=True, methods=["post"])
    def sync(self, request: Request, pk=None) -> Response:
        """Start a sync for this source."""
        source = self.get_object()

        # Create discovery run
        run = DiscoveryRun.objects.create(
            source=source,
            run_type=DiscoveryRun.RunType.INCREMENTAL,
            status=DiscoveryRun.Status.PENDING,
            initiated_by=request.user,
        )

        # In production, queue as Celery task
        # For now, simulate some discoveries
        import random
        import uuid

        run.status = DiscoveryRun.Status.RUNNING
        run.save()

        # Generate mock discovered apps
        mock_apps = [
            ("Microsoft Office 365", "Microsoft Corporation", "16.0.14326"),
            ("Google Chrome", "Google LLC", "120.0.6099"),
            ("Adobe Acrobat Reader", "Adobe Inc.", "2024.001"),
            ("Slack", "Slack Technologies", "4.35.126"),
            ("Zoom", "Zoom Video Communications", "5.17.5"),
        ]

        for name, publisher, version in mock_apps:
            DiscoveredApplication.objects.create(
                discovery_run=run,
                source_id=str(uuid.uuid4()),
                source_type=source.source_type,
                raw_name=name,
                raw_publisher=publisher,
                raw_version=version,
                install_count=random.randint(50, 500),
            )

        run.records_discovered = len(mock_apps)
        run.records_new = len(mock_apps)
        run.status = DiscoveryRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.save()

        # Update source
        source.last_sync = timezone.now()
        source.last_sync_status = "success"
        source.save()

        return Response(DiscoveryRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="upload")
    def upload(self, request: Request, pk=None) -> Response:
        """Upload spreadsheet for this source."""
        source = self.get_object()

        if source.source_type != DiscoverySource.SourceType.SPREADSHEET:
            return Response(
                {"error": "Upload only supported for spreadsheet sources"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # In production, process uploaded file
        return Response({"message": "Upload processing started"})


class DiscoveryRunViewSet(viewsets.ModelViewSet):
    """ViewSet for discovery runs."""

    queryset = DiscoveryRun.objects.all()
    serializer_class = DiscoveryRunSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        """Filter by source and correlation_id."""
        queryset = DiscoveryRun.objects.select_related("source", "initiated_by")

        source_id = self.request.query_params.get("source_id")
        if source_id:
            queryset = queryset.filter(source_id=source_id)

        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by("-started_at")

    def create(self, request: Request) -> Response:
        """Start a new discovery run."""
        serializer = DiscoveryRunStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_id = serializer.validated_data["source_id"]
        run_type = serializer.validated_data["run_type"]

        try:
            source = DiscoverySource.objects.get(id=source_id, is_active=True)
        except DiscoverySource.DoesNotExist:
            return Response(
                {"error": "Source not found or inactive"},
                status=status.HTTP_404_NOT_FOUND,
            )

        run = DiscoveryRun.objects.create(
            source=source,
            run_type=run_type,
            status=DiscoveryRun.Status.PENDING,
            initiated_by=request.user,
        )

        return Response(DiscoveryRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def applications(self, request: Request, pk=None) -> Response:
        """Get discovered applications for this run."""
        run = self.get_object()
        apps = run.applications.select_related("normalized_app")
        serializer = DiscoveredApplicationSerializer(apps, many=True)
        return Response(serializer.data)


class NormalizedApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for normalized applications."""

    queryset = NormalizedApplication.objects.all()
    serializer_class = NormalizedApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter applications."""
        queryset = NormalizedApplication.objects.prefetch_related("versions")

        is_managed = self.request.query_params.get("is_managed")
        if is_managed is not None:
            queryset = queryset.filter(is_managed=is_managed.lower() == "true")

        is_approved = self.request.query_params.get("is_approved")
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved.lower() == "true")

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        publisher = self.request.query_params.get("publisher")
        if publisher:
            queryset = queryset.filter(publisher__icontains=publisher)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(publisher__icontains=search))

        return queryset.order_by("-total_installs")

    def get_serializer_class(self):
        """Use detail serializer for retrieve."""
        if self.action == "retrieve":
            return NormalizedApplicationDetailSerializer
        return NormalizedApplicationSerializer

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Mark application as approved."""
        app = self.get_object()
        app.is_approved = True
        app.save()
        return Response(NormalizedApplicationSerializer(app).data)

    @action(detail=True, methods=["post"])
    def restrict(self, request: Request, pk=None) -> Response:
        """Mark application as restricted."""
        app = self.get_object()
        app.is_restricted = True
        app.is_approved = False
        app.save()
        return Response(NormalizedApplicationSerializer(app).data)

    @action(detail=False, methods=["post"])
    def merge(self, request: Request) -> Response:
        """Merge duplicate applications."""
        serializer = MergeApplicationsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_ids = serializer.validated_data["source_ids"]
        target_id = serializer.validated_data["target_id"]

        try:
            target = NormalizedApplication.objects.get(id=target_id)
        except NormalizedApplication.DoesNotExist:
            return Response({"error": "Target not found"}, status=status.HTTP_404_NOT_FOUND)

        merged_count = 0
        for source_id in source_ids:
            if source_id == target_id:
                continue

            try:
                source = NormalizedApplication.objects.get(id=source_id)
                # Move discovered applications
                source.discovered_instances.update(normalized_app=target)
                # Add install count
                target.total_installs += source.total_installs
                merged_count += 1
                source.delete()
            except NormalizedApplication.DoesNotExist:
                pass

        target.save()

        return Response(
            {
                "merged": merged_count,
                "target": NormalizedApplicationSerializer(target).data,
            }
        )


class LicenseGapViewSet(viewsets.ModelViewSet):
    """ViewSet for license gaps."""

    queryset = LicenseGap.objects.all()
    serializer_class = LicenseGapSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        """Filter gaps."""
        queryset = LicenseGap.objects.select_related("application", "resolved_by")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        risk_level = self.request.query_params.get("risk_level")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)

        gap_type = self.request.query_params.get("gap_type")
        if gap_type:
            queryset = queryset.filter(gap_type=gap_type)

        return queryset.order_by("-risk_level", "-created_at")

    @action(detail=True, methods=["post"])
    def acknowledge(self, request: Request, pk=None) -> Response:
        """Acknowledge a license gap."""
        gap = self.get_object()
        gap.status = LicenseGap.Status.ACKNOWLEDGED
        gap.save()
        return Response(LicenseGapSerializer(gap).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request: Request, pk=None) -> Response:
        """Resolve a license gap."""
        gap = self.get_object()
        serializer = GapResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gap.status = LicenseGap.Status.RESOLVED
        gap.resolved_by = request.user
        gap.resolved_at = timezone.now()
        gap.resolution_notes = serializer.validated_data.get("notes", "")
        gap.save()

        return Response(LicenseGapSerializer(gap).data)


class PatchGapViewSet(viewsets.ModelViewSet):
    """ViewSet for patch gaps."""

    queryset = PatchGap.objects.all()
    serializer_class = PatchGapSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        """Filter gaps."""
        queryset = PatchGap.objects.select_related("application", "current_version", "target_version")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        gap_type = self.request.query_params.get("gap_type")
        if gap_type:
            queryset = queryset.filter(gap_type=gap_type)

        return queryset.order_by("-severity", "-created_at")

    @action(detail=True, methods=["post"])
    def plan(self, request: Request, pk=None) -> Response:
        """Plan remediation for a patch gap."""
        gap = self.get_object()
        serializer = GapResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gap.status = PatchGap.Status.PLANNED
        gap.planned_date = serializer.validated_data.get("planned_date")
        gap.save()

        return Response(PatchGapSerializer(gap).data)


class DiscoveryReportViewSet(viewsets.ModelViewSet):
    """ViewSet for discovery reports."""

    queryset = DiscoveryReport.objects.all()
    serializer_class = DiscoveryReportSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        """Filter reports."""
        queryset = DiscoveryReport.objects.select_related("generated_by")

        report_type = self.request.query_params.get("report_type")
        if report_type:
            queryset = queryset.filter(report_type=report_type)

        return queryset.order_by("-generated_at")

    @action(detail=False, methods=["post"])
    def generate(self, request: Request) -> Response:
        """Generate a new report."""
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report_type = serializer.validated_data["report_type"]
        title = serializer.validated_data.get("title", f"{report_type.title()} Report")

        # Generate report data based on type
        summary = {}
        details = {}

        if report_type == DiscoveryReport.ReportType.INVENTORY:
            summary = {
                "total_applications": NormalizedApplication.objects.count(),
                "managed": NormalizedApplication.objects.filter(is_managed=True).count(),
                "unmanaged": NormalizedApplication.objects.filter(is_managed=False).count(),
            }
        elif report_type == DiscoveryReport.ReportType.SHADOW_IT:
            shadow_apps = NormalizedApplication.objects.filter(is_managed=False, is_approved=False).order_by(
                "-total_installs"
            )[:20]
            summary = {
                "shadow_it_count": shadow_apps.count(),
                "top_shadow_apps": [{"name": a.name, "installs": a.total_installs} for a in shadow_apps],
            }
        elif report_type == DiscoveryReport.ReportType.LICENSE_COMPLIANCE:
            summary = {
                "total_gaps": LicenseGap.objects.filter(status="open").count(),
                "critical": LicenseGap.objects.filter(status="open", risk_level="critical").count(),
                "high": LicenseGap.objects.filter(status="open", risk_level="high").count(),
            }
        elif report_type == DiscoveryReport.ReportType.PATCH_COMPLIANCE:
            summary = {
                "total_gaps": PatchGap.objects.filter(status="open").count(),
                "critical": PatchGap.objects.filter(status="open", severity="critical").count(),
                "high": PatchGap.objects.filter(status="open", severity="high").count(),
            }

        report = DiscoveryReport.objects.create(
            report_type=report_type,
            title=title,
            summary=summary,
            details=details,
            generated_by=request.user,
        )

        return Response(DiscoveryReportSerializer(report).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def export(self, request: Request, pk=None) -> Response:
        """Export report (placeholder)."""
        report = self.get_object()
        # In production, generate CSV/PDF
        return Response(
            {
                "message": "Export functionality coming soon",
                "report_id": str(report.id),
            }
        )


class DiscoveryDashboardViewSet(viewsets.ViewSet):
    """ViewSet for discovery dashboard data."""

    permission_classes = [IsAuthenticated]

    def list(self, request: Request) -> Response:
        """Get dashboard data."""
        total_apps = NormalizedApplication.objects.count()
        managed = NormalizedApplication.objects.filter(is_managed=True).count()
        unmanaged = NormalizedApplication.objects.filter(is_managed=False).count()
        shadow_it = NormalizedApplication.objects.filter(is_managed=False, is_approved=False).count()

        license_gaps = LicenseGap.objects.filter(status="open").count()
        patch_gaps = PatchGap.objects.filter(status="open").count()

        total_installs = NormalizedApplication.objects.aggregate(total=Sum("total_installs"))["total"] or 0

        last_run = DiscoveryRun.objects.filter(status=DiscoveryRun.Status.COMPLETED).order_by("-completed_at").first()

        # Applications by category
        by_category = dict(
            NormalizedApplication.objects.values("category")
            .annotate(count=Count("id"))
            .values_list("category", "count")
        )

        # Risk distribution
        risk_dist = dict(
            LicenseGap.objects.filter(status="open")
            .values("risk_level")
            .annotate(count=Count("id"))
            .values_list("risk_level", "count")
        )

        return Response(
            {
                "total_applications": total_apps,
                "managed_applications": managed,
                "unmanaged_applications": unmanaged,
                "shadow_it_count": shadow_it,
                "license_gaps_count": license_gaps,
                "patch_gaps_count": patch_gaps,
                "total_installs": total_installs,
                "last_discovery": last_run.completed_at if last_run else None,
                "applications_by_category": by_category,
                "risk_distribution": risk_dist,
            }
        )
