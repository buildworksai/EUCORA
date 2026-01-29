# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Custom pagination classes for efficient result set handling.

Implements cursor-based pagination for large datasets and sequential paging
for smaller datasets to prevent N+1 queries and improve response times.
"""
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class StandardCursorPagination(CursorPagination):
    """
    Cursor-based pagination for efficient querying of large datasets.

    Uses cursor-based pagination which is more efficient than offset pagination
    for large datasets. Cursor is a base64-encoded string containing the sort order.

    Default: 100 items per page
    Max: 1000 items per page
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000
    page_size_query_description = "Number of results to return per page (max 1000)"
    ordering = "-created_at"  # Default ordering: newest first


class LargeResultsCursorPagination(CursorPagination):
    """
    Cursor pagination for very large result sets (100s of thousands of records).

    Optimized for scanning large datasets with minimal overhead.
    """

    page_size = 500
    page_size_query_param = "page_size"
    max_page_size = 5000
    ordering = "-created_at"


class SmallPageNumberPagination(PageNumberPagination):
    """
    Page-number based pagination for small result sets.

    Simple page number pagination suitable for datasets with <10k records.
    Default: 50 items per page
    Max: 500 items per page
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500
    page_size_query_description = "Number of results to return per page (max 500)"


class StandardPageNumberPagination(PageNumberPagination):
    """
    Page-number based pagination (standard).

    Default: 100 items per page
    Max: 1000 items per page
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000
    page_size_query_description = "Number of results to return per page (max 1000)"


class TelemetryCursorPagination(CursorPagination):
    """
    Cursor-based pagination for telemetry data.

    Orders by collected_at instead of created_at since telemetry uses collected_at.
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000
    ordering = "-collected_at"  # Telemetry uses collected_at, not created_at
