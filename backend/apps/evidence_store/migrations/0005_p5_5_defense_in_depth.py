# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: Defense-in-Depth Security Controls
Migration for blast radius classification, incident tracking, and trust maturity framework
"""
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence_store", "0004_seed_risk_factors_v1"),
    ]

    operations = [
        # RiskModelVersion table
        migrations.CreateModel(
            name="RiskModelVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.CharField(max_length=10, unique=True, help_text="e.g., '1.0', '1.1', '2.0'")),
                (
                    "mode",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("GREENFIELD_CONSERVATIVE", "Greenfield Conservative (100% CAB Review)"),
                            ("CAUTIOUS", "Cautious (Limited Auto-Approve)"),
                            ("MODERATE", "Moderate (Balanced)"),
                            ("MATURE", "Mature (Evidence-Based Automation)"),
                            ("OPTIMIZED", "Optimized (Maximum Automation)"),
                        ],
                        help_text="Operating mode",
                    ),
                ),
                ("effective_date", models.DateTimeField(help_text="When this version becomes active")),
                ("review_date", models.DateTimeField(help_text="When to review for calibration")),
                (
                    "is_active",
                    models.BooleanField(default=False, db_index=True, help_text="Only one version can be active"),
                ),
                (
                    "approved_by_cab",
                    models.BooleanField(default=False, help_text="CAB approval required for activation"),
                ),
                ("cab_approval_date", models.DateTimeField(null=True, blank=True)),
                ("cab_approval_notes", models.TextField(blank=True)),
                (
                    "auto_approve_thresholds",
                    models.JSONField(
                        help_text="Thresholds per blast radius class: {'CRITICAL_INFRASTRUCTURE': 0, ...}"
                    ),
                ),
                (
                    "risk_factor_weights",
                    models.JSONField(help_text="Risk factor weights (must sum to 1.0): {'test_coverage': 0.20, ...}"),
                ),
                (
                    "calibration_data",
                    models.JSONField(
                        default=dict,
                        help_text="Incident correlation, risk score distribution, false positive/negative rates",
                    ),
                ),
                ("calibration_notes", models.TextField(blank=True, help_text="Evidence supporting this version")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.CharField(max_length=255, default="system")),
            ],
            options={
                "db_table": "evidence_store_riskmodelversion",
                "ordering": ["-version"],
                "verbose_name": "Risk Model Version",
                "verbose_name_plural": "Risk Model Versions",
            },
        ),
        # BlastRadiusClass table
        migrations.CreateModel(
            name="BlastRadiusClass",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "name",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("CRITICAL_INFRASTRUCTURE", "Critical Infrastructure"),
                            ("BUSINESS_CRITICAL", "Business Critical"),
                            ("PRODUCTIVITY_TOOLS", "Productivity Tools"),
                            ("NON_CRITICAL", "Non-Critical"),
                        ],
                        unique=True,
                        help_text="Blast radius classification level",
                    ),
                ),
                ("description", models.TextField(help_text="What qualifies for this classification")),
                (
                    "user_impact_max",
                    models.IntegerField(
                        help_text="Maximum users that can be impacted (enterprise-wide, department, team)"
                    ),
                ),
                (
                    "business_criticality",
                    models.CharField(
                        max_length=20,
                        choices=[("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low")],
                        help_text="Business criticality level",
                    ),
                ),
                (
                    "cab_quorum_required",
                    models.IntegerField(default=1, help_text="Minimum CAB members required for approval"),
                ),
                (
                    "auto_approve_allowed",
                    models.BooleanField(default=False, help_text="Whether auto-approve is ever allowed for this class"),
                ),
                (
                    "example_applications",
                    models.JSONField(default=list, help_text="Example applications in this class"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "evidence_store_blastradiusclass",
                "verbose_name": "Blast Radius Class",
                "verbose_name_plural": "Blast Radius Classes",
            },
        ),
        # DeploymentIncident table
        migrations.CreateModel(
            name="DeploymentIncident",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False)),
                (
                    "deployment_intent_id",
                    models.CharField(max_length=255, db_index=True, help_text="Deployment intent correlation ID"),
                ),
                (
                    "evidence_package_id",
                    models.CharField(max_length=255, db_index=True, help_text="Evidence package ID"),
                ),
                (
                    "cab_approval_id",
                    models.CharField(
                        max_length=255, null=True, blank=True, help_text="CAB approval request ID (if CAB-reviewed)"
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("P1", "P1 - Critical (Service Down)"),
                            ("P2", "P2 - High (Major Degradation)"),
                            ("P3", "P3 - Medium (Minor Impact)"),
                            ("P4", "P4 - Low (Cosmetic)"),
                        ],
                        db_index=True,
                    ),
                ),
                ("incident_date", models.DateTimeField(db_index=True, help_text="When incident occurred")),
                (
                    "detection_method",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("MONITORING_ALERT", "Monitoring Alert"),
                            ("USER_REPORT", "User Report"),
                            ("CAB_REVIEW", "CAB Review"),
                            ("SECURITY_SCAN", "Security Scan"),
                            ("AUTOMATED_TEST", "Automated Test"),
                        ],
                    ),
                ),
                ("title", models.CharField(max_length=255, help_text="Incident title")),
                ("description", models.TextField(help_text="Detailed incident description")),
                ("root_cause", models.TextField(blank=True, help_text="Root cause analysis")),
                (
                    "was_auto_approved",
                    models.BooleanField(db_index=True, help_text="Was deployment auto-approved (vs CAB-reviewed)"),
                ),
                (
                    "risk_score_at_approval",
                    models.DecimalField(
                        max_digits=5, decimal_places=2, help_text="Risk score when deployment was approved"
                    ),
                ),
                (
                    "risk_model_version",
                    models.CharField(max_length=10, help_text="Risk model version used for approval"),
                ),
                (
                    "blast_radius_class",
                    models.CharField(max_length=50, help_text="Blast radius classification of deployment"),
                ),
                ("affected_user_count", models.IntegerField(default=0, help_text="Number of users affected")),
                ("downtime_minutes", models.IntegerField(default=0, help_text="Total downtime in minutes")),
                (
                    "business_impact_usd",
                    models.DecimalField(
                        max_digits=12,
                        decimal_places=2,
                        null=True,
                        blank=True,
                        help_text="Estimated business impact in USD",
                    ),
                ),
                ("resolved_at", models.DateTimeField(null=True, blank=True, help_text="When incident was resolved")),
                (
                    "resolution_method",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("ROLLBACK", "Rollback to Previous Version"),
                            ("HOTFIX", "Hotfix Deployment"),
                            ("MANUAL_REMEDIATION", "Manual Remediation"),
                            ("WORKAROUND", "Temporary Workaround"),
                        ],
                        blank=True,
                    ),
                ),
                ("resolution_notes", models.TextField(blank=True)),
                (
                    "time_to_resolution_minutes",
                    models.IntegerField(null=True, blank=True, help_text="Time from detection to resolution"),
                ),
                (
                    "was_preventable",
                    models.BooleanField(null=True, help_text="Could this have been prevented by better controls?"),
                ),
                (
                    "preventability_notes",
                    models.TextField(
                        blank=True,
                        help_text="Analysis of whether CAB review or additional controls would have caught this",
                    ),
                ),
                (
                    "control_improvements",
                    models.JSONField(
                        default=dict,
                        help_text="Recommended improvements: risk factor adjustments, new controls, threshold changes",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.CharField(max_length=255, default="system")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "evidence_store_deploymentincident",
                "ordering": ["-incident_date"],
                "verbose_name": "Deployment Incident",
                "verbose_name_plural": "Deployment Incidents",
            },
        ),
        # TrustMaturityLevel table
        migrations.CreateModel(
            name="TrustMaturityLevel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "level",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("LEVEL_0_BASELINE", "Level 0: Baseline (100% CAB Review)"),
                            ("LEVEL_1_CAUTIOUS", "Level 1: Cautious (Limited Auto-Approve)"),
                            ("LEVEL_2_MODERATE", "Level 2: Moderate (Balanced)"),
                            ("LEVEL_3_MATURE", "Level 3: Mature (Evidence-Based)"),
                            ("LEVEL_4_OPTIMIZED", "Level 4: Optimized (Maximum Automation)"),
                        ],
                        unique=True,
                    ),
                ),
                ("description", models.TextField(help_text="What this maturity level represents")),
                ("weeks_required", models.IntegerField(help_text="Minimum weeks at previous level")),
                (
                    "max_incident_rate",
                    models.DecimalField(max_digits=5, decimal_places=4, help_text="Maximum incident rate (0.01 = 1%)"),
                ),
                ("max_p1_incidents", models.IntegerField(help_text="Maximum P1 incidents allowed")),
                ("max_p2_incidents", models.IntegerField(help_text="Maximum P2 incidents allowed")),
                (
                    "risk_model_version",
                    models.CharField(
                        max_length=10, help_text="Risk model version to activate when reaching this level"
                    ),
                ),
                (
                    "auto_approve_thresholds",
                    models.JSONField(help_text="Auto-approve thresholds per blast radius class"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "evidence_store_trustmaturitylevel",
                "ordering": ["level"],
                "verbose_name": "Trust Maturity Level",
                "verbose_name_plural": "Trust Maturity Levels",
            },
        ),
        # TrustMaturityProgress table
        migrations.CreateModel(
            name="TrustMaturityProgress",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False)),
                ("evaluation_date", models.DateTimeField(db_index=True)),
                ("current_level", models.CharField(max_length=50)),
                ("next_level", models.CharField(max_length=50, blank=True)),
                ("evaluation_period_start", models.DateTimeField()),
                ("evaluation_period_end", models.DateTimeField()),
                ("deployments_total", models.IntegerField(help_text="Total deployments in period")),
                ("incidents_total", models.IntegerField(help_text="Total incidents in period")),
                (
                    "incident_rate",
                    models.DecimalField(
                        max_digits=5, decimal_places=4, help_text="Incident rate (incidents / deployments)"
                    ),
                ),
                ("p1_incidents", models.IntegerField(default=0)),
                ("p2_incidents", models.IntegerField(default=0)),
                ("p3_incidents", models.IntegerField(default=0)),
                ("p4_incidents", models.IntegerField(default=0)),
                ("auto_approved_deployments", models.IntegerField(default=0)),
                ("auto_approved_incidents", models.IntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("EVALUATING", "Evaluating"),
                            ("CRITERIA_MET", "Criteria Met - Ready to Progress"),
                            ("CRITERIA_NOT_MET", "Criteria Not Met"),
                            ("PROGRESSED", "Progressed to Next Level"),
                            ("REGRESSED", "Regressed Due to Incidents"),
                        ],
                    ),
                ),
                ("decision_notes", models.TextField(help_text="Rationale for progression decision")),
                (
                    "blocking_criteria",
                    models.JSONField(default=list, help_text="List of criteria that blocked progression (if any)"),
                ),
                ("requires_cab_approval", models.BooleanField(default=True)),
                ("cab_approved", models.BooleanField(default=False)),
                ("cab_approval_date", models.DateTimeField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "evidence_store_trustmaturityprogress",
                "ordering": ["-evaluation_date"],
                "verbose_name": "Trust Maturity Progress",
                "verbose_name_plural": "Trust Maturity Progress Records",
            },
        ),
        # Indexes for RiskModelVersion
        migrations.AddIndex(
            model_name="riskmodelversion",
            index=models.Index(fields=["is_active", "effective_date"], name="evidence_st_is_acti_idx"),
        ),
        migrations.AddIndex(
            model_name="riskmodelversion",
            index=models.Index(fields=["version"], name="evidence_st_version_idx"),
        ),
        # Indexes for DeploymentIncident
        migrations.AddIndex(
            model_name="deploymentincident",
            index=models.Index(fields=["incident_date", "severity"], name="evidence_st_inciden_idx"),
        ),
        migrations.AddIndex(
            model_name="deploymentincident",
            index=models.Index(fields=["was_auto_approved", "severity"], name="evidence_st_was_aut_idx"),
        ),
        migrations.AddIndex(
            model_name="deploymentincident",
            index=models.Index(fields=["blast_radius_class", "incident_date"], name="evidence_st_blast_r_idx"),
        ),
        migrations.AddIndex(
            model_name="deploymentincident",
            index=models.Index(fields=["risk_score_at_approval"], name="evidence_st_risk_sc_idx"),
        ),
        # Indexes for TrustMaturityProgress
        migrations.AddIndex(
            model_name="trustmaturityprogress",
            index=models.Index(fields=["evaluation_date", "status"], name="evidence_st_evaluat_idx"),
        ),
        migrations.AddIndex(
            model_name="trustmaturityprogress",
            index=models.Index(fields=["current_level"], name="evidence_st_current_idx"),
        ),
    ]
