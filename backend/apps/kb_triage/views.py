# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for KB & Triage Agent.
"""
import logging

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import IncidentPattern, KnowledgeArticle, KnowledgeSource, TriageFeedback, TriageRequest
from .serializers import (
    IncidentPatternSerializer,
    KnowledgeArticleSerializer,
    KnowledgeSourceSerializer,
    ResolutionStepSerializer,
    TriageFeedbackSerializer,
    TriageRequestSerializer,
    TriageSuggestionSerializer,
)

logger = logging.getLogger(__name__)


class KnowledgeSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for knowledge sources."""

    queryset = KnowledgeSource.objects.all()
    serializer_class = KnowledgeSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by source_type and is_active."""
        queryset = KnowledgeSource.objects.all()
        source_type = self.request.query_params.get("source_type")
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def sync(self, request: Request, pk=None) -> Response:
        """Sync articles from source."""
        source = self.get_object()
        # TODO: Implement knowledge source sync
        source.last_sync = timezone.now()
        source.save()
        return Response({"synced": 0})

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test source connection."""
        # TODO: Implement connection test
        return Response({"success": True})


class KnowledgeArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for knowledge articles."""

    queryset = KnowledgeArticle.objects.select_related("source")
    serializer_class = KnowledgeArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by source, category, and search."""
        queryset = KnowledgeArticle.objects.select_related("source")
        source_id = self.request.query_params.get("source_id")
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))
        return queryset.order_by("-published_date", "-view_count")

    @action(detail=False, methods=["post"])
    def search(self, request: Request) -> Response:
        """Semantic search across knowledge articles."""
        query = request.data.get("query", "")
        limit = int(request.data.get("limit", 10))

        # TODO: Implement semantic search using E7 pgvector
        # For now, use basic text search
        articles = KnowledgeArticle.objects.filter(Q(title__icontains=query) | Q(content__icontains=query))[:limit]

        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)


class TriageRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for triage requests."""

    queryset = TriageRequest.objects.all()
    serializer_class = TriageRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, status, and servicenow_number."""
        queryset = TriageRequest.objects.all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        servicenow_number = self.request.query_params.get("servicenow_number")
        if servicenow_number:
            queryset = queryset.filter(servicenow_number=servicenow_number)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["get"])
    def suggestions(self, request: Request, pk=None) -> Response:
        """Get triage suggestions."""
        triage_request = self.get_object()
        suggestions = triage_request.suggestions.all()
        serializer = TriageSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def resolution_steps(self, request: Request, pk=None) -> Response:
        """Get resolution steps."""
        triage_request = self.get_object()
        steps = triage_request.resolution_steps.all()
        serializer = ResolutionStepSerializer(steps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def feedback(self, request: Request, pk=None) -> Response:
        """Submit feedback on triage."""
        triage_request = self.get_object()
        feedback = TriageFeedback.objects.create(
            triage_request=triage_request,
            feedback_type=request.data.get("feedback_type"),
            was_accurate=request.data.get("was_accurate", False),
            correct_value=request.data.get("correct_value"),
            comments=request.data.get("comments"),
            submitted_by=request.user,
        )
        serializer = TriageFeedbackSerializer(feedback)
        return Response(serializer.data)


class TriageFeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for triage feedback."""

    queryset = TriageFeedback.objects.select_related("triage_request", "submitted_by")
    serializer_class = TriageFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by triage_request and feedback_type."""
        queryset = TriageFeedback.objects.select_related("triage_request", "submitted_by")
        triage_request_id = self.request.query_params.get("triage_request_id")
        if triage_request_id:
            queryset = queryset.filter(triage_request_id=triage_request_id)
        feedback_type = self.request.query_params.get("feedback_type")
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        return queryset.order_by("-created_at")


class IncidentPatternViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for incident patterns."""

    queryset = IncidentPattern.objects.all()
    serializer_class = IncidentPatternSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, pattern_type, status, and category."""
        queryset = IncidentPattern.objects.all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        pattern_type = self.request.query_params.get("pattern_type")
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return queryset.order_by("-last_detected")

    @action(detail=True, methods=["post"])
    def investigate(self, request: Request, pk=None) -> Response:
        """Mark pattern as investigating."""
        pattern = self.get_object()
        pattern.status = IncidentPattern.Status.INVESTIGATING
        pattern.save()
        serializer = self.get_serializer(pattern)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def resolve(self, request: Request, pk=None) -> Response:
        """Resolve pattern."""
        pattern = self.get_object()
        pattern.status = IncidentPattern.Status.RESOLVED
        pattern.root_cause = request.data.get("root_cause")
        pattern.resolution = request.data.get("resolution")
        pattern.save()
        serializer = self.get_serializer(pattern)
        return Response(serializer.data)


class KBTriageReportsViewSet(viewsets.ViewSet):
    """ViewSet for KB & Triage reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def accuracy(self, request: Request) -> Response:
        """Get triage accuracy statistics."""
        feedback = TriageFeedback.objects.all()
        total = feedback.count()
        accurate = feedback.filter(was_accurate=True).count()

        accuracy_by_type = {}
        for feedback_type in TriageFeedback.FeedbackType.choices:
            type_feedback = feedback.filter(feedback_type=feedback_type[0])
            type_total = type_feedback.count()
            type_accurate = type_feedback.filter(was_accurate=True).count()
            accuracy_by_type[feedback_type[0]] = {
                "total": type_total,
                "accurate": type_accurate,
                "accuracy": (type_accurate / type_total * 100) if type_total > 0 else 0,
            }

        return Response(
            {
                "overall_accuracy": (accurate / total * 100) if total > 0 else 0,
                "total_feedback": total,
                "accurate_feedback": accurate,
                "by_type": accuracy_by_type,
            }
        )

    @action(detail=False, methods=["get"])
    def categories(self, request: Request) -> Response:
        """Get category distribution."""
        categories = TriageRequest.objects.values("suggested_category").annotate(count=Count("id")).order_by("-count")
        return Response({"categories": list(categories)})

    @action(detail=False, methods=["get"])
    def patterns(self, request: Request) -> Response:
        """Get pattern statistics."""
        active_patterns = IncidentPattern.objects.filter(status=IncidentPattern.Status.ACTIVE).count()
        investigating_patterns = IncidentPattern.objects.filter(status=IncidentPattern.Status.INVESTIGATING).count()

        patterns_by_type = {}
        for pattern_type in IncidentPattern.PatternType.choices:
            patterns_by_type[pattern_type[0]] = IncidentPattern.objects.filter(pattern_type=pattern_type[0]).count()

        return Response(
            {
                "active_patterns": active_patterns,
                "investigating_patterns": investigating_patterns,
                "by_type": patterns_by_type,
            }
        )
