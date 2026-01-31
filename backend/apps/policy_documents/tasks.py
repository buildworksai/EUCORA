# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for document processing.
"""
from celery import shared_task

from apps.policy_documents.models import PolicyDocument
from apps.policy_documents.services.processing import DocumentProcessingPipeline


@shared_task
def process_document_task(document_id: str):
    """Process a document asynchronously."""
    document = PolicyDocument.objects.get(id=document_id)
    pipeline = DocumentProcessingPipeline()
    return pipeline.process_document(document)


@shared_task
def reindex_document_task(document_id: str):
    """Re-process an existing document."""
    document = PolicyDocument.objects.get(id=document_id)
    # Delete existing chunks
    document.chunks.all().delete()
    # Process again
    pipeline = DocumentProcessingPipeline()
    return pipeline.process_document(document)
