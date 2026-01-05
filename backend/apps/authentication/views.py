# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Authentication views for session-based login.

Supports:
- Email/password login (development and production)
- Entra ID OAuth2 integration (production)
- Session management with CSRF protection
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def entra_id_login(request):
    """
    Session-based login supporting both email/password and Entra ID OAuth.
    
    POST /api/v1/auth/login
    Body options:
        - {"email": "...", "password": "..."} - Email/password login
        - {"username": "...", "password": "..."} - Username login (legacy)
        - {"code": "...", "redirect_uri": "..."} - Entra ID OAuth
    
    Returns:
        200: {"user": {...}, "session_id": "..."}
        400: {"error": "Email and password required"}
        401: {"error": "Invalid credentials"}
    """
    # Email/password login
    email = request.data.get('email')
    username = request.data.get('username')
    password = request.data.get('password')
    
    if (email or username) and password:
        # Try to authenticate with email first
        user = None
        login_identifier = email or username
        
        if email:
            # Look up user by email
            try:
                user_obj = User.objects.filter(email=email).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        # Fallback to username authentication
        if not user and username:
            user = authenticate(request, username=username, password=password)
        
        # Also try email as username (for compatibility)
        if not user and email:
            user = authenticate(request, username=email, password=password)
        
        if user:
            login(request, user)
            logger.info(
                f'User logged in: {user.username}',
                extra={'correlation_id': getattr(request, 'correlation_id', 'N/A'), 'user': user.username}
            )
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                },
                'session_id': request.session.session_key,
            })
        else:
            logger.warning(
                f'Failed login attempt for: {login_identifier}',
                extra={'correlation_id': getattr(request, 'correlation_id', 'N/A')}
            )
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    # Entra ID OAuth code exchange
    code = request.data.get('code')
    redirect_uri = request.data.get('redirect_uri', getattr(settings, 'ENTRA_ID_REDIRECT_URI', ''))
    
    if not code:
        return Response(
            {'error': 'Email and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Exchange code for token
    try:
        token_data = _exchange_code_for_token(code, redirect_uri)
    except Exception as e:
        logger.error(f'Token exchange failed: {e}', extra={'correlation_id': getattr(request, 'correlation_id', 'N/A')})
        return Response(
            {'error': 'Invalid authorization code'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get user profile from Microsoft Graph
    try:
        user_profile = _get_user_profile(token_data['access_token'])
    except Exception as e:
        logger.error(f'User profile fetch failed: {e}', extra={'correlation_id': getattr(request, 'correlation_id', 'N/A')})
        return Response(
            {'error': 'Failed to fetch user profile'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get or create Django user
    user, created = User.objects.get_or_create(
        username=user_profile['userPrincipalName'],
        defaults={
            'email': user_profile.get('mail', user_profile['userPrincipalName']),
            'first_name': user_profile.get('givenName', ''),
            'last_name': user_profile.get('surname', ''),
        }
    )
    
    # Create Django session
    login(request, user)
    
    logger.info(
        f'Entra ID login: {user.username}',
        extra={
            'correlation_id': getattr(request, 'correlation_id', 'N/A'),
            'user': user.username,
            'created': created,
        }
    )
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        },
        'session_id': request.session.session_key,
    })


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated logout for session cleanup
def auth_logout(request):
    """
    Logout and destroy Django session.
    
    POST /api/v1/auth/logout
    
    Returns:
        200: {"message": "Logged out successfully"}
    """
    username = request.user.username if request.user.is_authenticated else 'anonymous'
    logout(request)
    
    logger.info(
        f'User logged out: {username}',
        extra={'correlation_id': getattr(request, 'correlation_id', 'N/A'), 'user': username}
    )
    
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Get current authenticated user.
    
    GET /api/v1/auth/me
    
    Returns:
        200: {"user": {...}}
    """
    return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_session(request):
    """
    Validate current session is active.
    
    GET /api/v1/auth/validate
    
    Returns:
        200: {"valid": true, "user": {...}}
        401: If session is invalid
    """
    return Response({
        'valid': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
        },
        'session_expiry': request.session.get_expiry_date().isoformat() if request.session.session_key else None,
    })


def _exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    """
    Exchange authorization code for access token via Entra ID.
    
    Args:
        code: Authorization code from Entra ID
        redirect_uri: Redirect URI used in authorization request
    
    Returns:
        dict: Token response with access_token, refresh_token, etc.
    
    Raises:
        Exception: If token exchange fails
    """
    tenant_id = getattr(settings, 'ENTRA_ID_TENANT_ID', '')
    client_id = getattr(settings, 'ENTRA_ID_CLIENT_ID', '')
    client_secret = getattr(settings, 'ENTRA_ID_CLIENT_SECRET', '')
    
    if not all([tenant_id, client_id, client_secret]):
        raise Exception('Entra ID not configured')
    
    token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'scope': 'User.Read',
    }
    
    response = requests.post(token_url, data=data, timeout=10)
    response.raise_for_status()
    
    return response.json()


def _get_user_profile(access_token: str) -> dict:
    """
    Fetch user profile from Microsoft Graph API.
    
    Args:
        access_token: Access token from Entra ID
    
    Returns:
        dict: User profile with userPrincipalName, mail, givenName, surname, etc.
    
    Raises:
        Exception: If profile fetch fails
    """
    graph_url = 'https://graph.microsoft.com/v1.0/me'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    
    response = requests.get(graph_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    return response.json()
