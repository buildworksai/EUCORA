# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Policy Documents.
"""
import uuid

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.policy_documents.models import DocumentCategory, PolicyDocument
from apps.policy_documents.serializers import (
    DocumentCategorySerializer,
    PolicyDocumentDetailSerializer,
    PolicyDocumentSerializer,
    SearchRequestSerializer,
    SemanticSearchRequestSerializer,
)
from apps.policy_documents.services.rag import PolicyContextRetriever
from apps.policy_documents.tasks import process_document_task, reindex_document_task
from apps.rbac.permissions import RBACPermission
from apps.storage.services import get_storage_service


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    """API viewset for DocumentCategory."""

    permission_classes = [RBACPermission("policy_documents", "read")]
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    lookup_field = "id"

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [RBACPermission("policy_documents", "create")()]
        return super().get_permissions()


class PolicyDocumentViewSet(viewsets.ModelViewSet):
    """API viewset for PolicyDocument."""

    permission_classes = [RBACPermission("policy_documents", "read")]
    queryset = PolicyDocument.objects.select_related("category", "uploaded_by").all()
    serializer_class = PolicyDocumentSerializer
    lookup_field = "id"

    def get_serializer_class(self):
        """Use detail serializer for retrieve."""
        if self.action == "retrieve":
            return PolicyDocumentDetailSerializer
        return PolicyDocumentSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [RBACPermission("policy_documents", "create")()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter by query parameters."""
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")

        if category:
            qs = qs.filter(category_id=category)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return qs

    @action(detail=False, methods=["post"])
    def upload(self, request: Request) -> Response:
        """Upload document(s)."""
        files = request.FILES.getlist("files")
        if not files:
            return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)

        category_id = request.data.get("category_id")
        if not category_id:
            return Response({"error": "category_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = DocumentCategory.objects.get(id=category_id)
        except DocumentCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

        storage_service = get_storage_service()
        created_documents = []

        for file in files:
            # Validate file type
            file_type = file.name.split(".")[-1].lower()
            if file_type not in ["pdf", "docx", "doc", "html", "htm", "txt", "md"]:
                continue

            # Upload to storage
            storage_path = f"policy-documents/{uuid.uuid4()}/{file.name}"
            # Reset file pointer after reading for hash
            file.seek(0)
            result = storage_service.upload(storage_path, file, content_type=file.content_type)

            # Create document record
            document = PolicyDocument.objects.create(
                title=file.name,
                category=category,
                file_name=file.name,
                file_type=file_type,
                file_size=file.size,
                storage_path=result.path,
                content_hash=PolicyDocument.hash_content(file.read()),
                uploaded_by=request.user,
                status=PolicyDocument.DocumentStatus.DRAFT,
            )

            # Trigger async processing
            process_document_task.delay(str(document.id))

            created_documents.append(PolicyDocumentSerializer(document).data)

        return Response({"documents": created_documents}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def download(self, request: Request, id=None) -> Response:
        """Download original file."""
        document = self.get_object()
        storage_service = get_storage_service()
        file_content = storage_service.download(document.storage_path)

        from django.http import HttpResponse

        response = HttpResponse(file_content, content_type=f"application/{document.file_type}")
        response["Content-Disposition"] = f'attachment; filename="{document.file_name}"'
        return response

    @action(detail=True, methods=["post"])
    def reprocess(self, request: Request, id=None) -> Response:
        """Reprocess document."""
        document = self.get_object()
        reindex_document_task.delay(str(document.id))
        return Response({"message": "Reprocessing started"})

    @action(detail=False, methods=["post"])
    def search(self, request: Request) -> Response:
        """Full-text search."""
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qs = PolicyDocument.objects.filter(status=PolicyDocument.DocumentStatus.ACTIVE)

        if serializer.validated_data.get("query"):
            query = serializer.validated_data["query"]
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

        if serializer.validated_data.get("categories"):
            qs = qs.filter(category__category_type__in=serializer.validated_data["categories"])

        total = qs.count()
        offset = serializer.validated_data["offset"]
        limit = serializer.validated_data["limit"]
        results = qs[offset : offset + limit]

        return Response(
            {
                "results": PolicyDocumentSerializer(results, many=True).data,
                "total": total,
            }
        )

    @action(detail=False, methods=["post"])
    def semantic_search(self, request: Request) -> Response:
        """Semantic similarity search."""
        serializer = SemanticSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        retriever = PolicyContextRetriever()
        chunks = retriever.get_context(**serializer.validated_data)

        return Response(
            {
                "results": [
                    {
                        "id": chunk.id,
                        "content": chunk.content,
                        "document_id": chunk.document_id,
                        "document_title": chunk.document_title,
                        "category": chunk.category,
                        "similarity": chunk.similarity,
                        "heading": chunk.heading,
                    }
                    for chunk in chunks
                ],
            }
        )
