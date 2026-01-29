# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for P7 AI Governance models (AIModel, AgentExecution, ModelDriftMetric)."""
import hashlib
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.ai_agents.models import AgentExecution, AIModel, ModelDriftMetric

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
        email="test@example.com",
    )


@pytest.fixture
def ai_model(db, user):
    """Create a test AI model."""
    return AIModel.objects.create(
        model_id="incident-classifier-v1",
        model_type="classification",
        version="1.0.0",
        display_name="Incident Classifier",
        description="Classifies incidents by severity",
        status=AIModel.ModelStatus.DEPLOYED,
        risk_level=AIModel.RiskLevel.R1_LOW,
        dataset_version="dataset-2026-01",
        training_params={"epochs": 100, "batch_size": 32},
        validation_report={"accuracy": 0.92, "f1_score": 0.89},
        baseline_accuracy=0.92,
        baseline_confidence_mean=0.85,
        baseline_latency_ms=150.0,
        created_by=user,
        deployed_at=timezone.now(),
        deployed_by=user,
    )


class TestAIModel:
    """Tests for AIModel."""

    def test_create_ai_model(self, db, user):
        """Test creating an AI model."""
        model = AIModel.objects.create(
            model_id="test-model-v1",
            model_type="recommendation",
            version="1.0.0",
            display_name="Test Model",
            status=AIModel.ModelStatus.DRAFT,
            risk_level=AIModel.RiskLevel.R2_MEDIUM,
            created_by=user,
        )
        assert model.id is not None
        assert model.model_id == "test-model-v1"
        assert model.status == AIModel.ModelStatus.DRAFT

    def test_model_status_choices(self, ai_model):
        """Test model status choices."""
        valid_statuses = [
            AIModel.ModelStatus.DRAFT,
            AIModel.ModelStatus.VALIDATED,
            AIModel.ModelStatus.DEPLOYED,
            AIModel.ModelStatus.DEPRECATED,
            AIModel.ModelStatus.RETIRED,
        ]
        for status in valid_statuses:
            ai_model.status = status
            ai_model.save()
            ai_model.refresh_from_db()
            assert ai_model.status == status

    def test_model_risk_level_choices(self, ai_model):
        """Test model risk level choices."""
        valid_levels = [
            AIModel.RiskLevel.R1_LOW,
            AIModel.RiskLevel.R2_MEDIUM,
            AIModel.RiskLevel.R3_HIGH,
        ]
        for level in valid_levels:
            ai_model.risk_level = level
            ai_model.save()
            ai_model.refresh_from_db()
            assert ai_model.risk_level == level

    def test_model_id_unique(self, ai_model, user):
        """Test model_id must be unique."""
        with pytest.raises(Exception):  # IntegrityError
            AIModel.objects.create(
                model_id="incident-classifier-v1",  # Duplicate
                model_type="classification",
                version="2.0.0",
                display_name="Duplicate Model",
                created_by=user,
            )

    def test_model_lineage_tracking(self, db, user, ai_model):
        """Test model lineage with parent_model."""
        child_model = AIModel.objects.create(
            model_id="incident-classifier-v2",
            model_type="classification",
            version="2.0.0",
            display_name="Incident Classifier v2",
            parent_model=ai_model,
            created_by=user,
        )
        assert child_model.parent_model == ai_model
        assert ai_model.derived_models.count() == 1
        assert ai_model.derived_models.first() == child_model

    def test_model_str(self, ai_model):
        """Test model string representation."""
        result = str(ai_model)
        assert "Incident Classifier" in result
        assert "1.0.0" in result
        assert "deployed" in result.lower()

    def test_model_training_params_json(self, ai_model):
        """Test training params JSON field."""
        assert ai_model.training_params["epochs"] == 100
        assert ai_model.training_params["batch_size"] == 32


