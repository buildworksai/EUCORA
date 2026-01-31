# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for Portfolio Management endpoints.

Tests REST API functionality including CRUD operations, filtering, and custom actions.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.license_management.models import Vendor
from apps.portfolio_management.models import ApplicationManagerPerformance, LicenseTrueUpForecast, Portfolio

User = get_user_model()


class PortfolioAPITestCase(TestCase):
    """Test cases for Portfolio API endpoints."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.manager = User.objects.create_user(username="portfolio_mgr", email="pm@example.com", password="testpass")
        self.client.force_authenticate(user=self.manager)

        self.portfolio = Portfolio.objects.create(
            name="Test Portfolio",
            manager=self.manager,
            scope={"business_units": ["IT"]},
            budget_annual=Decimal("500000.00"),
        )

    def test_list_portfolios(self):
        """Test listing portfolios."""
        url = reverse("portfolio-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Portfolio")

    def test_retrieve_portfolio(self):
        """Test retrieving a single portfolio."""
        url = reverse("portfolio-detail", args=[self.portfolio.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Portfolio")
        self.assertEqual(response.data["manager_name"], "portfolio_mgr")

    def test_create_portfolio(self):
        """Test creating a new portfolio."""
        url = reverse("portfolio-list")
        data = {
            "name": "New Portfolio",
            "manager": self.manager.id,
            "scope": {"business_units": ["HR"]},
            "budget_annual": "250000.00",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Portfolio.objects.count(), 2)
        self.assertEqual(response.data["name"], "New Portfolio")

    def test_update_portfolio(self):
        """Test updating a portfolio."""
        url = reverse("portfolio-detail", args=[self.portfolio.id])
        data = {"name": "Updated Portfolio", "budget_annual": "600000.00"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.name, "Updated Portfolio")
        self.assertEqual(self.portfolio.budget_annual, Decimal("600000.00"))

    def test_delete_portfolio(self):
        """Test deleting a portfolio."""
        url = reverse("portfolio-detail", args=[self.portfolio.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Portfolio.objects.count(), 0)

    def test_portfolio_metrics_action(self):
        """Test portfolio metrics custom action."""
        url = reverse("portfolio-metrics", args=[self.portfolio.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("portfolio_id", response.data)
        self.assertIn("total_applications", response.data)
        self.assertIn("health_score", response.data)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        self.client.force_authenticate(user=None)
        url = reverse("portfolio-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LicenseTrueUpForecastAPITestCase(TestCase):
    """Test cases for License True-Up Forecast API endpoints."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.manager = User.objects.create_user(username="portfolio_mgr", email="pm@example.com", password="testpass")
        self.client.force_authenticate(user=self.manager)

        self.portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.manager)
        self.vendor = Vendor.objects.create(name="Test Vendor", identifier="test-vendor")

        self.forecast = LicenseTrueUpForecast.objects.create(
            vendor=self.vendor,
            portfolio=self.portfolio,
            forecast_period="2026-Q4",
            entitled_quantity=1000,
            projected_consumption=1150,
            true_up_quantity=150,
            true_up_cost=Decimal("15000.00"),
            risk_level="MEDIUM",
            confidence_score=0.85,
        )

    def test_list_forecasts(self):
        """Test listing forecasts."""
        url = reverse("forecast-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_risk_level(self):
        """Test filtering forecasts by risk level."""
        url = reverse("forecast-list")
        response = self.client.get(url, {"risk_level": "MEDIUM"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_high_risk_action(self):
        """Test high-risk forecasts custom action."""
        # Create a high-risk forecast
        LicenseTrueUpForecast.objects.create(
            vendor=self.vendor,
            portfolio=self.portfolio,
            forecast_period="2027-Q1",
            entitled_quantity=1000,
            projected_consumption=1600,
            true_up_quantity=600,
            true_up_cost=Decimal("60000.00"),
            risk_level="HIGH",
            confidence_score=0.90,
        )

        url = reverse("forecast-high-risk")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["risk_level"], "HIGH")


class ApplicationManagerPerformanceAPITestCase(TestCase):
    """Test cases for Application Manager Performance API endpoints."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.manager = User.objects.create_user(username="app_mgr", email="am@example.com", password="testpass")
        self.portfolio_mgr = User.objects.create_user(
            username="portfolio_mgr", email="pm@example.com", password="testpass"
        )
        self.client.force_authenticate(user=self.portfolio_mgr)

        self.portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.portfolio_mgr)

        self.performance = ApplicationManagerPerformance.objects.create(
            manager=self.manager,
            portfolio=self.portfolio,
            deployments_total=10,
            success_rate_percent=90.0,
            composite_score=85.0,
        )

    def test_list_performance_metrics(self):
        """Test listing performance metrics."""
        url = reverse("performance-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_manager(self):
        """Test filtering performance by manager."""
        url = reverse("performance-list")
        response = self.client.get(url, {"manager": self.manager.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_readonly_viewset(self):
        """Test that performance endpoints are read-only."""
        url = reverse("performance-list")
        data = {"manager": self.manager.id, "composite_score": 95.0}
        response = self.client.post(url, data, format="json")

        # Should not allow POST on read-only viewset
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
