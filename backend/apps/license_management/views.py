# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for license_management.
"""
import logging

from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Assignment,
    ConsumptionSignal,
    ConsumptionSnapshot,
    Entitlement,
    ImportJob,
    LicenseAlert,
    LicensePool,
    LicenseSKU,
    ReconciliationRun,
    ReconciliationStatus,
    Vendor,
)
from .serializers import (
    AssignmentCreateSerializer,
    AssignmentSerializer,
    ConsumptionSignalSerializer,
    ConsumptionSnapshotSerializer,
    EntitlementCreateSerializer,
    EntitlementSerializer,
    ImportJobSerializer,
    LicenseAlertSerializer,
    LicensePoolSerializer,
    LicenseSKUListSerializer,
    LicenseSKUSerializer,
    LicenseSummarySerializer,
    ReconciliationRunSerializer,
    VendorListSerializer,
    VendorSerializer,
)
from .services import (
    AssignmentService,
    ConsumptionSignalService,
    EntitlementService,
    LicenseSummaryService,
    ReconciliationService,
)

logger = logging.getLogger(__name__)


class LicenseSummaryView(APIView):
    """API endpoint for license summary."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Get overall license summary with health status.

        Returns summary of total entitled, consumed, remaining, and health status.
        """
        summary = LicenseSummaryService.get_summary()
        serializer = LicenseSummarySerializer(summary)
        return Response(serializer.data)


class VendorViewSet(viewsets.ModelViewSet):
    """API viewset for Vendor CRUD operations."""

    permission_classes = [IsAuthenticated]
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    def get_serializer_class(self):
        """Use compact serializer for list view."""
        if self.action == "list":
            return VendorListSerializer
        return VendorSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class LicenseSKUViewSet(viewsets.ModelViewSet):
    """API viewset for LicenseSKU CRUD operations."""

    permission_classes = [IsAuthenticated]
    queryset = LicenseSKU.objects.select_related("vendor").all()
    serializer_class = LicenseSKUSerializer

    def get_serializer_class(self):
        """Use compact serializer for list view."""
        if self.action == "list":
            return LicenseSKUListSerializer
        return LicenseSKUSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        vendor_id = self.request.query_params.get("vendor")
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        license_model_type = self.request.query_params.get("license_model_type")
        if license_model_type:
            queryset = queryset.filter(license_model_type=license_model_type)

        return queryset

    @action(detail=True, methods=["get"])
    def consumption(self, request: Request, pk=None) -> Response:
        """Get consumption history for a SKU."""
        sku = self.get_object()
        snapshots = ConsumptionSnapshot.objects.filter(sku=sku, pool__isnull=True).order_by("-reconciled_at")[:30]
        serializer = ConsumptionSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)


class EntitlementViewSet(viewsets.ModelViewSet):
    """API viewset for Entitlement CRUD operations."""

    permission_classes = [IsAuthenticated]
    queryset = Entitlement.objects.select_related("sku", "sku__vendor", "created_by", "approved_by").all()

    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == "create":
            return EntitlementCreateSerializer
        return EntitlementSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        sku_id = self.request.query_params.get("sku")
        if sku_id:
            queryset = queryset.filter(sku_id=sku_id)

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve a pending entitlement."""
        entitlement = self.get_object()
        try:
            approved = EntitlementService.approve_entitlement(entitlement, request.user)
            serializer = EntitlementSerializer(approved)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LicensePoolViewSet(viewsets.ModelViewSet):
    """API viewset for LicensePool CRUD operations."""

    permission_classes = [IsAuthenticated]
    queryset = LicensePool.objects.select_related("sku").all()
    serializer_class = LicensePoolSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        sku_id = self.request.query_params.get("sku")
        if sku_id:
            queryset = queryset.filter(sku_id=sku_id)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset


