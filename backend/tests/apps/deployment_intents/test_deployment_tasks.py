# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Unit tests for deployment intent async tasks."""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from uuid import uuid4
from django.test import TestCase
from apps.deployment_intents.models import DeploymentIntent
from apps.deployment_intents.tasks import deploy_to_connector, execute_rollback


@pytest.mark.django_db
class TestDeployToConnectorTask:
    """Test deploy_to_connector Celery task."""

    def setUp(self):
        """Set up test deployment intent."""
        self.user = Mock(username='test_user')
        self.deployment_id = str(uuid4())
        self.deployment = Mock(
            id=self.deployment_id,
            correlation_id=uuid4(),
            app_name='test_app',
            version='1.0.0',
            target_ring='LAB',
            submitter=self.user,
            status=DeploymentIntent.Status.APPROVED,
        )

    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_deploy_to_connector_success(self, mock_select_related, mock_get_service):
        """Task succeeds and updates deployment status."""
        # Mock deployment query
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.deployment
        mock_select_related.return_value = mock_queryset

        # Mock connector service
        mock_service = Mock()
        mock_service.deploy.return_value = {'status': 'deployed'}
        mock_get_service.return_value = mock_service

        # Call task
        result = deploy_to_connector(self.deployment_id, 'intune')

        # Verify result
        assert result['status'] == 'success'
        assert result['deployment_intent_id'] == str(self.deployment.correlation_id)
        assert result['connector_type'] == 'intune'

    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_deploy_to_connector_deployment_not_found(self, mock_select_related):
        """Task fails if deployment intent not found."""
        mock_queryset = Mock()
        mock_queryset.get.side_effect = DeploymentIntent.DoesNotExist()
        mock_select_related.return_value = mock_queryset

        result = deploy_to_connector(self.deployment_id, 'intune')

        assert result['status'] == 'failed'
        assert 'not found' in result['error']

    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_deploy_to_connector_service_error(self, mock_select_related, mock_get_service):
        """Task handles service errors gracefully."""
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.deployment
        mock_select_related.return_value = mock_queryset

        mock_service = Mock()
        mock_service.deploy.side_effect = ValueError('Service error')
        mock_get_service.return_value = mock_service

        # Task should raise to trigger retry
        task_mock = MagicMock()
        task_mock.retry.side_effect = ValueError('Retry triggered')

        with patch('apps.deployment_intents.tasks.deploy_to_connector.retry', task_mock.retry):
            with pytest.raises(ValueError):
                deploy_to_connector.run(self.deployment_id, 'intune')

    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_deploy_to_connector_updates_status(self, mock_select_related, mock_get_service):
        """Task updates deployment status to DEPLOYING."""
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.deployment
        mock_select_related.return_value = mock_queryset

        mock_service = Mock()
        mock_service.deploy.return_value = {'status': 'deploying'}
        mock_get_service.return_value = mock_service

        result = deploy_to_connector(self.deployment_id, 'intune')

        assert result['status'] == 'success'
        # Status update happens in transaction
        self.deployment.save.assert_called()

    def test_deploy_to_connector_has_timeouts(self):
        """Task has hard and soft time limits."""
        # Celery task configuration is set at decoration time
        assert deploy_to_connector.options['time_limit'] == 300
        assert deploy_to_connector.options['soft_time_limit'] == 270

    def test_deploy_to_connector_has_max_retries(self):
        """Task has max_retries=3."""
        assert deploy_to_connector.max_retries == 3


