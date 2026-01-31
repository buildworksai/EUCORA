# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for CMDB Integration.
"""
import logging

from apps.core.async_utils import run_async
from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    CMDBConnection,
    CMDBDataQualityReport,
    CMDBDiscrepancy,
    CMDBSyncRecord,
    CMDBTableMapping,
    CMDBValidationRule,
)
from .serializers import (
    CMDBConnectionCreateSerializer,
    CMDBConnectionSerializer,
    CMDBDiscrepancyBulkResolveSerializer,
    CMDBDiscrepancyResolveSerializer,
    CMDBDiscrepancySerializer,
    CMDBSyncRecordSerializer,
    CMDBSyncStartSerializer,
    CMDBTableMappingSerializer,
    CMDBValidationRuleSerializer,
)
from .services import CMDBSyncService

logger = logging.getLogger(__name__)


class CMDBConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CMDB connection management.

    Provides CRUD operations and connection testing.
    """

    queryset = CMDBConnection.objects.all()
    serializer_class = CMDBConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use create serializer for write operations."""
        if self.action in ["create", "update", "partial_update"]:
            return CMDBConnectionCreateSerializer
        return CMDBConnectionSerializer

    def get_queryset(self):
        """Filter by correlation_id if provided."""
        queryset = CMDBConnection.objects.all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            # Connections don't have correlation_id, but we can filter by related sync records
            queryset = queryset.filter(sync_records__correlation_id=correlation_id)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test connection to ServiceNow instance."""
        connection = self.get_object()

        # Run async test
        service = CMDBSyncService(connection, use_mock=True)

        async def run_test():
            try:
                result = await service.client.test_connection()
                return result
            finally:
                await service.close()

        result = run_async(run_test())

        return Response(result)


