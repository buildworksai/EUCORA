# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for demo data admin endpoints.
"""
import pytest
from django.contrib.auth.models import User


@pytest.fixture
def admin_client(api_client, db):
    user = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True,
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_demo_mode_toggle(admin_client):
    response = admin_client.get('/api/v1/admin/demo-mode')
    assert response.status_code == 200
    assert response.data['demo_mode_enabled'] is False

    response = admin_client.post('/api/v1/admin/demo-mode', {'enabled': True}, format='json')
    assert response.status_code == 200
    assert response.data['demo_mode_enabled'] is True


@pytest.mark.django_db
def test_seed_and_clear_demo_data(admin_client):
    seed_payload = {
        'assets': 5,
        'applications': 4,
        'deployments': 3,
        'users': 2,
        'events': 5,
        'clear_existing': True,
        'batch_size': 2,
    }
    response = admin_client.post('/api/v1/admin/seed-demo-data', seed_payload, format='json')
    assert response.status_code == 200
    assert response.data['counts']['assets'] >= 1
    assert response.data['counts']['applications'] >= 1

    stats_response = admin_client.get('/api/v1/admin/demo-data-stats')
    assert stats_response.status_code == 200
    assert stats_response.data['counts']['assets'] >= 1

    clear_response = admin_client.delete('/api/v1/admin/clear-demo-data')
    assert clear_response.status_code == 200

    stats_response = admin_client.get('/api/v1/admin/demo-data-stats')
    assert stats_response.status_code == 200
    assert stats_response.data['counts']['assets'] == 0
