# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Management command to seed comprehensive demo data for EUCORA.

Seeds all modules in correct dependency order:
1. Core data (users, applications, assets, deployments)
2. License Management (vendors, entitlements, consumption)
3. Portfolio Management (portfolios, ownerships, performance, forecasts)
"""
from django.core.management.base import BaseCommand

from apps.core.demo_data import seed_demo_data
from apps.core.seed_license_data import seed_license_management_data
from apps.core.seed_portfolio_data import seed_portfolio_management_data


class Command(BaseCommand):
    help = "Seed comprehensive demo data for all EUCORA modules"

    def add_arguments(self, parser):
        # Core data arguments
        parser.add_argument("--assets", type=int, default=20000, help="Number of assets to create")
        parser.add_argument("--applications", type=int, default=500, help="Number of applications to create")
        parser.add_argument("--deployments", type=int, default=100, help="Number of deployments to create")
        parser.add_argument("--users", type=int, default=100, help="Number of demo users to create")
        parser.add_argument("--events", type=int, default=1000, help="Number of deployment events to create")

        # Control arguments
        parser.add_argument("--clear-existing", action="store_true", help="Clear existing demo data before seeding")
        parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for bulk inserts")

        # Module selection arguments
        parser.add_argument("--skip-core", action="store_true", help="Skip core data seeding")
        parser.add_argument("--skip-licenses", action="store_true", help="Skip license management seeding")
        parser.add_argument("--skip-portfolios", action="store_true", help="Skip portfolio management seeding")

    def handle(self, *args, **options):  # noqa: C901
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("EUCORA Comprehensive Demo Data Seeder"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

        all_results = {}

        # Step 1: Core data (users, applications, assets, deployments, events)
        if not options["skip_core"]:
            self.stdout.write("\n" + self.style.WARNING("[1/3] Seeding Core Data..."))
            try:
                core_results = seed_demo_data(
                    assets=options["assets"],
                    applications=options["applications"],
                    deployments=options["deployments"],
                    users=options["users"],
                    events=options["events"],
                    clear_existing=options["clear_existing"],
                    batch_size=options["batch_size"],
                )
                all_results["core"] = core_results
                self.stdout.write(self.style.SUCCESS("✓ Core data seeded successfully"))
                for key, value in core_results.items():
                    self.stdout.write(f"  - {key}: {value}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error seeding core data: {e}"))

        # Step 2: License Management (requires applications to exist)
        if not options["skip_licenses"]:
            self.stdout.write("\n" + self.style.WARNING("[2/3] Seeding License Management Data..."))
            try:
                license_results = seed_license_management_data(clear_existing=options["clear_existing"])
                all_results["licenses"] = license_results
                self.stdout.write(self.style.SUCCESS("✓ License data seeded successfully"))
                for key, value in license_results.items():
                    self.stdout.write(f"  - {key}: {value}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error seeding license data: {e}"))

        # Step 3: Portfolio Management (requires users, applications, vendors)
        if not options["skip_portfolios"]:
            self.stdout.write("\n" + self.style.WARNING("[3/3] Seeding Portfolio Management Data..."))
            try:
                portfolio_results = seed_portfolio_management_data(clear_existing=options["clear_existing"])
                all_results["portfolios"] = portfolio_results
                self.stdout.write(self.style.SUCCESS("✓ Portfolio data seeded successfully"))
                for key, value in portfolio_results.items():
                    self.stdout.write(f"  - {key}: {value}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error seeding portfolio data: {e}"))

        # Summary
        self.stdout.write("\n" + self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("✓ Demo data seeding completed"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