class AssignmentViewSet(viewsets.ModelViewSet):
    """API viewset for Assignment CRUD operations."""

    permission_classes = [IsAuthenticated]
    queryset = Assignment.objects.select_related("pool", "pool__sku", "assigned_by").all()

    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == "create":
            return AssignmentCreateSerializer
        return AssignmentSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        pool_id = self.request.query_params.get("pool")
        if pool_id:
            queryset = queryset.filter(pool_id=pool_id)

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        principal_type = self.request.query_params.get("principal_type")
        if principal_type:
            queryset = queryset.filter(principal_type=principal_type)

        principal_id = self.request.query_params.get("principal_id")
        if principal_id:
            queryset = queryset.filter(principal_id=principal_id)

        return queryset

    @action(detail=True, methods=["post"])
    def revoke(self, request: Request, pk=None) -> Response:
        """Revoke an active assignment."""
        assignment = self.get_object()
        reason = request.data.get("reason", "")
        try:
            revoked = AssignmentService.revoke_assignment(assignment, request.user, reason)
            serializer = AssignmentSerializer(revoked)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConsumptionSignalViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for ConsumptionSignal (read-only)."""

    permission_classes = [IsAuthenticated]
    queryset = ConsumptionSignal.objects.select_related("sku").all()
    serializer_class = ConsumptionSignalSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        source_system = self.request.query_params.get("source_system")
        if source_system:
            queryset = queryset.filter(source_system=source_system)

        sku_id = self.request.query_params.get("sku")
        if sku_id:
            queryset = queryset.filter(sku_id=sku_id)

        is_processed = self.request.query_params.get("is_processed")
        if is_processed is not None:
            queryset = queryset.filter(is_processed=is_processed.lower() == "true")

        return queryset


class ConsumptionSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for ConsumptionSnapshot (read-only)."""

    permission_classes = [IsAuthenticated]
    queryset = ConsumptionSnapshot.objects.select_related("sku", "pool", "reconciliation_run").all()
    serializer_class = ConsumptionSnapshotSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        sku_id = self.request.query_params.get("sku")
        if sku_id:
            queryset = queryset.filter(sku_id=sku_id)

        pool_id = self.request.query_params.get("pool")
        if pool_id:
            queryset = queryset.filter(pool_id=pool_id)

        return queryset

    @action(detail=True, methods=["get"])
    def evidence(self, request: Request, pk=None) -> Response:
        """Get evidence pack download URL for a snapshot."""
        snapshot = self.get_object()
        # In production, this would generate a presigned URL for MinIO
        return Response(
            {
                "evidence_pack_ref": snapshot.evidence_pack_ref,
                "evidence_pack_hash": snapshot.evidence_pack_hash,
                "download_url": f"/api/licenses/evidence/{snapshot.evidence_pack_ref}",
            }
        )


class ReconciliationRunViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for ReconciliationRun."""

    permission_classes = [IsAuthenticated]
    queryset = ReconciliationRun.objects.select_related("triggered_by").all()
    serializer_class = ReconciliationRunSerializer


class ReconcileView(APIView):
    """API endpoint to trigger reconciliation."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Trigger a reconciliation run.

        Returns the created ReconciliationRun.
        """
        # Check if reconciliation is already running
        running = ReconciliationRun.objects.filter(status=ReconciliationStatus.RUNNING).exists()
        if running:
            return Response(
                {"error": "Reconciliation is already running"},
                status=status.HTTP_409_CONFLICT,
            )

        service = ReconciliationService(triggered_by=request.user)
        run = service.run_reconciliation()

        serializer = ReconciliationRunSerializer(run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request: Request) -> Response:
        """
        Get status of the latest or running reconciliation.
        """
        run = ReconciliationRun.objects.order_by("-started_at").first()
        if not run:
            return Response({"status": "no_runs", "message": "No reconciliation runs found"})

        serializer = ReconciliationRunSerializer(run)
        return Response(serializer.data)


class LicenseAlertViewSet(viewsets.ModelViewSet):
    """API viewset for LicenseAlert."""

    permission_classes = [IsAuthenticated]
    queryset = LicenseAlert.objects.select_related("sku", "pool", "acknowledged_by").all()
    serializer_class = LicenseAlertSerializer

    def get_queryset(self) -> QuerySet:
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        alert_type = self.request.query_params.get("alert_type")
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)

        acknowledged = self.request.query_params.get("acknowledged")
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=acknowledged.lower() == "true")

        sku_id = self.request.query_params.get("sku")
        if sku_id:
            queryset = queryset.filter(sku_id=sku_id)

        return queryset

    @action(detail=True, methods=["post"])
    def acknowledge(self, request: Request, pk=None) -> Response:
        """Acknowledge an alert."""
        alert = self.get_object()
        if alert.acknowledged:
            return Response({"error": "Alert already acknowledged"}, status=status.HTTP_400_BAD_REQUEST)

        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.resolution_notes = request.data.get("notes", "")
        alert.save()

        serializer = LicenseAlertSerializer(alert)
        return Response(serializer.data)


class ImportJobViewSet(viewsets.ModelViewSet):
    """API viewset for ImportJob."""

    permission_classes = [IsAuthenticated]
    queryset = ImportJob.objects.select_related("uploaded_by").all()
    serializer_class = ImportJobSerializer

    # TODO: Implement file upload handling in create method


class IngestSignalView(APIView):
    """API endpoint to ingest consumption signals."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Ingest a consumption signal.

        Required fields:
        - source_system: str
        - raw_id: str
        - timestamp: ISO datetime
        - principal_type: str
        - principal_id: str
        - sku_id: UUID

        Optional fields:
        - confidence: float (default 1.0)
        - raw_payload: dict
        - principal_name: str
        """
        required_fields = ["source_system", "raw_id", "timestamp", "principal_type", "principal_id", "sku_id"]
        for field in required_fields:
            if field not in request.data:
                return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            signal = ConsumptionSignalService.ingest_signal(
                source_system=request.data["source_system"],
                raw_id=request.data["raw_id"],
                timestamp=request.data["timestamp"],
                principal_type=request.data["principal_type"],
                principal_id=request.data["principal_id"],
                sku_id=request.data["sku_id"],
                confidence=request.data.get("confidence", 1.0),
                raw_payload=request.data.get("raw_payload"),
                principal_name=request.data.get("principal_name", ""),
            )
            serializer = ConsumptionSignalSerializer(signal)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error ingesting signal: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