class CMDBTableMappingViewSet(viewsets.ModelViewSet):
    """ViewSet for CMDB table mappings."""

    queryset = CMDBTableMapping.objects.all()
    serializer_class = CMDBTableMappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by connection if provided."""
        queryset = CMDBTableMapping.objects.select_related("connection")
        connection_id = self.request.query_params.get("connection_id")
        if connection_id:
            queryset = queryset.filter(connection_id=connection_id)
        return queryset.order_by("priority")


class CMDBValidationRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for CMDB validation rules."""

    queryset = CMDBValidationRule.objects.all()
    serializer_class = CMDBValidationRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by table if provided."""
        queryset = CMDBValidationRule.objects.all()
        cmdb_table = self.request.query_params.get("cmdb_table")
        if cmdb_table:
            queryset = queryset.filter(cmdb_table=cmdb_table)
        return queryset.order_by("cmdb_table", "field_name")


class CMDBSyncRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CMDB sync records.

    Provides sync history and initiation.
    """

    queryset = CMDBSyncRecord.objects.all()
    serializer_class = CMDBSyncRecordSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        """Filter by connection and correlation_id."""
        queryset = CMDBSyncRecord.objects.select_related("connection", "initiated_by")

        connection_id = self.request.query_params.get("connection_id")
        if connection_id:
            queryset = queryset.filter(connection_id=connection_id)

        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by("-started_at")

    def create(self, request: Request) -> Response:
        """Start a new sync operation."""
        serializer = CMDBSyncStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connection_id = serializer.validated_data["connection_id"]
        sync_type = serializer.validated_data["sync_type"]
        tables = serializer.validated_data.get("tables", [])

        try:
            connection = CMDBConnection.objects.get(id=connection_id, is_active=True)
        except CMDBConnection.DoesNotExist:
            return Response(
                {"error": "Connection not found or inactive"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create sync record
        sync_record = CMDBSyncRecord.objects.create(
            connection=connection,
            sync_type=sync_type,
            status=CMDBSyncRecord.Status.PENDING,
            initiated_by=request.user,
        )

        # In production, this would be queued as a Celery task
        # For now, we'll run the sync synchronously with mock data

        async def run_sync():
            service = CMDBSyncService(connection, use_mock=True)
            try:
                await service.initialize()

                # Generate mock source data
                mock_source_data = {
                    "sccm": [
                        {"name": f"DESKTOP-{i:04d}", "serial_number": f"SN-{i:06d}", "os": "Windows 11"}
                        for i in range(10)
                    ],
                    "intune": [
                        {"name": f"MOBILE-{i:04d}", "serial_number": f"MN-{i:06d}", "os": "iOS 17"} for i in range(5)
                    ],
                }

                await service.run_sync(sync_record, mock_source_data, tables or None)
            finally:
                await service.close()

        run_async(run_sync())

        # Refresh and return
        sync_record.refresh_from_db()
        return Response(
            CMDBSyncRecordSerializer(sync_record).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def discrepancies(self, request: Request, pk=None) -> Response:
        """Get discrepancies for a sync record."""
        sync_record = self.get_object()
        discrepancies = sync_record.discrepancies.all()

        # Apply filters
        status_filter = request.query_params.get("status")
        if status_filter:
            discrepancies = discrepancies.filter(status=status_filter)

        disc_type = request.query_params.get("type")
        if disc_type:
            discrepancies = discrepancies.filter(discrepancy_type=disc_type)

        serializer = CMDBDiscrepancySerializer(discrepancies, many=True)
        return Response(serializer.data)


class CMDBDiscrepancyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CMDB discrepancies.

    Provides discrepancy review and resolution.
    """

    queryset = CMDBDiscrepancy.objects.all()
    serializer_class = CMDBDiscrepancySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        """Filter by various criteria."""
        queryset = CMDBDiscrepancy.objects.select_related("sync_record", "resolved_by")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        disc_type = self.request.query_params.get("type")
        if disc_type:
            queryset = queryset.filter(discrepancy_type=disc_type)

        ci_class = self.request.query_params.get("ci_class")
        if ci_class:
            queryset = queryset.filter(ci_class=ci_class)

        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(recommended_action=action)

        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve and apply a discrepancy."""
        discrepancy = self.get_object()

        if discrepancy.status != CMDBDiscrepancy.Status.PENDING:
            return Response(
                {"error": f"Discrepancy is not pending (status: {discrepancy.status})"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CMDBDiscrepancyResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notes = serializer.validated_data.get("resolution_notes", "")

        # In production, apply the change to CMDB
        # For now, just update status
        discrepancy.status = CMDBDiscrepancy.Status.APPROVED
        discrepancy.resolved_by = request.user
        discrepancy.resolved_at = timezone.now()
        discrepancy.resolution_notes = notes
        discrepancy.save()

        return Response(CMDBDiscrepancySerializer(discrepancy).data)

    @action(detail=True, methods=["post"])
    def reject(self, request: Request, pk=None) -> Response:
        """Reject a discrepancy."""
        discrepancy = self.get_object()

        if discrepancy.status != CMDBDiscrepancy.Status.PENDING:
            return Response(
                {"error": f"Discrepancy is not pending (status: {discrepancy.status})"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CMDBDiscrepancyResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notes = serializer.validated_data.get("resolution_notes", "")

        discrepancy.status = CMDBDiscrepancy.Status.REJECTED
        discrepancy.resolved_by = request.user
        discrepancy.resolved_at = timezone.now()
        discrepancy.resolution_notes = notes
        discrepancy.save()

        return Response(CMDBDiscrepancySerializer(discrepancy).data)

    @action(detail=False, methods=["post"], url_path="bulk-approve")
    def bulk_approve(self, request: Request) -> Response:
        """Bulk approve discrepancies."""
        serializer = CMDBDiscrepancyBulkResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        disc_ids = serializer.validated_data["discrepancy_ids"]
        action = serializer.validated_data["action"]
        notes = serializer.validated_data.get("resolution_notes", "")

        if action == "approve":
            target_status = CMDBDiscrepancy.Status.APPROVED
        elif action == "reject":
            target_status = CMDBDiscrepancy.Status.REJECTED
        else:
            target_status = CMDBDiscrepancy.Status.IGNORED

        updated = CMDBDiscrepancy.objects.filter(
            id__in=disc_ids,
            status=CMDBDiscrepancy.Status.PENDING,
        ).update(
            status=target_status,
            resolved_by=request.user,
            resolved_at=timezone.now(),
            resolution_notes=notes,
        )

        return Response({"updated": updated})


class CMDBReportsViewSet(viewsets.ViewSet):
    """
    ViewSet for CMDB reports and dashboards.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="quality-score")
    def quality_score(self, request: Request) -> Response:
        """Get current quality score dashboard data."""
        connection_id = request.query_params.get("connection_id")

        # Get latest quality report
        reports = CMDBDataQualityReport.objects.select_related("connection", "sync_record")

        if connection_id:
            reports = reports.filter(connection_id=connection_id)

        latest_report = reports.order_by("-created_at").first()

        if not latest_report:
            return Response(
                {
                    "overall_score": 0,
                    "completeness_score": 0,
                    "accuracy_score": 0,
                    "consistency_score": 0,
                    "timeliness_score": 0,
                    "total_cis": 0,
                    "cis_with_issues": 0,
                    "pending_discrepancies": 0,
                    "last_sync": None,
                    "trend": {},
                }
            )

        # Count pending discrepancies
        pending_count = CMDBDiscrepancy.objects.filter(status=CMDBDiscrepancy.Status.PENDING)
        if connection_id:
            pending_count = pending_count.filter(sync_record__connection_id=connection_id)
        pending_count = pending_count.count()

        # Get last sync
        last_sync = CMDBSyncRecord.objects.filter(status=CMDBSyncRecord.Status.COMPLETED)
        if connection_id:
            last_sync = last_sync.filter(connection_id=connection_id)
        last_sync = last_sync.order_by("-completed_at").first()

        # Calculate trend (compare to 7 days ago)
        week_ago_report = (
            reports.filter(created_at__lte=timezone.now() - timezone.timedelta(days=7)).order_by("-created_at").first()
        )

        trend = {}
        if week_ago_report:
            trend = {
                "overall_score_change": latest_report.overall_score - week_ago_report.overall_score,
                "period_days": 7,
            }

        data = {
            "overall_score": latest_report.overall_score,
            "completeness_score": latest_report.completeness_score,
            "accuracy_score": latest_report.accuracy_score,
            "consistency_score": latest_report.consistency_score,
            "timeliness_score": latest_report.timeliness_score,
            "total_cis": latest_report.total_cis,
            "cis_with_issues": latest_report.cis_with_issues,
            "pending_discrepancies": pending_count,
            "last_sync": last_sync.completed_at if last_sync else None,
            "trend": trend,
        }

        return Response(data)

    @action(detail=False, methods=["get"], url_path="sync-history")
    def sync_history(self, request: Request) -> Response:
        """Get sync history summary."""
        connection_id = request.query_params.get("connection_id")
        days = int(request.query_params.get("days", 30))

        syncs = CMDBSyncRecord.objects.filter(
            started_at__gte=timezone.now() - timezone.timedelta(days=days),
            status=CMDBSyncRecord.Status.COMPLETED,
        )

        if connection_id:
            syncs = syncs.filter(connection_id=connection_id)

        # Group by date
        from django.db.models.functions import TruncDate

        daily_stats = (
            syncs.annotate(date=TruncDate("started_at"))
            .values("date")
            .annotate(
                syncs=Count("id"),
                records_processed=Count("records_processed"),
            )
            .order_by("date")
        )

        return Response(list(daily_stats))
