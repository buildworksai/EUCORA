# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Documentation Agent.
"""
import logging

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import CodeAnalysis, CodeRepository, DocumentationTemplate, DocumentedModule, GeneratedDocument
from .serializers import (
    CodeAnalysisSerializer,
    CodeAnalysisStartSerializer,
    CodeRepositoryCreateSerializer,
    CodeRepositorySerializer,
    DocumentationTemplateSerializer,
    DocumentedModuleSerializer,
    GeneratedDocumentPublishSerializer,
    GeneratedDocumentSerializer,
    GenerateDocumentSerializer,
)
from .services.analyzers.python_analyzer import DjangoCodeAnalyzer
from .services.generators.doc_generator import DocGenerator
from .services.quality_scorer import QualityScorer

logger = logging.getLogger(__name__)


class CodeRepositoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for code repository management.

    Provides CRUD operations and repository analysis.
    """

    queryset = CodeRepository.objects.all()
    serializer_class = CodeRepositorySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use create serializer for write operations."""
        if self.action in ["create", "update", "partial_update"]:
            return CodeRepositoryCreateSerializer
        return CodeRepositorySerializer

    def get_queryset(self):
        """Filter by active status and correlation_id if provided."""
        queryset = CodeRepository.objects.annotate(analysis_count=Count("analyses"))
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(analyses__correlation_id=correlation_id).distinct()
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def analyze(self, request: Request, pk=None) -> Response:
        """Start code analysis for repository."""
        repository = self.get_object()
        serializer = CodeAnalysisStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create analysis record
        analysis = CodeAnalysis.objects.create(
            repository=repository,
            branch=serializer.validated_data.get("branch", "main"),
            commit_sha=serializer.validated_data.get("commit_sha", ""),
            status=CodeAnalysis.Status.RUNNING,
            started_at=timezone.now(),
        )

        # Run analysis asynchronously (simplified - would use Celery in production)
        try:
            # Determine base path
            base_path = repository.local_path or repository.url

            # Analyze based on repository type
            if repository.repo_type == CodeRepository.RepoType.LOCAL:
                # Python/Django analysis
                python_analyzer = DjangoCodeAnalyzer(base_path)
                models = python_analyzer.analyze_models("apps/*/models.py")
                views = python_analyzer.analyze_views("apps/*/views.py")
                serializers = python_analyzer.analyze_serializers("apps/*/serializers.py")

                # Create documented modules
                for model in models:
                    DocumentedModule.objects.create(
                        analysis=analysis,
                        module_path=f"apps/{model.module_path}",
                        module_type=DocumentedModule.ModuleType.CLASS,
                        name=model.name,
                        docstring=model.docstring,
                        metadata={"fields": model.fields, "relationships": model.relationships},
                    )

                # Update summary
                analysis.summary = {
                    "modules": len(models) + len(views) + len(serializers),
                    "classes": len(models),
                    "functions": len(views),
                }
                analysis.status = CodeAnalysis.Status.COMPLETED
                analysis.completed_at = timezone.now()
                analysis.save()

                repository.last_analyzed = timezone.now()
                repository.save()

        except Exception as e:
            logger.exception("Error during code analysis")
            analysis.status = CodeAnalysis.Status.FAILED
            analysis.errors = [str(e)]
            analysis.completed_at = timezone.now()
            analysis.save()

        return Response(CodeAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)


class CodeAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for code analyses (read-only)."""

    queryset = CodeAnalysis.objects.select_related("repository")
    serializer_class = CodeAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, repository, and status."""
        queryset = CodeAnalysis.objects.select_related("repository")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        repository_id = self.request.query_params.get("repository_id")
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-started_at")

    @action(detail=True, methods=["get"])
    def modules(self, request: Request, pk=None) -> Response:
        """Get documented modules for this analysis."""
        analysis = self.get_object()
        modules = analysis.modules.all()
        serializer = DocumentedModuleSerializer(modules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def quality(self, request: Request, pk=None) -> Response:
        """Get quality score for this analysis."""
        analysis = self.get_object()
        scorer = QualityScorer()
        quality_score = scorer.calculate_quality_score(analysis)
        return Response(quality_score)


class DocumentedModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for documented modules (read-only)."""

    queryset = DocumentedModule.objects.select_related("analysis")
    serializer_class = DocumentedModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by analysis and module type."""
        queryset = DocumentedModule.objects.select_related("analysis")
        analysis_id = self.request.query_params.get("analysis_id")
        if analysis_id:
            queryset = queryset.filter(analysis_id=analysis_id)
        module_type = self.request.query_params.get("module_type")
        if module_type:
            queryset = queryset.filter(module_type=module_type)
        return queryset.order_by("module_path", "name")


class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for generated documents."""

    queryset = GeneratedDocument.objects.select_related("analysis", "reviewed_by")
    serializer_class = GeneratedDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, analysis, doc_type, and status."""
        queryset = GeneratedDocument.objects.select_related("analysis", "reviewed_by")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        analysis_id = self.request.query_params.get("analysis_id")
        if analysis_id:
            queryset = queryset.filter(analysis_id=analysis_id)
        doc_type = self.request.query_params.get("doc_type")
        if doc_type:
            queryset = queryset.filter(doc_type=doc_type)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def review(self, request: Request, pk=None) -> Response:
        """Mark document as under review."""
        document = self.get_object()
        document.status = GeneratedDocument.DocStatus.REVIEW
        document.reviewed_by = request.user
        document.save()
        return Response(GeneratedDocumentSerializer(document).data)

    @action(detail=True, methods=["post"])
    def publish(self, request: Request, pk=None) -> Response:
        """Publish document."""
        document = self.get_object()
        serializer = GeneratedDocumentPublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("target_path"):
            document.target_path = serializer.validated_data["target_path"]

        document.status = GeneratedDocument.DocStatus.PUBLISHED
        document.reviewed_by = request.user
        document.published_at = timezone.now()
        document.save()

        return Response(GeneratedDocumentSerializer(document).data)


class DocumentationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for documentation templates."""

    queryset = DocumentationTemplate.objects.all()
    serializer_class = DocumentationTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by doc_type and active status."""
        queryset = DocumentationTemplate.objects.all()
        doc_type = self.request.query_params.get("doc_type")
        if doc_type:
            queryset = queryset.filter(doc_type=doc_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("doc_type", "name")


class DocumentationGenerationViewSet(viewsets.ViewSet):
    """ViewSet for documentation generation actions."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def generate(self, request: Request) -> Response:
        """Generate documentation."""
        serializer = GenerateDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        analysis_id = request.data.get("analysis_id")
        if not analysis_id:
            return Response({"error": "analysis_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            analysis = CodeAnalysis.objects.get(id=analysis_id)
        except CodeAnalysis.DoesNotExist:
            return Response({"error": "Analysis not found"}, status=status.HTTP_404_NOT_FOUND)

        doc_type = serializer.validated_data["doc_type"]
        generator = DocGenerator()

        # Generate content based on type
        if doc_type == GeneratedDocument.DocType.API:
            content = generator.generate_api_docs(analysis)
            title = f"{analysis.repository.name} API Documentation"
        elif doc_type == GeneratedDocument.DocType.README:
            content = generator.generate_readme(analysis)
            title = f"{analysis.repository.name} README"
        elif doc_type == GeneratedDocument.DocType.ARCHITECTURE:
            content = generator.generate_mermaid_diagram(analysis)
            title = f"{analysis.repository.name} Architecture Diagram"
        else:
            content = f"# {analysis.repository.name}\n\nDocumentation placeholder."
            title = f"{analysis.repository.name} Documentation"

        # Create document
        document = GeneratedDocument.objects.create(
            analysis=analysis,
            doc_type=doc_type,
            title=title,
            content=content,
            format=(
                GeneratedDocument.DocFormat.MARKDOWN
                if doc_type != GeneratedDocument.DocType.API
                else GeneratedDocument.DocFormat.OPENAPI
            ),
            target_path=serializer.validated_data.get("target_path"),
        )

        return Response(GeneratedDocumentSerializer(document).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def api_docs(self, request: Request) -> Response:
        """Generate API documentation specifically."""
        return self.generate(request)

    @action(detail=False, methods=["post"])
    def runbook(self, request: Request) -> Response:
        """Generate runbook documentation."""
        return self.generate(request)

    @action(detail=False, methods=["post"])
    def adr(self, request: Request) -> Response:
        """Generate ADR documentation."""
        return self.generate(request)
