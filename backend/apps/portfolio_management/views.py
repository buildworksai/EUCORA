# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF ViewSets for Portfolio Management API.

Implements REST API endpoints for Portfolio Manager and Application Manager personas,
with filtering, search, and action-based workflows.
"""
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.portfolio_management.models import (
    ApplicationManagerPerformance,
    ApplicationOwnership,
    LicenseTrueUpForecast,
    PackagingRequest,
    Portfolio,
)
from apps.portfolio_management.serializers import (
    ApplicationManagerPerformanceSerializer,
    ApplicationOwnershipDetailSerializer,
    ApplicationOwnershipListSerializer,
    LicenseTrueUpForecastSerializer,
    PackagingRequestSerializer,
    PortfolioDetailSerializer,
    PortfolioListSerializer,
)


class PortfolioViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Portfolio management.

    Provides CRUD operations for portfolios with metrics and scope management.
    Portfolio Managers can view/edit their own portfolios; Platform Admins can see all.
    """

    queryset = Portfolio.objects.select_related("manager").all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "manager__username"]
    ordering_fields = ["name", "health_score", "compliance_score", "created_at"]
    ordering = ["-health_score"]

    def get_serializer_class(self):
        """Use detailed serializer for retrieve, list serializer otherwise."""
        if self.action == "retrieve":
            return PortfolioDetailSerializer
        return PortfolioListSerializer

    def get_queryset(self):
        """Filter portfolios based on user role."""
        queryset = super().get_queryset()
        user = self.request.user

        # TODO: Implement proper RBAC checks
        # For now, Portfolio Managers see only their portfolios
        # Platform Admins see all portfolios
        if not user.is_staff:
            queryset = queryset.filter(manager=user)

        return queryset

    @action(detail=True, methods=["get"])
    def metrics(self, request, pk=None):
        """Get current metrics for a portfolio."""
        portfolio = self.get_object()
        return Response(
            {
                "portfolio_id": str(portfolio.id),
                "total_applications": portfolio.total_applications,
                "total_licenses_entitled": portfolio.total_licenses_entitled,
                "total_licenses_consumed": portfolio.total_licenses_consumed,
                "license_utilization_percent": portfolio.license_utilization_percent,
                "health_score": portfolio.health_score,
                "compliance_score": portfolio.compliance_score,
                "budget_annual": str(portfolio.budget_annual),
            }
        )

    @action(detail=True, methods=["post"])
    def refresh_metrics(self, request, pk=None):
        """Trigger metric recalculation for a portfolio."""
        portfolio = self.get_object()
        # TODO: Implement metric refresh logic
        # This would trigger background job to recalculate cached metrics
        return Response(
            {"message": "Metric refresh triggered", "portfolio_id": str(portfolio.id)},
            status=status.HTTP_202_ACCEPTED,
        )


class ApplicationOwnershipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Application Ownership management.

    Manages assignment of Application Managers to applications within portfolios.
    Enforces unique ownership constraints and scope validation.
    """

    queryset = ApplicationOwnership.objects.select_related("application", "owner", "portfolio", "assigned_by").all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["application__name", "owner__username", "portfolio__name"]
    ordering_fields = ["created_at", "assigned_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Use detailed serializer for retrieve/create/update, list serializer otherwise."""
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return ApplicationOwnershipDetailSerializer
        return ApplicationOwnershipListSerializer

    def get_queryset(self):
        """Filter ownerships based on query parameters."""
        queryset = super().get_queryset()

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by ownership type
        ownership_type = self.request.query_params.get("ownership_type")
        if ownership_type:
            queryset = queryset.filter(ownership_type=ownership_type)

        # Filter by portfolio
        portfolio_id = self.request.query_params.get("portfolio")
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)

        # Filter by owner
        owner_id = self.request.query_params.get("owner")
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        return queryset

    def perform_create(self, serializer):
        """Set assigned_by to current user."""
        serializer.save(assigned_by=self.request.user, assigned_at=timezone.now())

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate an application ownership."""
        ownership = self.get_object()
        ownership.is_active = False
        ownership.save(update_fields=["is_active", "updated_at"])
        return Response({"message": "Ownership deactivated", "ownership_id": str(ownership.id)})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Reactivate an application ownership."""
        ownership = self.get_object()
        ownership.is_active = True
        ownership.save(update_fields=["is_active", "updated_at"])
        return Response({"message": "Ownership activated", "ownership_id": str(ownership.id)})


class ApplicationManagerPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Application Manager performance metrics.

    Read-only access to performance snapshots with filtering by manager and date range.
    Performance metrics are calculated and recorded by background jobs.
    """

    queryset = ApplicationManagerPerformance.objects.select_related("manager", "portfolio").all()
    serializer_class = ApplicationManagerPerformanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["recorded_at", "composite_score", "success_rate_percent"]
    ordering = ["-recorded_at"]

    def get_queryset(self):
        """Filter performance metrics by manager and date range."""
        queryset = super().get_queryset()

        # Filter by manager
        manager_id = self.request.query_params.get("manager")
        if manager_id:
            queryset = queryset.filter(manager_id=manager_id)

        # Filter by portfolio
        portfolio_id = self.request.query_params.get("portfolio")
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)

        # Filter by date range
        period_start = self.request.query_params.get("period_start")
        period_end = self.request.query_params.get("period_end")

        if period_start:
            queryset = queryset.filter(period_start__gte=period_start)
        if period_end:
            queryset = queryset.filter(period_end__lte=period_end)

        return queryset

    @action(detail=False, methods=["get"])
    def leaderboard(self, request):
        """Get top-performing Application Managers by composite score."""
        from django.db.models import Max

        limit = int(request.query_params.get("limit", 10))
        portfolio_id = request.query_params.get("portfolio")

        queryset = self.get_queryset()
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)

        # Get latest recorded_at for each manager
        latest_records = queryset.values("manager").annotate(latest_recorded=Max("recorded_at"))

        # Build list of (manager_id, latest_recorded_at) pairs
        manager_dates = {record["manager"]: record["latest_recorded"] for record in latest_records}

        # Get the actual performance records for these manager/date pairs
        import operator
        from functools import reduce

        from django.db.models import Q

        q_objects = [
            Q(manager=manager_id, recorded_at=recorded_at) for manager_id, recorded_at in manager_dates.items()
        ]

        if q_objects:
            latest_performances = queryset.filter(reduce(operator.or_, q_objects)).order_by("-composite_score")[:limit]
        else:
            latest_performances = queryset.none()

        serializer = self.get_serializer(latest_performances, many=True)
        return Response(serializer.data)


class LicenseTrueUpForecastViewSet(viewsets.ModelViewSet):
    """
    ViewSet for License True-Up forecasts.

    Manages vendor ELA renewal forecasts with true-up quantity and cost predictions.
    Portfolio Managers use this for budget planning and vendor negotiations.
    """

    queryset = LicenseTrueUpForecast.objects.select_related("vendor", "portfolio").all()
    serializer_class = LicenseTrueUpForecastSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["forecast_generated_at", "true_up_cost", "risk_level"]
    ordering = ["-forecast_generated_at"]

    def get_queryset(self):
        """Filter forecasts by vendor, portfolio, and risk level."""
        queryset = super().get_queryset()

        # Filter by vendor
        vendor_id = self.request.query_params.get("vendor")
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        # Filter by portfolio
        portfolio_id = self.request.query_params.get("portfolio")
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)

        # Filter by risk level
        risk_level = self.request.query_params.get("risk_level")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level.upper())

        # Filter by forecast period
        forecast_period = self.request.query_params.get("forecast_period")
        if forecast_period:
            queryset = queryset.filter(forecast_period=forecast_period)

        return queryset

    @action(detail=False, methods=["get"])
    def high_risk(self, request):
        """Get high-risk and critical true-up forecasts (>= 25% additional licenses needed)."""
        from django.db.models import ExpressionWrapper, F, FloatField

        # Calculate risk percentage: (additional_licenses_needed / entitled_quantity_current) * 100
        # HIGH: >= 25%, CRITICAL: >= 50%
        queryset = (
            self.get_queryset()
            .annotate(
                risk_percent=ExpressionWrapper(
                    (F("additional_licenses_needed") * 100.0) / F("entitled_quantity_current"),
                    output_field=FloatField(),
                )
            )
            .filter(risk_percent__gte=25.0)
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PackagingRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Packaging Requests workflow.

    Manages the handoff from Application Manager to Packaging Engineer.
    Tracks request status, turnaround time, and completion metrics.
    """

    queryset = PackagingRequest.objects.select_related("application", "requested_by", "assigned_to").all()
    serializer_class = PackagingRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["application__name", "requested_by__username"]
    ordering_fields = ["created_at", "priority", "status"]
    ordering = ["-priority", "created_at"]

    def get_queryset(self):
        """Filter packaging requests by status and assignment."""
        queryset = super().get_queryset()

        # Filter by status
        request_status = self.request.query_params.get("status")
        if request_status:
            queryset = queryset.filter(status=request_status.upper())

        # Filter by priority
        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority.upper())

        # Filter by requested_by
        requested_by_id = self.request.query_params.get("requested_by")
        if requested_by_id:
            queryset = queryset.filter(requested_by_id=requested_by_id)

        # Filter by assigned_to
        assigned_to_id = self.request.query_params.get("assigned_to")
        if assigned_to_id:
            queryset = queryset.filter(assigned_to_id=assigned_to_id)

        return queryset

    def perform_create(self, serializer):
        """Set requested_by to current user."""
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Assign a packaging request to a Packaging Engineer."""
        packaging_request = self.get_object()

        if packaging_request.status == "COMPLETED":
            return Response({"error": "Cannot assign a completed request"}, status=status.HTTP_400_BAD_REQUEST)

        assigned_to_id = request.data.get("assigned_to")
        if not assigned_to_id:
            return Response({"error": "assigned_to is required"}, status=status.HTTP_400_BAD_REQUEST)

        packaging_request.assigned_to_id = assigned_to_id
        packaging_request.assigned_at = timezone.now()
        packaging_request.status = "IN_PROGRESS"
        packaging_request.save(update_fields=["assigned_to", "assigned_at", "status", "updated_at"])

        return Response(
            {
                "message": "Request assigned",
                "request_id": str(packaging_request.id),
                "assigned_to": assigned_to_id,
            }
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark a packaging request as completed."""
        packaging_request = self.get_object()

        if packaging_request.status == "COMPLETED":
            return Response({"error": "Request is already completed"}, status=status.HTTP_400_BAD_REQUEST)

        packaging_request.status = "COMPLETED"
        packaging_request.completed_at = timezone.now()
        packaging_request.save(update_fields=["status", "completed_at", "updated_at"])

        return Response(
            {
                "message": "Request completed",
                "request_id": str(packaging_request.id),
                "turnaround_time_hours": packaging_request.turnaround_time_hours,
            }
        )

    @action(detail=False, methods=["get"])
    def my_requests(self, request):
        """Get packaging requests created by the current user."""
        queryset = self.get_queryset().filter(requested_by=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def assigned_to_me(self, request):
        """Get packaging requests assigned to the current user."""
        queryset = self.get_queryset().filter(assigned_to=request.user, status="IN_PROGRESS")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
