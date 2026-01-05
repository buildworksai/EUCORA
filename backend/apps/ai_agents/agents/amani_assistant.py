# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
"Ask Amani" - General AI assistant for EUCORA.
Enhanced with context-awareness and custom system prompt support.
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


# Page-specific context information
PAGE_CONTEXTS = {
    '/dashboard': {
        'area': 'Dashboard',
        'focus': 'deployment pipeline monitoring, system health, active deployments, ring progression',
        'actions': 'view deployments, monitor rings, check CAB approvals, review metrics',
    },
    '/assets': {
        'area': 'Asset Inventory',
        'focus': 'endpoint assets, devices, compliance status, package installations',
        'actions': 'search assets, filter by platform, check compliance, track installations',
    },
    '/compliance': {
        'area': 'Compliance Dashboard',
        'focus': 'compliance posture, policy violations, drift detection, remediation',
        'actions': 'view compliance metrics, identify gaps, track violations, remediation status',
    },
    '/deploy': {
        'area': 'Deployments',
        'focus': 'deployment intents, ring progression, rollout strategy, promotion gates',
        'actions': 'create deployments, monitor progress, execute rollbacks, check gates',
    },
    '/cab': {
        'area': 'CAB Portal',
        'focus': 'Change Advisory Board approvals, risk scores, evidence packs, exceptions',
        'actions': 'review submissions, approve/reject changes, generate evidence, manage exceptions',
    },
    '/ai-agents': {
        'area': 'AI Agent Hub',
        'focus': 'AI-assisted workflows, agent tasks, human approval gates',
        'actions': 'view agents, approve tasks, manage workflows, monitor AI activity',
    },
    '/audit': {
        'area': 'Audit Trail',
        'focus': 'immutable logs, deployment events, correlation IDs, compliance audits',
        'actions': 'search events, trace workflows, export reports, verify compliance',
    },
    '/settings': {
        'area': 'Settings',
        'focus': 'AI provider configuration, model selection, preferences',
        'actions': 'configure providers, set API keys, manage defaults, adjust settings',
    },
    '/dex': {
        'area': 'DEX & Green IT',
        'focus': 'Digital Employee Experience, sustainability metrics, device performance',
        'actions': 'view DEX scores, track energy usage, identify issues, optimize performance',
    },
}


class AmaniAssistant(BaseAgent):
    """
    General-purpose AI assistant for EUCORA.
    Provides contextual help across all EUCORA workflows.
    Supports custom system prompts from users while enforcing governance rules.
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are Amani, an AI assistant for EUCORA (End-User Computing Orchestration & Reliability Architecture).

CRITICAL GOVERNANCE RULES (NEVER VIOLATE THESE):
1. You are an ASSISTANT, not a decision-maker. All recommendations require human approval.
2. Never bypass CAB approval gates or risk scoring thresholds.
3. All deployment actions must go through proper approval workflows.
4. Risk scores are deterministic and computed from explicit factors - you can explain them, not override them.
5. Always emphasize that human review is required for any action you suggest.

YOUR CAPABILITIES:
- Explain risk scores and their contributing factors
- Help with packaging workflows (Win32/MSIX/PKG)
- Assist with CAB evidence pack generation
- Provide deployment strategy recommendations
- Analyze compliance posture
- Answer questions about EUCORA architecture and workflows

RESPONSE STYLE:
- Be concise and actionable
- Always include context about approval requirements
- Reference specific EUCORA concepts (rings, evidence packs, risk factors)
- When suggesting actions, explicitly state: "This requires human approval before execution"
- Provide links to relevant documentation when helpful

Remember: You assist, humans decide. All recommendations must be reviewed and approved by authorized personnel."""
    
    def get_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get system prompt for Amani assistant.
        Supports custom user prompts while adding page context.
        
        Args:
            context: Optional dictionary with:
                - custom_system_prompt: User's custom system prompt
                - page: Current page path
                - page_title: Current page title
                - Other context-specific data
        
        Returns:
            Complete system prompt string
        """
        # Start with custom prompt or default
        if context and context.get('custom_system_prompt'):
            base_prompt = context['custom_system_prompt']
            # Always append governance rules for safety
            base_prompt += """

