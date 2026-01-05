# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Management command to seed demo data for EUCORA.

Creates:
- 20,000+ assets (devices)
- 2,000+ applications
- Deployment intents with various states
- CAB approvals
- Events
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import uuid
from apps.connectors.models import Asset, Application
from apps.deployment_intents.models import DeploymentIntent, RingDeployment
from apps.evidence_store.models import EvidencePack
from apps.cab_workflow.models import CABApproval
from apps.event_store.models import DeploymentEvent


class Command(BaseCommand):
    help = 'Seed database with demo data (20k+ assets, 2k+ applications)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assets',
            type=int,
            default=20000,
            help='Number of assets to create (default: 20000)',
        )
        parser.add_argument(
            '--applications',
            type=int,
            default=2000,
            help='Number of applications to create (default: 2000)',
        )
        parser.add_argument(
            '--deployments',
            type=int,
            default=500,
            help='Number of deployment intents to create (default: 500)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        assets_count = options['assets']
        applications_count = options['applications']
        deployments_count = options['deployments']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Asset.objects.all().delete()
            Application.objects.all().delete()
            DeploymentIntent.objects.all().delete()
            EvidencePack.objects.all().delete()
            CABApproval.objects.all().delete()
            DeploymentEvent.objects.all().delete()

        # Get or create admin user
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@eucora.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )

        # Seed Applications
        self.stdout.write(self.style.SUCCESS(f'Creating {applications_count} applications...'))
        self._seed_applications(applications_count)

        # Seed Assets
        self.stdout.write(self.style.SUCCESS(f'Creating {assets_count} assets...'))
        self._seed_assets(assets_count)

        # Seed Deployments
        self.stdout.write(self.style.SUCCESS(f'Creating {deployments_count} deployment intents...'))
        applications = list(Application.objects.all())
        self._seed_deployments(deployments_count, applications, admin_user)

        self.stdout.write(self.style.SUCCESS('Demo data seeding completed!'))

    def _seed_applications(self, count):
        """Create applications with realistic names and versions."""
        applications_data = [
            # Productivity
            ('Microsoft Office', 'Microsoft', 'Productivity', 'Windows'),
            ('Google Workspace', 'Google', 'Productivity', 'Multi-Platform'),
            ('Adobe Acrobat Reader', 'Adobe', 'Productivity', 'Multi-Platform'),
            ('Slack', 'Slack Technologies', 'Communication', 'Multi-Platform'),
            ('Microsoft Teams', 'Microsoft', 'Communication', 'Multi-Platform'),
            ('Zoom', 'Zoom Video Communications', 'Communication', 'Multi-Platform'),
            # Security
            ('CrowdStrike Falcon', 'CrowdStrike', 'Security', 'Multi-Platform'),
            ('Microsoft Defender', 'Microsoft', 'Security', 'Windows'),
            ('Symantec Endpoint Protection', 'Broadcom', 'Security', 'Windows'),
            ('Okta Verify', 'Okta', 'Security', 'Mobile'),
            # Development
            ('Visual Studio Code', 'Microsoft', 'Development', 'Multi-Platform'),
            ('Git', 'Git', 'Development', 'Multi-Platform'),
            ('Docker Desktop', 'Docker', 'Development', 'Multi-Platform'),
            ('Postman', 'Postman', 'Development', 'Multi-Platform'),
            # Browsers
            ('Google Chrome', 'Google', 'Browser', 'Multi-Platform'),
            ('Microsoft Edge', 'Microsoft', 'Browser', 'Windows'),
            ('Mozilla Firefox', 'Mozilla', 'Browser', 'Multi-Platform'),
            # Media
            ('Adobe Photoshop', 'Adobe', 'Media', 'Multi-Platform'),
            ('VLC Media Player', 'VideoLAN', 'Media', 'Multi-Platform'),
            # Enterprise
            ('SAP GUI', 'SAP', 'Enterprise', 'Windows'),
            ('Oracle Client', 'Oracle', 'Enterprise', 'Windows'),
            ('VMware Horizon Client', 'VMware', 'Enterprise', 'Multi-Platform'),
        ]

        platforms = ['Windows', 'macOS', 'Linux', 'Mobile', 'Multi-Platform']
        categories = ['Productivity', 'Security', 'Development', 'Media', 'Browser', 'Communication', 'Utility', 'Enterprise']
        
        applications_created = []
        batch_size = 1000
        
        for i in range(count):
            if i < len(applications_data):
                name, vendor, category, platform = applications_data[i]
                version = f"{random.randint(1, 30)}.{random.randint(0, 99)}.{random.randint(0, 9999)}"
            else:
                # Generate random application names
                name = f"Application-{random.choice(['Pro', 'Enterprise', 'Standard', 'Lite'])}-{i}"
                vendor = random.choice(['Microsoft', 'Google', 'Adobe', 'Oracle', 'VMware', 'Custom Vendor'])
                category = random.choice(categories)
                platform = random.choice(platforms)
                version = f"{random.randint(1, 30)}.{random.randint(0, 99)}.{random.randint(0, 9999)}"
            
            app = Application(
                name=name,
                vendor=vendor,
                version=version,
                platform=platform,
                category=category,
                description=f"{name} version {version} for {platform}",
                default_risk_score=random.randint(10, 70),
            )
            applications_created.append(app)
            
            if len(applications_created) >= batch_size:
                Application.objects.bulk_create(applications_created, ignore_conflicts=True)
                applications_created = []
                self.stdout.write(f'  Created {min((i + 1), count)}/{count} applications...')
        
        if applications_created:
            Application.objects.bulk_create(applications_created, ignore_conflicts=True)

    def _seed_assets(self, count):
        """Create assets with realistic data."""
        asset_types = ['Laptop', 'Desktop', 'Virtual Machine', 'Mobile', 'Server']
        os_versions = {
            'Laptop': ['Windows 11', 'Windows 10', 'macOS Sonoma', 'macOS Ventura', 'Ubuntu 22.04'],
            'Desktop': ['Windows 11', 'Windows 10', 'Ubuntu 22.04'],
            'Virtual Machine': ['Windows Server 2022', 'Ubuntu 22.04', 'RHEL 9'],
            'Mobile': ['iOS 17', 'iOS 16', 'Android 14', 'Android 13'],
            'Server': ['Windows Server 2022', 'Ubuntu 22.04', 'RHEL 9'],
        }
        statuses = ['Active', 'Active', 'Active', 'Active', 'Inactive', 'Maintenance', 'Retired']  # Weighted
        locations = [
            'New York Office', 'San Francisco Office', 'London Office', 'Tokyo Office',
            'Remote - US', 'Remote - EU', 'Remote - APAC', 'Data Center - East',
            'Data Center - West', 'Cloud - AWS', 'Cloud - Azure',
        ]
        connectors = ['intune', 'jamf', 'sccm', 'landscape', 'ansible']
        
        assets_created = []
        batch_size = 1000
        
        for i in range(count):
            asset_type = random.choice(asset_types)
            os = random.choice(os_versions.get(asset_type, ['Windows 11']))
            status = random.choice(statuses)
            
            # Determine connector based on OS
            if 'Windows' in os:
                connector = random.choice(['intune', 'sccm'])
            elif 'macOS' in os or 'iOS' in os:
                connector = random.choice(['jamf'])
            else:
                connector = random.choice(['landscape', 'ansible'])
            
            asset = Asset(
                name=f"{asset_type[:3].upper()}-{random.randint(1000, 9999)}-{i:05d}",
                asset_id=f"AST-{i:06d}",
                serial_number=f"SN{random.randint(100000, 999999)}",
                type=asset_type,
                os=os,
                status=status,
                location=random.choice(locations),
                owner=f"user{random.randint(1, 500)}@eucora.com",
                ip_address=f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}" if status == 'Active' else None,
                disk_encryption=random.choice([True, True, True, False]),  # Weighted
                firewall_enabled=random.choice([True, True, False]),  # Weighted
                compliance_score=random.randint(60, 100) if status == 'Active' else random.randint(0, 60),
                last_checkin=timezone.now() - timedelta(hours=random.randint(0, 72)) if status == 'Active' else None,
                dex_score=round(random.uniform(6.0, 9.5), 1) if status == 'Active' else None,
                boot_time=random.randint(15, 120) if status == 'Active' else None,
                carbon_footprint=round(random.uniform(50.0, 300.0), 2),
                user_sentiment=random.choice(['Positive', 'Positive', 'Neutral', 'Neutral', 'Negative']) if status == 'Active' else None,
                connector_type=connector,
                connector_object_id=f"{connector.upper()}-{random.randint(100000, 999999)}",
            )
            assets_created.append(asset)
            
            if len(assets_created) >= batch_size:
                Asset.objects.bulk_create(assets_created, ignore_conflicts=True)
                assets_created = []
                self.stdout.write(f'  Created {min((i + 1), count)}/{count} assets...')
        
        if assets_created:
            Asset.objects.bulk_create(assets_created, ignore_conflicts=True)

    def _seed_deployments(self, count, applications, user):
        """Create deployment intents with various states."""
        statuses = [
            'PENDING', 'AWAITING_CAB', 'APPROVED', 'DEPLOYING', 'COMPLETED',
            'COMPLETED', 'COMPLETED', 'FAILED', 'ROLLED_BACK',
        ]
        rings = ['LAB', 'CANARY', 'PILOT', 'DEPARTMENT', 'GLOBAL']
        
        deployments_created = []
        evidence_packs_created = []
        cab_approvals_created = []
        events_created = []
        batch_size = 100
        
        for i in range(count):
            app = random.choice(applications)
            status = random.choice(statuses)
            ring = random.choice(rings)
            
            # Create evidence pack
            evidence_correlation_id = uuid.uuid4()
            evidence_pack = EvidencePack(
                correlation_id=evidence_correlation_id,
                app_name=app.name,
                version=app.version,
                artifact_hash=f"{''.join(random.choices('0123456789abcdef', k=64))}",
                artifact_path=f"artifacts/{app.name.replace(' ', '-')}/{app.version}/{evidence_correlation_id}.pkg",
                sbom_data={'format': 'SPDX', 'components': []},
                vulnerability_scan_results={'critical': 0, 'high': random.randint(0, 3), 'medium': random.randint(0, 10)},
                rollback_plan=f"Rollback plan for {app.name} {app.version}",
                is_validated=status not in ['PENDING', 'AWAITING_CAB'],
            )
            evidence_packs_created.append(evidence_pack)
            
            # Calculate risk score
            risk_score = app.default_risk_score + random.randint(-10, 20)
            risk_score = max(0, min(100, risk_score))
            requires_cab = risk_score > 50
            
            # Create deployment intent
            deployment = DeploymentIntent(
                correlation_id=uuid.uuid4(),
                app_name=app.name,
                version=app.version,
                target_ring=ring,
                status=status,
                evidence_pack_id=evidence_correlation_id,
                risk_score=risk_score,
                requires_cab_approval=requires_cab,
                submitter=user,
            )
            deployments_created.append(deployment)
            
            # Create CAB approval if needed
            if requires_cab and status in ['AWAITING_CAB', 'APPROVED', 'REJECTED']:
                decision = 'APPROVED' if status == 'APPROVED' else ('REJECTED' if status == 'REJECTED' else 'PENDING')
                cab_approval = CABApproval(
                    deployment_intent=deployment,
                    decision=decision,
                    approver=user if decision != 'PENDING' else None,
                    comments=f"CAB review for {app.name} {app.version}",
                    reviewed_at=timezone.now() if decision != 'PENDING' else None,
                )
                cab_approvals_created.append(cab_approval)
            
            # Create events
            event_types = {
                'PENDING': 'DEPLOYMENT_CREATED',
                'AWAITING_CAB': 'CAB_SUBMITTED',
                'APPROVED': 'CAB_APPROVED',
                'REJECTED': 'CAB_REJECTED',
                'DEPLOYING': 'DEPLOYMENT_STARTED',
                'COMPLETED': 'DEPLOYMENT_COMPLETED',
                'FAILED': 'DEPLOYMENT_FAILED',
                'ROLLED_BACK': 'ROLLBACK_COMPLETED',
            }
            event = DeploymentEvent(
                correlation_id=deployment.correlation_id,
                event_type=event_types.get(status, 'DEPLOYMENT_CREATED'),
                event_data={'app_name': app.name, 'version': app.version, 'ring': ring},
                actor=user.username,
            )
            events_created.append(event)
            
            if len(deployments_created) >= batch_size:
                # Bulk create evidence packs first
                EvidencePack.objects.bulk_create(evidence_packs_created, ignore_conflicts=True)
                evidence_packs_created = []
                
                # Bulk create deployments (must be saved before CAB approvals)
                DeploymentIntent.objects.bulk_create(deployments_created, ignore_conflicts=True)
                
                # Now create CAB approvals with saved deployment references
                # We need to fetch the created deployments to link CAB approvals
                deployment_ids = [d.correlation_id for d in deployments_created]
                created_deployments = {d.correlation_id: d for d in DeploymentIntent.objects.filter(correlation_id__in=deployment_ids)}
                
                # Update CAB approvals with saved deployment references
                for cab_approval in cab_approvals_created:
                    deployment = created_deployments.get(cab_approval.deployment_intent.correlation_id)
                    if deployment:
                        cab_approval.deployment_intent = deployment
                
                if cab_approvals_created:
                    CABApproval.objects.bulk_create(cab_approvals_created, ignore_conflicts=True)
                    cab_approvals_created = []
                
                # Bulk create events
                DeploymentEvent.objects.bulk_create(events_created, ignore_conflicts=True)
                events_created = []
                
                deployments_created = []
                self.stdout.write(f'  Created {min((i + 1), count)}/{count} deployments...')
        
        # Create remaining
        if evidence_packs_created:
            EvidencePack.objects.bulk_create(evidence_packs_created, ignore_conflicts=True)
        if deployments_created:
            DeploymentIntent.objects.bulk_create(deployments_created, ignore_conflicts=True)
            
            # Create CAB approvals for remaining deployments
            if cab_approvals_created:
                deployment_ids = [d.correlation_id for d in deployments_created]
                created_deployments = {d.correlation_id: d for d in DeploymentIntent.objects.filter(correlation_id__in=deployment_ids)}
                for cab_approval in cab_approvals_created:
                    deployment = created_deployments.get(cab_approval.deployment_intent.correlation_id)
                    if deployment:
                        cab_approval.deployment_intent = deployment
                CABApproval.objects.bulk_create(cab_approvals_created, ignore_conflicts=True)
        if events_created:
            DeploymentEvent.objects.bulk_create(events_created, ignore_conflicts=True)

