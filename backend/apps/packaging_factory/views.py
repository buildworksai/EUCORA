# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
REST API views for packaging factory.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PackagingPipeline
from .serializers import PackagingPipelineCreateSerializer, PackagingPipelineListSerializer, PackagingPipelineSerializer
from .services import PackagingFactoryService


class PackagingPipelineViewSet(viewsets.ModelViewSet):
    """ViewSet for packaging pipeline management."""

    queryset = PackagingPipeline.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == "list":
            return PackagingPipelineListSerializer
        elif self.action == "create":
            return PackagingPipelineCreateSerializer
        return PackagingPipelineSerializer

    def get_queryset(self):
        """Filter queryset by query parameters."""
        queryset = super().get_queryset()

        # Filter by platform
        platform = self.request.query_params.get("platform")
        if platform:
            queryset = queryset.filter(platform=platform)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by policy decision
        policy_decision = self.request.query_params.get("policy_decision")
        if policy_decision:
            queryset = queryset.filter(policy_decision=policy_decision)

        # Filter by package name
        package_name = self.request.query_params.get("package_name")
        if package_name:
            queryset = queryset.filter(package_name__icontains=package_name)

        return queryset.select_related("created_by")

    def create(self, request):
        """Create and optionally execute packaging pipeline."""
        serializer = PackagingPipelineCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PackagingFactoryService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        # Create pipeline
        pipeline = service.create_pipeline(
            package_name=serializer.validated_data["package_name"],
            package_version=serializer.validated_data["package_version"],
            platform=serializer.validated_data["platform"],
            package_type=serializer.validated_data["package_type"],
            source_artifact_url=serializer.validated_data["source_artifact_url"],
            created_by=request.user,
            source_repo=serializer.validated_data.get("source_repo"),
            source_commit=serializer.validated_data.get("source_commit"),
            correlation_id=correlation_id,
        )

        # Set exception ID if provided
        if serializer.validated_data.get("exception_id"):
            pipeline.exception_id = serializer.validated_data["exception_id"]
            pipeline.save()

        # Auto-execute pipeline
        auto_execute = request.query_params.get("auto_execute", "true").lower() == "true"
        if auto_execute:
            try:
                pipeline = service.execute_pipeline(pipeline_id=str(pipeline.id), correlation_id=correlation_id)
            except Exception as e:
                # Pipeline failed - return with error details
                pass

        return Response(PackagingPipelineSerializer(pipeline).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """Execute packaging pipeline."""
        pipeline = self.get_object()
        service = PackagingFactoryService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        try:
            pipeline = service.execute_pipeline(pipeline_id=str(pipeline.id), correlation_id=correlation_id)
            return Response(PackagingPipelineSerializer(pipeline).data)
        except Exception as e:
            return Response(
                {"error": str(e), "pipeline_id": str(pipeline.id)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Get detailed pipeline status."""
        pipeline = self.get_object()
        service = PackagingFactoryService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        status_data = service.get_pipeline_status(pipeline_id=str(pipeline.id), correlation_id=correlation_id)

        return Response(status_data)
