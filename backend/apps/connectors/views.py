# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Connector views for execution plane integration.
"""
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import models
import logging
from apps.core.utils import apply_demo_filter
from apps.connectors import services

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
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
    queryset = apply_demo_filter(Asset.objects.all(), request)
    
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
    
    # Serialize assets - match frontend contracts.ts structure
    assets = []
    for asset in assets_queryset:
        # Map platform from OS
        platform_map = {
            'Windows': 'WINDOWS',
            'macOS': 'MACOS',
            'Linux': 'LINUX',
            'Ubuntu': 'LINUX',
            'RHEL': 'LINUX',
            'iOS': 'MOBILE',
            'Android': 'MOBILE',
        }
        platform = 'WINDOWS'  # default
        for os_key, plat_value in platform_map.items():
            if os_key in asset.os:
                platform = plat_value
                break
        
        assets.append({
            'id': asset.id,  # Use database ID (number) not asset_id (string)
            'hostname': asset.name,  # Frontend expects 'hostname' not 'name'
            'platform': platform,  # Frontend expects platform enum
            'device_type': asset.type,  # Frontend expects 'device_type' not 'type'
            'os_version': asset.os,  # Frontend expects 'os_version' not 'os'
            'user_sentiment': asset.user_sentiment,  # Optional
            'dex_score': asset.dex_score,  # Optional
            'boot_time': asset.boot_time,  # Optional
            'carbon_footprint': asset.carbon_footprint,  # Optional
            'last_seen': asset.last_checkin.isoformat() if asset.last_checkin else asset.created_at.isoformat(),  # Frontend expects 'last_seen'
            'created_at': asset.created_at.isoformat(),
            # Additional fields for backward compatibility (if needed by other pages)
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
        })
    
    return Response({
        'assets': assets,
        'total': total,
        'page': page,
        'page_size': page_size,
    })


@api_view(['GET'])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def get_asset(request, asset_id):
    """
    Get single asset details.
    
    GET /api/v1/assets/{asset_id}/
    """
    from apps.connectors.models import Asset
    
    try:
        asset = apply_demo_filter(Asset.objects.all(), request).get(asset_id=asset_id)
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
    if connector_type not in services.PowerShellConnectorService.CONNECTOR_SCRIPTS:
        return Response(
            {'error': f'Invalid connector type: {connector_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = services.get_connector_service()
    result = service.health_check(connector_type)
    status_code = status.HTTP_200_OK if result['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response({
        'connector_type': connector_type,
        **result,
    }, status=status_code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deploy(request, connector_type):
    """
    Deploy via connector.
    
    POST /api/v1/connectors/{connector_type}/deploy
    """
    if connector_type not in services.PowerShellConnectorService.CONNECTOR_SCRIPTS:
        return Response(
            {'error': f'Invalid connector type: {connector_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    required_fields = ['deployment_intent_id', 'artifact_path', 'target_ring', 'app_name', 'version']
    missing = [field for field in required_fields if not request.data.get(field)]
    if missing:
        return Response(
            {'error': f'Missing required fields: {", ".join(missing)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = services.get_connector_service()
    result = service.deploy(connector_type, {
        'deployment_intent_id': request.data['deployment_intent_id'],
        'artifact_path': request.data['artifact_path'],
        'target_ring': request.data['target_ring'],
        'app_name': request.data['app_name'],
        'version': request.data['version'],
    })

    status_code = status.HTTP_200_OK if result['status'] == 'success' else status.HTTP_500_INTERNAL_SERVER_ERROR
    return Response({
        'connector_type': connector_type,
        **result,
    }, status=status_code)
