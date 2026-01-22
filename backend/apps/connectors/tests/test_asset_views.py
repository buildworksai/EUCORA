# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for asset list/detail endpoints.
"""
import pytest
from apps.connectors.models import Asset
from apps.core.utils import set_demo_mode_enabled


@pytest.mark.django_db
def test_list_assets_filters_and_search(authenticated_client):
    Asset.objects.create(
        name="Laptop-001",
        asset_id="asset-1",
        serial_number="SN-1",
        type="Laptop",
        os="Windows 11",
        status="Active",
        location="HQ",
        owner="alice@example.com",
        is_demo=True,  # Set to True to pass demo filtering
    )
    Asset.objects.create(
        name="Desktop-001",
        asset_id="asset-2",
        serial_number="SN-2",
        type="Desktop",
        os="Ubuntu 22.04",
        status="Inactive",
        location="Branch",
        owner="bob@example.com",
        is_demo=True,  # Set to True to pass demo filtering
    )

    response = authenticated_client.get("/api/v1/assets/?type=Laptop&search=alice")
    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["assets"][0]["name"] == "Laptop-001"


@pytest.mark.django_db
def test_get_asset_not_found(authenticated_client):
    response = authenticated_client.get("/api/v1/assets/does-not-exist/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_list_assets_demo_mode(authenticated_client):
    Asset.objects.create(
        name="DemoAsset",
        asset_id="demo-asset",
        serial_number="SN-D",
        type="Laptop",
        os="Windows 11",
        status="Active",
        location="HQ",
        owner="demo@example.com",
        is_demo=True,
    )
    Asset.objects.create(
        name="ProdAsset",
        asset_id="prod-asset",
        serial_number="SN-P",
        type="Laptop",
        os="Windows 11",
        status="Active",
        location="HQ",
        owner="prod@example.com",
        is_demo=False,
    )

    set_demo_mode_enabled(True)
    response = authenticated_client.get("/api/v1/assets/")
    assert response.status_code == 200
    assert response.data["total"] == 1
    assert response.data["assets"][0]["id"] == "demo-asset"

    response = authenticated_client.get("/api/v1/assets/?include_demo=all")
    assert response.data["total"] == 2
