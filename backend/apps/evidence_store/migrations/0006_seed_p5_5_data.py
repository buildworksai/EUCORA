# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: Seed Data for Defense-in-Depth Security Controls

Seeds:
- Risk Model v1.1 (Greenfield Conservative)
- Blast Radius Class Definitions
- Trust Maturity Level Definitions
"""
from datetime import timedelta
from decimal import Decimal

from django.db import migrations
from django.utils import timezone


def seed_risk_model_v1_1(apps, schema_editor):
    """Seed Risk Model v1.1 - Greenfield Conservative Mode"""
    RiskModelVersion = apps.get_model("evidence_store", "RiskModelVersion")

    effective_date = timezone.now()
    review_date = effective_date + timedelta(days=30)

    RiskModelVersion.objects.create(
        version="1.1",
        mode="GREENFIELD_CONSERVATIVE",
        effective_date=effective_date,
        review_date=review_date,
        is_active=True,  # Activate immediately
        approved_by_cab=True,  # Pre-approved for Feb 10 go-live
        cab_approval_date=effective_date,
        cab_approval_notes="Initial greenfield deployment - 100% CAB review for trust baseline establishment",
        auto_approve_thresholds={
            "CRITICAL_INFRASTRUCTURE": 0,  # NEVER auto-approve
            "BUSINESS_CRITICAL": 0,  # Disabled until calibration
            "PRODUCTIVITY_TOOLS": 0,  # Disabled until calibration
            "NON_CRITICAL": 0,  # Disabled until calibration
        },
        risk_factor_weights={
            "test_coverage": 0.20,
            "security_issues": 0.15,
            "manual_testing": 0.10,
            "rollback_validation": 0.10,
            "change_scope": 0.10,
            "operational_complexity": 0.10,
            "business_impact": 0.10,
            "deployment_history": 0.15,
        },
        calibration_data={
            "note": "Greenfield baseline - no historical data",
            "deployment_capacity": "100 deployments/week",
            "calibration_period": "4 weeks (400 deployments)",
            "first_review_date": (effective_date + timedelta(weeks=4)).isoformat(),
        },
        calibration_notes=(
            "Risk Model v1.1 - Greenfield Conservative Mode\n\n"
            "Purpose: Establish baseline with 100% CAB review for first 4 weeks.\n\n"
            "Auto-approve disabled across all blast radius classes to:\n"
            "1. Collect incident baseline data\n"
            "2. Validate risk scoring accuracy\n"
            "3. Calibrate factor weights based on actual deployments\n\n"
            "Review Checkpoint: Week 4 (30 days)\n"
            "Progression Criteria: Incident rate ≤2%, zero P1 incidents\n"
            "Next Version: v1.2 (Cautious mode) with selective auto-approve"
        ),
        created_by="system_migration",
    )


def seed_blast_radius_classes(apps, schema_editor):
    """Seed Blast Radius Classification Definitions"""
    BlastRadiusClass = apps.get_model("evidence_store", "BlastRadiusClass")

    classes = [
        {
            "name": "CRITICAL_INFRASTRUCTURE",
            "description": (
                "Security tools, OS components, identity/authentication systems, PKI infrastructure. "
                "Failure impacts entire organization's security posture or operational capability."
            ),
            "user_impact_max": 999999,  # Enterprise-wide
            "business_criticality": "HIGH",
            "cab_quorum_required": 3,  # Requires 3 CAB members
            "auto_approve_allowed": False,  # NEVER auto-approve
            "example_applications": [
                "Windows Security Updates",
                "Antivirus Engine Updates",
                "VPN Client",
                "Certificate Authority Tools",
                "Active Directory Management Tools",
                "MFA/Authentication Tools",
                "Endpoint Security Agents",
                "Firewall/Network Security Tools",
            ],
        },
        {
            "name": "BUSINESS_CRITICAL",
            "description": (
                "ERP systems, financial applications, customer-facing services, revenue-generating platforms. "
                "Failure causes significant business disruption, revenue loss, or compliance violations."
            ),
            "user_impact_max": 50000,  # Large department or enterprise-wide
            "business_criticality": "HIGH",
            "cab_quorum_required": 2,  # Requires 2 CAB members
            "auto_approve_allowed": True,  # Allowed if risk very low (future maturity levels)
            "example_applications": [
                "SAP ERP",
                "Salesforce Desktop Client",
                "Oracle Financials",
                "Trading Platform Software",
                "Billing System Clients",
                "Customer Portal Applications",
                "Payroll Processing Software",
            ],
        },
        {
            "name": "PRODUCTIVITY_TOOLS",
            "description": (
                "Office productivity suites, collaboration tools, development environments. "
                "Failure impacts user productivity but not critical business functions."
            ),
            "user_impact_max": 10000,  # Department-level
            "business_criticality": "MEDIUM",
            "cab_quorum_required": 1,  # Single CAB member approval
            "auto_approve_allowed": True,  # Allowed for low-risk deployments
            "example_applications": [
                "Microsoft Office 365 Apps",
                "Slack Desktop",
                "Zoom Client",
                "Microsoft Teams",
                "Adobe Acrobat Reader",
                "Visual Studio Code",
                "Google Chrome",
                "Mozilla Firefox",
            ],
        },
        {
            "name": "NON_CRITICAL",
            "description": (
                "Optional utilities, personal productivity tools, non-essential software. "
                "Failure has minimal business impact."
            ),
            "user_impact_max": 1000,  # Team or individual
            "business_criticality": "LOW",
            "cab_quorum_required": 1,
            "auto_approve_allowed": True,  # Liberal auto-approve policy
            "example_applications": [
                "Screen Recording Utilities",
                "PDF Converters",
                "Image Viewers",
                "Notepad Alternatives",
                "Calculator Apps",
                "Wallpaper/Theme Utilities",
                "Personal Productivity Apps",
            ],
        },
    ]

    for class_data in classes:
        BlastRadiusClass.objects.create(**class_data)


def seed_trust_maturity_levels(apps, schema_editor):
    """Seed Trust Maturity Level Progression Framework"""
    TrustMaturityLevel = apps.get_model("evidence_store", "TrustMaturityLevel")

    levels = [
        {
            "level": "LEVEL_0_BASELINE",
            "description": (
                "Baseline trust establishment phase. 100% CAB review for all deployments "
                "to establish incident baseline and validate risk scoring accuracy."
            ),
            "weeks_required": 0,  # Entry level
            "max_incident_rate": Decimal("1.0000"),  # No limit (collecting baseline)
            "max_p1_incidents": 99,  # No limit
            "max_p2_incidents": 99,  # No limit
            "risk_model_version": "1.1",
            "auto_approve_thresholds": {
                "CRITICAL_INFRASTRUCTURE": 0,
                "BUSINESS_CRITICAL": 0,
                "PRODUCTIVITY_TOOLS": 0,
                "NON_CRITICAL": 0,
            },
        },
        {
            "level": "LEVEL_1_CAUTIOUS",
            "description": (
                "Cautious automation phase. Limited auto-approve for low-risk non-critical "
                "and productivity tool deployments with perfect risk scores."
            ),
            "weeks_required": 4,  # 4 weeks at Level 0
            "max_incident_rate": Decimal("0.0200"),  # ≤2% incident rate
            "max_p1_incidents": 0,  # Zero P1 incidents
            "max_p2_incidents": 4,  # ≤4 P2 incidents
            "risk_model_version": "1.2",
            "auto_approve_thresholds": {
                "CRITICAL_INFRASTRUCTURE": 0,
                "BUSINESS_CRITICAL": 0,
                "PRODUCTIVITY_TOOLS": 20,
                "NON_CRITICAL": 30,
            },
        },
        {
            "level": "LEVEL_2_MODERATE",
            "description": (
                "Moderate automation phase. Expanded auto-approve thresholds for proven "
                "low-incident deployment patterns. Business-critical apps with perfect scores eligible."
            ),
            "weeks_required": 4,  # 4 weeks at Level 1
            "max_incident_rate": Decimal("0.0100"),  # ≤1% incident rate
            "max_p1_incidents": 0,
            "max_p2_incidents": 1,  # ≤1 P2 incident
            "risk_model_version": "1.3",
            "auto_approve_thresholds": {
                "CRITICAL_INFRASTRUCTURE": 0,
                "BUSINESS_CRITICAL": 10,
                "PRODUCTIVITY_TOOLS": 35,
                "NON_CRITICAL": 50,
            },
        },
        {
            "level": "LEVEL_3_MATURE",
            "description": (
                "Mature automation phase. Risk model recalibrated based on 12 weeks of incident "
                "correlation data. Weights adjusted to optimize prediction accuracy."
            ),
            "weeks_required": 4,  # 4 weeks at Level 2
            "max_incident_rate": Decimal("0.0050"),  # ≤0.5% incident rate
            "max_p1_incidents": 0,
            "max_p2_incidents": 0,  # Zero high-severity incidents
            "risk_model_version": "2.0",
            "auto_approve_thresholds": {
                "CRITICAL_INFRASTRUCTURE": 0,  # Still NEVER auto-approve
                "BUSINESS_CRITICAL": 20,
                "PRODUCTIVITY_TOOLS": 45,
                "NON_CRITICAL": 65,
            },
        },
        {
            "level": "LEVEL_4_OPTIMIZED",
            "description": (
                "Optimized automation phase. Maximum safe automation based on sustained "
                "zero-incident operation. Continuous monitoring for regression."
            ),
            "weeks_required": 4,  # 4 weeks at Level 3
            "max_incident_rate": Decimal("0.0010"),  # ≤0.1% incident rate
            "max_p1_incidents": 0,
            "max_p2_incidents": 0,
            "risk_model_version": "2.1",
            "auto_approve_thresholds": {
                "CRITICAL_INFRASTRUCTURE": 0,  # NEVER auto-approve (permanent policy)
                "BUSINESS_CRITICAL": 25,
                "PRODUCTIVITY_TOOLS": 50,
                "NON_CRITICAL": 75,
            },
        },
    ]

    for level_data in levels:
        TrustMaturityLevel.objects.create(**level_data)


def reverse_seed(apps, schema_editor):
    """Remove seed data (for migration rollback)"""
    RiskModelVersion = apps.get_model("evidence_store", "RiskModelVersion")
    BlastRadiusClass = apps.get_model("evidence_store", "BlastRadiusClass")
    TrustMaturityLevel = apps.get_model("evidence_store", "TrustMaturityLevel")

    RiskModelVersion.objects.filter(version="1.1").delete()
    BlastRadiusClass.objects.all().delete()
    TrustMaturityLevel.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("evidence_store", "0005_p5_5_defense_in_depth"),
    ]

    operations = [
        migrations.RunPython(seed_risk_model_v1_1, reverse_seed),
        migrations.RunPython(seed_blast_radius_classes, reverse_seed),
        migrations.RunPython(seed_trust_maturity_levels, reverse_seed),
    ]
