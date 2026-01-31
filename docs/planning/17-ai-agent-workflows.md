# E8: AI Agent Workflows — Autonomous R1, Approval-Gated R2/R3

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P1-Critical
**Dependencies**: E1 (Document Management), E3 (RBAC), E7 (pgvector)

---

## Overview

Redesign AI Agent workflows to provide:
1. **Step-by-step workflow visualization** showing what the agent is doing
2. **Policy context display** at each step
3. **Autonomous execution for R1** (low-risk) operations
4. **Human approval gates for R2/R3** (medium/high-risk) operations
5. **Proper workflow orchestration** instead of pushing to chat

---

## Risk Level Classification

### Risk Levels

| Level | Name | Execution Mode | Examples |
|-------|------|----------------|----------|
| **R1** | Low Risk | Autonomous | Read-only queries, report generation, risk explanation |
| **R2** | Medium Risk | Policy-Dependent | Evidence pack generation, deployment recommendations |
| **R3** | High Risk | Mandatory Approval | CAB submission, deployment initiation, rollback triggers |

### Risk Classification by Agent Type

```python
AGENT_RISK_CLASSIFICATION = {
    "packaging": {
        "analyze_vulnerability": "R1",      # Read-only analysis
        "generate_sbom": "R1",              # Document generation
        "create_evidence_pack": "R2",       # Creates artifacts
        "submit_cab_request": "R3",         # Workflow initiation
    },
    "cab_evidence": {
        "explain_requirements": "R1",
        "compile_evidence": "R2",
        "generate_evidence_pack": "R2",
        "submit_for_approval": "R3",
    },
    "risk_explainer": {
        "explain_score": "R1",
        "suggest_mitigations": "R1",
        "compare_packages": "R1",
        "predict_risk_changes": "R2",
    },
    "deployment": {
        "analyze_deployment": "R1",
        "recommend_strategy": "R2",
        "initiate_deployment": "R3",
        "trigger_rollback": "R3",
        "pause_deployment": "R2",
    },
    "compliance": {
        "audit_gaps": "R1",
        "generate_report": "R1",
        "create_remediation_plan": "R2",
        "execute_remediation": "R3",
    },
    "incident": {
        "analyze_failure": "R1",
        "identify_root_cause": "R1",
        "generate_report": "R1",
        "trigger_recovery": "R3",
    },
}
```

---

## Workflow Engine

### Workflow Definition

```python
# backend/apps/ai_agents/workflows/models.py

class WorkflowDefinition(TimeStampedModel):
    """Defines a multi-step workflow for an agent."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    agent_type = models.CharField(max_length=32, choices=AIAgentType.choices)
    name = models.CharField(max_length=128)
    description = models.TextField()

    # Steps as JSON schema
    steps = models.JSONField(default=list)

    # Policy requirements
    required_policies = models.JSONField(default=list)  # Policy categories to retrieve

    # Risk level
    risk_level = models.CharField(max_length=4)  # R1, R2, R3

    is_active = models.BooleanField(default=True)


class WorkflowExecution(TimeStampedModel, CorrelationIdModel):
    """Instance of a workflow being executed."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE)

    # Execution context
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)

    # Status
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    current_step_index = models.IntegerField(default=0)

    # Policy context used
    policy_context = models.JSONField(default=list)  # Retrieved policy chunks

    # Approval
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_workflows'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class WorkflowStep(TimeStampedModel):
    """Individual step execution within a workflow."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        AWAITING_INPUT = "awaiting_input", "Awaiting User Input"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Approval"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='steps')
    step_index = models.IntegerField()

    # Step definition
    name = models.CharField(max_length=128)
    description = models.TextField()
    step_type = models.CharField(max_length=32)  # ai_action, approval_gate, user_input

    # Input/Output
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)

    # Policy context for this step
    policies_considered = models.JSONField(default=list)

    # LLM details
    prompt_used = models.TextField(blank=True)
    llm_response = models.TextField(blank=True)
    tokens_used = models.IntegerField(default=0)

    # Status
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

### Workflow Executor

```python
# backend/apps/ai_agents/workflows/executor.py

