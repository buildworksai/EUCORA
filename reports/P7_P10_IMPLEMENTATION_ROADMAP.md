# P7-P10 Implementation Roadmap

**SPDX-License-Identifier: Apache-2.0**
**Date**: January 23, 2026
**Status**: Ready for Implementation

---

## Executive Summary

This document provides the complete implementation roadmap for Phases 7-10 of the EUCORA Control Plane, covering:
- **P7**: Agent Foundation (endpoint agents for Windows/macOS/Linux)
- **P8**: Packaging Factory (automated build/sign/scan pipelines)
- **P9**: AI Strategy (LLM abstraction with guardrails)
- **P10**: Scale Validation (10k/50k/100k device simulation)

### Current Status (Jan 23, 2026)

**✅ Completed Phases**:
- P2: Resilience & Reliability (circuit breakers, retry logic)
- P3: Observability & Operations (structured logging, correlation IDs)
- P4: Testing & Quality (265 comprehensive tests)
- P5: Evidence & CAB Workflow (evidence packs, risk assessment, CAB REST API)
- P6: Connector Implementation (Intune + Jamf MVP with 78 tests)
- Integration Tests (21 E2E tests)

**📋 Remaining Work**:
- P7: Agent Foundation (4 weeks estimated)
- P8: Packaging Factory (2 weeks estimated)
- P9: AI Strategy (3 weeks estimated)
- P10: Scale Validation (2 weeks estimated)

**Total Estimated Time**: 11 weeks

---

## Phase P7: Agent Foundation (4 weeks)

### Overview

Build the Control Plane infrastructure for agent management and the endpoint agent specifications. The actual agent binaries (Go-based) are a parallel track.

### P7.1: Agent Management Control Plane (Week 1)

**Objective**: Create Control Plane APIs for agent registration, heartbeat, and task assignment.

#### Models to Create

**File**: `backend/apps/agent_management/models.py`

```python
from django.db import models
from django.contrib.postgres.fields import JSONField
import uuid

class Agent(models.Model):
    """Endpoint agent registration and status."""

    PLATFORM_CHOICES = [
        ('windows', 'Windows'),
        ('macos', 'macOS'),
        ('linux', 'Linux'),
    ]

    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('DEGRADED', 'Degraded'),
        ('UNKNOWN', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    hostname = models.CharField(max_length=255)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_version = models.CharField(max_length=100)
    agent_version = models.CharField(max_length=50)

    # Registration
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat_at = models.DateTimeField()
    registration_key = models.CharField(max_length=255, unique=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNKNOWN')
    last_error = models.TextField(null=True, blank=True)

    # Hardware info
    cpu_cores = models.IntegerField()
    memory_mb = models.IntegerField()
    disk_gb = models.IntegerField()

    # Network info
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17)

    # Metadata
    tags = JSONField(default=dict)
    metadata = JSONField(default=dict)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agents'
        indexes = [
            models.Index(fields=['platform', 'status']),
            models.Index(fields=['last_heartbeat_at']),
            models.Index(fields=['hostname']),
        ]


class AgentTask(models.Model):
    """Tasks assigned to agents (deployment, remediation, telemetry)."""

    TASK_TYPE_CHOICES = [
        ('DEPLOY', 'Package Deployment'),
        ('REMEDIATE', 'Remediation Script'),
        ('COLLECT', 'Telemetry Collection'),
        ('UPDATE', 'Agent Update'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('TIMEOUT', 'Timeout'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Task payload
    payload = JSONField()

    # Execution
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    timeout_seconds = models.IntegerField(default=3600)

    # Results
    result = JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    # Audit
    correlation_id = models.CharField(max_length=100, db_index=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_tasks'
        indexes = [
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['task_type', 'status']),
            models.Index(fields=['correlation_id']),
        ]


class AgentOfflineQueue(models.Model):
    """Offline queue for agents with intermittent connectivity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='offline_queue')
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE)

    queued_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    class Meta:
        db_table = 'agent_offline_queue'
        indexes = [
            models.Index(fields=['agent', 'delivered_at']),
        ]
```

#### REST API Endpoints

