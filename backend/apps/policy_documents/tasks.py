# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for document processing.
"""
import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from apps.policy_documents.models import PolicyDocument
from apps.policy_documents.services.processing import DocumentProcessingPipeline

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    soft_time_limit=300,
    time_limit=330,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_document_task(self, document_id: str):
    """
    Process a document asynchronously.

    Args:
        document_id: UUID of PolicyDocument to process

    Returns:
        Dict with processing results
    """
    try:
        document = PolicyDocument.objects.get(id=document_id)
        pipeline = DocumentProcessingPipeline()
        result = pipeline.process_document(document)
        logger.info(f"Document processed successfully: {document_id}")
        return result
    except ObjectDoesNotExist:
        logger.error(f"Document not found: {document_id}")
        return {"status": "failed", "error": "Document not found"}
    except Exception as e:
        logger.error(f"Document processing failed: {document_id}, error: {e}", exc_info=True)
        raise


@shared_task(
    bind=True,
    max_retries=3,
    soft_time_limit=300,
    time_limit=330,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def reindex_document_task(self, document_id: str):
    """
    Re-process an existing document.

    Args:
        document_id: UUID of PolicyDocument to reindex

    Returns:
        Dict with processing results
    """
    try:
        document = PolicyDocument.objects.get(id=document_id)
        # Delete existing chunks
        document.chunks.all().delete()
        # Process again
        pipeline = DocumentProcessingPipeline()
        result = pipeline.process_document(document)
        logger.info(f"Document reindexed successfully: {document_id}")
        return result
    except ObjectDoesNotExist:
        logger.error(f"Document not found: {document_id}")
        return {"status": "failed", "error": "Document not found"}
    except Exception as e:
        logger.error(f"Document reindexing failed: {document_id}, error: {e}", exc_info=True)
        raise
