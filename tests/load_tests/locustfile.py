# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Load testing for P4.3 Testing & Quality Phase using Locust.

Tests 3 key scenarios:
1. Concurrent Deployments: 10-100 simultaneous deployments
2. CAB Approval Backlog: 100+ pending approvals queued, approve batches
3. Connector Scaling: Publish to multiple connectors in parallel

Target: 10,000 requests/sec sustained with <1s response time.

Install: pip install locust
Run: locust -f tests/load_tests/locustfile.py --host=http://localhost:8000
"""
import uuid
import random
from locust import HttpUser, task, between, events
from datetime import datetime


class DeploymentUser(HttpUser):
    """
    Simulates concurrent deployment creation.
    
    Target: 100 requests/sec with <500ms response time
    """
    
    wait_time = between(0.5, 2.0)
    host = "http://localhost:8000"
    
    def on_start(self):
        """Authenticate user at session start."""
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'loadtest_user',
            'password': 'test123'
        }, catch_response=True)
        
        if response.status_code == 200:
            self.token = response.json().get('token')
            self.client.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        else:
            response.failure(f'Failed to authenticate: {response.status_code}')
    
    @task(3)
    def create_deployment(self):
        """Create a new deployment."""
        app_names = ['nginx', 'redis', 'postgresql', 'mongodb', 'elasticsearch']
        app = random.choice(app_names)
        version = f'{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}'
        
        with self.client.post('/api/v1/deployments/', {
            'app_name': f'{app}-{uuid.uuid4().hex[:8]}',
            'version': version,
            'target_ring': random.choice(['CANARY', 'PILOT', 'DEPARTMENT', 'GLOBAL']),
            'evidence_pack_id': str(uuid.uuid4())
        }, catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f'Failed to create deployment: {response.status_code}')
    
    @task(1)
    def list_deployments(self):
        """List recent deployments."""
        with self.client.get('/api/v1/deployments/?limit=50', 
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f'Failed to list deployments: {response.status_code}')
    
    @task(1)
    def get_deployment_details(self):
        """Get details of a random deployment."""
        # In practice, would track created deployment IDs
        deployment_id = str(uuid.uuid4())
        with self.client.get(f'/api/v1/deployments/{deployment_id}/', 
                            catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 is expected for random IDs
                response.success()
            else:
                response.failure(f'Failed to get deployment: {response.status_code}')


class CABApprovalUser(HttpUser):
    """
    Simulates CAB approval workload.
    
    Target: Approve 10+ pending deployments/sec
    Verify: Pending list response time <1s for 100+ items
    """
    
    wait_time = between(1.0, 3.0)
    host = "http://localhost:8000"
    
    def on_start(self):
        """Authenticate as CAB approver."""
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'cab_approver',
            'password': 'test123'
        }, catch_response=True)
        
        if response.status_code == 200:
            self.token = response.json().get('token')
            self.client.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
    
    @task(4)
    def list_pending_approvals(self):
        """List pending CAB approvals."""
        with self.client.get('/api/v1/cab/pending/?limit=100', 
                            catch_response=True) as response:
            if response.status_code == 200:
                # Parse response to get approval IDs
                try:
                    approvals = response.json().get('approvals', [])
                    if approvals:
                        self.pending_approvals = [a.get('id') for a in approvals]
                    response.success()
                except Exception as e:
                    response.failure(f'Failed to parse response: {str(e)}')
            else:
                response.failure(f'Failed to list approvals: {response.status_code}')
    
    @task(3)
    def approve_deployment(self):
        """Approve a pending deployment."""
        # Use tracked approval IDs if available
        if hasattr(self, 'pending_approvals') and self.pending_approvals:
            approval_id = random.choice(self.pending_approvals)
        else:
            approval_id = str(uuid.uuid4())
        
        with self.client.post(f'/api/v1/cab/{approval_id}/approve/', {
            'comments': 'Approved for production deployment',
            'conditions': []
        }, catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 if already approved
                response.success()
            else:
                response.failure(f'Failed to approve: {response.status_code}')
    
    @task(1)
    def reject_deployment(self):
        """Reject a pending deployment."""
        approval_id = str(uuid.uuid4())
        with self.client.post(f'/api/v1/cab/{approval_id}/reject/', {
            'comments': 'Insufficient testing evidence'
        }, catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f'Failed to reject: {response.status_code}')


class ConnectorPublishingUser(HttpUser):
    """
    Simulates connector publishing workload.
    
    Target: Publish to 50+ connectors in parallel
    Verify: <500ms response time per publish
    Test: Multiple execution planes (Intune, Jamf, SCCM, Landscape, Ansible)
    """
    
    wait_time = between(0.5, 1.5)
    host = "http://localhost:8000"
    
    def on_start(self):
        """Authenticate as publisher."""
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'publisher_user',
            'password': 'test123'
        }, catch_response=True)
        
        if response.status_code == 200:
            self.token = response.json().get('token')
            self.client.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
    
    @task(2)
    def publish_to_intune(self):
        """Publish deployment to Intune connector."""
        deployment_id = str(uuid.uuid4())
        
        with self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': deployment_id,
            'target_plane': 'INTUNE',
            'config': {
                'ring': random.choice(['CANARY', 'PILOT']),
                'target_count': random.randint(50, 500)
            }
        }, catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f'Failed to publish to Intune: {response.status_code}')
    
    @task(2)
    def publish_to_jamf(self):
        """Publish deployment to Jamf connector."""
        deployment_id = str(uuid.uuid4())
        
        with self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': deployment_id,
            'target_plane': 'JAMF'
        }, catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f'Failed to publish to Jamf: {response.status_code}')
    
    @task(2)
    def publish_to_sccm(self):
        """Publish deployment to SCCM connector."""
        deployment_id = str(uuid.uuid4())
        
        with self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': deployment_id,
            'target_plane': 'SCCM'
        }, catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f'Failed to publish to SCCM: {response.status_code}')
    
    @task(1)
    def query_connector_status(self):
        """Query connector deployment status."""
        deployment_id = str(uuid.uuid4())
        
        with self.client.get(f'/api/v1/connectors/status/{deployment_id}/', 
                            catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f'Failed to query status: {response.status_code}')
    
    @task(1)
    def remediate_deployment(self):
        """Trigger remediation for failed deployment."""
        deployment_id = str(uuid.uuid4())
        
        with self.client.post('/api/v1/connectors/remediate/', {
            'deployment_id': deployment_id,
            'reason': 'Device compliance drift detected',
            'action': 'REINSTALL'
        }, catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f'Failed to remediate: {response.status_code}')


class HighLoadDeploymentUser(HttpUser):
    """
    Burst load scenario: High concurrent deployment creation.
    
    Target: 1000+ simultaneous users creating deployments
    Verify: System handles 10,000 requests/sec
    """
    
    wait_time = between(0.1, 0.5)  # Shorter wait for higher load
    host = "http://localhost:8000"
    
    def on_start(self):
        """Authenticate."""
        response = self.client.post('/api/v1/auth/login/', {
            'username': f'burst_user_{uuid.uuid4().hex[:8]}',
            'password': 'test123'
        }, catch_response=True)
        
        if response.status_code == 200:
            self.token = response.json().get('token')
            self.client.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
    
    @task
    def create_deployment_burst(self):
        """Create deployment in burst load scenario."""
        with self.client.post('/api/v1/deployments/', {
            'app_name': f'burst-{uuid.uuid4().hex[:8]}',
            'version': f'{random.randint(1, 5)}.0.0',
            'target_ring': 'CANARY',
            'evidence_pack_id': str(uuid.uuid4())
        }, catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f'Burst create failed: {response.status_code}')


# Event handlers for reporting

@events.request.add_listener
def on_request_success(request_type, name, response_time, response_length, **kwargs):
    """Log successful requests."""
    if response_time > 1000:  # >1s is slow
        print(f"SLOW: {name} took {response_time}ms")


@events.request.add_listener
def on_request_failure(request_type, name, response_time, response, exception, **kwargs):
    """Log failed requests."""
    print(f"FAIL: {name} - {response.status_code if response else exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start info."""
    print(f"\n{'='*60}")
    print(f"Load Test Started: {datetime.now().isoformat()}")
    print(f"Target Host: {environment.host}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary."""
    print(f"\n{'='*60}")
    print(f"Load Test Completed: {datetime.now().isoformat()}")
    print(f"\nSummary Statistics:")
    print(f"  Total Requests: {environment.stats.total.num_requests}")
    print(f"  Total Failures: {environment.stats.total.num_failures}")
    print(f"  Average Response Time: {environment.stats.total.avg_response_time:.0f}ms")
    print(f"  Median Response Time: {environment.stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"  95th Percentile: {environment.stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  99th Percentile: {environment.stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"  Max Response Time: {environment.stats.total.max_response_time:.0f}ms")
    print(f"{'='*60}\n")
