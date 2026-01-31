#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""
Create demo data for Portfolio Management.

This script creates:
- Portfolio Managers and Application Managers
- Portfolios with scope and budget
- Application Ownerships
- Performance snapshots
- True-up forecasts
- Packaging requests
"""
import os
import sys
from datetime import timedelta
from decimal import Decimal

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.application_portfolio.models import Application  # noqa: E402
from apps.license_management.models import Vendor  # noqa: E402
from apps.portfolio_management.models import (  # noqa: E402
    ApplicationManagerPerformance,
    ApplicationOwnership,
    LicenseTrueUpForecast,
    PackagingRequest,
    Portfolio,
)

User = get_user_model()


def create_demo_data():  # noqa: C901
    print("\n" + "=" * 60)
    print("Creating Portfolio Management Demo Data")
    print("=" * 60)

    # Create users
    print("\n[1/6] Creating Users...")

    # Portfolio Managers
    pm1, created = User.objects.get_or_create(
        username="sarah_thompson",
        defaults={
            "email": "sarah.thompson@example.com",
            "first_name": "Sarah",
            "last_name": "Thompson",
        },
    )
    if created:
        pm1.set_password("demo123")
        pm1.save()
    print(f"  ✓ Portfolio Manager: {pm1.username}")

    pm2, created = User.objects.get_or_create(
        username="michael_chen",
        defaults={
            "email": "michael.chen@example.com",
            "first_name": "Michael",
            "last_name": "Chen",
        },
    )
    if created:
        pm2.set_password("demo123")
        pm2.save()
    print(f"  ✓ Portfolio Manager: {pm2.username}")

    # Application Managers
    am1, created = User.objects.get_or_create(
        username="jennifer_rodriguez",
        defaults={
            "email": "jennifer.rodriguez@example.com",
            "first_name": "Jennifer",
            "last_name": "Rodriguez",
        },
    )
    if created:
        am1.set_password("demo123")
        am1.save()
    print(f"  ✓ Application Manager: {am1.username}")

    am2, created = User.objects.get_or_create(
        username="david_patel",
        defaults={
            "email": "david.patel@example.com",
            "first_name": "David",
            "last_name": "Patel",
        },
    )
    if created:
        am2.set_password("demo123")
        am2.save()
    print(f"  ✓ Application Manager: {am2.username}")

    # Create Portfolios
    print("\n[2/6] Creating Portfolios...")

    portfolio1, created = Portfolio.objects.get_or_create(
        name="Enterprise Applications",
        defaults={
            "manager": pm1,
            "scope": {
                "business_units": ["IT", "Operations", "Finance"],
                "geographies": ["NA", "EMEA"],
                "sites": ["HQ", "DC-East", "DC-West"],
            },
            "budget_annual": Decimal("2500000.00"),
            "total_applications": 45,
            "total_licenses_entitled": 5000,
            "total_licenses_consumed": 3850,
            "health_score": 87.5,
            "compliance_score": 92.0,
        },
    )
    print(f"  ✓ Portfolio: {portfolio1.name} (Manager: {portfolio1.manager.username})")
    print(f"    - Budget: ${portfolio1.budget_annual:,.2f}")
    print(f"    - Applications: {portfolio1.total_applications}")
    print(f"    - License Utilization: {portfolio1.license_utilization_percent:.1f}%")

    portfolio2, created = Portfolio.objects.get_or_create(
        name="Security & Compliance",
        defaults={
            "manager": pm2,
            "scope": {
                "business_units": ["Security", "Risk", "Legal"],
                "geographies": ["Global"],
                "sites": ["All"],
            },
            "budget_annual": Decimal("1200000.00"),
            "total_applications": 22,
            "total_licenses_entitled": 2000,
            "total_licenses_consumed": 1650,
            "health_score": 94.2,
            "compliance_score": 98.5,
        },
    )
    print(f"  ✓ Portfolio: {portfolio2.name} (Manager: {portfolio2.manager.username})")
    print(f"    - Budget: ${portfolio2.budget_annual:,.2f}")
    print(f"    - Applications: {portfolio2.total_applications}")
    print(f"    - License Utilization: {portfolio2.license_utilization_percent:.1f}%")

    # Create Application Ownerships (if applications exist)
    print("\n[3/6] Creating Application Ownerships...")

    applications = Application.objects.all()[:5]
    if applications.exists():
        for idx, app in enumerate(applications):
            owner = am1 if idx % 2 == 0 else am2
            ownership, created = ApplicationOwnership.objects.get_or_create(
                application=app,
                owner=owner,
                portfolio=portfolio1,
                ownership_type="PRIMARY",
                defaults={
                    "assigned_by": pm1,
                    "assigned_at": timezone.now() - timedelta(days=30),
                    "is_active": True,
                },
            )
            if created:
                print(f"  ✓ {app.name} → {owner.username} (PRIMARY)")
    else:
        print("  ⚠️  No applications found. Skipping ownerships.")

    # Create Performance Snapshots
    print("\n[4/6] Creating Performance Snapshots...")

    now = timezone.now()
    for i in range(3):
        period_end = now - timedelta(days=i * 30)
        period_start = period_end - timedelta(days=30)

        perf1, created = ApplicationManagerPerformance.objects.get_or_create(
            manager=am1,
            portfolio=portfolio1,
            period_start=period_start,
            period_end=period_end,
            defaults={
                "recorded_at": period_end,
                # Deployment metrics
                "deployments_total": 25 - i * 2,
                "deployments_successful": 23 - i * 2,
                "deployments_failed": i,
                "deployments_rolled_back": 1 if i > 0 else 0,
                "success_rate_percent": 92.0 - i,
                "avg_deployment_duration_days": 2.5 + i * 0.3,
                # Health metrics
                "applications_total": 12,
                "applications_healthy": 10 - i,
                "applications_degraded": 1 + i,
                "applications_critical": 1 if i > 1 else 0,
                "avg_health_score": 88.0 - i * 2,
                # License metrics
                "licenses_entitled": 1200,
                "licenses_consumed": 920 + i * 30,
                "licenses_wasted": 280 - i * 30,
                "utilization_percent": 76.5 + i * 2.5,
                # Incident metrics
                "incidents_total": 3 + i,
                "incidents_resolved": 2 + i,
                "avg_mttr_hours": 4.5 + i * 1.5,
                # Composite score
                "composite_score": 85.0 - i * 3,
            },
        )
        if created:
            print(f"  ✓ {am1.username}: Period {i+1} - Score: {perf1.composite_score:.1f}")

    # Create True-Up Forecasts
    print("\n[5/6] Creating License True-Up Forecasts...")

    # Get or create vendors
    vendor_ms, _ = Vendor.objects.get_or_create(identifier="microsoft", defaults={"name": "Microsoft Corporation"})
    vendor_adobe, _ = Vendor.objects.get_or_create(identifier="adobe", defaults={"name": "Adobe Systems"})

    forecast1, created = LicenseTrueUpForecast.objects.get_or_create(
        vendor=vendor_ms,
        portfolio=portfolio1,
        forecast_period="2026-Q4",
        defaults={
            "forecast_horizon_days": 180,
            "entitled_quantity_current": 1000,
            "consumed_quantity_current": 850,
            "utilization_current_percent": 85.0,
            "consumed_quantity_forecast": 1150,
            "consumption_growth_percent": 35.3,
            "additional_licenses_needed": 150,
            "estimated_cost_impact": Decimal("75000.00"),
            "confidence_percent": 87.0,
            "mitigation_recommendations": [
                {
                    "strategy": "right_sizing",
                    "description": "Review over-entitled SKUs and reduce allocation",
                    "licenses_saved": 80,
                    "cost_savings": 40000.00,
                },
                {
                    "strategy": "license_harvesting",
                    "description": "Reclaim unused licenses from inactive users",
                    "licenses_saved": 70,
                    "cost_savings": 35000.00,
                },
            ],
            "potential_savings": Decimal("75000.00"),
        },
    )
    if created:
        print(f"  ✓ {vendor_ms.name} - 2026-Q4")
        print(
            f"    Current: {forecast1.consumed_quantity_current}/{forecast1.entitled_quantity_current} ({forecast1.utilization_current_percent:.1f}%)"  # noqa: E501
        )
        print(
            f"    Forecast: {forecast1.consumed_quantity_forecast} licenses (+{forecast1.consumption_growth_percent:.1f}%)"  # noqa: E501
        )
        print(
            f"    Additional needed: {forecast1.additional_licenses_needed} (${forecast1.estimated_cost_impact:,.2f})"
        )

    forecast2, created = LicenseTrueUpForecast.objects.get_or_create(
        vendor=vendor_adobe,
        portfolio=portfolio1,
        forecast_period="2027-Q1",
        defaults={
            "forecast_horizon_days": 180,
            "entitled_quantity_current": 500,
            "consumed_quantity_current": 380,
            "utilization_current_percent": 76.0,
            "consumed_quantity_forecast": 480,
            "consumption_growth_percent": 26.3,
            "additional_licenses_needed": 0,
            "estimated_cost_impact": Decimal("0.00"),
            "confidence_percent": 92.0,
            "mitigation_recommendations": [
                {
                    "strategy": "monitor",
                    "description": "Continue monitoring consumption trends",
                    "licenses_saved": 0,
                    "cost_savings": 0.00,
                },
            ],
            "potential_savings": Decimal("0.00"),
        },
    )
    if created:
        print(f"  ✓ {vendor_adobe.name} - 2027-Q1")
        print(
            f"    Current: {forecast2.consumed_quantity_current}/{forecast2.entitled_quantity_current} ({forecast2.utilization_current_percent:.1f}%)"  # noqa: E501
        )
        print(f"    Forecast: {forecast2.consumed_quantity_forecast} licenses - Within entitlement")

    # Create Packaging Requests
    print("\n[6/6] Creating Packaging Requests...")

    if applications.exists():
        app = applications.first()

        req1, created = PackagingRequest.objects.get_or_create(
            application=app,
            requested_by=am1,
            priority="HIGH",
            defaults={
                "business_justification": "Critical security update required for compliance",
                "target_platforms": ["Windows", "macOS"],
                "special_requirements": "Must support offline installation for air-gapped sites",
                "status": "IN_PROGRESS",
                "assigned_at": timezone.now() - timedelta(hours=12),
            },
        )
        if created:
            print(f"  ✓ {app.name}: {req1.priority} priority - {req1.status}")

        if len(applications) > 1:
            app2 = applications[1]
            req2, created = PackagingRequest.objects.get_or_create(
                application=app2,
                requested_by=am2,
                priority="NORMAL",
                defaults={
                    "business_justification": "New application deployment for Q1 2026 rollout",
                    "target_platforms": ["Windows"],
                    "special_requirements": "Silent installation with custom configuration",
                    "status": "PENDING",
                },
            )
            if created:
                print(f"  ✓ {app2.name}: {req2.priority} priority - {req2.status}")
    else:
        print("  ⚠️  No applications found. Skipping packaging requests.")

    # Summary
    print("\n" + "=" * 60)
    print("Demo Data Creation Complete!")
    print("=" * 60)
    print("\nCreated:")
    print(
        f"  - {User.objects.filter(username__in=['sarah_thompson', 'michael_chen', 'jennifer_rodriguez', 'david_patel']).count()} Users"  # noqa: E501
    )
    print(f"  - {Portfolio.objects.count()} Portfolios")
    print(f"  - {ApplicationOwnership.objects.count()} Application Ownerships")
    print(f"  - {ApplicationManagerPerformance.objects.count()} Performance Snapshots")
    print(f"  - {LicenseTrueUpForecast.objects.count()} True-Up Forecasts")
    print(f"  - {PackagingRequest.objects.count()} Packaging Requests")

    print("\n📊 Portfolio Summary:")
    for portfolio in Portfolio.objects.all():
        print(f"\n  {portfolio.name}")
        print(f"    Manager: {portfolio.manager.username}")
        print(f"    Budget: ${portfolio.budget_annual:,.2f}")
        print(f"    Applications: {portfolio.total_applications}")
        print(f"    License Utilization: {portfolio.license_utilization_percent:.1f}%")
        print(f"    Health Score: {portfolio.health_score:.1f}")
        print(f"    Compliance Score: {portfolio.compliance_score:.1f}")

    print("\n✅ Demo data is ready for testing!")
    print("\nAccess the API at: http://localhost:8000/api/v1/portfolio-management/")
    print("API Documentation: http://localhost:8000/api/docs/")


if __name__ == "__main__":
    try:
        create_demo_data()
    except Exception as e:
        print(f"\n❌ Error creating demo data: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
