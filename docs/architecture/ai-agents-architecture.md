# AI Agents Architecture

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-31

---

## Overview

The AI Agents Architecture defines how AI-powered agents are orchestrated within EUCORA to automate application lifecycle management tasks. This architecture supports 12 specialized agents (E10-E21) that work together to provide intelligent automation across the platform.

## Architecture Principles

1. **Agent Autonomy**: Agents operate autonomously within defined risk boundaries (R1/R2/R3)
2. **Workflow Orchestration**: Agents are coordinated through the AI Workflow Engine (E8)
3. **Deterministic Decisions**: All agent decisions are explainable and auditable
4. **Correlation Tracking**: All agent actions include correlation IDs for audit trails

---

## AI Agent Orchestration Flow

```mermaid
graph TB
    UserRequest[User Request] --> WorkflowEngine[AI Workflow Engine]
    WorkflowEngine --> TaskRouter[Task Router]
    TaskRouter --> AgentSelection{Select Agent}

    AgentSelection --> CMDB[CMDB Agent]
    AgentSelection --> ChangeComm[Change Communications]
    AgentSelection --> Discovery[Discovery Agent]
    AgentSelection --> Planning[Planning Agent]
    AgentSelection --> SecOps[SecOps Agent]
    AgentSelection --> SRE[SRE Agent]
    AgentSelection --> KB[KB Triage Agent]
    AgentSelection --> SLA[SLA Governance]
    AgentSelection --> RequestCoord[Request Coordination]
    AgentSelection --> DocAgent[Documentation Agent]
    AgentSelection --> AutoAdvisor[Automation Advisor]
    AgentSelection --> IAM[IAM Security Agent]

    CMDB --> RiskAssessment{Risk Assessment}
    ChangeComm --> RiskAssessment
    Discovery --> RiskAssessment
    Planning --> RiskAssessment
    SecOps --> RiskAssessment
    SRE --> RiskAssessment
    KB --> RiskAssessment
    SLA --> RiskAssessment
    RequestCoord --> RiskAssessment
    DocAgent --> RiskAssessment
    AutoAdvisor --> RiskAssessment
    IAM --> RiskAssessment

    RiskAssessment -->|R1: Low Risk| AutoExecute[Auto Execute]
    RiskAssessment -->|R2: Medium Risk| ApprovalWorkflow[Approval Workflow]
    RiskAssessment -->|R3: High Risk| CABApproval[CAB Approval]

    AutoExecute --> EventStore[Event Store]
    ApprovalWorkflow --> EventStore
    CABApproval --> EventStore

    EventStore --> Telemetry[Telemetry & Reporting]
```

---

## Agent Risk Classification

Agents classify operations into three risk levels:

### R1: Autonomous Operations (Low Risk)
- Read-only operations
- Informational alerts
- Documentation updates
- Non-critical data synchronization

**Example**: CMDB data sync, knowledge base article indexing

### R2: Approval Required (Medium Risk)
- Configuration changes
- Non-critical patches
- Data updates
- Workflow state changes

**Example**: Remediation plan creation, SLA definition updates

### R3: Mandatory Approval (High Risk)
- Critical patches
- Emergency changes
- Bulk operations
- Security actions

**Example**: Access revocation, critical vulnerability remediation

---

## Agent Coordination Patterns

### Pattern 1: Sequential Workflow

```mermaid
sequenceDiagram
    participant User
    participant WorkflowEngine
    participant PlanningAgent
    participant SecOpsAgent
    participant ExecutionPlane

    User->>WorkflowEngine: Create deployment plan
    WorkflowEngine->>PlanningAgent: Generate plan
    PlanningAgent->>PlanningAgent: Risk assessment
    PlanningAgent->>WorkflowEngine: Plan created (R2)
    WorkflowEngine->>User: Approval required
    User->>WorkflowEngine: Approve plan
    WorkflowEngine->>SecOpsAgent: Check vulnerabilities
    SecOpsAgent->>WorkflowEngine: Vulnerability status
    WorkflowEngine->>ExecutionPlane: Execute deployment
    ExecutionPlane->>WorkflowEngine: Deployment status
    WorkflowEngine->>User: Deployment complete
```