class WorkflowExecutor:
    """Executes agent workflows step by step."""

    def __init__(
        self,
        knowledge_service: KnowledgeRetrievalService,
        llm_service: LLMService,
    ):
        self.knowledge_service = knowledge_service
        self.llm_service = llm_service

    async def start_workflow(
        self,
        workflow: WorkflowDefinition,
        user: User,
        input_data: dict,
    ) -> WorkflowExecution:
        """Start a new workflow execution."""

        # 1. Retrieve relevant policies
        policy_context = await self._retrieve_policies(
            workflow.required_policies,
            input_data,
        )

        # 2. Create execution record
        execution = await WorkflowExecution.objects.acreate(
            workflow=workflow,
            initiated_by=user,
            input_data=input_data,
            policy_context=policy_context,
            status=WorkflowExecution.Status.RUNNING,
            started_at=timezone.now(),
        )

        # 3. Create step records
        for i, step_def in enumerate(workflow.steps):
            await WorkflowStep.objects.acreate(
                execution=execution,
                step_index=i,
                name=step_def['name'],
                description=step_def['description'],
                step_type=step_def['type'],
                status=WorkflowStep.Status.PENDING,
            )

        # 4. Execute first step (or until approval needed)
        await self._execute_until_gate(execution)

        return execution

    async def _execute_until_gate(self, execution: WorkflowExecution):
        """Execute steps until an approval gate or completion."""

        while execution.current_step_index < len(execution.workflow.steps):
            step = await execution.steps.filter(
                step_index=execution.current_step_index
            ).afirst()

            step_def = execution.workflow.steps[step.step_index]

            # Check if this step requires approval
            if step_def['type'] == 'approval_gate':
                execution.status = WorkflowExecution.Status.AWAITING_APPROVAL
                step.status = WorkflowStep.Status.AWAITING_APPROVAL
                await step.asave()
                await execution.asave()
                return

            # Execute the step
            await self._execute_step(execution, step, step_def)

            # Move to next step
            execution.current_step_index += 1
            await execution.asave()

        # All steps completed
        execution.status = WorkflowExecution.Status.COMPLETED
        execution.completed_at = timezone.now()
        await execution.asave()

    async def _execute_step(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_def: dict,
    ):
        """Execute a single workflow step."""

        step.status = WorkflowStep.Status.RUNNING
        step.started_at = timezone.now()
        await step.asave()

        try:
            # Get relevant policies for this step
            step_policies = await self._get_step_policies(
                execution.policy_context,
                step_def.get('policy_tags', []),
            )
            step.policies_considered = step_policies

            # Build prompt with policy context
            prompt = self._build_step_prompt(
                step_def,
                execution.input_data,
                step_policies,
                self._get_previous_outputs(execution, step.step_index),
            )
            step.prompt_used = prompt

            # Execute LLM call
            response = await self.llm_service.complete(prompt)
            step.llm_response = response.content
            step.tokens_used = response.tokens_used

            # Parse output
            step.output_data = self._parse_output(response.content, step_def)
            step.status = WorkflowStep.Status.COMPLETED
            step.completed_at = timezone.now()

        except Exception as e:
            step.status = WorkflowStep.Status.FAILED
            step.error_message = str(e)
            step.completed_at = timezone.now()
            raise

        finally:
            await step.asave()

    def _build_step_prompt(
        self,
        step_def: dict,
        input_data: dict,
        policies: list,
        previous_outputs: list,
    ) -> str:
        """Build prompt with policy context."""

        policy_text = "\n\n".join([
            f"## Policy: {p['title']}\n{p['content']}"
            for p in policies
        ])

        return f"""
You are executing step "{step_def['name']}" of a workflow.

## RELEVANT POLICIES (You MUST follow these)
{policy_text}

## STEP INSTRUCTIONS
{step_def['instructions']}

## INPUT DATA
{json.dumps(input_data, indent=2)}

## PREVIOUS STEP OUTPUTS
{json.dumps(previous_outputs, indent=2)}

## YOUR TASK
{step_def['task']}

Provide your response in the following JSON format:
{step_def.get('output_schema', '{}')}
"""
```

---

## Frontend Workflow UI

### Workflow Visualization

```tsx
// frontend/src/components/ai/WorkflowExecution.tsx

interface Props {
  workflowId: string;
  executionId: string;
}

