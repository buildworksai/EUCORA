# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Management command to seed ALM Agent workflow definitions.

Creates workflow definitions for:
- E10: CMDB Integration Agent
- E11: Change Communications Agent
- E14: Discovery Agent
"""
from django.core.management.base import BaseCommand

from apps.ai_agents.workflows.models import WorkflowDefinition


class Command(BaseCommand):
    """Seed ALM Agent workflow definitions."""

    help = "Seed ALM Agent workflow definitions for E10, E11, E12, E13, E14, E15, E16"

    def handle(self, *args, **options):  # noqa: C901
        """Execute the command."""
        self.stdout.write("Seeding ALM Agent workflow definitions...")

        workflows_created = 0

        # E10: CMDB Integration Agent Workflows
        e10_workflows = self._get_e10_workflows()
        for workflow_data in e10_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E11: Change Communications Agent Workflows
        e11_workflows = self._get_e11_workflows()
        for workflow_data in e11_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E14: Discovery Agent Workflows
        e14_workflows = self._get_e14_workflows()
        for workflow_data in e14_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E12: Documentation Agent Workflows
        e12_workflows = self._get_e12_workflows()
        for workflow_data in e12_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E13: Automation Advisor Agent Workflows
        e13_workflows = self._get_e13_workflows()
        for workflow_data in e13_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E15: IAM Security Agent Workflows
        e15_workflows = self._get_e15_workflows()
        for workflow_data in e15_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E16: Request Coordination Agent Workflows
        e16_workflows = self._get_e16_workflows()
        for workflow_data in e16_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E17: SecOps Agent Workflows
        e17_workflows = self._get_e17_workflows()
        for workflow_data in e17_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E18: SRE Agent Workflows
        e18_workflows = self._get_e18_workflows()
        for workflow_data in e18_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E21: KB & Triage Agent Workflows
        e21_workflows = self._get_e21_workflows()
        for workflow_data in e21_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E19: SLA Governance Agent Workflows
        e19_workflows = self._get_e19_workflows()
        for workflow_data in e19_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        # E20: Planning Agent Workflows
        e20_workflows = self._get_e20_workflows()
        for workflow_data in e20_workflows:
            workflow, created = WorkflowDefinition.objects.update_or_create(
                agent_type=workflow_data["agent_type"],
                name=workflow_data["name"],
                defaults=workflow_data,
            )
            if created:
                workflows_created += 1
                self.stdout.write(f"  Created: {workflow.name}")
            else:
                self.stdout.write(f"  Updated: {workflow.name}")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {workflows_created} workflow definitions"))

    def _get_e10_workflows(self) -> list:
        """Get E10 CMDB Integration Agent workflows."""
        return [
            {
                "agent_type": "cmdb_maintenance",
                "name": "CMDB Sync Workflow",
                "description": "Synchronize data from discovery sources to ServiceNow CMDB",
                "risk_level": "R2",
                "required_policies": ["cmdb", "data_quality", "security"],
                "steps": [
                    {
                        "name": "Analyze Source Data",
                        "type": "ai_action",
                        "description": "Analyze data from discovery sources (SCCM, Intune, AD)",
                        "instructions": "Review the incoming data from discovery sources and identify "
                        "CIs that need to be created, updated, or validated in the CMDB.",
                        "task": "Analyze discovery data and categorize changes",
                        "output_schema": {
                            "new_cis": "list",
                            "updated_cis": "list",
                            "unchanged_cis": "list",
                            "validation_issues": "list",
                        },
                        "policy_tags": ["cmdb_schema", "data_mapping"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Validate Data Quality",
                        "type": "ai_action",
                        "description": "Validate CI data against quality rules",
                        "instructions": "Apply validation rules to ensure data quality. Check for "
                        "required fields, format compliance, and reference integrity.",
                        "task": "Run validation engine and generate quality report",
                        "output_schema": {
                            "validation_passed": "boolean",
                            "quality_score": "number",
                            "issues": "list",
                            "recommendations": "list",
                        },
                        "policy_tags": ["data_quality", "validation_rules"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Identify Discrepancies",
                        "type": "ai_action",
                        "description": "Detect discrepancies between source and CMDB",
                        "instructions": "Compare source data with existing CMDB records. Identify "
                        "mismatches, orphans, duplicates, and stale records.",
                        "task": "Generate discrepancy report",
                        "output_schema": {
                            "discrepancy_count": "number",
                            "discrepancies": "list",
                            "auto_resolvable": "number",
                            "requires_review": "number",
                        },
                        "policy_tags": ["cmdb_schema", "discrepancy_handling"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Approval Gate",
                        "type": "approval_gate",
                        "description": "Review and approve CMDB changes",
                        "instructions": "Review the proposed changes to the CMDB. Approve for "
                        "R1 (low risk) changes or escalate for R2/R3 changes.",
                        "task": "Approve CMDB synchronization",
                        "output_schema": {
                            "approved": "boolean",
                            "approver": "string",
                            "conditions": "list",
                        },
                        "policy_tags": ["change_approval", "cmdb_governance"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "Apply Changes",
                        "type": "ai_action",
                        "description": "Apply approved changes to CMDB",
                        "instructions": "Execute the approved CMDB updates. Create new CIs, update "
                        "existing CIs, and record all changes for audit.",
                        "task": "Apply CMDB changes and generate audit log",
                        "output_schema": {
                            "created": "number",
                            "updated": "number",
                            "failed": "number",
                            "audit_records": "list",
                        },
                        "policy_tags": ["cmdb_write", "audit_trail"],
                        "risk_level": "R2",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "cmdb_maintenance",
                "name": "CMDB Discrepancy Resolution Workflow",
                "description": "Resolve discrepancies detected between discovery sources and CMDB",
                "risk_level": "R2",
                "required_policies": ["cmdb", "data_quality"],
                "steps": [
                    {
                        "name": "Analyze Discrepancy",
                        "type": "ai_action",
                        "description": "Analyze the nature and impact of the discrepancy",
                        "instructions": "Review the discrepancy details and determine the root cause. "
                        "Assess business impact and recommend resolution approach.",
                        "task": "Analyze discrepancy and recommend resolution",
                        "output_schema": {
                            "root_cause": "string",
                            "impact": "string",
                            "resolution_options": "list",
                            "recommended_action": "string",
                        },
                        "policy_tags": ["discrepancy_handling"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "User Input",
                        "type": "user_input",
                        "description": "Get user confirmation for resolution approach",
                        "instructions": "Present resolution options to the user and get confirmation "
                        "on the preferred approach.",
                        "task": "Collect user decision",
                        "output_schema": {
                            "selected_action": "string",
                            "user_notes": "string",
                        },
                        "policy_tags": [],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Apply Resolution",
                        "type": "ai_action",
                        "description": "Apply the selected resolution",
                        "instructions": "Execute the user-selected resolution. Update CMDB or source "
                        "data as appropriate and mark discrepancy as resolved.",
                        "task": "Apply resolution and update records",
                        "output_schema": {
                            "resolution_applied": "boolean",
                            "changes_made": "list",
                            "audit_record": "object",
                        },
                        "policy_tags": ["cmdb_write", "audit_trail"],
                        "risk_level": "R2",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e11_workflows(self) -> list:
        """Get E11 Change Communications Agent workflows."""
        return [
            {
                "agent_type": "change_communications",
                "name": "Change Notification Workflow",
                "description": "Generate and send notifications for change requests",
                "risk_level": "R1",
                "required_policies": ["change_management", "communications"],
                "steps": [
                    {
                        "name": "Analyze Change Request",
                        "type": "ai_action",
                        "description": "Analyze the change request and determine notification requirements",
                        "instructions": "Review the change request details including type, scope, "
                        "impact, and timeline. Determine which stakeholder groups need to be notified.",
                        "task": "Analyze change and identify stakeholders",
                        "output_schema": {
                            "change_type": "string",
                            "impact_level": "string",
                            "affected_services": "list",
                            "stakeholder_groups": "list",
                            "notification_priority": "string",
                        },
                        "policy_tags": ["change_classification", "stakeholder_mapping"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Communications",
                        "type": "ai_action",
                        "description": "Generate communication content for each stakeholder group",
                        "instructions": "Use the appropriate template for each stakeholder group. "
                        "Customize the message with change details and ensure clarity.",
                        "task": "Generate notification content",
                        "output_schema": {
                            "communications": "list",
                            "templates_used": "list",
                            "personalization_applied": "boolean",
                        },
                        "policy_tags": ["communication_templates", "messaging_standards"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Send Notifications",
                        "type": "ai_action",
                        "description": "Send notifications through configured channels",
                        "instructions": "Dispatch notifications via Email, Teams, Slack, or ServiceNow "
                        "based on stakeholder preferences. Track delivery status.",
                        "task": "Send notifications and track delivery",
                        "output_schema": {
                            "sent_count": "number",
                            "delivery_status": "object",
                            "failed_deliveries": "list",
                        },
                        "policy_tags": ["notification_channels"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "change_communications",
                "name": "KB Article Generation Workflow",
                "description": "Generate or update KB articles for completed changes",
                "risk_level": "R2",
                "required_policies": ["knowledge_management", "documentation"],
                "steps": [
                    {
                        "name": "Analyze Change Completion",
                        "type": "ai_action",
                        "description": "Analyze completed change for KB article requirements",
                        "instructions": "Review the completed change including implementation details, "
                        "issues encountered, and resolutions. Determine if KB article is needed.",
                        "task": "Analyze change and determine KB requirements",
                        "output_schema": {
                            "kb_required": "boolean",
                            "article_type": "string",
                            "key_topics": "list",
                            "related_articles": "list",
                        },
                        "policy_tags": ["knowledge_classification"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate KB Content",
                        "type": "ai_action",
                        "description": "Generate KB article content",
                        "instructions": "Create comprehensive KB article content including problem "
                        "description, solution steps, and troubleshooting guidance.",
                        "task": "Generate KB article draft",
                        "output_schema": {
                            "title": "string",
                            "summary": "string",
                            "content_sections": "list",
                            "tags": "list",
                        },
                        "policy_tags": ["kb_templates", "documentation_standards"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Review and Approve",
                        "type": "approval_gate",
                        "description": "Review and approve KB article before publishing",
                        "instructions": "Review the generated KB article for accuracy and completeness. "
                        "Approve for publishing or request revisions.",
                        "task": "Approve KB article",
                        "output_schema": {
                            "approved": "boolean",
                            "revision_notes": "string",
                            "approver": "string",
                        },
                        "policy_tags": ["kb_approval"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "Publish Article",
                        "type": "ai_action",
                        "description": "Publish KB article to ServiceNow",
                        "instructions": "Create or update the KB article in ServiceNow. Link to the "
                        "change record and notify relevant stakeholders.",
                        "task": "Publish KB article",
                        "output_schema": {
                            "article_id": "string",
                            "article_url": "string",
                            "published_at": "string",
                        },
                        "policy_tags": ["kb_publishing"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "change_communications",
                "name": "Emergency Change Communication Workflow",
                "description": "Handle emergency change communications with expedited process",
                "risk_level": "R3",
                "required_policies": ["emergency_change", "communications", "escalation"],
                "steps": [
                    {
                        "name": "Identify Emergency Stakeholders",
                        "type": "ai_action",
                        "description": "Quickly identify all stakeholders for emergency notification",
                        "instructions": "For emergency changes, immediately identify all affected "
                        "stakeholders including on-call personnel, management, and affected users.",
                        "task": "Identify emergency stakeholders",
                        "output_schema": {
                            "primary_contacts": "list",
                            "escalation_chain": "list",
                            "affected_groups": "list",
                        },
                        "policy_tags": ["emergency_contacts", "escalation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Emergency Notification",
                        "type": "ai_action",
                        "description": "Generate emergency notification with high priority",
                        "instructions": "Create clear, concise emergency notification with immediate "
                        "action items, timeline, and contact information.",
                        "task": "Generate emergency notification",
                        "output_schema": {
                            "subject": "string",
                            "body": "string",
                            "action_items": "list",
                            "priority": "string",
                        },
                        "policy_tags": ["emergency_templates"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Immediate Dispatch",
                        "type": "ai_action",
                        "description": "Immediately dispatch notifications through all channels",
                        "instructions": "Send emergency notifications through all configured channels "
                        "simultaneously. Confirm receipt from critical stakeholders.",
                        "task": "Dispatch emergency notifications",
                        "output_schema": {
                            "channels_used": "list",
                            "confirmations": "list",
                            "pending_acknowledgments": "list",
                        },
                        "policy_tags": ["emergency_dispatch"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e14_workflows(self) -> list:
        """Get E14 Discovery Agent workflows."""
        return [
            {
                "agent_type": "discovery",
                "name": "Application Discovery Workflow",
                "description": "Discover and normalize applications from multiple sources",
                "risk_level": "R1",
                "required_policies": ["discovery", "application_catalog"],
                "steps": [
                    {
                        "name": "Collect Discovery Data",
                        "type": "ai_action",
                        "description": "Collect application data from discovery sources",
                        "instructions": "Connect to configured discovery sources (SCCM, Intune, AD) "
                        "and collect raw application data.",
                        "task": "Collect raw discovery data",
                        "output_schema": {
                            "source_type": "string",
                            "records_collected": "number",
                            "collection_timestamp": "string",
                            "errors": "list",
                        },
                        "policy_tags": ["discovery_sources"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Normalize Applications",
                        "type": "ai_action",
                        "description": "Normalize discovered applications to canonical form",
                        "instructions": "Apply normalization rules to standardize application names, "
                        "publishers, and versions. Match to existing catalog entries or create new ones.",
                        "task": "Normalize and deduplicate applications",
                        "output_schema": {
                            "normalized_count": "number",
                            "new_applications": "number",
                            "matched_existing": "number",
                            "normalization_failures": "number",
                        },
                        "policy_tags": ["normalization_rules", "catalog_matching"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Classify Applications",
                        "type": "ai_action",
                        "description": "Classify applications by category and management status",
                        "instructions": "Categorize applications (productivity, development, security, etc.) "
                        "and determine management status (managed, unmanaged, shadow IT).",
                        "task": "Classify and categorize applications",
                        "output_schema": {
                            "categories": "object",
                            "managed_count": "number",
                            "unmanaged_count": "number",
                            "shadow_it_count": "number",
                        },
                        "policy_tags": ["application_categories", "management_policies"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Discovery Report",
                        "type": "ai_action",
                        "description": "Generate comprehensive discovery report",
                        "instructions": "Create a summary report of discovery findings including "
                        "new applications, shadow IT, and recommendations.",
                        "task": "Generate discovery report",
                        "output_schema": {
                            "report_id": "string",
                            "summary": "object",
                            "recommendations": "list",
                        },
                        "policy_tags": ["reporting"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "discovery",
                "name": "License Gap Analysis Workflow",
                "description": "Analyze license gaps between deployed and entitled software",
                "risk_level": "R2",
                "required_policies": ["license_management", "compliance"],
                "steps": [
                    {
                        "name": "Collect Deployment Data",
                        "type": "ai_action",
                        "description": "Collect current deployment counts from discovery",
                        "instructions": "Aggregate deployment counts for all managed applications "
                        "from the latest discovery data.",
                        "task": "Collect deployment statistics",
                        "output_schema": {
                            "applications_analyzed": "number",
                            "total_deployments": "number",
                            "by_application": "object",
                        },
                        "policy_tags": ["deployment_tracking"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Compare with Entitlements",
                        "type": "ai_action",
                        "description": "Compare deployments with license entitlements",
                        "instructions": "Match deployment counts against license entitlements. "
                        "Identify over-deployed, under-licensed, and missing licenses.",
                        "task": "Analyze license gaps",
                        "output_schema": {
                            "gaps_found": "number",
                            "over_deployed": "list",
                            "under_licensed": "list",
                            "missing_license": "list",
                            "estimated_cost": "number",
                        },
                        "policy_tags": ["license_compliance", "entitlement_mapping"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Risk Assessment",
                        "type": "ai_action",
                        "description": "Assess compliance risk for each gap",
                        "instructions": "Evaluate each license gap for compliance risk including "
                        "audit exposure, financial impact, and vendor relationship.",
                        "task": "Assess license gap risks",
                        "output_schema": {
                            "critical_gaps": "number",
                            "high_risk_gaps": "number",
                            "risk_details": "list",
                            "total_exposure": "number",
                        },
                        "policy_tags": ["risk_assessment", "compliance"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Remediation Review",
                        "type": "approval_gate",
                        "description": "Review and approve remediation plan",
                        "instructions": "Review identified license gaps and approve remediation "
                        "actions (purchase licenses, remove deployments, or accept risk).",
                        "task": "Approve license gap remediation",
                        "output_schema": {
                            "approved_actions": "list",
                            "deferred_actions": "list",
                            "risk_accepted": "list",
                        },
                        "policy_tags": ["license_remediation", "approval"],
                        "risk_level": "R2",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "discovery",
                "name": "Patch Gap Analysis Workflow",
                "description": "Identify applications with missing security patches or EOL versions",
                "risk_level": "R2",
                "required_policies": ["patch_management", "security"],
                "steps": [
                    {
                        "name": "Collect Version Data",
                        "type": "ai_action",
                        "description": "Collect current version data for all applications",
                        "instructions": "Aggregate version information for all discovered applications "
                        "including major, minor, and patch versions.",
                        "task": "Collect application versions",
                        "output_schema": {
                            "applications_analyzed": "number",
                            "versions_collected": "number",
                            "version_distribution": "object",
                        },
                        "policy_tags": ["version_tracking"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Check EOL Status",
                        "type": "ai_action",
                        "description": "Check versions against EOL data",
                        "instructions": "Compare deployed versions against known EOL dates. "
                        "Flag applications running EOL versions.",
                        "task": "Identify EOL versions",
                        "output_schema": {
                            "eol_count": "number",
                            "eol_applications": "list",
                            "approaching_eol": "list",
                        },
                        "policy_tags": ["eol_data", "lifecycle_management"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Identify Security Gaps",
                        "type": "ai_action",
                        "description": "Identify applications missing security updates",
                        "instructions": "Check for applications without latest security patches. "
                        "Cross-reference with CVE data if available.",
                        "task": "Identify security patch gaps",
                        "output_schema": {
                            "security_gaps": "number",
                            "critical_cves": "list",
                            "high_cves": "list",
                            "affected_devices": "number",
                        },
                        "policy_tags": ["security_patches", "vulnerability_data"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Patch Report",
                        "type": "ai_action",
                        "description": "Generate patch gap report with recommendations",
                        "instructions": "Create comprehensive patch gap report including severity, "
                        "affected devices, and remediation recommendations.",
                        "task": "Generate patch gap report",
                        "output_schema": {
                            "report_id": "string",
                            "total_gaps": "number",
                            "severity_breakdown": "object",
                            "recommendations": "list",
                        },
                        "policy_tags": ["reporting", "remediation"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "discovery",
                "name": "Shadow IT Detection Workflow",
                "description": "Detect and analyze unauthorized shadow IT applications",
                "risk_level": "R2",
                "required_policies": ["shadow_it", "security", "compliance"],
                "steps": [
                    {
                        "name": "Identify Unapproved Applications",
                        "type": "ai_action",
                        "description": "Identify applications not in approved catalog",
                        "instructions": "Compare discovered applications against the approved "
                        "application catalog. Flag all unapproved applications.",
                        "task": "Identify shadow IT applications",
                        "output_schema": {
                            "shadow_it_count": "number",
                            "applications": "list",
                            "install_counts": "object",
                        },
                        "policy_tags": ["approved_catalog", "shadow_it_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Risk Analysis",
                        "type": "ai_action",
                        "description": "Analyze security and compliance risks",
                        "instructions": "Evaluate each shadow IT application for security risks, "
                        "data exposure, and compliance violations.",
                        "task": "Analyze shadow IT risks",
                        "output_schema": {
                            "high_risk_apps": "list",
                            "data_risk_apps": "list",
                            "compliance_risks": "list",
                            "risk_score": "number",
                        },
                        "policy_tags": ["risk_assessment", "security"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Remediation Planning",
                        "type": "ai_action",
                        "description": "Plan remediation for shadow IT",
                        "instructions": "Develop remediation plan for each shadow IT application: "
                        "block, allow with conditions, or add to approved catalog.",
                        "task": "Create remediation plan",
                        "output_schema": {
                            "block_list": "list",
                            "conditional_allow": "list",
                            "catalog_additions": "list",
                        },
                        "policy_tags": ["remediation", "catalog_management"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Approval and Enforcement",
                        "type": "approval_gate",
                        "description": "Approve and enforce shadow IT remediation",
                        "instructions": "Review shadow IT findings and approve enforcement actions. "
                        "Escalate high-risk items for management review.",
                        "task": "Approve shadow IT remediation",
                        "output_schema": {
                            "approved_actions": "list",
                            "escalated_items": "list",
                            "enforcement_date": "string",
                        },
                        "policy_tags": ["approval", "enforcement"],
                        "risk_level": "R2",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e12_workflows(self) -> list:
        """Get E12 Documentation Agent workflows."""
        return [
            {
                "agent_type": "documentation",
                "name": "Documentation Generation Workflow",
                "description": "Automatically generate comprehensive documentation from codebase",
                "risk_level": "R1",
                "required_policies": ["documentation_standards"],
                "steps": [
                    {
                        "name": "Fetch Repository",
                        "type": "ai_action",
                        "description": "Clone or pull latest from repository",
                        "instructions": "Fetch the latest code from the configured repository.",
                        "task": "Retrieve repository code",
                        "output_schema": {"repository_path": "string", "commit_sha": "string"},
                        "policy_tags": ["repository_access"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Analyze Structure",
                        "type": "ai_action",
                        "description": "Analyze code structure and dependencies",
                        "instructions": "Analyze the codebase structure, identify modules, classes, and dependencies.",
                        "task": "Extract code structure",
                        "output_schema": {"modules": "list", "dependencies": "list"},
                        "policy_tags": ["code_analysis"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Extract Docstrings",
                        "type": "ai_action",
                        "description": "Extract existing documentation and comments",
                        "instructions": "Extract docstrings, comments, and existing documentation from code.",
                        "task": "Extract documentation",
                        "output_schema": {"docstrings": "list", "comments": "list"},
                        "policy_tags": ["documentation_extraction"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Identify Patterns",
                        "type": "ai_action",
                        "description": "Identify architectural patterns and abstractions",
                        "instructions": "Identify design patterns, architectural patterns, and code abstractions.",
                        "task": "Identify patterns",
                        "output_schema": {"patterns": "list", "abstractions": "list"},
                        "policy_tags": ["architecture"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Documentation",
                        "type": "ai_action",
                        "description": "Generate documentation using templates and LLM",
                        "instructions": "Generate comprehensive documentation using templates and AI assistance.",
                        "task": "Generate docs",
                        "output_schema": {"documents": "list"},
                        "policy_tags": ["documentation_generation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Review Quality",
                        "type": "ai_action",
                        "description": "Review generated documentation quality",
                        "instructions": "Review documentation quality and completeness.",
                        "task": "Review quality",
                        "output_schema": {"quality_score": "number", "issues": "list"},
                        "policy_tags": ["quality_assurance"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Publish Documentation",
                        "type": "approval_gate",
                        "description": "Publish documentation to target location",
                        "instructions": "Review generated documentation before publishing.",
                        "task": "Publish docs",
                        "output_schema": {"published": "boolean", "target_path": "string"},
                        "policy_tags": ["publishing"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "Index in Knowledge Base",
                        "type": "ai_action",
                        "description": "Index documentation in vector store for RAG",
                        "instructions": "Index documentation in the knowledge base for retrieval.",
                        "task": "Index docs",
                        "output_schema": {"indexed": "boolean"},
                        "policy_tags": ["knowledge_base"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e13_workflows(self) -> list:
        """Get E13 Automation Advisor Agent workflows."""
        return [
            {
                "agent_type": "automation_advisor",
                "name": "Automation Advisor Workflow",
                "description": "Detect automation opportunities and calculate ROI",
                "risk_level": "R1",
                "required_policies": ["automation_policy", "roi_thresholds"],
                "steps": [
                    {
                        "name": "Collect Operational Data",
                        "type": "ai_action",
                        "description": "Collect incident, request, and change data",
                        "instructions": "Collect operational data from ServiceNow and other sources.",
                        "task": "Collect data",
                        "output_schema": {"incidents": "list", "requests": "list", "changes": "list"},
                        "policy_tags": ["data_collection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Analyze Patterns",
                        "type": "ai_action",
                        "description": "Detect repetitive, manual, and error-prone patterns",
                        "instructions": "Analyze data to detect automation opportunity patterns.",
                        "task": "Detect patterns",
                        "output_schema": {"patterns": "list"},
                        "policy_tags": ["pattern_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Score Candidates",
                        "type": "ai_action",
                        "description": "Score automation candidates by impact and complexity",
                        "instructions": "Score each automation candidate based on frequency, time impact, and complexity.",  # noqa: E501
                        "task": "Score candidates",
                        "output_schema": {"candidates": "list", "scores": "list"},
                        "policy_tags": ["scoring"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Calculate ROI",
                        "type": "ai_action",
                        "description": "Calculate ROI for each candidate",
                        "instructions": "Calculate ROI, payback period, and annual savings for each candidate.",
                        "task": "Calculate ROI",
                        "output_schema": {"roi_data": "list"},
                        "policy_tags": ["roi_calculation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Recommendations",
                        "type": "ai_action",
                        "description": "Generate ranked recommendations with approaches",
                        "instructions": "Generate ranked recommendations with implementation approaches.",
                        "task": "Generate recommendations",
                        "output_schema": {"recommendations": "list"},
                        "policy_tags": ["recommendations"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Publish Report",
                        "type": "ai_action",
                        "description": "Publish automation opportunity report",
                        "instructions": "Publish the automation opportunity report.",
                        "task": "Publish report",
                        "output_schema": {"published": "boolean"},
                        "policy_tags": ["reporting"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e15_workflows(self) -> list:
        """Get E15 IAM Security Agent workflows."""
        return [
            {
                "agent_type": "iam_security",
                "name": "IAM Security Workflow",
                "description": "Monitor identity provider access logs and detect security anomalies",
                "risk_level": "R2",
                "required_policies": ["security_policy", "access_control_policy"],
                "steps": [
                    {
                        "name": "Collect Events",
                        "type": "ai_action",
                        "description": "Collect sign-in and audit events from identity providers",
                        "instructions": "Collect sign-in logs and audit events from configured identity providers.",
                        "task": "Collect events",
                        "output_schema": {"sign_ins": "list", "audit_events": "list"},
                        "policy_tags": ["event_collection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Analyze Patterns",
                        "type": "ai_action",
                        "description": "Analyze events for anomalous patterns",
                        "instructions": "Analyze events to identify anomalous patterns and behaviors.",
                        "task": "Analyze patterns",
                        "output_schema": {"patterns": "list"},
                        "policy_tags": ["pattern_analysis"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Detect Anomalies",
                        "type": "ai_action",
                        "description": "Apply detection rules and identify anomalies",
                        "instructions": "Apply detection rules to identify security anomalies.",
                        "task": "Detect anomalies",
                        "output_schema": {"anomalies": "list"},
                        "policy_tags": ["anomaly_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Assess Severity",
                        "type": "ai_action",
                        "description": "Assess severity and priority of detected anomalies",
                        "instructions": "Assess the severity and priority of each detected anomaly.",
                        "task": "Assess severity",
                        "output_schema": {"assessments": "list"},
                        "policy_tags": ["severity_assessment"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Alerts",
                        "type": "ai_action",
                        "description": "Generate and send security alerts",
                        "instructions": "Generate and send security alerts to stakeholders.",
                        "task": "Generate alerts",
                        "output_schema": {"alerts_sent": "list"},
                        "policy_tags": ["alerting"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Recommend Response",
                        "type": "approval_gate",
                        "description": "Recommend response actions for critical anomalies",
                        "instructions": "Review and approve security response actions for critical anomalies.",
                        "task": "Recommend response",
                        "output_schema": {"recommended_actions": "list"},
                        "policy_tags": ["response_planning"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "Execute Response",
                        "type": "approval_gate",
                        "description": "Execute approved response actions",
                        "instructions": "CRITICAL: Confirm security action execution.",
                        "task": "Execute response",
                        "output_schema": {"actions_executed": "list"},
                        "policy_tags": ["response_execution"],
                        "risk_level": "R3",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e16_workflows(self) -> list:
        """Get E16 Request Coordination Agent workflows."""
        return [
            {
                "agent_type": "request_coordination",
                "name": "Request Coordination Workflow",
                "description": "Sync requests from ServiceNow, track SLA status, detect changes, and trigger escalations",
                "risk_level": "R1",
                "required_policies": ["sla_policy", "escalation_policy"],
                "steps": [
                    {
                        "name": "Sync Requests",
                        "type": "ai_action",
                        "description": "Sync request status from ServiceNow",
                        "instructions": "Sync request status from ServiceNow for all tracked requests.",
                        "task": "Sync requests",
                        "output_schema": {"synced_count": "integer", "requests": "list"},
                        "policy_tags": ["request_sync"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Check SLA Status",
                        "type": "ai_action",
                        "description": "Check SLA status for all tracked requests",
                        "instructions": "Check SLA status and identify requests at risk or breached.",
                        "task": "Check SLA status",
                        "output_schema": {"at_risk": "list", "breached": "list"},
                        "policy_tags": ["sla_tracking"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Detect Status Changes",
                        "type": "ai_action",
                        "description": "Detect requests with status changes since last check",
                        "instructions": "Detect requests with status changes and prepare notifications.",
                        "task": "Detect status changes",
                        "output_schema": {"changed_requests": "list"},
                        "policy_tags": ["change_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Identify Blocked",
                        "type": "ai_action",
                        "description": "Identify blocked or stalled requests",
                        "instructions": "Identify requests that are blocked or stalled.",
                        "task": "Identify blocked",
                        "output_schema": {"blocked_requests": "list"},
                        "policy_tags": ["blocked_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Send Updates",
                        "type": "ai_action",
                        "description": "Send status update notifications to stakeholders",
                        "instructions": "Send status update notifications to stakeholders.",
                        "task": "Send updates",
                        "output_schema": {"notifications_sent": "list"},
                        "policy_tags": ["notification"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Trigger Escalations",
                        "type": "approval_gate",
                        "description": "Trigger escalations based on rules",
                        "instructions": "Review escalation before notifying management.",
                        "task": "Trigger escalations",
                        "output_schema": {"escalations_triggered": "list"},
                        "policy_tags": ["escalation"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "Generate Digest",
                        "type": "ai_action",
                        "description": "Generate periodic digest for managers",
                        "instructions": "Generate periodic digest report for managers.",
                        "task": "Generate digest",
                        "output_schema": {"digest": "object"},
                        "policy_tags": ["reporting"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e17_workflows(self) -> list:
        """Get E17 SecOps Agent workflows."""
        return [
            {
                "agent_type": "secops",
                "name": "secops_vulnerability_workflow",
                "description": "Vulnerability scanning, correlation, risk assessment, and remediation planning",
                "risk_level": "R2",
                "required_policies": ["security_policy", "patch_management_policy", "change_management_policy"],
                "steps": [
                    {
                        "name": "sync_vulnerabilities",
                        "type": "ai_action",
                        "description": "Sync latest vulnerability scan results",
                        "instructions": "Sync vulnerabilities from configured scanners (Qualys, Nessus, Defender).",
                        "task": "Sync vulnerabilities",
                        "output_schema": {"synced_count": "integer", "vulnerabilities": "list"},
                        "policy_tags": ["vulnerability_scanning"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "correlate_assets",
                        "type": "ai_action",
                        "description": "Correlate vulnerabilities with application inventory",
                        "instructions": "Match vulnerabilities to installed applications and assets.",
                        "task": "Correlate vulnerabilities",
                        "output_schema": {"correlated_instances": "list"},
                        "policy_tags": ["asset_correlation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "calculate_risk",
                        "type": "ai_action",
                        "description": "Calculate risk scores and prioritize",
                        "instructions": "Calculate risk scores based on CVSS, exploitability, and asset criticality.",
                        "task": "Calculate risk scores",
                        "output_schema": {"risk_scores": "list", "prioritized": "list"},
                        "policy_tags": ["risk_assessment"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "check_compliance",
                        "type": "ai_action",
                        "description": "Check affected assets against compliance baselines",
                        "instructions": "Check compliance status for affected assets.",
                        "task": "Check compliance",
                        "output_schema": {"compliance_status": "object"},
                        "policy_tags": ["compliance"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "generate_remediation_plan",
                        "type": "ai_action",
                        "description": "Generate remediation plan for critical/high vulnerabilities",
                        "instructions": "Generate remediation plans with steps and risk levels.",
                        "task": "Generate remediation plans",
                        "output_schema": {"remediation_plans": "list"},
                        "policy_tags": ["remediation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "execute_remediation",
                        "type": "approval_gate",
                        "description": "Execute approved remediation actions",
                        "instructions": "CRITICAL: Review and approve remediation actions before execution.",
                        "task": "Execute remediation",
                        "output_schema": {"executed": "boolean", "results": "list"},
                        "policy_tags": ["remediation_execution"],
                        "risk_level": "R3",
                    },
                    {
                        "name": "verify_remediation",
                        "type": "ai_action",
                        "description": "Verify remediation was successful",
                        "instructions": "Verify vulnerabilities are remediated.",
                        "task": "Verify remediation",
                        "output_schema": {"verified": "boolean", "remaining": "list"},
                        "policy_tags": ["verification"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "update_compliance_status",
                        "type": "ai_action",
                        "description": "Update compliance status post-remediation",
                        "instructions": "Update compliance status after remediation.",
                        "task": "Update compliance",
                        "output_schema": {"updated": "boolean"},
                        "policy_tags": ["compliance"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "secops",
                "name": "secops_compliance_workflow",
                "description": "Compliance baseline checking and drift detection",
                "risk_level": "R1",
                "required_policies": ["compliance_policy"],
                "steps": [
                    {
                        "name": "Select Baseline",
                        "type": "ai_action",
                        "description": "Select compliance baseline to check",
                        "instructions": "Select appropriate compliance baseline (CIS, NIST, SOC2, ISO27001).",
                        "task": "Select baseline",
                        "output_schema": {"baseline": "string"},
                        "policy_tags": ["compliance"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Run Compliance Check",
                        "type": "ai_action",
                        "description": "Run compliance check against baseline",
                        "instructions": "Execute compliance checks for all assets.",
                        "task": "Run compliance checks",
                        "output_schema": {"check_results": "list"},
                        "policy_tags": ["compliance"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Detect Drift",
                        "type": "ai_action",
                        "description": "Detect compliance drift",
                        "instructions": "Compare current state to baseline and detect drift.",
                        "task": "Detect drift",
                        "output_schema": {"drift_detected": "list"},
                        "policy_tags": ["drift_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Report",
                        "type": "ai_action",
                        "description": "Generate compliance report",
                        "instructions": "Generate compliance report with scores and recommendations.",
                        "task": "Generate report",
                        "output_schema": {"report": "object"},
                        "policy_tags": ["reporting"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "secops",
                "name": "secops_siem_response_workflow",
                "description": "SIEM alert correlation and incident response",
                "risk_level": "R2",
                "required_policies": ["security_policy", "incident_response"],
                "steps": [
                    {
                        "name": "Sync SIEM Alerts",
                        "type": "ai_action",
                        "description": "Sync alerts from SIEM platforms",
                        "instructions": "Sync security alerts from Sentinel, Splunk, QRadar.",
                        "task": "Sync alerts",
                        "output_schema": {"alerts": "list"},
                        "policy_tags": ["siem_integration"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Correlate with Vulnerabilities",
                        "type": "ai_action",
                        "description": "Correlate alerts with known vulnerabilities",
                        "instructions": "Match alerts to known vulnerabilities.",
                        "task": "Correlate alerts",
                        "output_schema": {"correlated": "list"},
                        "policy_tags": ["correlation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Assess Severity",
                        "type": "ai_action",
                        "description": "Assess alert severity and impact",
                        "instructions": "Assess alert severity and business impact.",
                        "task": "Assess severity",
                        "output_schema": {"severity": "string", "impact": "string"},
                        "policy_tags": ["risk_assessment"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Create Incident",
                        "type": "approval_gate",
                        "description": "Create security incident",
                        "instructions": "CRITICAL: Review before creating incident.",
                        "task": "Create incident",
                        "output_schema": {"incident_id": "string"},
                        "policy_tags": ["incident_management"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "Generate Response Plan",
                        "type": "ai_action",
                        "description": "Generate incident response plan",
                        "instructions": "Generate response plan with remediation steps.",
                        "task": "Generate response plan",
                        "output_schema": {"response_plan": "object"},
                        "policy_tags": ["incident_response"],
                        "risk_level": "R2",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e18_workflows(self) -> list:
        """Get E18 SRE Agent workflows."""
        return [
            {
                "agent_type": "sre",
                "name": "sre_self_healing_workflow",
                "description": "Self-healing automation with monitoring and remediation",
                "risk_level": "R2",
                "required_policies": ["operations_policy", "change_management_policy"],
                "steps": [
                    {
                        "name": "collect_metrics",
                        "type": "ai_action",
                        "description": "Collect metrics from monitoring platforms",
                        "instructions": "Collect metrics from Prometheus, Datadog, Azure Monitor.",
                        "task": "Collect metrics",
                        "output_schema": {"metrics": "object"},
                        "policy_tags": ["monitoring"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "check_health_endpoints",
                        "type": "ai_action",
                        "description": "Check all configured health endpoints",
                        "instructions": "Check health endpoints and record results.",
                        "task": "Check health endpoints",
                        "output_schema": {"health_results": "list"},
                        "policy_tags": ["health_checks"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "evaluate_slos",
                        "type": "ai_action",
                        "description": "Evaluate SLO compliance and error budget",
                        "instructions": "Evaluate SLO compliance and calculate error budget burn rate.",
                        "task": "Evaluate SLOs",
                        "output_schema": {"slo_status": "list"},
                        "policy_tags": ["slo_tracking"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "detect_anomalies",
                        "type": "ai_action",
                        "description": "Detect anomalies and degradation patterns",
                        "instructions": "Detect anomalies and degradation patterns.",
                        "task": "Detect anomalies",
                        "output_schema": {"anomalies": "list"},
                        "policy_tags": ["anomaly_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "trigger_self_healing",
                        "type": "approval_gate",
                        "description": "Trigger self-healing rules if conditions met",
                        "instructions": "Review self-healing triggers before execution.",
                        "task": "Trigger self-healing",
                        "output_schema": {"triggered_rules": "list"},
                        "policy_tags": ["self_healing"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "execute_remediation",
                        "type": "ai_action",
                        "description": "Execute remediation scripts",
                        "instructions": "Execute PowerShell or other remediation scripts.",
                        "task": "Execute remediation",
                        "output_schema": {"executed": "boolean", "results": "list"},
                        "policy_tags": ["remediation"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "verify_recovery",
                        "type": "ai_action",
                        "description": "Verify system recovery after remediation",
                        "instructions": "Verify system recovery and health restoration.",
                        "task": "Verify recovery",
                        "output_schema": {"recovered": "boolean", "metrics": "object"},
                        "policy_tags": ["verification"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "update_metrics",
                        "type": "ai_action",
                        "description": "Update metrics and SLO status",
                        "instructions": "Update metrics and SLO status after remediation.",
                        "task": "Update metrics",
                        "output_schema": {"updated": "boolean"},
                        "policy_tags": ["metrics"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "sre",
                "name": "sre_slo_monitoring_workflow",
                "description": "Continuous SLO monitoring and error budget tracking",
                "risk_level": "R1",
                "required_policies": ["slo_policy"],
                "steps": [
                    {
                        "name": "Collect SLO Metrics",
                        "type": "ai_action",
                        "description": "Collect SLO metrics from monitoring",
                        "instructions": "Collect SLO metrics for all active SLOs.",
                        "task": "Collect SLO metrics",
                        "output_schema": {"metrics": "list"},
                        "policy_tags": ["slo_tracking"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Calculate Error Budget",
                        "type": "ai_action",
                        "description": "Calculate error budget remaining",
                        "instructions": "Calculate error budget burn rate and remaining budget.",
                        "task": "Calculate error budget",
                        "output_schema": {"error_budgets": "list"},
                        "policy_tags": ["error_budget"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Detect Budget Alerts",
                        "type": "ai_action",
                        "description": "Detect error budget alerts",
                        "instructions": "Detect SLOs with error budget alerts.",
                        "task": "Detect alerts",
                        "output_schema": {"alerts": "list"},
                        "policy_tags": ["alerting"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate SLO Report",
                        "type": "ai_action",
                        "description": "Generate SLO compliance report",
                        "instructions": "Generate SLO compliance report.",
                        "task": "Generate report",
                        "output_schema": {"report": "object"},
                        "policy_tags": ["reporting"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "sre",
                "name": "sre_runbook_workflow",
                "description": "Runbook execution with step-by-step guidance",
                "risk_level": "R1",
                "required_policies": ["runbook_policy"],
                "steps": [
                    {
                        "name": "Select Runbook",
                        "type": "ai_action",
                        "description": "Select appropriate runbook",
                        "instructions": "Select runbook based on incident type.",
                        "task": "Select runbook",
                        "output_schema": {"runbook": "string"},
                        "policy_tags": ["runbook_selection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Execute Steps",
                        "type": "ai_action",
                        "description": "Execute runbook steps",
                        "instructions": "Execute runbook steps sequentially.",
                        "task": "Execute steps",
                        "output_schema": {"step_results": "list"},
                        "policy_tags": ["runbook_execution"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Collect Evidence",
                        "type": "ai_action",
                        "description": "Collect evidence during execution",
                        "instructions": "Collect evidence for each step.",
                        "task": "Collect evidence",
                        "output_schema": {"evidence": "list"},
                        "policy_tags": ["evidence_collection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Verify Completion",
                        "type": "ai_action",
                        "description": "Verify runbook completion",
                        "instructions": "Verify all steps completed successfully.",
                        "task": "Verify completion",
                        "output_schema": {"completed": "boolean"},
                        "policy_tags": ["verification"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e21_workflows(self) -> list:
        """Get E21 KB & Triage Agent workflows."""
        return [
            {
                "agent_type": "kb_triage",
                "name": "kb_triage_workflow",
                "description": "AI-powered ticket triage with knowledge synthesis",
                "risk_level": "R1",
                "required_policies": ["incident_management_policy"],
                "steps": [
                    {
                        "name": "parse_incident",
                        "type": "ai_action",
                        "description": "Parse incident description and extract key information",
                        "instructions": "Parse incident description and extract entities, symptoms, and context.",
                        "task": "Parse incident",
                        "output_schema": {"entities": "object", "symptoms": "list"},
                        "policy_tags": ["incident_parsing"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "search_knowledge",
                        "type": "ai_action",
                        "description": "Search knowledge base for relevant articles",
                        "instructions": "Perform semantic search across knowledge sources.",
                        "task": "Search knowledge",
                        "output_schema": {"articles": "list"},
                        "policy_tags": ["knowledge_search"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "categorize_incident",
                        "type": "ai_action",
                        "description": "Determine category and subcategory",
                        "instructions": "Categorize incident using AI and knowledge context.",
                        "task": "Categorize incident",
                        "output_schema": {"category": "string", "subcategory": "string", "confidence": "float"},
                        "policy_tags": ["categorization"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "assess_priority",
                        "type": "ai_action",
                        "description": "Assess priority and urgency",
                        "instructions": "Assess priority based on impact and urgency.",
                        "task": "Assess priority",
                        "output_schema": {"priority": "string", "urgency": "string"},
                        "policy_tags": ["priority_assessment"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "check_duplicates",
                        "type": "ai_action",
                        "description": "Check for duplicate or related incidents",
                        "instructions": "Check for duplicate or related incidents.",
                        "task": "Check duplicates",
                        "output_schema": {"duplicates": "list", "related": "list"},
                        "policy_tags": ["duplicate_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "generate_resolution",
                        "type": "ai_action",
                        "description": "Generate step-by-step resolution guidance",
                        "instructions": "Generate step-by-step resolution steps from knowledge articles.",
                        "task": "Generate resolution",
                        "output_schema": {"resolution_steps": "list"},
                        "policy_tags": ["resolution_generation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "suggest_assignment",
                        "type": "ai_action",
                        "description": "Suggest assignment group",
                        "instructions": "Suggest assignment group based on category and priority.",
                        "task": "Suggest assignment",
                        "output_schema": {"assignment_group": "string"},
                        "policy_tags": ["assignment"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "detect_patterns",
                        "type": "ai_action",
                        "description": "Check for incident patterns",
                        "instructions": "Detect recurring or trending incident patterns.",
                        "task": "Detect patterns",
                        "output_schema": {"patterns": "list"},
                        "policy_tags": ["pattern_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "present_triage",
                        "type": "ai_action",
                        "description": "Present triage results to agent",
                        "instructions": "Present triage results with confidence scores and recommendations.",
                        "task": "Present triage",
                        "output_schema": {"triage_results": "object"},
                        "policy_tags": ["presentation"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "kb_triage",
                "name": "kb_pattern_detection_workflow",
                "description": "Detect incident patterns and trends",
                "risk_level": "R1",
                "required_policies": ["pattern_detection"],
                "steps": [
                    {
                        "name": "Analyze Incident History",
                        "type": "ai_action",
                        "description": "Analyze historical incidents",
                        "instructions": "Analyze historical incidents for patterns.",
                        "task": "Analyze history",
                        "output_schema": {"analysis": "object"},
                        "policy_tags": ["pattern_analysis"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Detect Recurring Patterns",
                        "type": "ai_action",
                        "description": "Detect recurring incident patterns",
                        "instructions": "Detect recurring patterns in incidents.",
                        "task": "Detect recurring",
                        "output_schema": {"recurring_patterns": "list"},
                        "policy_tags": ["pattern_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Detect Trending Issues",
                        "type": "ai_action",
                        "description": "Detect trending issues",
                        "instructions": "Detect trending issues and spikes.",
                        "task": "Detect trending",
                        "output_schema": {"trending": "list"},
                        "policy_tags": ["trend_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Correlate with Changes",
                        "type": "ai_action",
                        "description": "Correlate patterns with changes",
                        "instructions": "Correlate incident patterns with recent changes.",
                        "task": "Correlate changes",
                        "output_schema": {"correlations": "list"},
                        "policy_tags": ["change_correlation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Pattern Report",
                        "type": "ai_action",
                        "description": "Generate pattern detection report",
                        "instructions": "Generate report on detected patterns.",
                        "task": "Generate report",
                        "output_schema": {"report": "object"},
                        "policy_tags": ["reporting"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "kb_triage",
                "name": "kb_knowledge_sync_workflow",
                "description": "Synchronize knowledge sources",
                "risk_level": "R1",
                "required_policies": ["knowledge_management"],
                "steps": [
                    {
                        "name": "Select Source",
                        "type": "ai_action",
                        "description": "Select knowledge source to sync",
                        "instructions": "Select knowledge source (ServiceNow KB, Confluence, etc.).",
                        "task": "Select source",
                        "output_schema": {"source": "string"},
                        "policy_tags": ["source_selection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Fetch Articles",
                        "type": "ai_action",
                        "description": "Fetch articles from source",
                        "instructions": "Fetch articles from knowledge source.",
                        "task": "Fetch articles",
                        "output_schema": {"articles": "list"},
                        "policy_tags": ["article_fetch"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Generate Embeddings",
                        "type": "ai_action",
                        "description": "Generate embeddings for semantic search",
                        "instructions": "Generate vector embeddings for articles using E7 pgvector.",
                        "task": "Generate embeddings",
                        "output_schema": {"embeddings_generated": "integer"},
                        "policy_tags": ["embedding_generation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "Index Articles",
                        "type": "ai_action",
                        "description": "Index articles in knowledge base",
                        "instructions": "Index articles with embeddings for semantic search.",
                        "task": "Index articles",
                        "output_schema": {"indexed": "integer"},
                        "policy_tags": ["indexing"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e19_workflows(self) -> list:
        """Get E19 SLA Governance Agent workflows."""
        return [
            {
                "agent_type": "sla_governance",
                "name": "sla_creation_workflow",
                "description": "Create SLA from natural language request",
                "risk_level": "R2",
                "required_policies": ["sla_policy", "contract_policy"],
                "steps": [
                    {
                        "name": "parse_request",
                        "type": "ai_action",
                        "description": "Parse natural language SLA request",
                        "instructions": "Parse the user's natural language request and extract service name, targets, and requirements.",
                        "task": "Parse SLA request",
                        "output_schema": {"service": "string", "targets": "list", "requirements": "object"},
                        "policy_tags": ["sla_parsing"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "identify_service",
                        "type": "ai_action",
                        "description": "Identify or create service catalog item",
                        "instructions": "Identify existing service or create new service catalog item.",
                        "task": "Identify service",
                        "output_schema": {"service_id": "string", "created": "boolean"},
                        "policy_tags": ["service_catalog"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "generate_sla_draft",
                        "type": "ai_action",
                        "description": "Generate SLA definition draft",
                        "instructions": "Generate SLA definition with targets and thresholds.",
                        "task": "Generate SLA draft",
                        "output_schema": {"sla_draft": "object"},
                        "policy_tags": ["sla_generation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "define_targets",
                        "type": "ai_action",
                        "description": "Define SLA targets and thresholds",
                        "instructions": "Define availability, response time, resolution time, and quality targets.",
                        "task": "Define targets",
                        "output_schema": {"targets": "list"},
                        "policy_tags": ["target_definition"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "link_kpis",
                        "type": "ai_action",
                        "description": "Link or create KPIs for measurement",
                        "instructions": "Link existing KPIs or create new KPIs for SLA measurement.",
                        "task": "Link KPIs",
                        "output_schema": {"kpi_links": "list"},
                        "policy_tags": ["kpi_linking"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "review_and_approve",
                        "type": "approval_gate",
                        "description": "Submit for review and approval",
                        "instructions": "Review SLA definition before activation. Approve for R1 (low risk) or escalate for R2/R3.",
                        "task": "Review and approve SLA",
                        "output_schema": {"approved": "boolean", "approver": "string", "conditions": "list"},
                        "policy_tags": ["sla_approval"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "activate_sla",
                        "type": "approval_gate",
                        "description": "Activate SLA and begin monitoring",
                        "instructions": "Activate SLA and begin compliance monitoring.",
                        "task": "Activate SLA",
                        "output_schema": {"activated": "boolean", "monitoring_started": "boolean"},
                        "policy_tags": ["sla_activation"],
                        "risk_level": "R2",
                    },
                ],
                "is_active": True,
            },
            {
                "agent_type": "sla_governance",
                "name": "sla_monitoring_workflow",
                "description": "Monitor SLA compliance and detect breaches",
                "risk_level": "R1",
                "required_policies": ["sla_policy"],
                "steps": [
                    {
                        "name": "collect_measurements",
                        "type": "ai_action",
                        "description": "Collect KPI measurements",
                        "instructions": "Collect KPI measurements from data sources.",
                        "task": "Collect measurements",
                        "output_schema": {"measurements": "list"},
                        "policy_tags": ["measurement_collection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "calculate_compliance",
                        "type": "ai_action",
                        "description": "Calculate SLA compliance",
                        "instructions": "Calculate compliance for each SLA target and overall compliance.",
                        "task": "Calculate compliance",
                        "output_schema": {"compliance": "object"},
                        "policy_tags": ["compliance_calculation"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "detect_breaches",
                        "type": "ai_action",
                        "description": "Detect SLA breaches",
                        "instructions": "Detect breaches and near-misses based on thresholds.",
                        "task": "Detect breaches",
                        "output_schema": {"breaches": "list", "near_misses": "list"},
                        "policy_tags": ["breach_detection"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "generate_alerts",
                        "type": "ai_action",
                        "description": "Generate alerts for breaches",
                        "instructions": "Generate alerts and create ServiceNow incidents for breaches.",
                        "task": "Generate alerts",
                        "output_schema": {"alerts": "list", "incidents": "list"},
                        "policy_tags": ["alerting"],
                        "risk_level": "R1",
                    },
                ],
                "is_active": True,
            },
        ]

    def _get_e20_workflows(self) -> list:
        """Get E20 Planning Agent workflows."""
        return [
            {
                "agent_type": "planning",
                "name": "deployment_planning_workflow",
                "description": "Generate deployment plan from natural language request",
                "risk_level": "R2",
                "required_policies": ["deployment_policy", "change_management_policy", "risk_policy"],
                "steps": [
                    {
                        "name": "parse_request",
                        "type": "ai_action",
                        "description": "Parse deployment request and requirements",
                        "instructions": "Parse the user's natural language request and extract application, version, scope, and preferences.",
                        "task": "Parse deployment request",
                        "output_schema": {
                            "application": "string",
                            "version": "string",
                            "scope": "object",
                            "preferences": "object",
                        },
                        "policy_tags": ["plan_parsing"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "gather_inventory",
                        "type": "ai_action",
                        "description": "Gather device and user inventory from sources",
                        "instructions": "Gather device and user inventory from Intune, SCCM, and other sources.",
                        "task": "Gather inventory",
                        "output_schema": {"devices": "list", "users": "list"},
                        "policy_tags": ["inventory_gathering"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "analyze_compatibility",
                        "type": "ai_action",
                        "description": "Analyze hardware/software compatibility",
                        "instructions": "Analyze device compatibility with application requirements.",
                        "task": "Analyze compatibility",
                        "output_schema": {"compatible_devices": "list", "incompatible_devices": "list"},
                        "policy_tags": ["compatibility_analysis"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "calculate_blast_radius",
                        "type": "ai_action",
                        "description": "Calculate blast radius and impact",
                        "instructions": "Calculate blast radius including users affected, departments, regions, and productivity impact.",
                        "task": "Calculate blast radius",
                        "output_schema": {"blast_radius": "object", "impact_score": "number"},
                        "policy_tags": ["blast_radius"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "generate_ring_strategy",
                        "type": "ai_action",
                        "description": "Generate optimal ring assignment strategy",
                        "instructions": "Generate ring assignment strategy based on device scores, risk tolerance, and ring sizes.",
                        "task": "Generate ring strategy",
                        "output_schema": {"rings": "list", "strategy": "object"},
                        "policy_tags": ["ring_strategy"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "optimize_schedule",
                        "type": "ai_action",
                        "description": "Optimize deployment schedule",
                        "instructions": "Optimize schedule considering deployment windows, change freezes, and business hours.",
                        "task": "Optimize schedule",
                        "output_schema": {"schedule": "object", "windows": "list", "freezes": "list"},
                        "policy_tags": ["schedule_optimization"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "generate_rollback_plan",
                        "type": "ai_action",
                        "description": "Generate rollback plan",
                        "instructions": "Generate rollback plan with trigger conditions and steps.",
                        "task": "Generate rollback plan",
                        "output_schema": {"rollback_plan": "object"},
                        "policy_tags": ["rollback_planning"],
                        "risk_level": "R1",
                    },
                    {
                        "name": "present_plan",
                        "type": "approval_gate",
                        "description": "Present deployment plan for review",
                        "instructions": "Review deployment plan including rings, schedule, blast radius, and rollback plan. Approve for R1 (low risk) or escalate for R2/R3.",
                        "task": "Review and approve plan",
                        "output_schema": {"approved": "boolean", "approver": "string", "conditions": "list"},
                        "policy_tags": ["plan_approval"],
                        "risk_level": "R2",
                    },
                    {
                        "name": "create_deployment",
                        "type": "approval_gate",
                        "description": "Create deployment intent from approved plan",
                        "instructions": "Create deployment intent from approved plan.",
                        "task": "Create deployment intent",
                        "output_schema": {"deployment_id": "string", "created": "boolean"},
                        "policy_tags": ["deployment_creation"],
                        "risk_level": "R2",
                    },
                ],
                "is_active": True,
            },
        ]
