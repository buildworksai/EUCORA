# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Workflow Executor for AI Agent multi-step workflows.

Implements step-by-step execution with policy context retrieval,
approval gates, and LLM integration.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from django.contrib.auth.models import User
from django.utils import timezone

from apps.ai_agents.agents.execution_framework import AgentExecutionFramework, get_execution_framework
from apps.ai_agents.services import get_ai_agent_service
from apps.policy_documents.services.rag import PolicyContextRetriever, RetrievedChunk

from .models import WorkflowDefinition, WorkflowExecution, WorkflowStep

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Executes agent workflows step by step.

    Integrates with:
    - PolicyContextRetriever: For policy context at each step
    - AgentExecutionFramework: For guardrail enforcement
    - LLM providers: For AI-powered steps
    """

    def __init__(
        self,
        policy_retriever: Optional[PolicyContextRetriever] = None,
        execution_framework: Optional[AgentExecutionFramework] = None,
    ):
        """
        Initialize workflow executor.

        Args:
            policy_retriever: Policy context retriever (defaults to new instance)
            execution_framework: Agent execution framework (defaults to global instance)
        """
        self.policy_retriever = policy_retriever or PolicyContextRetriever()
        self.execution_framework = execution_framework or get_execution_framework()
        self.ai_service = get_ai_agent_service()

    async def start_workflow(
        self,
        workflow: WorkflowDefinition,
        user: User,
        input_data: Dict[str, Any],
    ) -> WorkflowExecution:
        """
        Start a new workflow execution.

        Args:
            workflow: Workflow definition to execute
            user: User initiating the workflow
            input_data: Input data for workflow execution

        Returns:
            Created WorkflowExecution instance
        """
        logger.info(f"Starting workflow {workflow.name} for user {user.username}")

        # 1. Retrieve relevant policies for the workflow
        policy_context = await self._retrieve_policies(
            workflow.required_policies,
            input_data,
        )

        # 2. Create execution record
        execution = await WorkflowExecution.objects.acreate(
            workflow=workflow,
            initiated_by=user,
            input_data=input_data,
            policy_context=[self._chunk_to_dict(chunk) for chunk in policy_context],
            status=WorkflowExecution.Status.RUNNING,
            started_at=timezone.now(),
        )

        # 3. Create step records
        for i, step_def in enumerate(workflow.steps):
            await WorkflowStep.objects.acreate(
                execution=execution,
                step_index=i,
                name=step_def.get("name", f"Step {i+1}"),
                description=step_def.get("description", ""),
                step_type=step_def.get("type", "ai_action"),
                status=WorkflowStep.Status.PENDING,
                input_data=step_def.get("input_data", {}),
            )

        # 4. Execute first step (or until approval needed)
        await self._execute_until_gate(execution)

        return execution

    async def _retrieve_policies(
        self,
        required_policies: List[str],
        input_data: Dict[str, Any],
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant policy context for workflow.

        Args:
            required_policies: List of policy categories to retrieve
            input_data: Input data to build query from

        Returns:
            List of retrieved policy chunks
        """
        # Build query from input data
        query_parts = []
        if "application_name" in input_data:
            query_parts.append(f"application {input_data['application_name']}")
        if "package_name" in input_data:
            query_parts.append(f"package {input_data['package_name']}")
        if "deployment_intent" in input_data:
            query_parts.append("deployment")
        if "risk_level" in input_data:
            query_parts.append(f"risk {input_data['risk_level']}")

        query = " ".join(query_parts) if query_parts else "policy requirements"

        # Retrieve policies
        chunks = self.policy_retriever.get_context(
            query=query,
            categories=required_policies if required_policies else None,
            top_k=10,
            min_similarity=0.7,
        )

        return chunks

    async def _execute_until_gate(self, execution: WorkflowExecution) -> None:
        """
        Execute steps until an approval gate or completion.

        Args:
            execution: Workflow execution to process
        """
        workflow = execution.workflow

        while execution.current_step_index < len(workflow.steps):
            step = await WorkflowStep.objects.filter(
                execution=execution, step_index=execution.current_step_index
            ).afirst()

            if not step:
                logger.error(f"Step {execution.current_step_index} not found for execution {execution.id}")
                execution.status = WorkflowExecution.Status.FAILED
                await execution.asave()
                return

            step_def = workflow.steps[step.step_index]

            # Check if this step requires approval
            if step_def.get("type") == "approval_gate":
                execution.status = WorkflowExecution.Status.AWAITING_APPROVAL
                step.status = WorkflowStep.Status.AWAITING_APPROVAL
                await step.asave()
                await execution.asave()
                logger.info(f"Workflow {execution.id} paused at approval gate step {step.step_index}")
                return

            # Execute the step
            try:
                await self._execute_step(execution, step, step_def)
            except Exception as e:
                logger.exception(f"Step {step.step_index} failed: {e}")
                step.status = WorkflowStep.Status.FAILED
                step.error_message = str(e)
                step.completed_at = timezone.now()
                await step.asave()
                execution.status = WorkflowExecution.Status.FAILED
                await execution.asave()
                return

            # Move to next step
            execution.current_step_index += 1
            await execution.asave()

        # All steps completed
        execution.status = WorkflowExecution.Status.COMPLETED
        execution.completed_at = timezone.now()
        await execution.asave()
        logger.info(f"Workflow {execution.id} completed successfully")

    async def _execute_step(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_def: Dict[str, Any],
    ) -> None:
        """
        Execute a single workflow step.

        Args:
            execution: Workflow execution
            step: Step instance to execute
            step_def: Step definition from workflow
        """
        step.status = WorkflowStep.Status.RUNNING
        step.started_at = timezone.now()
        await step.asave()

        try:
            # Get relevant policies for this step
            step_policies = await self._get_step_policies(
                execution.policy_context,
                step_def.get("policy_tags", []),
            )
            step.policies_considered = step_policies

            # Build prompt with policy context
            previous_outputs = await self._get_previous_outputs(execution, step.step_index)
            prompt = self._build_step_prompt(
                step_def,
                execution.input_data,
                step_policies,
                previous_outputs,
            )
            step.prompt_used = prompt

            # Execute LLM call if this is an AI action
            if step_def.get("type") == "ai_action":
                response = await self._call_llm(prompt)
                step.llm_response = response.get("content", "")
                step.tokens_used = response.get("tokens_used", 0)

                # Parse output
                step.output_data = self._parse_output(response.get("content", ""), step_def)
            else:
                # For non-AI steps, just mark as completed
                step.output_data = {}

            step.status = WorkflowStep.Status.COMPLETED
            step.completed_at = timezone.now()

        except Exception as e:
            step.status = WorkflowStep.Status.FAILED
            step.error_message = str(e)
            step.completed_at = timezone.now()
            raise

        finally:
            await step.asave()

    async def _get_step_policies(
        self,
        policy_context: List[Dict[str, Any]],
        policy_tags: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Filter policy context for specific step.

        Args:
            policy_context: Full policy context from workflow
            policy_tags: Tags to filter by

        Returns:
            Filtered policy chunks
        """
        if not policy_tags:
            return policy_context

        filtered = []
        for chunk in policy_context:
            if chunk.get("category") in policy_tags:
                filtered.append(chunk)

        return filtered if filtered else policy_context

    def _build_step_prompt(
        self,
        step_def: Dict[str, Any],
        input_data: Dict[str, Any],
        policies: List[Dict[str, Any]],
        previous_outputs: List[Dict[str, Any]],
    ) -> str:
        """
        Build prompt with policy context for LLM.

        Args:
            step_def: Step definition
            input_data: Workflow input data
            policies: Policy chunks to include
            previous_outputs: Outputs from previous steps

        Returns:
            Formatted prompt string
        """
        policy_text = "\n\n".join(
            [
                f"## Policy: {p.get('document_title', 'Unknown')} ({p.get('category', 'Unknown')})\n{p.get('content', '')}"  # noqa: E501
                for p in policies
            ]
        )

        previous_outputs_text = ""
        if previous_outputs:
            previous_outputs_text = "\n\n## PREVIOUS STEP OUTPUTS\n" + json.dumps(previous_outputs, indent=2)

        return f"""
You are executing step "{step_def.get('name', 'Unknown')}" of a workflow.

## RELEVANT POLICIES (You MUST follow these)
{policy_text if policy_text else "No specific policies provided."}

## STEP INSTRUCTIONS
{step_def.get('instructions', step_def.get('description', ''))}

## INPUT DATA
{json.dumps(input_data, indent=2)}
{previous_outputs_text}

## YOUR TASK
{step_def.get('task', 'Complete this step according to the instructions.')}

Provide your response in the following JSON format:
{step_def.get('output_schema', '{}')}
"""

    async def _get_previous_outputs(
        self, execution: WorkflowExecution, current_step_index: int
    ) -> List[Dict[str, Any]]:
        """
        Get outputs from previous steps.

        Args:
            execution: Workflow execution
            current_step_index: Current step index

        Returns:
            List of previous step outputs
        """
        # Get previous steps
        previous_steps = (
            await WorkflowStep.objects.filter(
                execution=execution,
                step_index__lt=current_step_index,
                status=WorkflowStep.Status.COMPLETED,
            )
            .order_by("step_index")
            .values("output_data")
        )

        return [step["output_data"] for step in previous_steps]

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM provider with prompt.

        Args:
            prompt: Prompt to send

        Returns:
            Dict with 'content' and 'tokens_used'
        """
        try:
            provider = self.ai_service.get_provider()
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant helping with enterprise application management.",
                },
                {"role": "user", "content": prompt},
            ]

            # Run async provider.chat
            response_text = await provider.chat(messages)
            tokens_used = provider.count_tokens(prompt) + provider.count_tokens(response_text)

            return {
                "content": response_text,
                "tokens_used": tokens_used,
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _parse_output(self, content: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM output according to step schema.

        Args:
            content: LLM response content
            step_def: Step definition with output_schema

        Returns:
            Parsed output data
        """
        try:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: return as text
                return {"response": content}
        except Exception as e:
            logger.warning(f"Failed to parse output as JSON: {e}")
            return {"response": content}

    def _chunk_to_dict(self, chunk: RetrievedChunk) -> Dict[str, Any]:
        """Convert RetrievedChunk to dict for JSON storage."""
        return {
            "id": chunk.id,
            "content": chunk.content,
            "document_id": chunk.document_id,
            "document_title": chunk.document_title,
            "category": chunk.category,
            "similarity": chunk.similarity,
            "heading": chunk.heading,
            "chunk_index": chunk.chunk_index,
        }

    async def resume_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """
        Resume workflow execution after approval.

        Args:
            execution: Workflow execution to resume

        Returns:
            Updated execution
        """
        if execution.status != WorkflowExecution.Status.APPROVED:
            raise ValueError(f"Cannot resume workflow in status {execution.status}")

        execution.status = WorkflowExecution.Status.RUNNING
        await execution.asave()

        # Continue execution
        await self._execute_until_gate(execution)

        return execution

    async def approve_step(
        self,
        execution: WorkflowExecution,
        approver: User,
        notes: Optional[str] = None,
    ) -> WorkflowExecution:
        """
        Approve current step and continue workflow.

        Args:
            execution: Workflow execution
            approver: User approving the step
            notes: Optional approval notes

        Returns:
            Updated execution
        """
        if execution.status != WorkflowExecution.Status.AWAITING_APPROVAL:
            raise ValueError(f"Cannot approve workflow in status {execution.status}")

        # Update approval info
        execution.approved_by = approver
        execution.approved_at = timezone.now()
        execution.status = WorkflowExecution.Status.APPROVED
        await execution.asave()

        # Update step
        step = await WorkflowStep.objects.filter(execution=execution, step_index=execution.current_step_index).afirst()
        if step:
            step.status = WorkflowStep.Status.COMPLETED
            step.completed_at = timezone.now()
            await step.asave()

        # Resume workflow
        return await self.resume_workflow(execution)

    async def reject_step(
        self,
        execution: WorkflowExecution,
        rejector: User,
        reason: str,
    ) -> WorkflowExecution:
        """
        Reject current step and stop workflow.

        Args:
            execution: Workflow execution
            rejector: User rejecting the step
            reason: Rejection reason

        Returns:
            Updated execution
        """
        if execution.status != WorkflowExecution.Status.AWAITING_APPROVAL:
            raise ValueError(f"Cannot reject workflow in status {execution.status}")

        execution.status = WorkflowExecution.Status.REJECTED
        execution.rejection_reason = reason
        execution.completed_at = timezone.now()
        await execution.asave()

        # Update step
        step = await WorkflowStep.objects.filter(execution=execution, step_index=execution.current_step_index).afirst()
        if step:
            step.status = WorkflowStep.Status.FAILED
            step.error_message = f"Rejected: {reason}"
            step.completed_at = timezone.now()
            await step.asave()

        return execution
