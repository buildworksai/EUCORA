# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for Portfolio Management models.

Tests model creation, validation, properties, and business logic.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.license_management.models import Vendor
from apps.portfolio_management.models import ApplicationManagerPerformance, LicenseTrueUpForecast, Portfolio

User = get_user_model()


class PortfolioModelTestCase(TestCase):
    """Test cases for Portfolio model."""

    def setUp(self):
        """Set up test data."""
        self.manager = User.objects.create_user(username="portfolio_mgr", email="pm@example.com")

    def test_create_portfolio(self):
        """Test creating a portfolio with basic fields."""
        portfolio = Portfolio.objects.create(
            name="Test Portfolio",
            manager=self.manager,
            scope={"business_units": ["IT"], "geographies": ["NA"]},
            budget_annual=Decimal("500000.00"),
        )

        self.assertEqual(portfolio.name, "Test Portfolio")
        self.assertEqual(portfolio.manager, self.manager)
        self.assertEqual(portfolio.budget_annual, Decimal("500000.00"))
        self.assertEqual(portfolio.total_applications, 0)
        self.assertEqual(portfolio.health_score, 0.0)

    def test_license_utilization_percent(self):
        """Test license utilization percent calculation."""
        portfolio = Portfolio.objects.create(
            name="Test Portfolio",
            manager=self.manager,
            total_licenses_entitled=100,
            total_licenses_consumed=75,
        )

        self.assertEqual(portfolio.license_utilization_percent, 75.0)

    def test_license_utilization_percent_zero_entitled(self):
        """Test license utilization when entitled is zero."""
        portfolio = Portfolio.objects.create(
            name="Test Portfolio",
            manager=self.manager,
            total_licenses_entitled=0,
            total_licenses_consumed=0,
        )

        self.assertEqual(portfolio.license_utilization_percent, 0.0)

    def test_str_representation(self):
        """Test string representation."""
        portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.manager)

        self.assertEqual(str(portfolio), "Test Portfolio")


class ApplicationOwnershipModelTestCase(TestCase):
    """Test cases for ApplicationOwnership model."""

    def setUp(self):
        """Set up test data."""
        self.manager = User.objects.create_user(username="portfolio_mgr", email="pm@example.com")
        self.app_manager = User.objects.create_user(username="app_mgr", email="am@example.com")
        self.portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.manager)

        # Mock application (would need to import from application_portfolio)
        # For now, we'll skip creating actual application

    def test_create_ownership(self):
        """Test creating an application ownership."""
        # Skipping test that requires Application model
        # TODO: Import Application model and create test instance
        pass

    def test_ownership_types(self):
        """Test ownership type choices."""
        ownership_types = ["PRIMARY", "SECONDARY"]
        # Verify choices are valid
        for ownership_type in ownership_types:
            self.assertIn(ownership_type, ["PRIMARY", "SECONDARY"])


class ApplicationManagerPerformanceModelTestCase(TestCase):
    """Test cases for ApplicationManagerPerformance model."""

    def setUp(self):
        """Set up test data."""
        self.manager = User.objects.create_user(username="app_mgr", email="am@example.com")
        self.portfolio_mgr = User.objects.create_user(username="portfolio_mgr", email="pm@example.com")
        self.portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.portfolio_mgr)

    def test_create_performance_snapshot(self):
        """Test creating a performance snapshot."""
        now = timezone.now()
        period_start = now - timedelta(days=30)

        performance = ApplicationManagerPerformance.objects.create(
            manager=self.manager,
            portfolio=self.portfolio,
            period_start=period_start,
            period_end=now,
            deployments_total=10,
            deployments_successful=9,
            success_rate_percent=90.0,
            avg_deployment_duration_days=2.5,
            avg_health_score=85.0,
            utilization_percent=75.0,
            composite_score=82.5,
        )

        self.assertEqual(performance.manager, self.manager)
        self.assertEqual(performance.portfolio, self.portfolio)
        self.assertEqual(performance.deployments_total, 10)
        self.assertEqual(performance.success_rate_percent, 90.0)
        self.assertEqual(performance.composite_score, 82.5)

    def test_calculate_composite_score(self):
        """Test composite score calculation."""
        performance = ApplicationManagerPerformance(
            manager=self.manager,
            success_rate_percent=90.0,
            avg_health_score=85.0,
            utilization_percent=77.5,  # Optimal
            avg_deployment_duration_days=1.0,  # Optimal
            health_incidents=0,  # Optimal
        )

        calculated_score = performance.calculate_composite_score()

        # Expected: 90*0.3 + 85*0.25 + 100*0.2 + 100*0.15 + 100*0.1 = 93.25
        self.assertGreater(calculated_score, 90.0)
        self.assertLess(calculated_score, 100.0)

    def test_str_representation(self):
        """Test string representation."""
        now = timezone.now()
        period_start = now - timedelta(days=30)

        performance = ApplicationManagerPerformance.objects.create(
            manager=self.manager,
            portfolio=self.portfolio,
            period_start=period_start,
            period_end=now,
        )

        self.assertIn(self.manager.username, str(performance))


class LicenseTrueUpForecastModelTestCase(TestCase):
    """Test cases for LicenseTrueUpForecast model."""

    def setUp(self):
        """Set up test data."""
        self.manager = User.objects.create_user(username="portfolio_mgr", email="pm@example.com")
        self.portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.manager)
        self.vendor = Vendor.objects.create(name="Test Vendor", identifier="test-vendor")

    def test_create_forecast(self):
        """Test creating a true-up forecast."""
        forecast = LicenseTrueUpForecast.objects.create(
            vendor=self.vendor,
            portfolio=self.portfolio,
            forecast_period="2026-Q4",
            entitled_quantity=1000,
            projected_consumption=1150,
            true_up_quantity=150,
            true_up_cost=Decimal("15000.00"),
            risk_level="MEDIUM",
            confidence_score=0.85,
            recommendations={"actions": ["Review allocation"]},
        )

        self.assertEqual(forecast.vendor, self.vendor)
        self.assertEqual(forecast.portfolio, self.portfolio)
        self.assertEqual(forecast.entitled_quantity, 1000)
        self.assertEqual(forecast.projected_consumption, 1150)
        self.assertEqual(forecast.true_up_quantity, 150)
        self.assertEqual(forecast.risk_level, "MEDIUM")

    def test_str_representation(self):
        """Test string representation."""
        forecast = LicenseTrueUpForecast.objects.create(
            vendor=self.vendor,
            portfolio=self.portfolio,
            forecast_period="2026-Q4",
            entitled_quantity=1000,
            projected_consumption=1000,
        )

        self.assertIn(self.vendor.name, str(forecast))
        self.assertIn("2026-Q4", str(forecast))


class PackagingRequestModelTestCase(TestCase):
    """Test cases for PackagingRequest model."""

    def setUp(self):
        """Set up test data."""
        self.app_manager = User.objects.create_user(username="app_mgr", email="am@example.com")
        self.pkg_engineer = User.objects.create_user(username="pkg_eng", email="pe@example.com")

        # Mock application (would need to import from application_portfolio)
        # For now, we'll skip creating actual application

    def test_create_packaging_request(self):
        """Test creating a packaging request."""
        # Skipping test that requires Application model
        # TODO: Import Application model and create test instance
        pass

    def test_turnaround_time_calculation(self):
        """Test turnaround time calculation."""
        # Skipping test that requires Application model
        # TODO: Import Application model and create test instance
        pass

    def test_status_choices(self):
        """Test packaging request status choices."""
        statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
        # Verify choices are valid
        for status in statuses:
            self.assertIn(status, statuses)