class TestAgentExecution:
    """Tests for AgentExecution."""

    @pytest.fixture
    def execution(self, db, user, ai_model):
        """Create a test agent execution."""
        return AgentExecution.objects.create(
            agent_type="incident_classifier",
            model=ai_model,
            input_hash=hashlib.sha256(b"test input").hexdigest(),
            input_summary={"title": "Test Incident", "severity": "medium"},
            output={"classification": "P2", "confidence": 0.87},
            confidence=0.87,
            latency_ms=145.5,
            risk_level="R1",
            approval_required=False,
            approval_status=AgentExecution.ApprovalStatus.NOT_REQUIRED,
            initiated_by=user,
        )

    def test_create_execution(self, execution):
        """Test creating an agent execution."""
        assert execution.id is not None
        assert execution.correlation_id is not None
        assert execution.agent_type == "incident_classifier"

    def test_execution_approval_workflow(self, db, user, ai_model):
        """Test execution approval workflow."""
        execution = AgentExecution.objects.create(
            agent_type="auto_remediator",
            model=ai_model,
            input_hash=hashlib.sha256(b"remediation input").hexdigest(),
            input_summary={"action": "restart_service", "target": "app-server-1"},
            output={"script": "systemctl restart myapp"},
            risk_level="R3",
            approval_required=True,
            approval_status=AgentExecution.ApprovalStatus.PENDING,
            initiated_by=user,
        )

        # Approve the execution
        execution.approval_status = AgentExecution.ApprovalStatus.APPROVED
        execution.approved_by = user
        execution.approved_at = timezone.now()
        execution.save()

        execution.refresh_from_db()
        assert execution.approval_status == AgentExecution.ApprovalStatus.APPROVED
        assert execution.approved_by == user

    def test_execution_rejection(self, db, user, ai_model):
        """Test execution rejection."""
        execution = AgentExecution.objects.create(
            agent_type="remediation_advisor",
            model=ai_model,
            input_hash=hashlib.sha256(b"risky input").hexdigest(),
            input_summary={"action": "risky_operation"},
            output={"recommendation": "proceed with caution"},
            risk_level="R2",
            approval_required=True,
            approval_status=AgentExecution.ApprovalStatus.PENDING,
            initiated_by=user,
        )

        # Reject the execution
        execution.approval_status = AgentExecution.ApprovalStatus.REJECTED
        execution.approved_by = user
        execution.approved_at = timezone.now()
        execution.rejection_reason = "Too risky for production environment"
        execution.save()

        execution.refresh_from_db()
        assert execution.approval_status == AgentExecution.ApprovalStatus.REJECTED
        assert execution.rejection_reason != ""

    def test_execution_result_tracking(self, execution, user):
        """Test execution result tracking."""
        execution.executed = True
        execution.executed_at = timezone.now()
        execution.execution_result = {"status": "success", "affected_count": 5}
        execution.save()

        execution.refresh_from_db()
        assert execution.executed is True
        assert execution.execution_result["status"] == "success"

    def test_execution_error_tracking(self, execution):
        """Test execution error tracking."""
        execution.executed = True
        execution.executed_at = timezone.now()
        execution.execution_error = "Connection timeout to target system"
        execution.execution_result = {"status": "failed"}
        execution.save()

        execution.refresh_from_db()
        assert "timeout" in execution.execution_error.lower()

    def test_execution_input_hash_index(self, db, user, ai_model):
        """Test that input_hash can be used for deduplication."""
        input_data = b"same input data"
        input_hash = hashlib.sha256(input_data).hexdigest()

        # Create first execution
        AgentExecution.objects.create(
            agent_type="incident_classifier",
            input_hash=input_hash,
            input_summary={"data": "test"},
            output={},
            initiated_by=user,
        )

        # Create second with same hash
        AgentExecution.objects.create(
            agent_type="incident_classifier",
            input_hash=input_hash,
            input_summary={"data": "test"},
            output={},
            initiated_by=user,
        )

        # Can query by hash
        matching = AgentExecution.objects.filter(input_hash=input_hash)
        assert matching.count() == 2


