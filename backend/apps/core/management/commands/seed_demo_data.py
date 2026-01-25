# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Management command to seed demo data for EUCORA.
"""
from django.core.management.base import BaseCommand

from apps.core.demo_data import seed_demo_data


class Command(BaseCommand):
    help = "Seed database with demo data (assets, applications, deployments, events)"

    def add_arguments(self, parser):
        parser.add_argument("--assets", type=int, default=50000, help="Number of assets to create")
        parser.add_argument("--applications", type=int, default=5000, help="Number of applications to create")
        parser.add_argument("--deployments", type=int, default=10000, help="Number of deployments to create")
        parser.add_argument("--users", type=int, default=1000, help="Number of demo users to create")
        parser.add_argument("--events", type=int, default=100000, help="Number of deployment events to create")
        parser.add_argument("--clear-existing", action="store_true", help="Clear existing demo data before seeding")
        parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for bulk inserts")

    def handle(self, *args, **options):
        results = seed_demo_data(
            assets=options["assets"],
            applications=options["applications"],
            deployments=options["deployments"],
            users=options["users"],
            events=options["events"],
            clear_existing=options["clear_existing"],
            batch_size=options["batch_size"],
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeding completed."))
        for key, value in results.items():
            self.stdout.write(f"  {key}: {value}")
