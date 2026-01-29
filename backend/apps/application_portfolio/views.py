# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Application Portfolio API views.

REST API endpoints for application catalog, versions, artifacts,
and deployment management.
"""
from __future__ import annotations

from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    Application,
    ApplicationDependency,
    ApplicationHealth,
    ApplicationVersion,
    DeploymentIntent,
    DeploymentMetric,
    DeploymentStatus,
    PackageArtifact,
    Publisher,
)
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationDependencySerializer,
    ApplicationHealthSerializer,
    ApplicationListSerializer,
    ApplicationPortfolioSummarySerializer,
    ApplicationSerializer,
    ApplicationVersionListSerializer,
    ApplicationVersionSerializer,
    DeploymentIntentCreateSerializer,
    DeploymentIntentListSerializer,
    DeploymentIntentSerializer,
    DeploymentMetricSerializer,
    PackageArtifactListSerializer,
    PackageArtifactSerializer,
    PackageArtifactUploadSerializer,
    PublisherListSerializer,
    PublisherSerializer,
)


class PublisherViewSet(viewsets.ModelViewSet):
    """
    API endpoint for software publishers.

    list: List all publishers
    retrieve: Get publisher details
    create: Create a new publisher
    update: Update publisher details
    destroy: Deactivate a publisher
    """

    queryset = Publisher.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return PublisherListSerializer
        return PublisherSerializer

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by verified status
        is_verified = self.request.query_params.get("is_verified")
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == "true")

        return queryset


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for applications.

    list: List all applications with filtering
    retrieve: Get application details
    create: Create a new application
    update: Update application details
    destroy: Deactivate an application
    versions: List versions for an application
    health: Get health status for an application
    dependencies: List dependencies for an application
    """

    queryset = Application.objects.select_related("publisher", "owner").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ApplicationListSerializer
        if self.action == "create":
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by publisher
        publisher = self.request.query_params.get("publisher")
        if publisher:
            queryset = queryset.filter(publisher_id=publisher)

        # Filter by status
        app_status = self.request.query_params.get("status")
        if app_status:
            queryset = queryset.filter(status=app_status)

        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__icontains=category)

        # Filter by platform
        platform = self.request.query_params.get("platform")
        if platform:
            queryset = queryset.filter(supported_platforms__contains=[platform])

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by privileged
        is_privileged = self.request.query_params.get("is_privileged")
        if is_privileged is not None:
            queryset = queryset.filter(is_privileged=is_privileged.lower() == "true")

        # Search by name or identifier
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(identifier__icontains=search))

        return queryset

    def perform_create(self, serializer):
        """Set owner on creation."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def versions(self, request: Request, pk=None) -> Response:
        """List versions for an application."""
        application = self.get_object()
        versions = application.versions.all()
        serializer = ApplicationVersionListSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def health(self, request: Request, pk=None) -> Response:
        """Get latest health status for an application."""
        application = self.get_object()
        health = application.health_snapshots.first()
        if not health:
            return Response(
                {"detail": "No health data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ApplicationHealthSerializer(health)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def dependencies(self, request: Request, pk=None) -> Response:
        """List dependencies for an application."""
        application = self.get_object()
        deps = application.dependencies.select_related("depends_on").all()
        serializer = ApplicationDependencySerializer(deps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def dependents(self, request: Request, pk=None) -> Response:
        """List applications that depend on this application."""
        application = self.get_object()
        deps = application.dependents.select_related("application").all()
        serializer = ApplicationDependencySerializer(deps, many=True)
        return Response(serializer.data)


class ApplicationVersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for application versions.

    list: List all versions
    retrieve: Get version details
    create: Create a new version
    update: Update version details
    artifacts: List artifacts for a version
    approve: Approve a version
    """

    queryset = ApplicationVersion.objects.select_related("application", "approved_by").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ApplicationVersionListSerializer
        return ApplicationVersionSerializer

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by application
        application = self.request.query_params.get("application")
        if application:
            queryset = queryset.filter(application_id=application)

        # Filter by latest only
        latest_only = self.request.query_params.get("latest_only")
        if latest_only and latest_only.lower() == "true":
            queryset = queryset.filter(is_latest=True)

        # Filter by security updates
        security_only = self.request.query_params.get("security_only")
        if security_only and security_only.lower() == "true":
            queryset = queryset.filter(is_security_update=True)

        return queryset

    @action(detail=True, methods=["get"])
    def artifacts(self, request: Request, pk=None) -> Response:
        """List artifacts for a version."""
        version = self.get_object()
        artifacts = version.artifacts.all()
        serializer = PackageArtifactListSerializer(artifacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve a version."""
        version = self.get_object()
        from django.utils import timezone

        version.approved_by = request.user
        version.approved_at = timezone.now()
        version.save(update_fields=["approved_by", "approved_at"])

        serializer = ApplicationVersionSerializer(version)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def set_latest(self, request: Request, pk=None) -> Response:
        """Mark version as latest."""
        version = self.get_object()
        version.is_latest = True
        version.save()

        serializer = ApplicationVersionSerializer(version)
        return Response(serializer.data)


class PackageArtifactViewSet(viewsets.ModelViewSet):
    """
    API endpoint for package artifacts.

    list: List all artifacts
    retrieve: Get artifact details
    create: Create a new artifact (upload)
    update: Update artifact metadata
    initiate_upload: Get upload URL for artifact
    complete_upload: Mark upload as complete
    scan_results: Get vulnerability scan results
    """

    queryset = PackageArtifact.objects.select_related("version", "version__application", "uploaded_by").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return PackageArtifactListSerializer
        if self.action == "create" or self.action == "initiate_upload":
            return PackageArtifactUploadSerializer
        return PackageArtifactSerializer

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by version
        version = self.request.query_params.get("version")
        if version:
            queryset = queryset.filter(version_id=version)

        # Filter by platform
        platform = self.request.query_params.get("platform")
        if platform:
            queryset = queryset.filter(platform=platform)

        # Filter by status
        artifact_status = self.request.query_params.get("status")
        if artifact_status:
            queryset = queryset.filter(status=artifact_status)

        # Filter by signed only
        signed_only = self.request.query_params.get("signed_only")
        if signed_only and signed_only.lower() == "true":
            queryset = queryset.filter(is_signed=True)

        # Filter by has vulnerabilities
        has_vulns = self.request.query_params.get("has_vulnerabilities")
        if has_vulns is not None:
            if has_vulns.lower() == "true":
                queryset = queryset.filter(Q(vulnerability_count_critical__gt=0) | Q(vulnerability_count_high__gt=0))
            else:
                queryset = queryset.filter(
                    vulnerability_count_critical=0,
                    vulnerability_count_high=0,
                )

        return queryset

    def perform_create(self, serializer):
        """Set uploaded_by on creation."""
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=["get"])
    def scan_results(self, request: Request, pk=None) -> Response:
        """Get vulnerability scan results for artifact."""
        artifact = self.get_object()
        return Response(
            {
                "artifact_id": str(artifact.id),
                "scan_status": artifact.scan_status,
                "scan_completed_at": artifact.scan_completed_at,
                "vulnerabilities": {
                    "critical": artifact.vulnerability_count_critical,
                    "high": artifact.vulnerability_count_high,
                    "medium": artifact.vulnerability_count_medium,
                    "low": artifact.vulnerability_count_low,
                    "total": artifact.total_vulnerabilities,
                },
                "scan_report_ref": artifact.scan_report_ref,
                "sbom_ref": artifact.sbom_ref,
                "sbom_format": artifact.sbom_format,
            }
        )


class DeploymentIntentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for deployment intents.

    list: List all deployment intents
    retrieve: Get deployment intent details
    create: Create a new deployment intent
    update: Update deployment intent
    approve: Approve deployment (CAB)
    reject: Reject deployment (CAB)
    start: Start deployment
    pause: Pause deployment
    resume: Resume deployment
    rollback: Trigger rollback
    metrics: Get deployment metrics
    """

    queryset = DeploymentIntent.objects.select_related(
        "artifact",
        "artifact__version",
        "artifact__version__application",
        "approved_by",
        "created_by",
    ).all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return DeploymentIntentListSerializer
        if self.action == "create":
            return DeploymentIntentCreateSerializer
        return DeploymentIntentSerializer

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by artifact
        artifact = self.request.query_params.get("artifact")
        if artifact:
            queryset = queryset.filter(artifact_id=artifact)

        # Filter by application
        application = self.request.query_params.get("application")
        if application:
            queryset = queryset.filter(artifact__version__application_id=application)

        # Filter by status
        deployment_status = self.request.query_params.get("status")
        if deployment_status:
            queryset = queryset.filter(status=deployment_status)

        # Filter by ring
        ring = self.request.query_params.get("ring")
        if ring:
            queryset = queryset.filter(target_ring=ring)

        # Filter by requires CAB approval
        requires_cab = self.request.query_params.get("requires_cab_approval")
        if requires_cab is not None:
            queryset = queryset.filter(requires_cab_approval=requires_cab.lower() == "true")

        # Filter by pending approval
        pending_approval = self.request.query_params.get("pending_approval")
        if pending_approval and pending_approval.lower() == "true":
            queryset = queryset.filter(status=DeploymentStatus.PENDING_APPROVAL)

        return queryset

    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve deployment (CAB approval)."""
        deployment = self.get_object()
        from django.utils import timezone

        if deployment.status != DeploymentStatus.PENDING_APPROVAL:
            return Response(
                {"detail": "Deployment is not pending approval"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = DeploymentStatus.APPROVED
        deployment.approved_by = request.user
        deployment.approved_at = timezone.now()
        deployment.approval_notes = request.data.get("notes", "")
        deployment.save()

        serializer = DeploymentIntentSerializer(deployment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject(self, request: Request, pk=None) -> Response:
        """Reject deployment (CAB rejection)."""
        deployment = self.get_object()

        if deployment.status != DeploymentStatus.PENDING_APPROVAL:
            return Response(
                {"detail": "Deployment is not pending approval"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = DeploymentStatus.CANCELLED
        deployment.approval_notes = request.data.get("reason", "Rejected by CAB")
        deployment.save()

        serializer = DeploymentIntentSerializer(deployment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def start(self, request: Request, pk=None) -> Response:
        """Start deployment execution."""
        deployment = self.get_object()
        from django.utils import timezone

        valid_statuses = [DeploymentStatus.APPROVED, DeploymentStatus.SCHEDULED]
        if deployment.status not in valid_statuses:
            return Response(
                {"detail": f"Cannot start deployment in {deployment.status} status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = DeploymentStatus.IN_PROGRESS
        deployment.started_at = timezone.now()
        deployment.save()

        serializer = DeploymentIntentSerializer(deployment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def pause(self, request: Request, pk=None) -> Response:
        """Pause deployment."""
        deployment = self.get_object()

        if deployment.status != DeploymentStatus.IN_PROGRESS:
            return Response(
                {"detail": "Only in-progress deployments can be paused"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = DeploymentStatus.PAUSED
        deployment.save()

        serializer = DeploymentIntentSerializer(deployment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def resume(self, request: Request, pk=None) -> Response:
        """Resume paused deployment."""
        deployment = self.get_object()

        if deployment.status != DeploymentStatus.PAUSED:
            return Response(
                {"detail": "Only paused deployments can be resumed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = DeploymentStatus.IN_PROGRESS
        deployment.save()

        serializer = DeploymentIntentSerializer(deployment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def rollback(self, request: Request, pk=None) -> Response:
        """Trigger rollback."""
        deployment = self.get_object()
        from django.utils import timezone

        if deployment.rollback_triggered:
            return Response(
                {"detail": "Rollback already triggered"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = DeploymentStatus.ROLLED_BACK
        deployment.rollback_triggered = True
        deployment.rollback_at = timezone.now()
        deployment.rollback_reason = request.data.get("reason", "Manual rollback")
        deployment.save()

        serializer = DeploymentIntentSerializer(deployment)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def metrics(self, request: Request, pk=None) -> Response:
        """Get deployment metrics history."""
        deployment = self.get_object()
        metrics = deployment.metrics.all()[:100]  # Last 100 metric snapshots
        serializer = DeploymentMetricSerializer(metrics, many=True)
        return Response(serializer.data)


class DeploymentMetricViewSet(viewsets.ModelViewSet):
    """
    API endpoint for deployment metrics.

    list: List all metrics
    retrieve: Get metric details
    create: Record new metrics
    """

    queryset = DeploymentMetric.objects.select_related("deployment").all()
    serializer_class = DeploymentMetricSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by deployment
        deployment = self.request.query_params.get("deployment")
        if deployment:
            queryset = queryset.filter(deployment_id=deployment)

        return queryset


class ApplicationHealthViewSet(viewsets.ModelViewSet):
    """
    API endpoint for application health.

    list: List health records
    retrieve: Get health record details
    create: Record new health snapshot
    """

    queryset = ApplicationHealth.objects.select_related("application").all()
    serializer_class = ApplicationHealthSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by application
        application = self.request.query_params.get("application")
        if application:
            queryset = queryset.filter(application_id=application)

        # Filter by health status
        health_status = self.request.query_params.get("health_status")
        if health_status:
            queryset = queryset.filter(health_status=health_status)

        return queryset


class ApplicationDependencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for application dependencies.

    list: List all dependencies
    retrieve: Get dependency details
    create: Create a new dependency
    update: Update dependency
    destroy: Remove dependency
    """

    queryset = ApplicationDependency.objects.select_related("application", "depends_on").all()
    serializer_class = ApplicationDependencySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by application
        application = self.request.query_params.get("application")
        if application:
            queryset = queryset.filter(application_id=application)

        # Filter by depends_on
        depends_on = self.request.query_params.get("depends_on")
        if depends_on:
            queryset = queryset.filter(depends_on_id=depends_on)

        return queryset


class PortfolioSummaryViewSet(viewsets.ViewSet):
    """
    API endpoint for portfolio summary statistics.
    """

    permission_classes = [IsAuthenticated]

    def list(self, request: Request) -> Response:
        """Get portfolio summary statistics."""
        # Application counts
        total_apps = Application.objects.count()
        active_apps = Application.objects.filter(is_active=True).count()

        # Version and artifact counts
        total_versions = ApplicationVersion.objects.count()
        total_artifacts = PackageArtifact.objects.count()

        # Applications by status
        apps_by_status = dict(
            Application.objects.values("status").annotate(count=Count("id")).values_list("status", "count")
        )

        # Applications by category
        apps_by_category = dict(
            Application.objects.exclude(category="")
            .values("category")
            .annotate(count=Count("id"))
            .values_list("category", "count")
        )

        # Platform coverage
        platforms_coverage = dict(
            PackageArtifact.objects.values("platform").annotate(count=Count("id")).values_list("platform", "count")
        )

        # Publisher count
        publishers_count = Publisher.objects.filter(is_active=True).count()

        # Deployment counts
        pending_deployments = DeploymentIntent.objects.filter(status=DeploymentStatus.PENDING_APPROVAL).count()
        active_deployments = DeploymentIntent.objects.filter(status=DeploymentStatus.IN_PROGRESS).count()

        # Health summary
        health_counts = dict(
            ApplicationHealth.objects.values("health_status")
            .annotate(count=Count("application", distinct=True))
            .values_list("health_status", "count")
        )

        summary = {
            "total_applications": total_apps,
            "active_applications": active_apps,
            "total_versions": total_versions,
            "total_artifacts": total_artifacts,
            "applications_by_status": apps_by_status,
            "applications_by_category": apps_by_category,
            "platforms_coverage": platforms_coverage,
            "publishers_count": publishers_count,
            "pending_deployments": pending_deployments,
            "active_deployments": active_deployments,
            "health_summary": health_counts,
        }

        serializer = ApplicationPortfolioSummarySerializer(summary)
        return Response(serializer.data)