**File**: `backend/apps/agent_management/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

class AgentViewSet(viewsets.ModelViewSet):
    """Agent registration and management."""

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Agent registration endpoint."""
        # Validate registration_key
        # Create or update agent record
        # Return agent_id and configuration
        pass

    @action(detail=True, methods=['post'])
    def heartbeat(self, request, pk=None):
        """Agent heartbeat endpoint."""
        agent = self.get_object()
        agent.last_heartbeat_at = timezone.now()
        agent.status = 'ONLINE'
        agent.save()

        # Return pending tasks
        pending_tasks = AgentTask.objects.filter(
            agent=agent,
            status='PENDING'
        )[:10]

        return Response({
            'status': 'ok',
            'pending_tasks': AgentTaskSerializer(pending_tasks, many=True).data
        })

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get agent's tasks."""
        agent = self.get_object()
        tasks = agent.tasks.all()[:100]
        return Response(AgentTaskSerializer(tasks, many=True).data)


class AgentTaskViewSet(viewsets.ModelViewSet):
    """Agent task management."""

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark task as started."""
        task = self.get_object()
        task.status = 'IN_PROGRESS'
        task.started_at = timezone.now()
        task.save()
        return Response({'status': 'started'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed with results."""
        task = self.get_object()
        task.status = 'COMPLETED'
        task.completed_at = timezone.now()
        task.result = request.data.get('result', {})
        task.save()
        return Response({'status': 'completed'})

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark task as failed with error."""
        task = self.get_object()
        task.status = 'FAILED'
        task.completed_at = timezone.now()
        task.error_message = request.data.get('error', '')
        task.save()
        return Response({'status': 'failed'})
```

**Endpoints**:
- `POST /api/v1/agents/register/` - Agent registration
- `POST /api/v1/agents/{id}/heartbeat/` - Heartbeat (every 60s)
- `GET /api/v1/agents/{id}/tasks/` - Get pending tasks
- `POST /api/v1/agents/tasks/{id}/start/` - Start task execution
- `POST /api/v1/agents/tasks/{id}/complete/` - Complete task
- `POST /api/v1/agents/tasks/{id}/fail/` - Fail task

### P7.2: Agent Communication Protocol (Week 2)

**Protocol**: HTTPS/2 with mTLS (mutual TLS)

#### mTLS Setup

**File**: `backend/apps/agent_management/mtls.py`

```python
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

def generate_agent_certificate(agent_id: str, common_name: str):
    """Generate client certificate for agent mTLS."""

    # Load CA certificate and key
    ca_cert = load_ca_certificate()
    ca_key = load_ca_private_key()

    # Generate agent private key
    agent_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Create certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EUCORA Agents"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, agent_id),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        agent_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(common_name)]),
        critical=False,
    ).sign(ca_key, hashes.SHA256())

    return {
        'certificate': cert.public_bytes(serialization.Encoding.PEM),
        'private_key': agent_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
    }
```

#### Middleware for mTLS Validation

**File**: `backend/apps/agent_management/middleware.py`

```python
from django.http import HttpResponse

class AgentMTLSMiddleware:
    """Validate agent mTLS certificates."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to agent API endpoints
        if request.path.startswith('/api/v1/agents/'):
            if not self.validate_client_certificate(request):
                return HttpResponse('Unauthorized', status=401)

        return self.get_response(request)

    def validate_client_certificate(self, request):
        """Validate client certificate from request."""
        # Extract certificate from request headers
        # Verify against CA
        # Check expiry
        # Return True if valid
        pass
```

### P7.3: Offline Queue & Replay (Week 3)

**Service**: `backend/apps/agent_management/services.py`

```python
from django.utils import timezone
from datetime import timedelta

class AgentOfflineService:
    """Manage offline queue and replay for agents."""

    def queue_task_for_offline_agent(self, agent_id: str, task_id: str):
        """Queue task for offline agent."""
        AgentOfflineQueue.objects.create(
            agent_id=agent_id,
            task_id=task_id,
            queued_at=timezone.now()
        )

    def replay_offline_queue(self, agent_id: str):
        """Replay offline queue when agent comes online."""
        queued_items = AgentOfflineQueue.objects.filter(
            agent_id=agent_id,
            delivered_at__isnull=True
        ).order_by('queued_at')

        delivered = []
        for item in queued_items:
            try:
                # Deliver task to agent
                self.deliver_task(item.task)
                item.delivered_at = timezone.now()
                item.save()
                delivered.append(item.task_id)
            except Exception as e:
                item.retry_count += 1
                item.save()
                if item.retry_count >= item.max_retries:
                    # Mark task as failed
                    item.task.status = 'FAILED'
                    item.task.error_message = f'Max retries exceeded: {str(e)}'
                    item.task.save()

        return delivered

    def cleanup_stale_queue_items(self):
        """Cleanup queue items older than 7 days."""
        cutoff = timezone.now() - timedelta(days=7)
        AgentOfflineQueue.objects.filter(
            queued_at__lt=cutoff
        ).delete()
```

