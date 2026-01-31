# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Default workflow definitions for all agent types.

These workflows are seeded into the database via management command.
"""
from typing import Dict, List

# Workflow definitions for each agent type
WORKFLOW_DEFINITIONS: List[Dict] = [
    {
        "name": "Package Analysis and Evidence Generation",
        "agent_type": "packaging",
        "risk_level": "R2",
        "required_policies": ["application", "security", "compliance"],
        "steps": [
            {
                "name": "Analyze Package",
                "type": "ai_action",
                "description": "Analyze the application package structure and dependencies",
                "instructions": "Examine the package structure, identify components, and document dependencies.",
                "task": "Provide a detailed analysis of the package structure, including all dependencies and components.",  # noqa: E501
                "risk_level": "R1",
                "policy_tags": ["application"],
                "output_schema": {
                    "package_structure": "object",
                    "dependencies": "array",
                    "components": "array",
                },
            },
            {
                "name": "Generate SBOM",
                "type": "ai_action",
                "description": "Generate Software Bill of Materials",
                "instructions": "Create a comprehensive SBOM listing all software components and their versions.",
                "task": "Generate a complete SBOM in SPDX format.",
                "risk_level": "R1",
                "policy_tags": ["application"],
                "output_schema": {
                    "sbom_format": "string",
                    "components": "array",
                },
            },
            {
                "name": "Vulnerability Analysis",
                "type": "ai_action",
                "description": "Analyze vulnerabilities against security policies",
                "instructions": "Scan the SBOM for known vulnerabilities and assess risk against security policies.",
                "task": "Identify all vulnerabilities and provide risk assessment.",
                "risk_level": "R1",
                "policy_tags": ["security"],
                "output_schema": {
                    "vulnerabilities": "array",
                    "risk_assessment": "object",
                },
            },
            {
                "name": "Generate Evidence Pack",
                "type": "approval_gate",
                "description": "Create evidence pack for CAB submission",
                "instructions": "Compile all analysis results into a complete evidence pack.",
                "task": "Generate the complete evidence pack document.",
                "risk_level": "R2",
                "policy_tags": ["compliance", "governance"],
                "output_schema": {
                    "evidence_pack": "object",
                },
            },
            {
                "name": "Submit to CAB",
                "type": "approval_gate",
                "description": "Submit evidence pack for CAB review",
                "instructions": "Submit the evidence pack to the Change Advisory Board for approval.",
                "task": "Prepare CAB submission with all required documentation.",
                "risk_level": "R3",
                "policy_tags": ["governance"],
                "output_schema": {
                    "cab_submission": "object",
                },
            },
        ],
    },
    {
        "name": "CAB Evidence Generation",
        "agent_type": "cab_evidence",
        "risk_level": "R3",
        "required_policies": ["governance", "compliance"],
        "steps": [
            {
                "name": "Explain Requirements",
                "type": "ai_action",
                "description": "Explain CAB evidence requirements",
                "instructions": "Analyze the deployment intent and explain what evidence is required.",
                "task": "Provide a clear explanation of CAB evidence requirements.",
                "risk_level": "R1",
                "policy_tags": ["governance"],
                "output_schema": {
                    "requirements": "array",
                    "explanation": "string",
                },
            },
            {
                "name": "Compile Evidence",
                "type": "ai_action",
                "description": "Gather and compile evidence from various sources",
                "instructions": "Collect all relevant evidence documents and data.",
                "task": "Compile all required evidence documents.",
                "risk_level": "R2",
                "policy_tags": ["compliance"],
                "output_schema": {
                    "evidence_documents": "array",
                },
            },
            {
                "name": "Generate Evidence Pack",
                "type": "approval_gate",
                "description": "Generate complete evidence pack",
                "instructions": "Create the final evidence pack document.",
                "task": "Generate the complete evidence pack.",
                "risk_level": "R2",
                "policy_tags": ["governance"],
                "output_schema": {
                    "evidence_pack": "object",
                },
            },
            {
                "name": "Submit for Approval",
                "type": "approval_gate",
                "description": "Submit evidence pack for CAB approval",
                "instructions": "Submit the evidence pack to CAB for review and approval.",
                "task": "Submit evidence pack to CAB.",
                "risk_level": "R3",
                "policy_tags": ["governance"],
                "output_schema": {
                    "submission": "object",
                },
            },
        ],
    },
    {
        "name": "Risk Score Explanation",
        "agent_type": "risk_explainer",
        "risk_level": "R1",
        "required_policies": ["application", "security"],
        "steps": [
            {
                "name": "Explain Score",
                "type": "ai_action",
                "description": "Explain the risk score calculation",
                "instructions": "Break down the risk score into its component factors.",
                "task": "Provide a detailed explanation of how the risk score was calculated.",
                "risk_level": "R1",
                "policy_tags": ["application"],
                "output_schema": {
                    "score_breakdown": "object",
                    "explanation": "string",
                },
            },
            {
                "name": "Suggest Mitigations",
                "type": "ai_action",
                "description": "Suggest risk mitigation strategies",
                "instructions": "Recommend ways to reduce the risk score.",
                "task": "Provide actionable mitigation recommendations.",
                "risk_level": "R1",
                "policy_tags": ["security"],
                "output_schema": {
                    "mitigations": "array",
                },
            },
            {
                "name": "Compare Packages",
                "type": "ai_action",
                "description": "Compare risk scores across packages",
                "instructions": "Compare this package's risk score with similar packages.",
                "task": "Provide comparative risk analysis.",
                "risk_level": "R1",
                "policy_tags": ["application"],
                "output_schema": {
                    "comparison": "object",
                },
            },
        ],
    },
    {
        "name": "Deployment Planning and Execution",
        "agent_type": "deployment",
        "risk_level": "R3",
        "required_policies": ["governance", "operational"],
        "steps": [
            {
                "name": "Analyze Current State",
                "type": "ai_action",
                "description": "Review current deployment status and history",
                "instructions": "Examine the current deployment state and historical patterns.",
                "task": "Provide analysis of current deployment state.",
                "risk_level": "R1",
                "policy_tags": ["operational"],
                "output_schema": {
                    "current_state": "object",
                    "history": "array",
                },
            },
            {
                "name": "Recommend Strategy",
                "type": "ai_action",
                "description": "Suggest optimal ring progression strategy",
                "instructions": "Recommend the best ring progression strategy based on policies and history.",
                "task": "Provide ring progression recommendations.",
                "risk_level": "R1",
                "policy_tags": ["governance"],
                "output_schema": {
                    "strategy": "object",
                    "recommendations": "array",
                },
            },
            {
                "name": "Review Dependencies",
                "type": "ai_action",
                "description": "Check application dependencies and conflicts",
                "instructions": "Analyze dependencies and identify potential conflicts.",
                "task": "Identify all dependencies and conflicts.",
                "risk_level": "R1",
                "policy_tags": ["operational"],
                "output_schema": {
                    "dependencies": "array",
                    "conflicts": "array",
                },
            },
            {
                "name": "Confirm Strategy",
                "type": "approval_gate",
                "description": "Review and approve deployment strategy",
                "instructions": "Review the proposed deployment strategy.",
                "task": "Present strategy for approval.",
                "risk_level": "R2",
                "policy_tags": ["governance"],
                "output_schema": {
                    "strategy_summary": "object",
                },
            },
            {
                "name": "Initiate Deployment",
                "type": "approval_gate",
                "description": "Start deployment to target ring",
                "instructions": "Begin the deployment process to the target ring.",
                "task": "Initiate deployment execution.",
                "risk_level": "R3",
                "policy_tags": ["governance"],
                "output_schema": {
                    "deployment_id": "string",
                },
            },
        ],
    },
    {
        "name": "Compliance Analysis",
        "agent_type": "compliance",
        "risk_level": "R2",
        "required_policies": ["compliance", "security"],
        "steps": [
            {
                "name": "Audit Gaps",
                "type": "ai_action",
                "description": "Identify compliance gaps",
                "instructions": "Analyze current state against compliance requirements.",
                "task": "Identify all compliance gaps.",
                "risk_level": "R1",
                "policy_tags": ["compliance"],
                "output_schema": {
                    "gaps": "array",
                },
            },
            {
                "name": "Generate Report",
                "type": "ai_action",
                "description": "Generate compliance report",
                "instructions": "Create a comprehensive compliance report.",
                "task": "Generate the compliance report.",
                "risk_level": "R1",
                "policy_tags": ["compliance"],
                "output_schema": {
                    "report": "object",
                },
            },
            {
                "name": "Create Remediation Plan",
                "type": "approval_gate",
                "description": "Create remediation plan for gaps",
                "instructions": "Develop a plan to address identified compliance gaps.",
                "task": "Create remediation plan.",
                "risk_level": "R2",
                "policy_tags": ["compliance"],
                "output_schema": {
                    "remediation_plan": "object",
                },
            },
        ],
    },
    {
        "name": "Incident Response",
        "agent_type": "incident",
        "risk_level": "R2",
        "required_policies": ["operational", "security"],
        "steps": [
            {
                "name": "Analyze Failure",
                "type": "ai_action",
                "description": "Analyze the incident or failure",
                "instructions": "Examine incident details and identify root causes.",
                "task": "Provide failure analysis.",
                "risk_level": "R1",
                "policy_tags": ["operational"],
                "output_schema": {
                    "analysis": "object",
                    "root_causes": "array",
                },
            },
            {
                "name": "Identify Root Cause",
                "type": "ai_action",
                "description": "Identify the root cause of the incident",
                "instructions": "Determine the primary root cause of the incident.",
                "task": "Identify root cause.",
                "risk_level": "R1",
                "policy_tags": ["operational"],
                "output_schema": {
                    "root_cause": "string",
                    "evidence": "array",
                },
            },
            {
                "name": "Generate Report",
                "type": "ai_action",
                "description": "Generate incident report",
                "instructions": "Create a comprehensive incident report.",
                "task": "Generate incident report.",
                "risk_level": "R1",
                "policy_tags": ["operational"],
                "output_schema": {
                    "report": "object",
                },
            },
            {
                "name": "Trigger Recovery",
                "type": "approval_gate",
                "description": "Trigger recovery actions",
                "instructions": "Execute recovery actions to resolve the incident.",
                "task": "Initiate recovery process.",
                "risk_level": "R3",
                "policy_tags": ["operational", "security"],
                "output_schema": {
                    "recovery_actions": "array",
                },
            },
        ],
    },
]


def get_workflow_definition(agent_type: str) -> Dict | None:
    """
    Get workflow definition for an agent type.

    Args:
        agent_type: Agent type identifier

    Returns:
        Workflow definition dict or None if not found
    """
    for workflow in WORKFLOW_DEFINITIONS:
        if workflow["agent_type"] == agent_type:
            return workflow
    return None