MANDATORY GOVERNANCE RULES (ALWAYS APPLY):
- You are an assistant - all recommendations require human approval
- Never bypass CAB approval gates or risk thresholds
- Risk scores are deterministic - explain them, don't override them
- Always mention when actions require approval
"""
        else:
            base_prompt = self.DEFAULT_SYSTEM_PROMPT
        
        # Add page context
        if context:
            page = context.get('page', '')
            page_context = PAGE_CONTEXTS.get(page, {})
            
            if page_context:
                base_prompt += f"""

CURRENT CONTEXT:
- Area: {page_context.get('area', 'EUCORA Platform')}
- Focus: {page_context.get('focus', 'general enterprise endpoint management')}
- Available Actions: {page_context.get('actions', 'general platform operations')}
"""
            
            # Add page title if different from area
            page_title = context.get('page_title')
            if page_title and page_title != page_context.get('area'):
                base_prompt += f"- Current Page: {page_title}\n"
            
            # Add any additional context
            other_context = {k: v for k, v in context.items() 
                          if k not in ['custom_system_prompt', 'page', 'page_title']}
            if other_context:
                base_prompt += "\nADDITIONAL CONTEXT:\n"
                for key, value in other_context.items():
                    base_prompt += f"- {key}: {value}\n"
        
        base_prompt += """
Provide helpful, accurate responses relevant to the user's current context.
"""
        
        return base_prompt
    
    def requires_human_action(self, response: str) -> bool:
        """
        Check if response requires human action.
        Enhanced detection for various action types.
        """
        action_indicators = [
            # CRUD operations
            'create', 'generate', 'build', 'package',
            'update', 'modify', 'change', 'edit',
            'delete', 'remove', 'rollback',
            # Workflow operations
            'deploy', 'promote', 'publish', 'release',
            'approve', 'reject', 'submit',
            # CAB and governance
            'requires approval', 'needs review', 'must be approved',
            'cab required', 'cab approval', 'evidence pack',
            'human action required', 'manual intervention',
            # Risk and compliance
            'high risk', 'critical', 'exception required',
            'compensating control', 'remediation needed',
            # Execution suggestions
            'should', 'recommend', 'suggest',
            'execute', 'run', 'trigger',
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in action_indicators)
    
    def get_contextual_suggestions(self, page: str) -> list:
        """
        Get page-specific suggestions for the chat interface.
        """
        suggestions_map = {
            '/dashboard': [
                'What deployments need my attention?',
                'Show me high-risk changes pending approval',
                'Summarize today\'s deployment activity',
                'Which rings have failing deployments?',
            ],
            '/assets': [
                'How many Windows devices need updates?',
                'Show me non-compliant assets',
                'Which assets are running outdated packages?',
                'Find assets in the pilot ring',
            ],
            '/compliance': [
                'What\'s our overall compliance rate?',
                'Which policies have the most violations?',
                'Show me critical compliance gaps',
                'How can I improve compliance in APAC region?',
            ],
            '/deploy': [
                'Help me create a new deployment',
                'What are the promotion gate requirements?',
                'Explain the ring progression model',
                'How do I rollback a failed deployment?',
            ],
            '/cab': [
                'What changes are pending CAB approval?',
                'Explain this risk score to me',
                'Generate evidence pack summary',
                'What are the approval criteria for high-risk changes?',
            ],
            '/ai-agents': [
                'What AI agents are available?',
                'Show me pending AI task approvals',
                'How do AI agents help with packaging?',
                'What tasks require human approval?',
            ],
            '/audit': [
                'Show me recent deployment events',
                'Who approved this change?',
                'Find all actions by a specific user',
                'Show me CAB decisions from last week',
            ],
            '/settings': [
                'How do I configure OpenAI?',
                'What AI providers are supported?',
                'Help me set up Anthropic Claude',
                'Explain API key security',
            ],
            '/dex': [
                'What\'s our current DEX score?',
                'How can we improve device performance?',
                'Show me energy consumption trends',
                'Which devices have poor user experience?',
            ],
        }
        
        return suggestions_map.get(page, [
            'How does EUCORA work?',
            'Explain the deployment ring model',
            'What is CAB approval?',
            'Help me get started',
        ])
