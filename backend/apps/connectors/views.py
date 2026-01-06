# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Connector views for execution plane integration.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import models
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_assets(request):
    """
    List assets from CMDB (Asset Inventory).
    
    GET /api/v1/assets/
    Query params: ?type=...&os=...&status=...&location=...&owner=...&page=1&page_size=50&search=...
    """
    from apps.connectors.models import Asset
    
    # Extract query parameters
    asset_type = request.query_params.get('type')
    os_filter = request.query_params.get('os')
    status_filter = request.query_params.get('status')
    location_filter = request.query_params.get('location')
    owner_filter = request.query_params.get('owner')
    search_query = request.query_params.get('search', '').lower()
    page = int(request.query_params.get('page', 1))
    page_size = min(int(request.query_params.get('page_size', 50)), 100)  # Max 100 per page
    
    # Build query
    queryset = Asset.objects.all()
    
    if asset_type:
        queryset = queryset.filter(type=asset_type)
    if os_filter:
        queryset = queryset.filter(os__icontains=os_filter)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if location_filter:
        queryset = queryset.filter(location__icontains=location_filter)
    if owner_filter:
        queryset = queryset.filter(owner__icontains=owner_filter)
    if search_query:
        queryset = queryset.filter(
            models.Q(name__icontains=search_query) |
            models.Q(asset_id__icontains=search_query) |
            models.Q(serial_number__icontains=search_query) |
            models.Q(owner__icontains=search_query)
        )
    
    # Get total count
    total = queryset.count()
    
    # Apply pagination
    start = (page - 1) * page_size
    end = start + page_size
    assets_queryset = queryset[start:end]
    
    # Serialize assets
    assets = []
    for asset in assets_queryset:
        assets.append({
            'id': asset.asset_id,
            'name': asset.name,
            'type': asset.type,
            'os': asset.os,
            'location': asset.location,
            'status': asset.status,
            'compliance_score': asset.compliance_score,
            'last_checkin': asset.last_checkin.isoformat() if asset.last_checkin else None,
            'owner': asset.owner,
            'serial_number': asset.serial_number,
            'ip_address': str(asset.ip_address) if asset.ip_address else None,
            'disk_encryption': asset.disk_encryption,
            'firewall_enabled': asset.firewall_enabled,
            'dex_score': asset.dex_score,
            'boot_time': asset.boot_time,
            'carbon_footprint': asset.carbon_footprint,
            'user_sentiment': asset.user_sentiment,
        })
    
    return Response({
        'assets': assets,
        'total': total,
        'page': page,
        'page_size': page_size,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_asset(request, asset_id):
    """
    Get single asset details.
    
    GET /api/v1/assets/{asset_id}/
    """
    from apps.connectors.models import Asset
    
    try:
        asset = Asset.objects.get(asset_id=asset_id)
        return Response({
            'id': asset.asset_id,
            'name': asset.name,
            'type': asset.type,
            'os': asset.os,
            'location': asset.location,
            'status': asset.status,
            'compliance_score': asset.compliance_score,
            'last_checkin': asset.last_checkin.isoformat() if asset.last_checkin else None,
            'owner': asset.owner,
            'serial_number': asset.serial_number,
            'ip_address': str(asset.ip_address) if asset.ip_address else None,
            'disk_encryption': asset.disk_encryption,
            'firewall_enabled': asset.firewall_enabled,
            'dex_score': asset.dex_score,
            'boot_time': asset.boot_time,
            'carbon_footprint': asset.carbon_footprint,
            'user_sentiment': asset.user_sentiment,
            'connector_type': asset.connector_type,
            'created_at': asset.created_at.isoformat(),
            'updated_at': asset.updated_at.isoformat(),
        })
    except Asset.DoesNotExist:
        return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request, connector_type):
    """
    Health check for connector.
    
    GET /api/v1/connectors/{connector_type}/health
    """
    # TODO: Implement real health checks per connector type
    return Response({
        'connector_type': connector_type,
        'status': 'healthy',
        'message': 'Connector is operational',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deploy(request, connector_type):
    """
    Deploy via connector.
    
    POST /api/v1/connectors/{connector_type}/deploy
    """
    # TODO: Implement deployment logic per connector type
    return Response({
        'connector_type': connector_type,
        'status': 'deployed',
        'message': 'Deployment initiated',
    }, status=status.HTTP_202_ACCEPTED)