export function WorkflowExecution({ workflowId, executionId }: Props) {
  const { data: execution, isLoading } = useWorkflowExecution(executionId);

  if (isLoading) return <WorkflowSkeleton />;

  return (
    <div className="flex h-full">
      {/* Left: Step Progress */}
      <div className="w-80 border-r p-4">
        <h3 className="font-semibold mb-4">Workflow Steps</h3>
        <StepProgress steps={execution.steps} currentIndex={execution.current_step_index} />
      </div>

      {/* Center: Current Step Detail */}
      <div className="flex-1 p-6">
        <CurrentStepDetail
          step={execution.steps[execution.current_step_index]}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      </div>

      {/* Right: Policy Context */}
      <div className="w-96 border-l p-4">
        <h3 className="font-semibold mb-4">Policies Considered</h3>
        <PolicyContextPanel policies={execution.policy_context} />
      </div>
    </div>
  );
}
```

### Step Progress Component

```tsx
// frontend/src/components/ai/StepProgress.tsx

export function StepProgress({ steps, currentIndex }: Props) {
  return (
    <div className="space-y-2">
      {steps.map((step, index) => (
        <div
          key={step.id}
          className={cn(
            "flex items-start gap-3 p-3 rounded-lg transition-colors",
            index === currentIndex && "bg-eucora-teal/10 border border-eucora-teal/30",
            step.status === 'completed' && "opacity-60",
          )}
        >
          {/* Status Icon */}
          <div className="flex-shrink-0 mt-0.5">
            {step.status === 'completed' && (
              <CheckCircle className="w-5 h-5 text-green-500" />
            )}
            {step.status === 'running' && (
              <Loader2 className="w-5 h-5 text-eucora-teal animate-spin" />
            )}
            {step.status === 'awaiting_approval' && (
              <AlertCircle className="w-5 h-5 text-yellow-500" />
            )}
            {step.status === 'pending' && (
              <Circle className="w-5 h-5 text-muted-foreground" />
            )}
            {step.status === 'failed' && (
              <XCircle className="w-5 h-5 text-red-500" />
            )}
          </div>

          {/* Step Info */}
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm">{step.name}</p>
            <p className="text-xs text-muted-foreground line-clamp-2">
              {step.description}
            </p>

            {/* Status Badge */}
            {step.status === 'awaiting_approval' && (
              <Badge className="mt-1 bg-yellow-500/20 text-yellow-600">
                Awaiting Your Approval
              </Badge>
            )}
          </div>

          {/* Duration */}
          {step.completed_at && (
            <span className="text-xs text-muted-foreground">
              {formatDuration(step.started_at, step.completed_at)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
```

### Current Step Detail

```tsx
// frontend/src/components/ai/CurrentStepDetail.tsx

export function CurrentStepDetail({ step, onApprove, onReject }: Props) {
  if (step.status === 'awaiting_approval') {
    return <ApprovalGateView step={step} onApprove={onApprove} onReject={onReject} />;
  }

  if (step.status === 'running') {
    return <RunningStepView step={step} />;
  }

  if (step.status === 'completed') {
    return <CompletedStepView step={step} />;
  }

  return <PendingStepView step={step} />;
}

function ApprovalGateView({ step, onApprove, onReject }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-yellow-500" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Approval Required</h2>
          <p className="text-muted-foreground">This action requires your explicit approval</p>
        </div>
      </div>

      {/* What the agent wants to do */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Proposed Action</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded text-sm overflow-auto">
            {JSON.stringify(step.output_data, null, 2)}
          </pre>
        </CardContent>
      </Card>

      {/* Policies that informed this decision */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Policies Considered</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {step.policies_considered.map((policy, i) => (
              <div key={i} className="p-3 bg-muted rounded">
                <p className="font-medium text-sm">{policy.title}</p>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {policy.excerpt}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* AI Reasoning */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">AI Reasoning</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{step.llm_response}</p>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button onClick={onApprove} className="flex-1 bg-green-600 hover:bg-green-700">
          <CheckCircle className="mr-2 h-4 w-4" />
          Approve Action
        </Button>
        <Button onClick={() => setRejectDialogOpen(true)} variant="outline" className="flex-1 text-red-500">
          <XCircle className="mr-2 h-4 w-4" />
          Reject
        </Button>
      </div>
    </div>
  );
}
```

### Policy Context Panel

```tsx
// frontend/src/components/ai/PolicyContextPanel.tsx

export function PolicyContextPanel({ policies }: { policies: PolicyChunk[] }) {
  return (
    <ScrollArea className="h-full">
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          The following policies are guiding this workflow:
        </p>

        {policies.map((policy, i) => (
          <Card key={i} className="p-3">
            <div className="flex items-start gap-2">
              <FileText className="w-4 h-4 text-eucora-teal mt-0.5" />
              <div>
                <p className="font-medium text-sm">{policy.document_title}</p>
                <Badge variant="outline" className="mt-1 text-xs">
                  {policy.category}
                </Badge>
                <p className="text-xs text-muted-foreground mt-2 line-clamp-4">
                  {policy.content}
                </p>
                <Button variant="ghost" size="sm" className="mt-2 text-xs">
                  View Full Document
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
```

---

## Agent Type Workflows

### Packaging Assistant Workflow

```python
PACKAGING_WORKFLOW = {
    "name": "Package Analysis and Evidence Generation",
    "agent_type": "packaging",
    "risk_level": "R2",
    "required_policies": ["application", "security", "compliance"],
    "steps": [
        {
            "name": "Analyze Package",
            "type": "ai_action",
            "description": "Analyze the application package structure and dependencies",
            "risk_level": "R1",
            "policy_tags": ["application"],
        },
        {
            "name": "Generate SBOM",
            "type": "ai_action",
            "description": "Generate Software Bill of Materials",
            "risk_level": "R1",
            "policy_tags": ["application"],
        },
        {
            "name": "Vulnerability Analysis",
            "type": "ai_action",
            "description": "Analyze vulnerabilities against security policies",
            "risk_level": "R1",
            "policy_tags": ["security"],
        },
        {
            "name": "Generate Evidence Pack",
            "type": "approval_gate",  # R2 - requires approval
            "description": "Create evidence pack for CAB submission",
            "risk_level": "R2",
            "policy_tags": ["compliance", "governance"],
        },
        {
            "name": "Submit to CAB",
            "type": "approval_gate",  # R3 - always requires approval
            "description": "Submit evidence pack for CAB review",
            "risk_level": "R3",
            "policy_tags": ["governance"],
        },
    ],
}
```

### Deployment Advisor Workflow

```python
DEPLOYMENT_WORKFLOW = {
    "name": "Deployment Planning and Execution",
    "agent_type": "deployment",
    "risk_level": "R3",
    "required_policies": ["governance", "operational"],
    "steps": [
        {
            "name": "Analyze Current State",
            "type": "ai_action",
            "description": "Review current deployment status and history",
            "risk_level": "R1",
        },
        {
            "name": "Recommend Strategy",
            "type": "ai_action",
            "description": "Suggest optimal ring progression strategy",
            "risk_level": "R1",
        },
        {
            "name": "Review Dependencies",
            "type": "ai_action",
            "description": "Check application dependencies and conflicts",
            "risk_level": "R1",
        },
        {
            "name": "Confirm Strategy",
            "type": "approval_gate",
            "description": "Review and approve deployment strategy",
            "risk_level": "R2",
        },
        {
            "name": "Initiate Deployment",
            "type": "approval_gate",
            "description": "Start deployment to target ring",
            "risk_level": "R3",
        },
    ],
}
```

---

## API Endpoints

```python
# backend/apps/ai_agents/urls.py

# Workflows
GET    /api/v1/ai/workflows/                         # List available workflows
GET    /api/v1/ai/workflows/{id}/                    # Get workflow definition
POST   /api/v1/ai/workflows/{id}/start/              # Start workflow execution

# Executions
GET    /api/v1/ai/executions/                        # List user's executions
GET    /api/v1/ai/executions/{id}/                   # Get execution details
POST   /api/v1/ai/executions/{id}/approve/           # Approve current step
POST   /api/v1/ai/executions/{id}/reject/            # Reject current step
POST   /api/v1/ai/executions/{id}/cancel/            # Cancel execution

# WebSocket
WS     /ws/ai/executions/{id}/                       # Real-time execution updates
```

---

## Deliverables

1. `backend/apps/ai_agents/workflows/` workflow engine
2. Workflow definitions for all agent types
3. `frontend/src/components/ai/` workflow visualization components
4. Approval gate UI with policy context
5. Real-time WebSocket updates for step progress
6. API documentation in `docs/api/ai-workflows-api.yaml`
7. Agent configuration guide in `docs/runbooks/ai-agent-configuration.md`