### P7.4: Agent Health Monitoring (Week 4)

**Celery Task**: `backend/apps/agent_management/tasks.py`

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def check_agent_health():
    """Check agent health and mark offline agents."""
    cutoff = timezone.now() - timedelta(minutes=5)

    # Mark agents offline if no heartbeat for 5 minutes
    Agent.objects.filter(
        last_heartbeat_at__lt=cutoff,
        status='ONLINE'
    ).update(status='OFFLINE')

    # Alert on critical offline agents
    critical_offline = Agent.objects.filter(
        status='OFFLINE',
        tags__critical=True
    )

    for agent in critical_offline:
        send_alert(f'Critical agent offline: {agent.hostname}')

@shared_task
def timeout_stale_tasks():
    """Timeout tasks that have been running too long."""
    cutoff = timezone.now() - timedelta(hours=1)

    stale_tasks = AgentTask.objects.filter(
        status='IN_PROGRESS',
        started_at__lt=cutoff
    )

    stale_tasks.update(
        status='TIMEOUT',
        completed_at=timezone.now(),
        error_message='Task timeout after 1 hour'
    )
```

### P7.5: Agent Specification Document

**File**: `docs/agent/AGENT_SPECIFICATION.md`

Document the agent binary requirements:
- Go-based cross-platform agent
- Communication protocol (HTTPS/2 + mTLS)
- Telemetry collection (CPU, memory, disk, installed software)
- Package deployment execution
- Remediation script execution
- Offline queue with local storage
- Auto-update mechanism

**Agent directories**:
- `/var/lib/eucora-agent/` (Linux)
- `C:\ProgramData\EUCORA\Agent\` (Windows)
- `/Library/Application Support/EUCORA/Agent/` (macOS)

---

## Phase P8: Packaging Factory (2 weeks)

### Overview

Automated packaging pipeline with supply chain controls.

### P8.1: Packaging Pipeline Models (Week 1)

**File**: `backend/apps/packaging_factory/models.py`

```python
class PackagingPipeline(models.Model):
    """Packaging pipeline execution record."""

    PLATFORM_CHOICES = [
        ('windows', 'Windows'),
        ('macos', 'macOS'),
        ('linux', 'Linux'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('BUILDING', 'Building'),
        ('SIGNING', 'Signing'),
        ('SCANNING', 'Scanning'),
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Input
    source_artifact_url = models.URLField()
    source_artifact_hash = models.CharField(max_length=64)

    # Build
    build_started_at = models.DateTimeField(null=True, blank=True)
    build_completed_at = models.DateTimeField(null=True, blank=True)
    build_logs = models.TextField(blank=True)

    # Sign
    signing_started_at = models.DateTimeField(null=True, blank=True)
    signing_completed_at = models.DateTimeField(null=True, blank=True)
    signing_certificate_thumbprint = models.CharField(max_length=64, blank=True)

    # SBOM
    sbom_generated_at = models.DateTimeField(null=True, blank=True)
    sbom_format = models.CharField(max_length=20, blank=True)
    sbom_url = models.URLField(blank=True)

    # Scan
    scan_started_at = models.DateTimeField(null=True, blank=True)
    scan_completed_at = models.DateTimeField(null=True, blank=True)
    scan_results = JSONField(default=dict)
    scan_pass = models.BooleanField(default=False)

    # Policy decision
    policy_decision = models.CharField(max_length=50, blank=True)
    exception_id = models.UUIDField(null=True, blank=True)

    # Output
    output_artifact_url = models.URLField(blank=True)
    output_artifact_hash = models.CharField(max_length=64, blank=True)

    # Audit
    correlation_id = models.CharField(max_length=100, db_index=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'packaging_pipelines'
```

### P8.2: Pipeline Execution Service

**File**: `backend/apps/packaging_factory/services.py`

```python
class PackagingFactoryService:
    """Execute packaging pipelines with gates."""

    def execute_pipeline(self, pipeline_id: str):
        """Execute complete packaging pipeline."""
        pipeline = PackagingPipeline.objects.get(id=pipeline_id)

        try:
            # Build
            self.build_package(pipeline)

            # Sign
            self.sign_package(pipeline)

            # Generate SBOM
            self.generate_sbom(pipeline)

            # Scan for vulnerabilities
            self.scan_vulnerabilities(pipeline)

            # Policy decision
            self.evaluate_policy(pipeline)

            # Store artifact
            self.store_artifact(pipeline)

            pipeline.status = 'PASSED'
        except Exception as e:
            pipeline.status = 'FAILED'
            pipeline.build_logs += f'\nError: {str(e)}'
        finally:
            pipeline.save()

    def build_package(self, pipeline):
        """Build platform-specific package."""
        if pipeline.platform == 'windows':
            self.build_windows_package(pipeline)
        elif pipeline.platform == 'macos':
            self.build_macos_package(pipeline)
        elif pipeline.platform == 'linux':
            self.build_linux_package(pipeline)

    def scan_vulnerabilities(self, pipeline):
        """Scan package for vulnerabilities using Trivy."""
        # Run: trivy fs --format json <package_path>
        scan_results = run_trivy_scan(pipeline.output_artifact_url)

        pipeline.scan_results = scan_results
        pipeline.scan_completed_at = timezone.now()

        # Count critical/high vulnerabilities
        critical_count = scan_results.get('critical', 0)
        high_count = scan_results.get('high', 0)

        pipeline.scan_pass = (critical_count == 0 and high_count == 0)
        pipeline.save()
```

### P8.3: Integration with Evidence Packs

Link packaging pipeline results to evidence packs:

```python
def create_evidence_pack_from_pipeline(pipeline_id: str):
    """Create evidence pack from completed pipeline."""
    pipeline = PackagingPipeline.objects.get(id=pipeline_id)

    evidence_pack = EvidencePack.objects.create(
        deployment_intent_id=pipeline.deployment_intent_id,
        evidence_data={
            'artifacts': {
                'source_hash': pipeline.source_artifact_hash,
                'output_hash': pipeline.output_artifact_hash,
                'signing_certificate': pipeline.signing_certificate_thumbprint,
            },
            'sbom': {
                'format': pipeline.sbom_format,
                'url': pipeline.sbom_url,
            },
            'scan_results': pipeline.scan_results,
        },
        correlation_id=pipeline.correlation_id
    )

    return evidence_pack
```

---

## Phase P9: AI Strategy (3 weeks)

### Overview

LLM-based AI with provider abstraction and guardrails.

### P9.1: LLM Provider Abstraction (Week 1)

**File**: `backend/apps/ai_agents/providers/base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class CompletionRequest:
    """LLM completion request."""
    prompt: str
    context: Dict
    temperature: float = 0.7
    max_tokens: int = 1000

@dataclass
class CompletionResponse:
    """LLM completion response."""
    text: str
    confidence: float
    model: str
    provider: str
    reasoning: Optional[List[str]] = None
    tokens_used: int = 0

class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate completion."""
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate API key configuration."""
        pass
```

**OpenAI Provider**: `backend/apps/ai_agents/providers/openai_provider.py`

```python
import openai

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = 'gpt-4'):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a deployment assistant."},
                {"role": "user", "content": request.prompt}
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return CompletionResponse(
            text=response.choices[0].message.content,
            confidence=1.0,
            model=self.model,
            provider='openai',
            tokens_used=response.usage.total_tokens
        )
```

### P9.2: Prompt Engineering Framework (Week 2)

**File**: `backend/apps/ai_agents/prompts/deployment_prompts.py`

```python
INCIDENT_CLASSIFICATION_PROMPT = """
Analyze the following incident report and classify it:

Incident Description: {description}
Affected Devices: {device_count}
Error Messages: {error_messages}

Classify the incident into one of:
- INSTALLATION_FAILURE
- COMPATIBILITY_ISSUE
- NETWORK_ISSUE
- PERMISSION_ISSUE
- CONFIGURATION_ERROR

Also provide:
1. Root cause analysis (1-2 sentences)
2. Recommended remediation steps
3. Severity (LOW/MEDIUM/HIGH/CRITICAL)

Format your response as JSON.
"""

REMEDIATION_SUGGESTION_PROMPT = """
Given the following incident, suggest remediation steps:

Incident Type: {incident_type}
Platform: {platform}
Error: {error_message}

Provide:
1. Immediate remediation steps (numbered list)
2. Long-term prevention measures
3. Estimated time to resolve
4. Risk of remediation actions

Be specific and actionable.
"""
```

### P9.3: Guardrails & Safety (Week 3)

**File**: `backend/apps/ai_agents/guardrails.py`

```python
import re
from typing import Dict, Any

class AIGuardrails:
    """Safety guardrails for AI suggestions."""

    # PII patterns
    PII_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{16}\b',  # Credit card
    ]

    def sanitize_input(self, text: str) -> str:
        """Remove PII from input."""
        sanitized = text
        for pattern in self.PII_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        return sanitized

    def validate_output(self, output: str) -> bool:
        """Validate AI output for safety."""
        # Check for harmful commands
        harmful_patterns = [
            r'rm\s+-rf\s+/',
            r'format\s+c:',
            r'del\s+/s\s+/q',
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return False

        return True

    def add_confidence_score(self, response: CompletionResponse) -> CompletionResponse:
        """Add confidence score based on output characteristics."""
        # Simple heuristic: longer, more detailed responses are more confident
        confidence = min(1.0, len(response.text) / 500)
        response.confidence = confidence
        return response
```

---

## Phase P10: Scale Validation (2 weeks)

### Overview

Simulate 10k/50k/100k devices and validate performance.

### P10.1: Device Simulator (Week 1)

**File**: `tools/load_testing/device_simulator.py`

```python
import asyncio
import aiohttp
import random
from datetime import datetime

class DeviceSimulator:
    """Simulate endpoint devices for scale testing."""

    def __init__(self, api_url: str, num_devices: int):
        self.api_url = api_url
        self.num_devices = num_devices
        self.devices = []

    async def register_device(self, session, device_id: int):
        """Register simulated device."""
        async with session.post(f'{self.api_url}/api/v1/agents/register/', json={
            'hostname': f'device-{device_id:06d}',
            'platform': random.choice(['windows', 'macos', 'linux']),
            'agent_version': '1.0.0',
            'cpu_cores': random.randint(2, 16),
            'memory_mb': random.randint(4096, 65536),
        }) as response:
            return await response.json()

    async def send_heartbeat(self, session, agent_id: str):
        """Send heartbeat for device."""
        async with session.post(f'{self.api_url}/api/v1/agents/{agent_id}/heartbeat/') as response:
            return await response.json()

    async def send_telemetry(self, session, agent_id: str):
        """Send telemetry data."""
        telemetry = {
            'cpu_usage': random.uniform(10, 90),
            'memory_usage': random.uniform(20, 80),
            'disk_usage': random.uniform(30, 70),
            'timestamp': datetime.now().isoformat(),
        }
        async with session.post(f'{self.api_url}/api/v1/agents/{agent_id}/telemetry/', json=telemetry) as response:
            return await response.json()

    async def run_simulation(self):
        """Run full simulation."""
        async with aiohttp.ClientSession() as session:
            # Register devices
            print(f'Registering {self.num_devices} devices...')
            tasks = [self.register_device(session, i) for i in range(self.num_devices)]
            self.devices = await asyncio.gather(*tasks)

            # Send heartbeats every 60s
            while True:
                print(f'Sending heartbeats for {len(self.devices)} devices...')
                tasks = [self.send_heartbeat(session, d['id']) for d in self.devices]
                await asyncio.gather(*tasks)

                # Send telemetry every 5 minutes
                if random.random() < 0.2:
                    print('Sending telemetry...')
                    tasks = [self.send_telemetry(session, d['id']) for d in self.devices]
                    await asyncio.gather(*tasks)

                await asyncio.sleep(60)

if __name__ == '__main__':
    simulator = DeviceSimulator('http://localhost:8000', num_devices=10000)
    asyncio.run(simulator.run_simulation())
```

### P10.2: Performance Baseline (Week 2)

**File**: `tools/load_testing/performance_test.py`

```python
import time
import statistics

class PerformanceTest:
    """Measure performance under load."""

    def test_api_latency(self):
        """Measure API latency under load."""
        latencies = []

        for i in range(1000):
            start = time.time()
            response = requests.get(f'{API_URL}/api/v1/agents/')
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        return {
            'p50': statistics.median(latencies),
            'p95': statistics.quantiles(latencies, n=20)[18],
            'p99': statistics.quantiles(latencies, n=100)[98],
            'mean': statistics.mean(latencies),
        }

    def test_deployment_throughput(self):
        """Measure deployment throughput."""
        start = time.time()

        # Create 1000 deployment intents
        for i in range(1000):
            create_deployment_intent()

        elapsed = time.time() - start
        throughput = 1000 / elapsed

        return {
            'deployments_per_second': throughput,
            'total_time': elapsed,
        }
```

---

## Testing Strategy

### Unit Tests

Each phase requires ≥90% test coverage:

**P7 Agent Management**:
- Agent registration
- Heartbeat processing
- Task assignment
- Offline queue replay
- Health monitoring

**P8 Packaging Factory**:
- Pipeline execution
- Signing operations
- Vulnerability scanning
- Policy enforcement

**P9 AI Strategy**:
- Provider abstraction
- Prompt rendering
- Guardrails (PII sanitization)
- Confidence scoring

**P10 Scale Validation**:
- Device simulator
- Performance metrics
- Auto-scaling triggers

### Integration Tests

Test end-to-end flows:
1. Agent registration → Task assignment → Execution → Result
2. Package intake → Build → Sign → Scan → Evidence pack
3. Incident → AI classification → Remediation suggestion → Approval
4. 10k devices → Heartbeats → Telemetry → Query performance

---

## Docker Testing Procedure

When Docker is available, test each phase:

```bash
# Start services
docker compose -f docker-compose.dev.yml up -d

# Run migrations
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

# Run tests
docker compose -f docker-compose.dev.yml exec backend pytest apps/agent_management/tests/
docker compose -f docker-compose.dev.yml exec backend pytest apps/packaging_factory/tests/
docker compose -f docker-compose.dev.yml exec backend pytest apps/ai_agents/tests/

# Check logs
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f celery

# Monitor performance
docker stats

# Cleanup
docker compose -f docker-compose.dev.yml down
```

---

## Implementation Order

1. **Week 1-2**: P7.1 + P7.2 (Agent management APIs + mTLS)
2. **Week 3-4**: P7.3 + P7.4 (Offline queue + Health monitoring)
3. **Week 5-6**: P8 (Packaging Factory)
4. **Week 7-9**: P9 (AI Strategy)
5. **Week 10-11**: P10 (Scale Validation)

**Total**: 11 weeks to complete P7-P10

---

## Success Criteria

### P7 Complete When:
- [ ] Agent registration API works
- [ ] Heartbeat processing works
- [ ] Task assignment works
- [ ] Offline queue with replay works
- [ ] Health monitoring works
- [ ] ≥90% test coverage
- [ ] Agent specification documented

### P8 Complete When:
- [ ] Windows packaging pipeline works
- [ ] macOS packaging pipeline works
- [ ] Linux packaging pipeline works
- [ ] SBOM generation works
- [ ] Vulnerability scanning works
- [ ] Policy enforcement works
- [ ] ≥90% test coverage

### P9 Complete When:
- [ ] Provider abstraction works (OpenAI + Azure OpenAI)
- [ ] Prompt framework documented
- [ ] Guardrails work (PII filtering)
- [ ] Confidence scoring works
- [ ] Human-in-loop integration works
- [ ] ≥90% test coverage

### P10 Complete When:
- [ ] 10k device simulation passes
- [ ] 50k device simulation passes
- [ ] 100k device simulation passes
- [ ] Performance baseline documented
- [ ] Auto-scaling rules configured

---

## Next Steps

1. **Review this roadmap** with tech lead and stakeholders
2. **Allocate resources** for 11-week implementation
3. **Start P7.1** (Agent Management Control Plane)
4. **Set up Docker environment** for testing
5. **Weekly status reviews** to track progress

**Estimated Completion**: April 7, 2026 (11 weeks from now)
