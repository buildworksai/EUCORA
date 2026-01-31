# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Automation Advisor.
"""
import logging

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import AutomationAnalysis, AutomationCandidate, ROIConfiguration, TaskPattern
from .serializers import (
    AutomationAnalysisSerializer,
    AutomationAnalysisStartSerializer,
    AutomationCandidateSerializer,
    CandidateReviewSerializer,
    ROIConfigurationSerializer,
    TaskPatternSerializer,
)
from .services.pattern_detector import PatternDetector
from .services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class TaskPatternViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for task patterns (read-only)."""

    queryset = TaskPattern.objects.all()
    serializer_class = TaskPatternSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by pattern_type, source, and active status."""
        queryset = TaskPattern.objects.annotate(candidate_count=Count("candidates"))
        pattern_type = self.request.query_params.get("pattern_type")
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(source=source)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-last_detected")


class AutomationCandidateViewSet(viewsets.ModelViewSet):
    """ViewSet for automation candidates."""

    queryset = AutomationCandidate.objects.select_related("pattern", "reviewed_by")
    serializer_class = AutomationCandidateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, status, and pattern."""
        queryset = AutomationCandidate.objects.select_related("pattern", "reviewed_by")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        pattern_id = self.request.query_params.get("pattern_id")
        if pattern_id:
            queryset = queryset.filter(pattern_id=pattern_id)
        return queryset.order_by("-overall_score")

    @action(detail=True, methods=["post"])
    def review(self, request: Request, pk=None) -> Response:
        """Review a candidate."""
        candidate = self.get_object()
        serializer = CandidateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        candidate.status = serializer.validated_data["status"]
        candidate.reviewed_by = request.user
        candidate.reviewed_at = timezone.now()
        if serializer.validated_data.get("implementation_notes"):
            candidate.implementation_notes = serializer.validated_data["implementation_notes"]
        candidate.save()

        return Response(AutomationCandidateSerializer(candidate).data)

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve a candidate."""
        candidate = self.get_object()
        candidate.status = AutomationCandidate.Status.APPROVED
        candidate.reviewed_by = request.user
        candidate.reviewed_at = timezone.now()
        candidate.save()
        return Response(AutomationCandidateSerializer(candidate).data)

    @action(detail=True, methods=["post"])
    def reject(self, request: Request, pk=None) -> Response:
        """Reject a candidate."""
        candidate = self.get_object()
        serializer = CandidateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        candidate.status = AutomationCandidate.Status.REJECTED
        candidate.reviewed_by = request.user
        candidate.reviewed_at = timezone.now()
        if serializer.validated_data.get("implementation_notes"):
            candidate.implementation_notes = serializer.validated_data["implementation_notes"]
        candidate.save()

        return Response(AutomationCandidateSerializer(candidate).data)


class AutomationAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for automation analyses."""

    queryset = AutomationAnalysis.objects.all()
    serializer_class = AutomationAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use start serializer for create action."""
        if self.action == "create":
            return AutomationAnalysisStartSerializer
        return AutomationAnalysisSerializer

    def get_queryset(self):
        """Filter by correlation_id and status."""
        queryset = AutomationAnalysis.objects.all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-started_at")

    def create(self, request: Request) -> Response:
        """Start a new automation analysis."""
        serializer = AutomationAnalysisStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        analysis = AutomationAnalysis.objects.create(
            name=serializer.validated_data["name"],
            date_range_start=serializer.validated_data["date_range_start"],
            date_range_end=serializer.validated_data["date_range_end"],
            sources_analyzed=serializer.validated_data["sources_analyzed"],
            status=AutomationAnalysis.Status.RUNNING,
            started_at=timezone.now(),
        )

        # Run analysis (simplified - would use Celery in production)
        try:
            # Mock data collection and pattern detection
            detector = PatternDetector()
            patterns = detector.detect_repetitive_tasks([])  # Would use real data

            # Generate recommendations
            engine = RecommendationEngine()
            recommendations = engine.generate_recommendations(patterns)

            # Create candidates
            for rec in recommendations:
                AutomationCandidate.objects.create(
                    pattern=rec["pattern"],
                    title=rec["title"],
                    description=rec["description"],
                    current_process=rec["current_process"],
                    proposed_automation=rec["proposed_automation"],
                    frequency_score=rec["scores"]["frequency_score"],
                    time_impact_score=rec["scores"]["time_impact_score"],
                    error_reduction_score=rec["scores"]["error_reduction_score"],
                    complexity_score=rec["scores"]["complexity_score"],
                    overall_score=rec["scores"]["overall_score"],
                    annual_occurrences=rec["roi"]["annual_occurrences"],
                    time_saved_per_occurrence=rec["roi"]["time_saved_per_occurrence"],
                    estimated_annual_savings=rec["roi"]["estimated_annual_savings"],
                    development_cost_estimate=rec["roi"]["development_cost_estimate"],
                    payback_period_months=rec["roi"]["payback_period_months"],
                )

            analysis.patterns_detected = len(patterns)
            analysis.candidates_generated = len(recommendations)
            analysis.status = AutomationAnalysis.Status.COMPLETED
            analysis.completed_at = timezone.now()
            analysis.save()

        except Exception as _e:  # noqa: F841
            logger.exception("Error during automation analysis")
            analysis.status = AutomationAnalysis.Status.FAILED
            analysis.completed_at = timezone.now()
            analysis.save()

        return Response(AutomationAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)


class ROIConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for ROI configuration."""

    queryset = ROIConfiguration.objects.all()
    serializer_class = ROIConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by default status."""
        queryset = ROIConfiguration.objects.all()
        is_default = self.request.query_params.get("is_default")
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == "true")
        return queryset.order_by("-is_default", "name")


class AutomationReportsViewSet(viewsets.ViewSet):
    """ViewSet for automation reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request: Request) -> Response:
        """Get summary statistics."""
        total_opportunities = AutomationCandidate.objects.count()
        pending_review = AutomationCandidate.objects.filter(status=AutomationCandidate.Status.IDENTIFIED).count()
        approved = AutomationCandidate.objects.filter(status=AutomationCandidate.Status.APPROVED).count()
        implemented = AutomationCandidate.objects.filter(status=AutomationCandidate.Status.IMPLEMENTED).count()

        total_savings = AutomationCandidate.objects.aggregate(total=Sum("estimated_annual_savings"))["total"] or 0

        return Response(
            {
                "total_opportunities": total_opportunities,
                "pending_review": pending_review,
                "approved": approved,
                "implemented": implemented,
                "potential_annual_savings": float(total_savings),
            }
        )
