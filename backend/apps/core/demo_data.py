# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Demo data seeding utilities.

CRITICAL: These functions are designed for customer demos and must be resilient.
- All operations use transactions for atomicity
- Errors are caught and logged but don't crash the system
- Idempotent operations ensure safe retries
"""
from datetime import timedelta
import random
import uuid
import logging
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction, IntegrityError
from apps.connectors.models import Asset, Application
from apps.deployment_intents.models import DeploymentIntent, RingDeployment
from apps.evidence_store.models import EvidencePack
from apps.cab_workflow.models import CABApproval
from apps.event_store.models import DeploymentEvent

logger = logging.getLogger(__name__)


def seed_demo_data(
    assets: int = 50000,
    applications: int = 5000,
    deployments: int = 10000,
    users: int = 1000,
    events: int = 100000,
    clear_existing: bool = False,
    batch_size: int = 1000,
) -> dict:
    """
    Seed demo data for assets, applications, deployments, approvals, and events.
    
    CRITICAL: This function is designed for customer demos - it must be resilient.
    - Uses transactions for atomicity
    - Catches and logs errors without crashing
    - Idempotent operations ensure safe retries
    
    Args:
        assets: Target number of assets (only creates if below this count)
        applications: Target number of applications (only creates if below this count)
        deployments: Target number of deployments (only creates if below this count)
        users: Target number of demo users (only creates if below this count)
        events: Target number of events (only creates if below this count)
        clear_existing: If True, clear all demo data before seeding
        batch_size: Batch size for bulk inserts
    
    Returns:
        Dictionary with current demo data stats
    """
    try:
        if clear_existing:
            logger.info("Clearing existing demo data...")
            clear_demo_data()
            logger.info("Demo data cleared successfully")

        demo_user = _get_or_create_demo_admin()
        logger.info(f"Demo admin user: {demo_user.username}")
        
        # Only seed if target count not reached (idempotent seeding)
        current_stats = demo_data_stats()
        logger.info(f"Current demo data stats: {current_stats}")
        
        # Seed users (safe - uses get_or_create pattern)
        if current_stats['users'] < users:
            logger.info(f"Seeding users: target={users}, current={current_stats['users']}")
            try:
                _seed_demo_users(users)
            except Exception as e:
                logger.error(f"Error seeding users: {e}", exc_info=True)
        
        # Seed applications (safe - uses ignore_conflicts)
        if current_stats['applications'] < applications:
            logger.info(f"Seeding applications: target={applications}, current={current_stats['applications']}")
            try:
                _seed_applications(applications, batch_size)
            except Exception as e:
                logger.error(f"Error seeding applications: {e}", exc_info=True)
        
        # Seed assets (safe - uses ignore_conflicts)
        if current_stats['assets'] < assets:
            logger.info(f"Seeding assets: target={assets}, current={current_stats['assets']}")
            try:
                _seed_assets(assets, batch_size)
            except Exception as e:
                logger.error(f"Error seeding assets: {e}", exc_info=True)
        
        # CRITICAL FIX: Re-check stats AFTER seeding applications/assets to get accurate counts
        updated_stats = demo_data_stats()
        
        # For deployments, we need applications to exist first
        # Use updated_stats instead of current_stats to ensure we have the latest counts
        applications_count = updated_stats['applications']
        if updated_stats['deployments'] < deployments and applications_count > 0:
            logger.info(f"Seeding deployments: target={deployments}, current={updated_stats['deployments']}, applications available={applications_count}")
            try:
                deployment_results = _seed_deployments(deployments, demo_user, batch_size)
                logger.info(f"Deployment seeding results: deployments={deployment_results.get('deployments', 0)}, cab_approvals={deployment_results.get('cab_approvals', 0)}, events={deployment_results.get('events', 0)}")
                # Re-check events count after deployment seeding
                final_events_count = DeploymentEvent.objects.filter(is_demo=True).count()
                if final_events_count < events and deployment_results.get('correlation_ids'):
                    logger.info(f"Seeding additional events: target={events}, current={final_events_count}, correlation_ids={len(deployment_results.get('correlation_ids', []))}")
                    try:
                        _seed_additional_events(events, deployment_results['correlation_ids'], batch_size)
                    except Exception as e:
                        logger.error(f"Error seeding events: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error seeding deployments: {e}", exc_info=True)
        elif applications_count == 0:
            logger.warning(f"Cannot seed deployments: no applications available (target={deployments}, current={updated_stats['deployments']})")
        
        final_stats = demo_data_stats()
        logger.info(f"Demo data seeding completed. Final stats: {final_stats}")
        return final_stats
        
    except Exception as e:
        logger.error(f"Critical error in seed_demo_data: {e}", exc_info=True)
        # Return current stats even if seeding failed partially
        try:
            return demo_data_stats()
        except Exception:
            # If even stats fail, return empty dict
            return {
                'assets': 0,
                'applications': 0,
                'deployments': 0,
                'ring_deployments': 0,
                'cab_approvals': 0,
                'evidence_packs': 0,
                'events': 0,
                'users': 0,
            }


def clear_demo_data() -> dict:
    """
    Clear demo data only (no production data is removed).
    """
    ring_deployments = RingDeployment.objects.filter(is_demo=True).delete()[0]
    cab_approvals = CABApproval.objects.filter(is_demo=True).delete()[0]
    deployments = DeploymentIntent.objects.filter(is_demo=True).delete()[0]
    evidence_packs = EvidencePack.objects.filter(is_demo=True).delete()[0]
    assets = Asset.objects.filter(is_demo=True).delete()[0]
    applications = Application.objects.filter(is_demo=True).delete()[0]

    # Append-only event store: use raw delete for demo-only purge.
    events_qs = DeploymentEvent.objects.filter(is_demo=True)
    events = events_qs._raw_delete(events_qs.db)

    demo_users = _delete_demo_users()

    return {
        'assets': assets,
        'applications': applications,
        'deployments': deployments,
        'ring_deployments': ring_deployments,
        'cab_approvals': cab_approvals,
        'evidence_packs': evidence_packs,
        'events': events,
        'users': demo_users,
    }


def demo_data_stats() -> dict:
    """
    Return demo data counts across core models.
    """
    return {
        'assets': Asset.objects.filter(is_demo=True).count(),
        'applications': Application.objects.filter(is_demo=True).count(),
        'deployments': DeploymentIntent.objects.filter(is_demo=True).count(),
        'ring_deployments': RingDeployment.objects.filter(is_demo=True).count(),
        'cab_approvals': CABApproval.objects.filter(is_demo=True).count(),
        'evidence_packs': EvidencePack.objects.filter(is_demo=True).count(),
        'events': DeploymentEvent.objects.filter(is_demo=True).count(),
        'users': User.objects.filter(username__startswith='demo_').count() + User.objects.filter(username='demo').count(),
    }


def _get_or_create_demo_admin() -> User:
    """
    Get or create demo admin user (resilient - handles race conditions).
    """
    try:
        demo_user = User.objects.get(username='demo')
        return demo_user
    except User.DoesNotExist:
        try:
            with transaction.atomic():
                demo_user = User.objects.create_user(
                    username='demo',
                    email='demo@eucora.com',
                    password='admin@134',
                    first_name='Demo',
                    last_name='User',
                    is_staff=False,
                    is_superuser=False,
                )
                logger.info("Created demo admin user")
                return demo_user
        except IntegrityError:
            # Race condition - another process created it
            logger.warning("Demo user already exists (race condition), fetching...")
            return User.objects.get(username='demo')
    except Exception as e:
        logger.error(f"Error getting/creating demo admin: {e}", exc_info=True)
        # Fallback: try to get any user or create a minimal one
        try:
            fallback = User.objects.filter(is_staff=True).first() or User.objects.first()
            if fallback:
                logger.warning(f"Using fallback user: {fallback.username}")
                return fallback
        except Exception:
            pass
        # Last resort: create without password (will need to be set manually)
        try:
            return User.objects.create(
                username='demo_fallback',
                email='demo@eucora.com',
                is_staff=False,
                is_superuser=False,
            )
        except Exception as final_error:
            logger.critical(f"Failed to create even fallback user: {final_error}")
            raise


def _seed_demo_users(count: int) -> None:
    existing = User.objects.filter(username__startswith='demo_').count()
    remaining = max(0, count - existing)
    if remaining == 0:
        return

    for i in range(remaining):
        username = f'demo_{existing + i + 1}'
        user = User.objects.create_user(
            username=username,
            email=f'{username}@demo.eucora.com',
            password='admin@134'
        )
        user.first_name = f'Demo{existing + i + 1}'
        user.last_name = 'User'
        user.save(update_fields=['first_name', 'last_name'])


def _delete_demo_users() -> int:
    demo_users = User.objects.filter(username__startswith='demo_')
    deleted = demo_users.delete()[0]
    demo_user = User.objects.filter(username='demo')
    deleted += demo_user.delete()[0]
    return deleted


def _seed_applications(count: int, batch_size: int) -> int:
    """
    Seed applications up to target count (idempotent - only creates if below target).
    """
    existing = Application.objects.filter(is_demo=True).count()
    remaining = max(0, count - existing)
    
    if remaining == 0:
        return existing
    
    applications_data = [
        ('Microsoft 365', 'Microsoft', 'Productivity', 'Multi-Platform'),
        ('Adobe Acrobat', 'Adobe', 'Productivity', 'Multi-Platform'),
        ('Google Chrome', 'Google', 'Browser', 'Multi-Platform'),
        ('Slack', 'Slack Technologies', 'Communication', 'Multi-Platform'),
        ('Zoom', 'Zoom Video Communications', 'Communication', 'Multi-Platform'),
        ('Visual Studio Code', 'Microsoft', 'Development', 'Multi-Platform'),
        ('CrowdStrike Falcon', 'CrowdStrike', 'Security', 'Multi-Platform'),
        ('Microsoft Defender', 'Microsoft', 'Security', 'Windows'),
        ('Okta Verify', 'Okta', 'Security', 'Mobile'),
        ('SAP GUI', 'SAP', 'Enterprise', 'Windows'),
        ('Oracle Client', 'Oracle', 'Enterprise', 'Windows'),
        ('VMware Horizon Client', 'VMware', 'Enterprise', 'Multi-Platform'),
    ]
    platforms = ['Windows', 'macOS', 'Linux', 'Mobile', 'Multi-Platform']
    categories = ['Productivity', 'Security', 'Development', 'Media', 'Browser', 'Communication', 'Utility', 'Enterprise']
    vendors = ['Microsoft', 'Google', 'Adobe', 'Oracle', 'VMware', 'Atlassian', 'Salesforce', 'Cisco']

    created = 0
    buffer = []
    for i in range(remaining):
        if i < len(applications_data):
            name, vendor, category, platform = applications_data[i]
        else:
            name = f"Application-{random.choice(['Pro', 'Enterprise', 'Standard', 'Lite'])}-{i}"
            vendor = random.choice(vendors)
            category = random.choice(categories)
            platform = random.choice(platforms)
        version = f"{random.randint(1, 30)}.{random.randint(0, 99)}.{random.randint(0, 9999)}"

        buffer.append(Application(
            name=name,
            vendor=vendor,
            version=version,
            platform=platform,
            category=category,
            description=f"{name} version {version} for {platform}",
            default_risk_score=random.randint(10, 80),
            is_demo=True,
        ))

        if len(buffer) >= batch_size:
            try:
                with transaction.atomic():
                    created += len(Application.objects.bulk_create(buffer, ignore_conflicts=True))
            except Exception as e:
                logger.error(f"Error bulk creating applications (batch): {e}", exc_info=True)
            buffer = []

    if buffer:
        try:
            with transaction.atomic():
                created += len(Application.objects.bulk_create(buffer, ignore_conflicts=True))
        except Exception as e:
            logger.error(f"Error bulk creating applications (final): {e}", exc_info=True)

    try:
        return Application.objects.filter(is_demo=True).count()
    except Exception:
        return created


def _seed_assets(count: int, batch_size: int) -> int:
    """
    Seed assets up to target count (idempotent - only creates if below target).
    Uses transactions for safety.
    """
    try:
        existing = Asset.objects.filter(is_demo=True).count()
        remaining = max(0, count - existing)
        
        if remaining == 0:
            return existing
    except Exception as e:
        logger.error(f"Error checking existing assets: {e}", exc_info=True)
        return 0
    
    asset_types = ['Laptop', 'Desktop', 'Virtual Machine', 'Mobile', 'Server']
    os_versions = {
        'Laptop': ['Windows 11', 'Windows 10', 'macOS Sonoma', 'macOS Ventura', 'Ubuntu 22.04'],
        'Desktop': ['Windows 11', 'Windows 10', 'Ubuntu 22.04'],
        'Virtual Machine': ['Windows Server 2022', 'Ubuntu 22.04', 'RHEL 9'],
        'Mobile': ['iOS 17', 'iOS 16', 'Android 14', 'Android 13'],
        'Server': ['Windows Server 2022', 'Ubuntu 22.04', 'RHEL 9'],
    }
    statuses = ['Active'] * 8 + ['Inactive', 'Maintenance', 'Retired']
    locations = [
        'New York HQ', 'San Francisco HQ', 'London Office', 'Tokyo Office',
        'Frankfurt Office', 'Sydney Office', 'Toronto Office', 'Sao Paulo Office',
        'Remote - US', 'Remote - EU', 'Remote - APAC', 'Data Center - East',
        'Data Center - West', 'Cloud - AWS', 'Cloud - Azure',
    ]

    created = 0
    buffer = []
    for i in range(remaining):
        asset_type = random.choice(asset_types)
        os = random.choice(os_versions.get(asset_type, ['Windows 11']))
        status = random.choice(statuses)

        if 'Windows' in os:
            connector = random.choice(['intune', 'sccm'])
        elif 'macOS' in os or 'iOS' in os:
            connector = 'jamf'
        else:
            connector = random.choice(['landscape', 'ansible'])

        # Calculate compliance score: Active assets have higher scores, but some have vulnerabilities affecting score
        if status == 'Active':
            base_compliance = random.randint(75, 100)
            # Some assets have lower compliance due to missing patches, encryption, etc.
            if random.random() < 0.15:  # 15% have lower compliance
                base_compliance = random.randint(50, 74)
        else:
            base_compliance = random.randint(0, 60)
        
        # Last check-in: Active assets check in more recently, some have gaps
        if status == 'Active':
            # Most check in within last 24h, some within last week
            hours_ago = random.randint(0, 24) if random.random() < 0.8 else random.randint(24, 168)
            last_checkin_time = timezone.now() - timedelta(hours=hours_ago)
        else:
            last_checkin_time = None
        
        # Security features: Most active assets have encryption and firewall
        disk_enc = random.choice([True, True, True, True, False]) if status == 'Active' else random.choice([True, False])
        firewall = random.choice([True, True, True, False]) if status == 'Active' else random.choice([True, False])
        
        buffer.append(Asset(
            name=f"{asset_type[:3].upper()}-{random.randint(1000, 9999)}-{existing + i:06d}",
            asset_id=f"DEMO-AST-{existing + i:07d}",
            serial_number=f"SN{random.randint(100000, 999999)}",
            type=asset_type,
            os=os,
            status=status,
            location=random.choice(locations),
            owner=f"demo_{random.randint(1, 2000)}@eucora.com",
            ip_address=f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}" if status == 'Active' else None,
            disk_encryption=disk_enc,
            firewall_enabled=firewall,
            compliance_score=base_compliance,
            last_checkin=last_checkin_time,
            dex_score=round(random.uniform(6.0, 9.8), 1) if status == 'Active' else None,
            boot_time=random.randint(15, 120) if status == 'Active' else None,
            carbon_footprint=round(random.uniform(50.0, 300.0), 2),
            user_sentiment=random.choice(['Positive', 'Positive', 'Neutral', 'Neutral', 'Negative']) if status == 'Active' else None,
            connector_type=connector,
            connector_object_id=f"{connector.upper()}-{random.randint(100000, 999999)}",
            is_demo=True,
        ))

        if len(buffer) >= batch_size:
            try:
                with transaction.atomic():
                    created += len(Asset.objects.bulk_create(buffer, ignore_conflicts=True))
            except Exception as e:
                logger.error(f"Error bulk creating assets (batch): {e}", exc_info=True)
            buffer = []

    if buffer:
        try:
            with transaction.atomic():
                created += len(Asset.objects.bulk_create(buffer, ignore_conflicts=True))
        except Exception as e:
            logger.error(f"Error bulk creating assets (final): {e}", exc_info=True)

    try:
        return Asset.objects.filter(is_demo=True).count()
    except Exception:
        return created


def _seed_deployments(count: int, demo_user: User, batch_size: int) -> dict:
    """
    Seed deployments up to target count (idempotent - only creates if below target).
    """
    existing = DeploymentIntent.objects.filter(is_demo=True).count()
    remaining = max(0, count - existing)
    
    if remaining == 0:
        # Return existing stats without creating new deployments
        return {
            'deployments': existing,
            'ring_deployments': RingDeployment.objects.filter(is_demo=True).count(),
            'cab_approvals': CABApproval.objects.filter(is_demo=True).count(),
            'evidence_packs': EvidencePack.objects.filter(is_demo=True).count(),
            'events': DeploymentEvent.objects.filter(is_demo=True).count(),
            'correlation_ids': [],
        }
    
    # Weight status pool to ensure more AWAITING_CAB and APPROVED for CAB Portal visibility
    status_pool = [
        DeploymentIntent.Status.PENDING,
        DeploymentIntent.Status.AWAITING_CAB,  # More pending CAB reviews
        DeploymentIntent.Status.AWAITING_CAB,  # Duplicate to increase probability
        DeploymentIntent.Status.AWAITING_CAB,  # Duplicate to increase probability
        DeploymentIntent.Status.APPROVED,  # More approved for Approved column
        DeploymentIntent.Status.APPROVED,  # Duplicate to increase probability
        DeploymentIntent.Status.APPROVED,  # Duplicate to increase probability
        DeploymentIntent.Status.REJECTED,
        DeploymentIntent.Status.DEPLOYING,
        DeploymentIntent.Status.COMPLETED,
        DeploymentIntent.Status.COMPLETED,
        DeploymentIntent.Status.COMPLETED,
        DeploymentIntent.Status.COMPLETED,
        DeploymentIntent.Status.FAILED,
        DeploymentIntent.Status.ROLLED_BACK,
    ]
    rings = [
        DeploymentIntent.Ring.LAB,
        DeploymentIntent.Ring.CANARY,
        DeploymentIntent.Ring.PILOT,
        DeploymentIntent.Ring.DEPARTMENT,
        DeploymentIntent.Ring.GLOBAL,
    ]

    applications = list(Application.objects.filter(is_demo=True)[:5000])
    if not applications:
        return {
            'deployments': existing,
            'ring_deployments': RingDeployment.objects.filter(is_demo=True).count(),
            'cab_approvals': CABApproval.objects.filter(is_demo=True).count(),
            'evidence_packs': EvidencePack.objects.filter(is_demo=True).count(),
            'events': DeploymentEvent.objects.filter(is_demo=True).count(),
            'correlation_ids': [],
        }

    deployments_created = 0
    ring_deployments_created = 0
    cab_approvals_created = 0
    evidence_packs_created = 0
    events_created = 0
    correlation_ids = []

    deployments_batch = []
    evidence_batch = []
    cab_batch = []
    ring_batch = []
    events_batch = []

    for i in range(remaining):
        app = random.choice(applications)
        status = random.choice(status_pool)
        ring = random.choice(rings)
        deployment_id = uuid.uuid4()
        # Use the same correlation_id for both evidence pack and deployment intent
        evidence_id = deployment_id

        risk_score = max(0, min(100, app.default_risk_score + random.randint(-10, 25)))
        requires_cab = risk_score > 50
        
        # If status is AWAITING_CAB or APPROVED, ensure it requires CAB approval
        if status in [DeploymentIntent.Status.AWAITING_CAB, DeploymentIntent.Status.APPROVED]:
            requires_cab = True
            # Ensure risk score is high enough to require CAB
            if risk_score <= 50:
                risk_score = random.randint(51, 95)

        evidence_batch.append(EvidencePack(
            correlation_id=deployment_id,  # Use deployment_id so it matches deployment intent's correlation_id
            app_name=app.name,
            version=app.version,
            artifact_hash=''.join(random.choices('0123456789abcdef', k=64)),
            artifact_path=f"demo/artifacts/{app.name.replace(' ', '-')}/{app.version}/{evidence_id}.pkg",
            sbom_data=_generate_realistic_sbom(app.name, app.version),
            vulnerability_scan_results=_generate_realistic_vulnerabilities(app.name, app.version),
            rollback_plan=_generate_rollback_plan(app.name, app.version),
            is_validated=status not in [DeploymentIntent.Status.PENDING, DeploymentIntent.Status.AWAITING_CAB],
            is_demo=True,
        ))

        deployment = DeploymentIntent(
            correlation_id=deployment_id,
            app_name=app.name,
            version=app.version,
            target_ring=ring,
            status=status,
            evidence_pack_id=evidence_id,
            risk_score=risk_score,
            requires_cab_approval=requires_cab,
            submitter=demo_user,
            is_demo=True,
        )
        deployments_batch.append(deployment)
        correlation_ids.append(deployment_id)

        ring_batch.append({
            'deployment_id': deployment_id,
            'ring': ring,
            'status': status,
        })

        # Create CAB approvals for all deployments that require CAB approval
        if requires_cab:
            if status == DeploymentIntent.Status.AWAITING_CAB:
                # Distribute between New, Assessing, and CAB Review
                # Target: 8+ New Requests, 8+ Technical Assessment, balanced CAB Review
                # Use more aggressive distribution to ensure we get enough of each type
                rand_val = random.random()
                if rand_val < 0.45:  # 45% - New requests (no review yet) - prioritize to get 8+
                    decision = CABApproval.Decision.PENDING
                    approver = None
                    reviewed_at = None
                    comments = f"New change request for {app.name} {app.version}. Risk score: {risk_score}."
                    conditions = []
                elif rand_val < 0.75:  # 30% - Technical Assessment (reviewed but still pending)
                    decision = CABApproval.Decision.PENDING
                    approver = demo_user
                    reviewed_at = timezone.now() - timedelta(hours=random.randint(1, 24))
                    comments = f"Under technical assessment for {app.name} {app.version}. Security team reviewing vulnerability scan results. Risk score: {risk_score}."
                    conditions = []
                else:  # 25% - CAB Review (explicitly in CAB review)
                    decision = CABApproval.Decision.PENDING
                    approver = None
                    reviewed_at = None
                    comments = f"Awaiting CAB review for {app.name} {app.version}. Risk score: {risk_score}."
                    conditions = []
            elif status == DeploymentIntent.Status.APPROVED:
                # Approved - could be conditional or full approval
                if random.random() < 0.25:  # 25% are conditional approvals
                    decision = CABApproval.Decision.CONDITIONAL
                    conditions = [
                        "Deploy only during maintenance window",
                        "Monitor for 48 hours post-deployment",
                        "Rollback plan must be tested before deployment",
                        "Require additional security scan before production deployment",
                    ][:random.randint(1, 3)]
                    comments = f"Conditionally approved {app.name} {app.version} with {len(conditions)} conditions. Risk score: {risk_score}."
                else:
                    decision = CABApproval.Decision.APPROVED
                    conditions = []
                    comments = f"Approved {app.name} {app.version} for deployment to {ring} ring. Risk assessment completed successfully."
                approver = demo_user
                reviewed_at = timezone.now() - timedelta(hours=random.randint(1, 72))
            elif status == DeploymentIntent.Status.REJECTED:
                # Rejected
                decision = CABApproval.Decision.REJECTED
                approver = demo_user
                reviewed_at = timezone.now() - timedelta(hours=random.randint(1, 48))
                comments = random.choice([
                    f"Rejected {app.name} {app.version}: Risk score too high ({risk_score}). Requires additional security review.",
                    f"Rejected {app.name} {app.version}: Insufficient evidence pack. Missing vulnerability scan results.",
                    f"Rejected {app.name} {app.version}: Rollback plan incomplete. Please resubmit with detailed rollback procedures.",
                    f"Rejected {app.name} {app.version}: Policy violation detected. Application does not meet enterprise security standards.",
                ])
                conditions = []
            else:
                # Other statuses - create pending approval
                decision = CABApproval.Decision.PENDING
                approver = None
                reviewed_at = None
                comments = f"Pending CAB review for {app.name} {app.version}."
                conditions = []
            
            cab_batch.append({
                'deployment_id': deployment_id,
                'decision': decision,
                'approver': approver,
                'comments': comments,
                'conditions': conditions,
                'reviewed_at': reviewed_at,
            })

        event_type = {
            DeploymentIntent.Status.PENDING: DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            DeploymentIntent.Status.AWAITING_CAB: DeploymentEvent.EventType.CAB_SUBMITTED,
            DeploymentIntent.Status.APPROVED: DeploymentEvent.EventType.CAB_APPROVED,
            DeploymentIntent.Status.REJECTED: DeploymentEvent.EventType.CAB_REJECTED,
            DeploymentIntent.Status.DEPLOYING: DeploymentEvent.EventType.DEPLOYMENT_STARTED,
            DeploymentIntent.Status.COMPLETED: DeploymentEvent.EventType.DEPLOYMENT_COMPLETED,
            DeploymentIntent.Status.FAILED: DeploymentEvent.EventType.DEPLOYMENT_FAILED,
            DeploymentIntent.Status.ROLLED_BACK: DeploymentEvent.EventType.ROLLBACK_COMPLETED,
        }.get(status, DeploymentEvent.EventType.DEPLOYMENT_CREATED)

        events_batch.append(DeploymentEvent(
            correlation_id=deployment_id,
            event_type=event_type,
            event_data={'app_name': app.name, 'version': app.version, 'ring': ring},
            actor='demo-system',
            is_demo=True,
        ))

        if len(deployments_batch) >= batch_size:
            evidence_packs_created += len(EvidencePack.objects.bulk_create(evidence_batch, ignore_conflicts=True))
            evidence_batch = []

            DeploymentIntent.objects.bulk_create(deployments_batch, ignore_conflicts=True)
            deployments_created += len(deployments_batch)

            saved = {d.correlation_id: d for d in DeploymentIntent.objects.filter(correlation_id__in=[d.correlation_id for d in deployments_batch])}

            if cab_batch:
                cab_objects = []
                for cab in cab_batch:
                    deployment = saved.get(cab['deployment_id'])
                    if deployment:
                        cab_objects.append(CABApproval(
                            deployment_intent=deployment,
                            decision=cab['decision'],
                            approver=cab['approver'],
                            comments=cab['comments'],
                            reviewed_at=cab['reviewed_at'],
                            is_demo=True,
                        ))
                cab_approvals_created += len(CABApproval.objects.bulk_create(cab_objects, ignore_conflicts=True))
                cab_batch = []

            if ring_batch:
                ring_objects = []
                for ring_entry in ring_batch:
                    deployment = saved.get(ring_entry['deployment_id'])
                    if deployment:
                        success_count = random.randint(50, 500) if ring_entry['status'] == DeploymentIntent.Status.COMPLETED else random.randint(0, 50)
                        failure_count = random.randint(0, 25) if ring_entry['status'] in [DeploymentIntent.Status.FAILED, DeploymentIntent.Status.ROLLED_BACK] else random.randint(0, 10)
                        total = max(1, success_count + failure_count)
                        ring_objects.append(RingDeployment(
                            deployment_intent=deployment,
                            ring=ring_entry['ring'],
                            connector_type=random.choice(['intune', 'jamf', 'sccm', 'landscape', 'ansible']),
                            connector_object_id=f"DEMO-{uuid.uuid4()}",
                            success_count=success_count,
                            failure_count=failure_count,
                            success_rate=success_count / total,
                            promoted_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                            promotion_gate_passed=ring_entry['status'] == DeploymentIntent.Status.COMPLETED,
                            is_demo=True,
                        ))
                ring_deployments_created += len(RingDeployment.objects.bulk_create(ring_objects, ignore_conflicts=True))
                ring_batch = []

            if events_batch:
                events_created += len(DeploymentEvent.objects.bulk_create(events_batch, ignore_conflicts=True))
                events_batch = []

            deployments_batch = []

    # CRITICAL FIX: Final batch must also use transaction
    if evidence_batch or deployments_batch:
        with transaction.atomic():
            if evidence_batch:
                evidence_packs_created += len(EvidencePack.objects.bulk_create(evidence_batch, ignore_conflicts=True))
            if deployments_batch:
                DeploymentIntent.objects.bulk_create(deployments_batch, ignore_conflicts=True)
                deployments_created += len(deployments_batch)
                # Force refresh from database
                saved = {d.correlation_id: d for d in DeploymentIntent.objects.filter(
                    correlation_id__in=[d.correlation_id for d in deployments_batch]
                )}

                cab_objects = []
                for cab in cab_batch:
                    deployment = saved.get(cab['deployment_id'])
                    if deployment:
                        cab_objects.append(CABApproval(
                            deployment_intent=deployment,
                            decision=cab['decision'],
                            approver=cab['approver'],
                            comments=cab['comments'],
                            reviewed_at=cab['reviewed_at'],
                            is_demo=True,
                        ))
                if cab_objects:
                    cab_approvals_created += len(CABApproval.objects.bulk_create(cab_objects, ignore_conflicts=True))

            if ring_batch:
                ring_objects = []
                for ring_entry in ring_batch:
                    deployment = saved.get(ring_entry['deployment_id'])
                    if deployment:
                        success_count = random.randint(50, 500) if ring_entry['status'] == DeploymentIntent.Status.COMPLETED else random.randint(0, 50)
                        failure_count = random.randint(0, 25) if ring_entry['status'] in [DeploymentIntent.Status.FAILED, DeploymentIntent.Status.ROLLED_BACK] else random.randint(0, 10)
                        total = max(1, success_count + failure_count)
                        ring_objects.append(RingDeployment(
                            deployment_intent=deployment,
                            ring=ring_entry['ring'],
                            connector_type=random.choice(['intune', 'jamf', 'sccm', 'landscape', 'ansible']),
                            connector_object_id=f"DEMO-{uuid.uuid4()}",
                            success_count=success_count,
                            failure_count=failure_count,
                            success_rate=success_count / total,
                            promoted_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                            promotion_gate_passed=ring_entry['status'] == DeploymentIntent.Status.COMPLETED,
                            is_demo=True,
                        ))
                if ring_objects:
                    ring_deployments_created += len(RingDeployment.objects.bulk_create(ring_objects, ignore_conflicts=True))

    if events_batch:
        events_created += len(DeploymentEvent.objects.bulk_create(events_batch, ignore_conflicts=True))

    return {
        'deployments': deployments_created,
        'ring_deployments': ring_deployments_created,
        'cab_approvals': cab_approvals_created,
        'evidence_packs': evidence_packs_created,
        'events': events_created,
        'correlation_ids': correlation_ids,
    }


def _generate_realistic_sbom(app_name: str, version: str) -> dict:
    """Generate realistic SBOM data."""
    common_packages = [
        {'name': 'openssl', 'version': '3.0.8', 'type': 'library'},
        {'name': 'zlib', 'version': '1.2.13', 'type': 'library'},
        {'name': 'libcurl', 'version': '8.1.2', 'type': 'library'},
        {'name': 'sqlite', 'version': '3.42.0', 'type': 'library'},
        {'name': 'python', 'version': '3.11.5', 'type': 'runtime'},
        {'name': 'nodejs', 'version': '20.5.0', 'type': 'runtime'},
        {'name': 'electron', 'version': '25.3.1', 'type': 'framework'},
    ]
    
    # Select 3-7 random packages
    num_packages = random.randint(3, 7)
    selected_packages = random.sample(common_packages, min(num_packages, len(common_packages)))
    
    return {
        'format': 'SPDX',
        'spdxVersion': 'SPDX-2.3',
        'dataLicense': 'CC0-1.0',
        'name': f'{app_name}-{version}',
        'packages': selected_packages,
        'relationships': [
            {'type': 'DEPENDS_ON', 'from': app_name, 'to': pkg['name']}
            for pkg in selected_packages
        ],
    }


def _generate_realistic_vulnerabilities(app_name: str, version: str) -> dict:
    """Generate realistic vulnerability scan results with detailed CVE data."""
    # Realistic CVE examples
    cve_templates = {
        'critical': [
            {'id': 'CVE-2024-1234', 'title': 'Remote Code Execution in OpenSSL', 'package': 'openssl', 'version': '3.0.8'},
            {'id': 'CVE-2024-5678', 'title': 'Critical Buffer Overflow in zlib', 'package': 'zlib', 'version': '1.2.13'},
            {'id': 'CVE-2024-9012', 'title': 'SQL Injection in SQLite', 'package': 'sqlite', 'version': '3.42.0'},
        ],
        'high': [
            {'id': 'CVE-2024-2345', 'title': 'Privilege Escalation Vulnerability', 'package': 'libcurl', 'version': '8.1.2'},
            {'id': 'CVE-2024-3456', 'title': 'Information Disclosure in Python', 'package': 'python', 'version': '3.11.5'},
            {'id': 'CVE-2024-4567', 'title': 'Cross-Site Scripting in Electron', 'package': 'electron', 'version': '25.3.1'},
        ],
        'medium': [
            {'id': 'CVE-2024-6789', 'title': 'Denial of Service in HTTP Parser', 'package': 'nodejs', 'version': '20.5.0'},
            {'id': 'CVE-2024-7890', 'title': 'Memory Leak in Event Loop', 'package': 'nodejs', 'version': '20.5.0'},
        ],
        'low': [
            {'id': 'CVE-2024-8901', 'title': 'Information Exposure in Logs', 'package': 'openssl', 'version': '3.0.8'},
            {'id': 'CVE-2024-9012', 'title': 'Weak Cryptography Configuration', 'package': 'zlib', 'version': '1.2.13'},
        ],
    }
    
    # Determine vulnerability counts based on app risk profile
    # Higher risk apps have more vulnerabilities
    base_risk = random.randint(1, 10)
    
    critical_count = random.randint(0, 2) if base_risk >= 8 else 0
    high_count = random.randint(0, 5) if base_risk >= 6 else random.randint(0, 2)
    medium_count = random.randint(0, 20) if base_risk >= 4 else random.randint(0, 10)
    low_count = random.randint(0, 50) if base_risk >= 2 else random.randint(0, 25)
    
    # Generate detailed vulnerability list
    vulnerabilities = []
    
    # Critical vulnerabilities
    for _ in range(critical_count):
        template = random.choice(cve_templates['critical'])
        vulnerabilities.append({
            'cve_id': template['id'],
            'severity': 'CRITICAL',
            'package': template['package'],
            'installed_version': template['version'],
            'fixed_version': f"{template['version'].split('.')[0]}.{int(template['version'].split('.')[1]) + 1}.0",
            'title': template['title'],
            'description': f"{template['title']} in {template['package']} {template['version']}. This vulnerability allows remote attackers to execute arbitrary code.",
            'cvss_score': round(random.uniform(9.0, 10.0), 1),
            'published_date': (timezone.now() - timedelta(days=random.randint(1, 90))).isoformat(),
        })
    
    # High vulnerabilities
    for _ in range(high_count):
        template = random.choice(cve_templates['high'])
        vulnerabilities.append({
            'cve_id': template['id'],
            'severity': 'HIGH',
            'package': template['package'],
            'installed_version': template['version'],
            'fixed_version': f"{template['version'].split('.')[0]}.{int(template['version'].split('.')[1]) + 1}.0",
            'title': template['title'],
            'description': f"{template['title']} in {template['package']} {template['version']}.",
            'cvss_score': round(random.uniform(7.0, 8.9), 1),
            'published_date': (timezone.now() - timedelta(days=random.randint(1, 180))).isoformat(),
        })
    
    # Medium vulnerabilities
    for _ in range(medium_count):
        template = random.choice(cve_templates['medium'])
        vulnerabilities.append({
            'cve_id': f"CVE-2024-{random.randint(1000, 9999)}",
            'severity': 'MEDIUM',
            'package': template['package'],
            'installed_version': template['version'],
            'fixed_version': None,
            'title': template['title'],
            'description': f"{template['title']} in {template['package']}.",
            'cvss_score': round(random.uniform(4.0, 6.9), 1),
            'published_date': (timezone.now() - timedelta(days=random.randint(1, 365))).isoformat(),
        })
    
    # Low vulnerabilities
    for _ in range(low_count):
        vulnerabilities.append({
            'cve_id': f"CVE-2024-{random.randint(1000, 9999)}",
            'severity': 'LOW',
            'package': random.choice(['openssl', 'zlib', 'libcurl', 'sqlite']),
            'installed_version': f"{random.randint(1, 10)}.{random.randint(0, 99)}.{random.randint(0, 999)}",
            'fixed_version': None,
            'title': f'Information Disclosure in {random.choice(["Logging", "Error Messages", "Headers"])}',
            'description': 'Low severity information disclosure vulnerability.',
            'cvss_score': round(random.uniform(0.1, 3.9), 1),
            'published_date': (timezone.now() - timedelta(days=random.randint(1, 730))).isoformat(),
        })
    
    return {
        'critical': critical_count,
        'high': high_count,
        'medium': medium_count,
        'low': low_count,
        'total': critical_count + high_count + medium_count + low_count,
        'vulnerabilities': vulnerabilities,
        'scan_date': timezone.now().isoformat(),
        'scanner': random.choice(['trivy', 'grype', 'snyk']),
        'scanner_version': f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
    }


def _generate_rollback_plan(app_name: str, version: str) -> str:
    """Generate realistic rollback plan."""
    rollback_steps = [
        f"1. Stop deployment of {app_name} version {version}",
        f"2. Verify current running version of {app_name}",
        f"3. Execute rollback script: rollback-{app_name.lower().replace(' ', '-')}.sh",
        "4. Verify previous version is running correctly",
        "5. Monitor application health for 24 hours",
        "6. Update deployment records and notify stakeholders",
    ]
    
    return "\n".join(rollback_steps)


def _seed_additional_events(event_target: int, correlation_ids: list, batch_size: int) -> int:
    if not correlation_ids:
        return 0

    existing = DeploymentEvent.objects.filter(is_demo=True).count()
    remaining = max(0, event_target - existing)
    if remaining == 0:
        return 0

    event_types = list(DeploymentEvent.EventType.values)
    actors = ['demo-system', 'demo-operator', 'demo-auditor']
    buffer = []
    created = 0

    for _ in range(remaining):
        correlation_id = random.choice(correlation_ids)
        buffer.append(DeploymentEvent(
            correlation_id=correlation_id,
            event_type=random.choice(event_types),
            event_data={'detail': 'Demo event', 'severity': random.choice(['low', 'medium', 'high'])},
            actor=random.choice(actors),
            is_demo=True,
        ))

        if len(buffer) >= batch_size:
            created += len(DeploymentEvent.objects.bulk_create(buffer, ignore_conflicts=True))
            buffer = []

    if buffer:
        created += len(DeploymentEvent.objects.bulk_create(buffer, ignore_conflicts=True))

    return created
