# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Portfolio Management Demo Data Seeder

Seeds:
- Portfolios
- Application Ownerships
- Performance Snapshots
- True-Up Forecasts
- Packaging Requests
"""
import logging
import random
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def seed_portfolio_management_data(clear_existing: bool = False) -> dict:  # noqa: C901
    """
    Seed portfolio management demo data.

    Returns:
        Dictionary with seeding statistics
    """
    from django.contrib.auth import get_user_model

    from apps.application_portfolio.models import Application
    from apps.license_management.models import Vendor
    from apps.portfolio_management.models import (
        ApplicationManagerPerformance,
        ApplicationOwnership,
        LicenseTrueUpForecast,
        PackagingRequest,
        Portfolio,
    )

    User = get_user_model()

    stats = {
        "users": 0,
        "portfolios": 0,
        "ownerships": 0,
        "performance_snapshots": 0,
        "forecasts": 0,
        "packaging_requests": 0,
    }

    try:
        if clear_existing:
            logger.info("Clearing existing portfolio data...")
            with transaction.atomic():
                # Clear demo-specific data by identifying patterns
                PackagingRequest.objects.filter(
                    requested_by__username__in=["jennifer_rodriguez", "michael_chen"]
                ).delete()
                LicenseTrueUpForecast.objects.filter(forecast_period="Q2_2026").delete()
                ApplicationManagerPerformance.objects.all().delete()  # No is_demo flag
                ApplicationOwnership.objects.all().delete()  # No is_demo flag
                Portfolio.objects.all().delete()  # No is_demo flag
            logger.info("Portfolio data cleared")

        # Create users
        logger.info("Creating portfolio users...")
        users_data = [
            {
                "username": "sarah_thompson",
                "email": "sarah.thompson@example.com",
                "first_name": "Sarah",
                "last_name": "Thompson",
            },
            {
                "username": "jennifer_rodriguez",
                "email": "jennifer.rodriguez@example.com",
                "first_name": "Jennifer",
                "last_name": "Rodriguez",
            },
            {
                "username": "michael_chen",
                "email": "michael.chen@example.com",
                "first_name": "Michael",
                "last_name": "Chen",
            },
            {
                "username": "emily_watson",
                "email": "emily.watson@example.com",
                "first_name": "Emily",
                "last_name": "Watson",
            },
        ]

        users = {}
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data["username"], defaults={**user_data, "is_staff": True}
            )
            users[user_data["username"]] = user
            stats["users"] += 1

        logger.info(f"Created/updated {stats['users']} users")

        # Create portfolios
        logger.info("Creating portfolios...")
        portfolio1, _ = Portfolio.objects.get_or_create(
            name="North America Portfolio",
            defaults={
                "manager": users["sarah_thompson"],
                "scope": {
                    "business_units": ["Corporate IT", "Finance", "HR"],
                    "geographies": ["US", "Canada"],
                    "sites": ["New York HQ", "Toronto Office", "San Francisco"],
                },
                "budget_annual": Decimal("2500000.00"),
            },
        )

        portfolio2, _ = Portfolio.objects.get_or_create(
            name="EMEA Portfolio",
            defaults={
                "manager": users["sarah_thompson"],
                "scope": {
                    "business_units": ["Sales", "Marketing", "Engineering"],
                    "geographies": ["UK", "Germany", "France"],
                    "sites": ["London Office", "Berlin Office", "Paris Office"],
                },
                "budget_annual": Decimal("1200000.00"),
            },
        )

        stats["portfolios"] = 2
        logger.info(f"Created {stats['portfolios']} portfolios")

        # Create application ownerships (requires applications)
        applications = list(Application.objects.all()[:20])

        if applications:
            logger.info(f"Creating application ownerships for {len(applications)} applications...")

            for i, app in enumerate(applications):
                owner = users["jennifer_rodriguez"] if i % 2 == 0 else users["michael_chen"]
                portfolio = portfolio1 if i % 2 == 0 else portfolio2

                ApplicationOwnership.objects.get_or_create(
                    application=app,
                    owner=owner,
                    ownership_type="PRIMARY",
                    defaults={
                        "portfolio": portfolio,
                        "assigned_by": users["sarah_thompson"],
                        "assigned_at": timezone.now(),
                        "is_active": True,
                    },
                )
                stats["ownerships"] += 1

            logger.info(f"Created {stats['ownerships']} ownerships")

        # Create performance snapshots
        logger.info("Creating performance snapshots...")
        base_date = timezone.now() - timedelta(days=150)

        for month in range(6):
            date = base_date + timedelta(days=30 * month)

            # Simulate improving performance over time
            improvement_factor = 1.0 + (month * 0.05)

            ApplicationManagerPerformance.objects.get_or_create(
                manager=users["jennifer_rodriguez"],
                portfolio=portfolio1,
                period_start=date,
                period_end=date + timedelta(days=30),
                defaults={
                    "recorded_at": date + timedelta(days=30),
                    "deployments_total": int(random.randint(15, 25) * improvement_factor),
                    "deployments_successful": int(random.randint(13, 23) * improvement_factor),
                    "deployments_failed": random.randint(0, 2),
                    "deployments_rolled_back": random.randint(0, 1),
                    "success_rate_percent": 90.0 + (month * 1.5),
                    "avg_deployment_duration_days": max(3.0, 7.0 - (month * 0.5)),
                    "applications_total": 10,
                    "applications_healthy": 8 + month // 2,
                    "avg_health_score": 80.0 + (month * 2.0),
                    "licenses_entitled": 1000,
                    "licenses_consumed": 850 + (month * 10),
                    "licenses_wasted": 150 - (month * 10),
                    "utilization_percent": 85.0 + (month * 1.0),
                    "incidents_total": max(1, 5 - month),
                    "incidents_resolved": max(1, 5 - month),
                    "avg_mttr_hours": max(1.0, 4.0 - (month * 0.5)),
                    "composite_score": 75.0 + (month * 3.0),
                },
            )
            stats["performance_snapshots"] += 1

        logger.info(f"Created {stats['performance_snapshots']} performance snapshots")

        # Create true-up forecasts
        vendors = list(Vendor.objects.filter(identifier__startswith="DEMO_")[:2])

        if vendors:
            logger.info("Creating license true-up forecasts...")

            # Microsoft forecast - over-entitled scenario
            LicenseTrueUpForecast.objects.get_or_create(
                vendor=vendors[0],
                portfolio=portfolio1,
                forecast_period="Q2_2026",
                defaults={
                    "forecast_horizon_days": 180,
                    "entitled_quantity_current": 5000,
                    "consumed_quantity_current": 4250,
                    "utilization_current_percent": 85.0,
                    "consumed_quantity_forecast": 5350,
                    "consumption_growth_percent": 25.9,
                    "additional_licenses_needed": 350,
                    "estimated_cost_impact": Decimal("75000.00"),
                    "confidence_percent": 87.5,
                    "mitigation_recommendations": [
                        {
                            "strategy": "right_sizing",
                            "description": "Identify and reclaim licenses from inactive users",
                            "licenses_saved": 150,
                            "cost_savings": 32000.00,
                        },
                        {
                            "strategy": "license_harvesting",
                            "description": "Implement automated license reclamation for 90-day inactive accounts",
                            "licenses_saved": 100,
                            "cost_savings": 21000.00,
                        },
                    ],
                    "potential_savings": Decimal("53000.00"),
                },
            )

            # VMware forecast - within entitlement
            if len(vendors) > 1:
                LicenseTrueUpForecast.objects.get_or_create(
                    vendor=vendors[1],
                    portfolio=portfolio1,
                    forecast_period="Q2_2026",
                    defaults={
                        "forecast_horizon_days": 180,
                        "entitled_quantity_current": 200,
                        "consumed_quantity_current": 165,
                        "utilization_current_percent": 82.5,
                        "consumed_quantity_forecast": 185,
                        "consumption_growth_percent": 12.1,
                        "additional_licenses_needed": 0,
                        "estimated_cost_impact": Decimal("0.00"),
                        "confidence_percent": 92.0,
                        "mitigation_recommendations": [],
                        "potential_savings": Decimal("0.00"),
                    },
                )

            stats["forecasts"] = 2
            logger.info(f"Created {stats['forecasts']} forecasts")

        # Create packaging requests
        if applications:
            logger.info("Creating packaging requests...")

            # Sample requests
            for i in range(3):
                app = applications[i % len(applications)]
                version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}"

                PackagingRequest.objects.get_or_create(
                    application=app,
                    version_identifier=version,
                    requested_by=users["jennifer_rodriguez"],
                    defaults={
                        "priority": random.choice(["HIGH", "MEDIUM", "LOW"]),
                        "requirements": {
                            "platforms": ["Windows", "macOS"],
                            "signing_required": True,
                            "detection_rules": {"type": "registry", "key": f"HKLM\\Software\\{app.name}"},
                            "notes": "Silent install required, no reboot",
                        },
                        "notes": f"Critical update required for {app.name}",
                        "status": random.choice(["PENDING", "IN_PROGRESS", "COMPLETED"]),
                        "assigned_to": users["emily_watson"] if i % 2 == 0 else None,
                        "assigned_at": timezone.now() if i % 2 == 0 else None,
                        "completed_at": timezone.now() if i == 0 else None,
                    },
                )
                stats["packaging_requests"] += 1

            logger.info(f"Created {stats['packaging_requests']} packaging requests")

        logger.info("Portfolio management demo data seeded successfully")
        return stats

    except Exception as e:
        logger.error(f"Error seeding portfolio data: {e}", exc_info=True)
        return stats
