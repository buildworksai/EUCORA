# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for Portfolio Management services.

Tests business logic for performance calculation, metrics aggregation, and forecasting.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.license_management.models import Vendor
from apps.portfolio_management.models import Portfolio
from apps.portfolio_management.services.forecasting import (
    _calculate_true_up_cost,
    _determine_risk_level,
    generate_license_true_up_forecast,
)
from apps.portfolio_management.services.metrics import aggregate_portfolio_metrics, refresh_portfolio_metrics
from apps.portfolio_management.services.performance import _calculate_composite_score, calculate_manager_performance

User = get_user_model()


class PerformanceServiceTestCase(TestCase):
    """Test cases for performance calculation service."""

    def setUp(self):
        """Set up test data."""
        self.manager = User.objects.create_user(username="app_mgr", email="am@example.com")
        self.portfolio_mgr = User.objects.create_user(username="portfolio_mgr", email="pm@example.com")
        self.portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.portfolio_mgr)

    def test_calculate_composite_score_optimal(self):
        """Test composite score calculation with optimal metrics."""
        metrics = {
            "success_rate_percent": 100.0,
            "avg_health_score": 100.0,
            "utilization_percent": 77.5,  # Optimal
            "avg_deployment_duration_days": 1.0,  # Optimal
            "health_incidents": 0,  # Optimal
        }

        score = _calculate_composite_score(metrics)

        # Should be near 100 with optimal metrics
        self.assertGreater(score, 95.0)
        self.assertLessEqual(score, 100.0)

    def test_calculate_composite_score_poor(self):
        """Test composite score calculation with poor metrics."""
        metrics = {
            "success_rate_percent": 50.0,
            "avg_health_score": 50.0,
            "utilization_percent": 150.0,  # Over-utilized
            "avg_deployment_duration_days": 14.0,  # Slow
            "health_incidents": 10,  # Many incidents
        }

        score = _calculate_composite_score(metrics)

        # Should be low with poor metrics
        self.assertLess(score, 60.0)

    def test_calculate_composite_score_license_utilization_normalization(self):
        """Test license utilization normalization in composite score."""
        # Optimal utilization (70-85%)
        metrics_optimal = {
            "success_rate_percent": 100.0,
            "avg_health_score": 100.0,
            "utilization_percent": 77.5,
            "avg_deployment_duration_days": 1.0,
            "health_incidents": 0,
        }

        # Under-utilized (< 70%)
        metrics_under = {**metrics_optimal, "utilization_percent": 50.0}

        # Over-utilized (> 85%)
        metrics_over = {**metrics_optimal, "utilization_percent": 150.0}

        score_optimal = _calculate_composite_score(metrics_optimal)
        score_under = _calculate_composite_score(metrics_under)
        score_over = _calculate_composite_score(metrics_over)

        # Optimal should be highest
        self.assertGreater(score_optimal, score_under)
        self.assertGreater(score_optimal, score_over)

    def test_calculate_manager_performance(self):
        """Test manager performance calculation."""
        now = timezone.now()
        period_start = now - timedelta(days=30)

        metrics = calculate_manager_performance(self.manager, self.portfolio, period_start, now)

        # Verify structure
        self.assertEqual(metrics["manager"], self.manager)
        self.assertEqual(metrics["portfolio"], self.portfolio)
        self.assertEqual(metrics["period_start"], period_start)
        self.assertEqual(metrics["period_end"], now)
        self.assertIn("composite_score", metrics)
        self.assertIn("deployments_total", metrics)


class MetricsServiceTestCase(TestCase):
    """Test cases for metrics aggregation service."""

    def setUp(self):
        """Set up test data."""
        self.manager = User.objects.create_user(username="portfolio_mgr", email="pm@example.com")
        self.portfolio = Portfolio.objects.create(
            name="Test Portfolio",
            manager=self.manager,
            total_applications=5,
            total_licenses_entitled=100,
            total_licenses_consumed=75,
        )

    def test_aggregate_portfolio_metrics(self):
        """Test portfolio metrics aggregation."""
        metrics = aggregate_portfolio_metrics(self.portfolio)

        # Verify structure
        self.assertIn("total_applications", metrics)
        self.assertIn("total_licenses_entitled", metrics)
        self.assertIn("total_licenses_consumed", metrics)
        self.assertIn("health_score", metrics)
        self.assertIn("compliance_score", metrics)

    def test_refresh_portfolio_metrics(self):
        """Test refreshing portfolio cached metrics."""
        # Set initial values
        self.portfolio.total_applications = 0
        self.portfolio.save()

        # Refresh metrics
        refreshed = refresh_portfolio_metrics(self.portfolio)

        # Verify updated
        self.assertIsNotNone(refreshed)
        self.assertEqual(refreshed.id, self.portfolio.id)


class ForecastingServiceTestCase(TestCase):
    """Test cases for license true-up forecasting service."""

    def setUp(self):
        """Set up test data."""
        self.manager = User.objects.create_user(username="portfolio_mgr", email="pm@example.com")
        self.portfolio = Portfolio.objects.create(name="Test Portfolio", manager=self.manager)
        self.vendor = Vendor.objects.create(name="Test Vendor", identifier="test-vendor")

    def test_determine_risk_level_low(self):
        """Test risk level determination for low true-up."""
        risk = _determine_risk_level(true_up_quantity=50, entitled_quantity=1000)
        self.assertEqual(risk, "LOW")

    def test_determine_risk_level_medium(self):
        """Test risk level determination for medium true-up."""
        risk = _determine_risk_level(true_up_quantity=150, entitled_quantity=1000)
        self.assertEqual(risk, "MEDIUM")

    def test_determine_risk_level_high(self):
        """Test risk level determination for high true-up."""
        risk = _determine_risk_level(true_up_quantity=350, entitled_quantity=1000)
        self.assertEqual(risk, "HIGH")

    def test_determine_risk_level_critical(self):
        """Test risk level determination for critical true-up."""
        risk = _determine_risk_level(true_up_quantity=600, entitled_quantity=1000)
        self.assertEqual(risk, "CRITICAL")

    def test_calculate_true_up_cost(self):
        """Test true-up cost calculation."""
        cost = _calculate_true_up_cost(self.vendor, true_up_quantity=100)

        # Should return a Decimal value
        self.assertIsInstance(cost, Decimal)
        self.assertGreater(cost, Decimal("0.00"))

    def test_generate_forecast(self):
        """Test generating a complete forecast."""
        forecast = generate_license_true_up_forecast(
            vendor=self.vendor,
            portfolio=self.portfolio,
            forecast_period="2026-Q4",
            entitled_quantity=1000,
        )

        # Verify forecast was created
        self.assertIsNotNone(forecast.id)
        self.assertEqual(forecast.vendor, self.vendor)
        self.assertEqual(forecast.portfolio, self.portfolio)
        self.assertEqual(forecast.forecast_period, "2026-Q4")
        self.assertEqual(forecast.entitled_quantity, 1000)
        self.assertIn(forecast.risk_level, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.assertIsInstance(forecast.recommendations, dict)