class TestModelDriftMetric:
    """Tests for ModelDriftMetric."""

    @pytest.fixture
    def drift_metric(self, db, ai_model):
        """Create a test drift metric."""
        now = timezone.now()
        return ModelDriftMetric.objects.create(
            model=ai_model,
            metric_type=ModelDriftMetric.MetricType.ACCURACY,
            value=0.88,
            threshold=0.85,
            baseline_value=0.92,
            is_alert=False,
            window_start=now - timedelta(hours=1),
            window_end=now,
            sample_count=1000,
        )

    def test_create_drift_metric(self, drift_metric):
        """Test creating a drift metric."""
        assert drift_metric.id is not None
        assert drift_metric.value == 0.88
        assert drift_metric.is_alert is False

    def test_drift_alert_triggered(self, db, ai_model, user):
        """Test drift alert when value exceeds threshold."""
        now = timezone.now()
        metric = ModelDriftMetric.objects.create(
            model=ai_model,
            metric_type=ModelDriftMetric.MetricType.OVERRIDE_RATE,
            value=0.25,  # 25% override rate
            threshold=0.10,  # Alert if > 10%
            baseline_value=0.05,
            is_alert=True,  # Alert triggered
            window_start=now - timedelta(hours=1),
            window_end=now,
            sample_count=500,
        )

        assert metric.is_alert is True

    def test_alert_acknowledgement(self, drift_metric, user):
        """Test alert acknowledgement workflow."""
        drift_metric.is_alert = True
        drift_metric.save()

        drift_metric.alert_acknowledged = True
        drift_metric.alert_acknowledged_by = user
        drift_metric.alert_acknowledged_at = timezone.now()
        drift_metric.save()

        drift_metric.refresh_from_db()
        assert drift_metric.alert_acknowledged is True
        assert drift_metric.alert_acknowledged_by == user

    def test_metric_types(self, db, ai_model):
        """Test all metric types can be created."""
        now = timezone.now()
        metric_types = [
            ModelDriftMetric.MetricType.ACCURACY,
            ModelDriftMetric.MetricType.CONFIDENCE_MEAN,
            ModelDriftMetric.MetricType.CONFIDENCE_STD,
            ModelDriftMetric.MetricType.OVERRIDE_RATE,
            ModelDriftMetric.MetricType.LATENCY_P50,
            ModelDriftMetric.MetricType.LATENCY_P95,
            ModelDriftMetric.MetricType.ERROR_RATE,
            ModelDriftMetric.MetricType.INPUT_DRIFT,
            ModelDriftMetric.MetricType.OUTPUT_DRIFT,
        ]

        for metric_type in metric_types:
            metric = ModelDriftMetric.objects.create(
                model=ai_model,
                metric_type=metric_type,
                value=0.5,
                threshold=0.8,
                window_start=now - timedelta(hours=1),
                window_end=now,
                sample_count=100,
            )
            assert metric.metric_type == metric_type

    def test_drift_metric_str(self, drift_metric):
        """Test drift metric string representation."""
        result = str(drift_metric)
        assert "incident-classifier-v1" in result
        assert "accuracy" in result.lower()

    def test_drift_metric_with_alert_str(self, db, ai_model):
        """Test drift metric string with alert."""
        now = timezone.now()
        metric = ModelDriftMetric.objects.create(
            model=ai_model,
            metric_type=ModelDriftMetric.MetricType.ERROR_RATE,
            value=0.15,
            threshold=0.05,
            is_alert=True,
            window_start=now - timedelta(hours=1),
            window_end=now,
            sample_count=100,
        )
        result = str(metric)
        assert "[ALERT]" in result


class TestP7ModelsIntegration:
    """Integration tests for P7 models working together."""

    def test_full_agent_execution_lifecycle(self, db, user):
        """Test complete agent execution lifecycle."""
        # 1. Create model
        model = AIModel.objects.create(
            model_id="remediation-advisor-v1",
            model_type="recommendation",
            version="1.0.0",
            display_name="Remediation Advisor",
            status=AIModel.ModelStatus.DEPLOYED,
            risk_level=AIModel.RiskLevel.R2_MEDIUM,
            created_by=user,
            deployed_at=timezone.now(),
            deployed_by=user,
        )

        # 2. Create execution requiring approval
        execution = AgentExecution.objects.create(
            agent_type="remediation_advisor",
            model=model,
            input_hash=hashlib.sha256(b"incident-123").hexdigest(),
            input_summary={"incident_id": "INC-123", "type": "service_down"},
            output={"recommendation": "restart_service", "confidence": 0.92},
            confidence=0.92,
            latency_ms=200.0,
            risk_level="R2",
            approval_required=True,
            approval_status=AgentExecution.ApprovalStatus.PENDING,
            initiated_by=user,
        )

        # 3. Approve execution
        execution.approval_status = AgentExecution.ApprovalStatus.APPROVED
        execution.approved_by = user
        execution.approved_at = timezone.now()
        execution.save()

        # 4. Execute and record result
        execution.executed = True
        execution.executed_at = timezone.now()
        execution.execution_result = {"status": "success", "service_restarted": True}
        execution.save()

        # 5. Record drift metric (confidence slightly below baseline)
        now = timezone.now()
        ModelDriftMetric.objects.create(
            model=model,
            metric_type=ModelDriftMetric.MetricType.CONFIDENCE_MEAN,
            value=0.88,
            threshold=0.80,
            baseline_value=0.92,
            is_alert=False,  # Within threshold
            window_start=now - timedelta(hours=24),
            window_end=now,
            sample_count=100,
        )

        # Verify complete lifecycle
        execution.refresh_from_db()
        assert execution.approval_status == AgentExecution.ApprovalStatus.APPROVED
        assert execution.executed is True
        assert execution.execution_result["status"] == "success"
        assert model.drift_metrics.count() == 1

    def test_model_deprecation_affects_executions(self, db, user, ai_model):
        """Test that deprecated models can still be referenced by executions."""
        # Create execution with deployed model
        execution = AgentExecution.objects.create(
            agent_type="incident_classifier",
            model=ai_model,
            input_hash=hashlib.sha256(b"test").hexdigest(),
            input_summary={"test": True},
            output={"result": "P2"},
            initiated_by=user,
        )

        # Deprecate the model
        ai_model.status = AIModel.ModelStatus.DEPRECATED
        ai_model.save()

        # Execution should still reference the model
        execution.refresh_from_db()
        assert execution.model == ai_model
        assert execution.model.status == AIModel.ModelStatus.DEPRECATED