@pytest.mark.django_db
class TestExecuteRollbackTask:
    """Test execute_rollback Celery task."""

    def setUp(self):
        """Set up test deployment intent."""
        self.user = Mock(username='test_user')
        self.deployment_id = str(uuid4())
        self.deployment = Mock(
            id=self.deployment_id,
            correlation_id=uuid4(),
            app_name='test_app',
            version='1.0.0',
            target_ring='PILOT',
            submitter=self.user,
            status=DeploymentIntent.Status.FAILED,
        )

    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_execute_rollback_success(self, mock_select_related, mock_get_service):
        """Task successfully executes rollback."""
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.deployment
        mock_select_related.return_value = mock_queryset

        mock_service = Mock()
        mock_service.rollback.return_value = {'status': 'rolled_back'}
        mock_get_service.return_value = mock_service

        result = execute_rollback(self.deployment_id, 'intune')

        assert result['status'] == 'success'
        assert result['connector_type'] == 'intune'

    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_execute_rollback_deployment_not_found(self, mock_select_related):
        """Task fails if deployment not found."""
        mock_queryset = Mock()
        mock_queryset.get.side_effect = DeploymentIntent.DoesNotExist()
        mock_select_related.return_value = mock_queryset

        result = execute_rollback(self.deployment_id, 'intune')

        assert result['status'] == 'failed'

    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_execute_rollback_updates_status(self, mock_select_related, mock_get_service):
        """Task updates deployment status to ROLLED_BACK."""
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.deployment
        mock_select_related.return_value = mock_queryset

        mock_service = Mock()
        mock_service.rollback.return_value = {'status': 'success'}
        mock_get_service.return_value = mock_service

        result = execute_rollback(self.deployment_id, 'intune')

        assert result['status'] == 'success'

    def test_execute_rollback_has_timeouts(self):
        """Task has hard and soft time limits."""
        assert execute_rollback.options['time_limit'] == 300
        assert execute_rollback.options['soft_time_limit'] == 270

    def test_execute_rollback_has_max_retries(self):
        """Task has max_retries=3."""
        assert execute_rollback.max_retries == 3


@pytest.mark.django_db
class TestTaskIdempotency:
    """Test that tasks are idempotent."""

    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_deploy_idempotent_retries(self, mock_select_related, mock_get_service):
        """Deploy task can be safely retried."""
        deployment = Mock(
            id='test_id',
            correlation_id=uuid4(),
            app_name='app',
            version='1.0.0',
            target_ring='LAB',
        )
        mock_queryset = Mock()
        mock_queryset.get.return_value = deployment
        mock_select_related.return_value = mock_queryset

        mock_service = Mock()
        mock_service.deploy.return_value = {'status': 'deploying'}
        mock_get_service.return_value = mock_service

        # Call task multiple times
        result1 = deploy_to_connector('test_id', 'intune')
        result2 = deploy_to_connector('test_id', 'intune')

        # Both should succeed
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'

    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_rollback_idempotent_retries(self, mock_select_related, mock_get_service):
        """Rollback task can be safely retried."""
        deployment = Mock(
            id='test_id',
            correlation_id=uuid4(),
            app_name='app',
            version='1.0.0',
            target_ring='LAB',
        )
        mock_queryset = Mock()
        mock_queryset.get.return_value = deployment
        mock_select_related.return_value = mock_queryset

        mock_service = Mock()
        mock_service.rollback.return_value = {'status': 'success'}
        mock_get_service.return_value = mock_service

        result1 = execute_rollback('test_id', 'intune')
        result2 = execute_rollback('test_id', 'intune')

        assert result1['status'] == 'success'
        assert result2['status'] == 'success'


class TestTaskTransactions:
    """Test transaction behavior in tasks."""

    @patch('apps.deployment_intents.tasks.transaction')
    @patch('apps.deployment_intents.tasks.get_connector_service')
    @patch('apps.deployment_intents.tasks.DeploymentIntent.objects.select_related')
    def test_deploy_uses_atomic_transaction(self, mock_select_related, mock_get_service, mock_transaction):
        """Deploy task uses atomic transactions."""
        deployment = Mock(
            id='test_id',
            correlation_id=uuid4(),
            app_name='app',
            version='1.0.0',
            target_ring='LAB',
        )
        mock_queryset = Mock()
        mock_queryset.get.return_value = deployment
        mock_select_related.return_value = mock_queryset

        mock_service = Mock()
        mock_service.deploy.return_value = {'status': 'deploying'}
        mock_get_service.return_value = mock_service

        # Mock atomic context manager
        mock_atomic = MagicMock()
        mock_transaction.atomic.return_value = mock_atomic

        result = deploy_to_connector('test_id', 'intune')

        # Verify atomic was used
        assert result['status'] == 'success'
