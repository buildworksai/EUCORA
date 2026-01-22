# Phase P7: AI Agent Foundation

**Duration**: 4 weeks  
**Owner**: AI Agent Lead  
**Prerequisites**: P6 complete  
**Status**: 🔴 NOT STARTED

---

## Objective

Implement foundation for AI-driven deployment orchestration: conversation engine for multi-turn interactions, task orchestration for async operations, autonomous remediation, and chat state management.

---

## Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P7.1 | Conversation engine | Multi-turn dialogue, context preservation |
| P7.2 | Task orchestration | Async task chains, retry + failure handling |
| P7.3 | Autonomous remediation | Drift detection → automated fix |
| P7.4 | Chat state management | Session state, conversation history |
| P7.5 | Agent integration tests | End-to-end agent flows |
| P7.6 | ≥90% test coverage | All agent components tested |

---

## Technical Specifications

### P7.1: Conversation Engine

**Location**: `backend/apps/ai_agents/conversation.py`

```python
class ConversationEngine:
    """
    Multi-turn conversation management with context preservation.
    
    Features:
    - Stateless message handling (no server-side session)
    - Context from conversation history
    - Tool call routing (query intents, execute remediation, etc.)
    - Correlation ID threading
    """
    
    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        Process user message and return agent response.
        
        Process:
        1. Load conversation history
        2. Build LLM prompt with context
        3. Call LLM (Claude, GPT, etc.)
        4. Parse response + tool calls
        5. Route tool calls
        6. Return response
        """
        
    async def call_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
    ) -> ToolResult:
        """
        Route tool calls to appropriate handlers.
        
        Tools:
        - query_deployments: Search deployment intents
        - check_health: Query /api/v1/health/
        - execute_remediation: Fix detected drift
        - submit_cab: Submit for approval
        - check_status: Query task status
        """
```

### P7.2: Task Orchestration

**Pattern**: Celery chain + error handling

```python
class TaskOrchestrator:
    """
    Orchestrate multi-step async operations.
    
    Example: Deployment flow
    1. Validate intent (sync)
    2. Generate evidence (async)
    3. Submit CAB (async)
    4. Wait for approval (polling)
    5. Execute (async)
    6. Monitor health (polling loop)
    """
    
    def orchestrate_deployment(
        self,
        deployment_intent_id: str,
        correlation_id: str,
    ) -> TaskChain:
        """
        Create task chain for full deployment.
        """
        chain = (
            tasks.validate_intent.s(deployment_intent_id, correlation_id) |
            tasks.generate_evidence.s(correlation_id) |
            tasks.submit_cab.s(correlation_id) |
            tasks.wait_for_approval.s(max_wait_seconds=3600) |
            tasks.execute_deployment.s(correlation_id) |
            tasks.monitor_deployment.s(correlation_id, poll_interval=60)
        )
        
        result = chain.apply_async()
        return result
```

### P7.3: Autonomous Remediation

**Trigger**: Reconciliation loop detects drift

```python
class AutonomousRemediator:
    """
    Automatically fix drift detected by reconciliation loops.
    
    Rules:
    - Only remediate within policy constraints
    - Escalate to human if constraint violation
    - Log all actions with correlation_id
    - Implement backoff (don't thrash on conflicts)
    """
    
    async def remediate_drift(
        self,
        assignment_id: str,
        current_state: DeviceState,
        intended_state: DeviceState,
    ) -> RemediationResult:
        """
        Detect drift type and remediate.
        
        Drift types:
        - Version mismatch: Execute update
        - Missing install: Trigger install
        - Configuration drift: Re-apply config
        - Service down: Restart/remediate
        """
        
        drift_type = self._classify_drift(current_state, intended_state)
        
        if drift_type == 'version_mismatch':
            return await self._remediate_version(assignment_id, intended_state)
        elif drift_type == 'missing_install':
            return await self._remediate_install(assignment_id, intended_state)
        else:
            # Escalate unknown drift
            return RemediationResult(
                status='escalated',
                reason=f'Unknown drift type: {drift_type}',
                requires_human_review=True,
            )
```

### P7.4: Chat State Management

**Storage**: SQLite + Redis cache

```python
class ChatStateManager:
    """
    Manage conversation state (history, context, user info).
    
    Storage:
    - PostgreSQL: Persistent conversation history
    - Redis: Active session cache (5min TTL)
    """
    
    async def create_conversation(
        self,
        user_id: str,
        correlation_id: str,
    ) -> ConversationSession:
        """Create new conversation session."""
        
    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> None:
        """Add message to history."""
        
    async def get_context(
        self,
        conversation_id: str,
    ) -> ConversationContext:
        """
        Retrieve conversation context for LLM.
        
        Includes:
        - Recent messages (last 10)
        - User role/permissions
        - In-flight tasks
        - Recent errors
        """
```

---

## Agent Capabilities

### Supported Intents

1. **Deployment Queries**
   - "Show me deployments in Ring 2"
   - "What's the status of app X?"
   - "Which devices have deployment failures?"

2. **Health Monitoring**
   - "Check system health"
   - "What circuit breakers are open?"
   - "Are there any integration failures?"

3. **Remediation**
   - "Fix the drift on device X"
   - "Restart the failed service"
   - "Rollback to previous version"

4. **CAB Workflows**
   - "Submit deployment for approval"
   - "Show me pending approvals"
   - "Approve with conditions..."

5. **Task Management**
   - "What async tasks are running?"
   - "Cancel the failing task"
   - "Show deployment history"

---

## Quality Gates

- [ ] Conversation engine handles multi-turn dialogue
- [ ] Task orchestration creates chains properly
- [ ] Autonomous remediation respects constraints
- [ ] Chat state persists across sessions
- [ ] Correlation ID threaded throughout
- [ ] ≥90% test coverage
- [ ] All tool calls tested
- [ ] Error scenarios handled (LLM failures, tool failures, etc.)

---

## Files to Create

```
backend/apps/ai_agents/
├── conversation.py (CREATE)
├── orchestration.py (CREATE)
├── remediation.py (CREATE)
├── chat_state.py (CREATE)
├── tools.py (MODIFY) - Tool definitions
├── views.py (MODIFY) - Chat API endpoints
├── serializers.py (MODIFY) - Chat serializers
└── tests/
    ├── test_conversation.py (CREATE)
    ├── test_orchestration.py (CREATE)
    ├── test_remediation.py (CREATE)
    └── test_chat_state.py (CREATE)
```

---

## Success Criteria

✅ **P7 is COMPLETE when**:
1. Conversation engine handles multi-turn dialogue
2. Task orchestration chains created correctly
3. Autonomous remediation works within constraints
4. Chat state persists and retrieves correctly
5. All agent tools routed properly
6. ≥90% test coverage
7. End-to-end agent flows tested
8. All quality gates green

**Target Completion**: 4 weeks (March 5 - April 2, 2026)
