# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for core utilities.
"""
import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from apps.core.utils import generate_correlation_id, get_demo_mode_enabled, set_demo_mode_enabled, apply_demo_filter
from apps.core.models import DemoModeConfig
from apps.connectors.models import Asset


@pytest.mark.django_db
def test_generate_correlation_id():
    cid = generate_correlation_id()
    assert len(cid) > 10
    prefixed = generate_correlation_id("deploy")
    assert prefixed.startswith("deploy-")


@pytest.mark.django_db
def test_demo_mode_toggle():
    assert get_demo_mode_enabled() is False
    set_demo_mode_enabled(True)
    assert get_demo_mode_enabled() is True
    set_demo_mode_enabled(False)
    assert get_demo_mode_enabled() is False


@pytest.mark.django_db
def test_apply_demo_filter_with_query_param():
    Asset.objects.create(
        name="DemoAsset",
        asset_id="demo-1",
        serial_number="SN1",
        type="Laptop",
        os="Windows 11",
        status="Active",
        location="HQ",
        owner="demo@eucora.com",
        is_demo=True,
    )
    Asset.objects.create(
        name="ProdAsset",
        asset_id="prod-1",
        serial_number="SN2",
        type="Laptop",
        os="Windows 11",
        status="Active",
        location="HQ",
        owner="prod@eucora.com",
        is_demo=False,
    )

    factory = APIRequestFactory()
    request = Request(factory.get("/api/v1/assets/?include_demo=true"))
    queryset = apply_demo_filter(Asset.objects.all(), request)
    assert queryset.count() == 1
    assert queryset.first().is_demo is True

    request = Request(factory.get("/api/v1/assets/?include_demo=all"))
    queryset = apply_demo_filter(Asset.objects.all(), request)
    assert queryset.count() == 2

    request = Request(factory.get("/api/v1/assets/?include_demo=false"))
    queryset = apply_demo_filter(Asset.objects.all(), request)
    assert queryset.count() == 1
    assert queryset.first().is_demo is False


@pytest.mark.django_db
def test_apply_demo_filter_with_global_mode():
    DemoModeConfig.objects.all().delete()
    set_demo_mode_enabled(True)

    Asset.objects.create(
        name="DemoAsset",
        asset_id="demo-2",
        serial_number="SN3",
        type="Laptop",
        os="Windows 11",
        status="Active",
        location="HQ",
        owner="demo@eucora.com",
        is_demo=True,
    )
    Asset.objects.create(
        name="ProdAsset",
        asset_id="prod-2",
        serial_number="SN4",
        type="Laptop",
        os="Windows 11",
        status="Active",
        location="HQ",
        owner="prod@eucora.com",
        is_demo=False,
    )

    factory = APIRequestFactory()
    request = Request(factory.get("/api/v1/assets/"))
    queryset = apply_demo_filter(Asset.objects.all(), request)
    assert queryset.count() == 1
    assert queryset.first().is_demo is True
