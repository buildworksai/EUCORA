# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Management command to seed default workflow definitions.

Seeds workflow definitions for all agent types from definitions.py.
"""
from django.core.management.base import BaseCommand

from apps.ai_agents.workflows.definitions import WORKFLOW_DEFINITIONS
from apps.ai_agents.workflows.models import WorkflowDefinition


class Command(BaseCommand):
    help = "Seed default workflow definitions for all agent types"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing workflow definitions before seeding",
        )
        parser.add_argument(
            "--agent-type",
            type=str,
            help="Seed workflow for specific agent type only",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("EUCORA Workflow Definitions Seeder"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

        # Clear existing if requested
        if options["clear_existing"]:
            count = WorkflowDefinition.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing workflow definitions"))

        # Filter workflows if agent_type specified
        workflows_to_seed = WORKFLOW_DEFINITIONS
        if options["agent_type"]:
            workflows_to_seed = [w for w in WORKFLOW_DEFINITIONS if w["agent_type"] == options["agent_type"]]
            if not workflows_to_seed:
                self.stdout.write(
                    self.style.ERROR(f"No workflow definition found for agent type: {options['agent_type']}")
                )
                return

        created_count = 0
        updated_count = 0
        _skipped_count = 0  # noqa: F841

        for workflow_def in workflows_to_seed:
            agent_type = workflow_def["agent_type"]
            name = workflow_def["name"]

            # Check if workflow already exists
            existing = WorkflowDefinition.objects.filter(agent_type=agent_type, name=name).first()

            if existing:
                # Update existing workflow
                existing.description = workflow_def.get("description", "")
                existing.steps = workflow_def.get("steps", [])
                existing.required_policies = workflow_def.get("required_policies", [])
                existing.risk_level = workflow_def.get("risk_level", "R2")
                existing.is_active = True
                existing.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Updated: {name} ({agent_type})"))
            else:
                # Create new workflow
                WorkflowDefinition.objects.create(
                    agent_type=agent_type,
                    name=name,
                    description=workflow_def.get("description", ""),
                    steps=workflow_def.get("steps", []),
                    required_policies=workflow_def.get("required_policies", []),
                    risk_level=workflow_def.get("risk_level", "R2"),
                    is_active=True,
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {name} ({agent_type})"))

        # Summary
        self.stdout.write("\n" + self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("Summary:"))
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated_count}"))
        self.stdout.write(
            self.style.SUCCESS(f"  Total workflows: {WorkflowDefinition.objects.filter(is_active=True).count()}")
        )
        self.stdout.write(self.style.SUCCESS("=" * 70))
