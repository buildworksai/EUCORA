# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
P5.3: Serializers for CAB Workflow REST API.
Handles request/response serialization for CAB approval workflows.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal

from .models import CABApprovalRequest, CABException, CABApprovalDecision


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serialization for approvers."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']


class CABApprovalRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing CAB approval requests."""
    
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CABApprovalRequest
        fields = [
            'id',
            'correlation_id',
            'deployment_intent_id',
            'risk_score',
            'status',
            'status_display',
            'submitted_by_username',
            'submitted_at',
            'approved_by_username',
            'approval_decision',
            'approved_at',
        ]
        read_only_fields = [
            'id',
            'correlation_id',
            'submitted_by_username',
            'approved_by_username',
            'submitted_at',
            'approved_at',
        ]
    
    def get_status_display(self, obj):
        """Return human-readable status."""
        status_map = {
            'submitted': 'Pending Review',
            'auto_approved': 'Auto-Approved',
            'under_review': 'Under CAB Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'conditional': 'Conditionally Approved',
            'exception_required': 'Exception Required',
        }
        return status_map.get(obj.status, obj.status)


class CABApprovalRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed CAB approval request view."""
    
    submitted_by = UserBasicSerializer(read_only=True)
    approved_by = UserBasicSerializer(read_only=True, allow_null=True)
    status_display = serializers.SerializerMethodField()
    risk_tier = serializers.SerializerMethodField()
    
    class Meta:
        model = CABApprovalRequest
        fields = [
            'id',
            'correlation_id',
            'deployment_intent_id',
            'evidence_package_id',
            'risk_score',
            'risk_tier',
            'status',
            'status_display',
            'submitted_by',
            'submitted_at',
            'approved_by',
            'approval_decision',
            'approval_rationale',
            'approval_conditions',
            'approved_at',
            'notes',
        ]
        read_only_fields = [
            'id',
            'correlation_id',
            'submitted_by',
            'submitted_at',
            'approved_by',
            'approved_at',
        ]
    
    def get_status_display(self, obj):
        """Return human-readable status."""
        status_map = {
            'submitted': 'Pending Review',
            'auto_approved': 'Auto-Approved',
            'under_review': 'Under CAB Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'conditional': 'Conditionally Approved',
            'exception_required': 'Exception Required',
        }
        return status_map.get(obj.status, obj.status)
    
    def get_risk_tier(self, obj):
        """Return risk tier based on score."""
        score = float(obj.risk_score)
        if score <= 50:
            return {'tier': 'LOW', 'description': 'Auto-Approved', 'requires_cab': False}
        elif score <= 75:
            return {'tier': 'MEDIUM', 'description': 'Manual CAB Review', 'requires_cab': True}
        else:
            return {'tier': 'HIGH', 'description': 'Exception Required', 'requires_exception': True}


class CABApprovalSubmitSerializer(serializers.Serializer):
    """Serializer for submitting CAB approval request."""
    
    evidence_package_id = serializers.CharField(
        max_length=255,
        help_text="ID of evidence package to submit"
    )
    risk_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        help_text="Risk score 0-100"
    )
    notes = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="Optional submission notes"
    )
    
    def validate_risk_score(self, value):
        """Validate risk score is in valid range."""
        if not (Decimal('0') <= value <= Decimal('100')):
            raise serializers.ValidationError("Risk score must be between 0 and 100")
        return value


class CABApprovalDecisionSerializer(serializers.ModelSerializer):
    """Serializer for CAB approval decisions."""
    
    decided_by_username = serializers.CharField(source='decided_by.username', read_only=True)
    decision_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CABApprovalDecision
        fields = [
            'id',
            'cab_request_id',
            'correlation_id',
            'decision',
            'decision_display',
            'rationale',
            'decided_by_username',
            'decided_at',
            'conditions',
        ]
        read_only_fields = [
            'id',
            'cab_request_id',
            'correlation_id',
            'decided_by_username',
            'decided_at',
        ]
    
    def get_decision_display(self, obj):
        """Return human-readable decision."""
        decision_map = {
            'approved': 'Approved',
            'rejected': 'Rejected',
            'conditional': 'Conditionally Approved',
        }
        return decision_map.get(obj.decision, obj.decision)


class CABApprovalActionSerializer(serializers.Serializer):
    """Serializer for CAB approval/rejection actions."""
    
    rationale = serializers.CharField(
        max_length=2000,
        help_text="Approval or rejection rationale"
    )
    conditions = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Optional conditions if conditionally approved (JSON object)"
    )
    
    def validate_conditions(self, value):
        """Validate conditions is a dict if provided."""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Conditions must be a JSON object")
        return value or {}


class CABExceptionListSerializer(serializers.ModelSerializer):
    """Serializer for listing CAB exceptions."""
    
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    status_display = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CABException
        fields = [
            'id',
            'correlation_id',
            'deployment_intent_id',
            'reason',
            'status',
            'status_display',
            'requested_by_username',
            'requested_at',
            'approved_by_username',
            'approved_at',
            'expires_at',
            'is_active',
            'is_expired',
        ]
        read_only_fields = [
            'id',
            'correlation_id',
            'requested_by_username',
            'requested_at',
            'approved_by_username',
            'approved_at',
            'is_active',
            'is_expired',
        ]
    
    def get_status_display(self, obj):
        """Return human-readable status."""
        status_map = {
            'pending': 'Pending Security Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'expired': 'Expired',
        }
        return status_map.get(obj.status, obj.status)


class CABExceptionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed CAB exception view."""
    
    requested_by = UserBasicSerializer(read_only=True)
    approved_by = UserBasicSerializer(read_only=True, allow_null=True)
    status_display = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CABException
        fields = [
            'id',
            'correlation_id',
            'deployment_intent_id',
            'reason',
            'risk_justification',
            'compensating_controls',
            'requested_by',
            'requested_at',
            'approval_decision',
            'approved_by',
            'approval_rationale',
            'approved_at',
            'expires_at',
            'status',
            'status_display',
            'is_active',
            'is_expired',
        ]
        read_only_fields = [
            'id',
            'correlation_id',
            'requested_by',
            'requested_at',
            'approved_by',
            'approved_at',
            'is_active',
            'is_expired',
        ]
    
    def get_status_display(self, obj):
        """Return human-readable status."""
        status_map = {
            'pending': 'Pending Security Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'expired': 'Expired',
        }
        return status_map.get(obj.status, obj.status)


class CABExceptionCreateSerializer(serializers.Serializer):
    """Serializer for creating CAB exceptions."""
    
    deployment_intent_id = serializers.CharField(
        max_length=255,
        help_text="Deployment intent ID for exception"
    )
    reason = serializers.CharField(
        max_length=2000,
        help_text="Why exception is needed"
    )
    risk_justification = serializers.CharField(
        max_length=2000,
        help_text="Why risk is acceptable despite threshold"
    )
    compensating_controls = serializers.ListField(
        child=serializers.CharField(max_length=500),
        help_text="List of compensating controls"
    )
    expiry_days = serializers.IntegerField(
        default=30,
        min_value=1,
        max_value=90,
        help_text="Days until exception expires (1-90)"
    )
    
    def validate_compensating_controls(self, value):
        """Validate at least one compensating control."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one compensating control is required")
        return value


class CABExceptionApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting CAB exceptions."""
    
    rationale = serializers.CharField(
        max_length=2000,
        help_text="Approval or rejection rationale"
    )