### Pattern 2: Parallel Processing

```mermaid
graph LR
    WorkflowEngine[Workflow Engine] --> Discovery[Discovery Agent]
    WorkflowEngine --> CMDB[CMDB Agent]
    WorkflowEngine --> SecOps[SecOps Agent]

    Discovery --> ResultsAggregator[Results Aggregator]
    CMDB --> ResultsAggregator
    SecOps --> ResultsAggregator

    ResultsAggregator --> DecisionEngine[Decision Engine]
    DecisionEngine --> Action[Take Action]
```

### Pattern 3: Event-Driven Coordination

```mermaid
graph TB
    EventSource[Event Source] --> EventBus[Event Bus]
    EventBus --> SecOpsAgent[SecOps Agent]
    EventBus --> SREAgent[SRE Agent]
    EventBus --> RequestCoord[Request Coordination]

    SecOpsAgent --> RemediationAction[Remediation Action]
    SREAgent --> SelfHealingAction[Self-Healing Action]
    RequestCoord --> CommunicationAction[Communication Action]
```

---

## Agent Integration Points

### 1. Workflow Engine Integration

All agents integrate with the AI Workflow Engine (E8) through:
- **Task API**: Agents receive tasks from workflow engine
- **Status Updates**: Agents report task status and progress
- **Approval Requests**: Agents request approvals for R2/R3 operations
- **Event Publishing**: Agents publish events to event store

### 2. RAG Pipeline Integration

Agents that require knowledge access (KB Triage, Documentation) integrate with:
- **Vector Storage**: Semantic search using pgvector (E7)
- **Document Management**: Document ingestion and indexing (E1)
- **Knowledge Sources**: ServiceNow KB, Confluence, SharePoint

### 3. External System Integration

Agents integrate with external systems through connectors:
- **ServiceNow**: CMDB, Change, Request, KB, IAM
- **SIEM Platforms**: Splunk, Sentinel, QRadar (SecOps)
- **Monitoring**: Prometheus, Datadog, Azure Monitor (SRE)
- **Vulnerability Scanners**: Qualys, Nessus, Rapid7 (SecOps)

---

## Agent Data Flow

```mermaid
graph TB
    Agent[Agent] --> TaskQueue[Task Queue]
    TaskQueue --> AgentProcessor[Agent Processor]
    AgentProcessor --> ExternalSystem[External System]
    ExternalSystem --> AgentProcessor
    AgentProcessor --> RiskEngine[Risk Engine]
    RiskEngine -->|R1| AutoExecute[Auto Execute]
    RiskEngine -->|R2/R3| ApprovalQueue[Approval Queue]
    ApprovalQueue --> Approver[Approver]
    Approver --> AgentProcessor
    AgentProcessor --> EventStore[Event Store]
    EventStore --> Telemetry[Telemetry]
```

---

## Agent Telemetry and Monitoring

All agents publish telemetry including:
- **Task Execution Metrics**: Success rate, duration, error rate
- **Risk Classification**: Distribution of R1/R2/R3 operations
- **Approval Metrics**: Approval rate, average approval time
- **Integration Health**: External system connectivity status

---

## Security and Compliance

### Authentication
- Agents authenticate using service principals with Entra ID
- Each agent has scoped permissions based on its responsibilities

### Audit Trail
- All agent actions include correlation IDs
- Agent decisions are logged with reasoning
- Approval workflows are fully auditable

### Data Isolation
- Agents respect correlation ID boundaries
- Multi-tenant isolation enforced at agent level
- Agent data scoped by acquisition boundary

---

## Related Documentation

- [ALM Agents Architecture](alm-agents-architecture.md)
- [RAG Pipeline Architecture](rag-pipeline-architecture.md)
- [Control Plane Design](control-plane-design.md)
- [Planning Document: AI Agent Workflows](../planning/17-ai-agent-workflows.md)
