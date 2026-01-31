# Django Patterns Reference

Complete Django development patterns for EUCORA backend.

---

## Model Layer

### Abstract Base Models

Located in `backend/apps/core/models.py`:

```python
from django.db import models
from django.utils import timezone
import uuid

class TimeStampedModel(models.Model):
    """Abstract model with automatic timestamps."""

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CorrelationIdModel(models.Model):
    """Abstract model with correlation ID for audit trail."""

    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Unique correlation ID for audit trail",
    )

    class Meta:
        abstract = True


class DemoQuerySet(models.QuerySet):
    """QuerySet with demo/production filtering."""

    def demo(self) -> "DemoQuerySet":
        return self.filter(is_demo=True)

    def production(self) -> "DemoQuerySet":
        return self.filter(is_demo=False)
```

### Model Implementation Pattern

```python
from django.db import models
from apps.core.models import TimeStampedModel, CorrelationIdModel, DemoQuerySet

class Deployment(TimeStampedModel, CorrelationIdModel):
    """Deployment intent with audit trail and ring-based rollout."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        ROLLED_BACK = "rolled_back", "Rolled Back"

    class Ring(models.IntegerChoices):
        LAB = 0, "Ring 0 - Lab"
        CANARY = 1, "Ring 1 - Canary"
        PILOT = 2, "Ring 2 - Pilot"
        DEPARTMENT = 3, "Ring 3 - Department"
        GLOBAL = 4, "Ring 4 - Global"

    # Core fields
    name = models.CharField(max_length=255)
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.PROTECT,
        related_name="deployments",
    )
    version = models.CharField(max_length=64)

    # Status tracking
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    target_ring = models.IntegerField(
        choices=Ring.choices,
        default=Ring.LAB,
    )

    # Risk assessment
    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
    )

    # Approval tracking
    approved_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_deployments",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Demo data flag
    is_demo = models.BooleanField(default=False, db_index=True)

    # Custom manager with demo filtering
    objects = DemoQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["application", "version"]),
            models.Index(
                fields=["risk_score"],
                condition=models.Q(status="pending"),
                name="pending_risk_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(risk_score__gte=0) & models.Q(risk_score__lte=100),
                name="valid_risk_score_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.application.name} v{self.version} ({self.status})"

    @property
    def requires_cab_approval(self) -> bool:
        """
        Check if deployment requires CAB approval.

        Per CLAUDE.md governance model:
        - CAB approval required for Risk > 50 when targeting Ring 2+ (Pilot or higher)
        - Ring 1 (Canary) deployments bypass CAB even for high-risk artifacts
        - Low-risk deployments (Risk <= 50) never require CAB approval
        """
        return self.risk_score > 50 and self.target_ring >= self.Ring.PILOT
```

---

## Serializer Layer

### Multiple Serializers Pattern

```python
from rest_framework import serializers
from .models import Deployment

class DeploymentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    application_name = serializers.CharField(source="application.name", read_only=True)

    class Meta:
        model = Deployment
        fields = [
            "id",
            "correlation_id",
            "name",
            "application_name",
            "version",
            "status",
            "risk_score",
            "target_ring",
            "created_at",
        ]


class DeploymentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""

    application = ApplicationSerializer(read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)
    requires_cab = serializers.BooleanField(source="requires_cab_approval", read_only=True)

    class Meta:
        model = Deployment
        fields = [
            "id",
            "correlation_id",
            "name",
            "application",
            "version",
            "status",
            "risk_score",
            "target_ring",
            "requires_cab",
            "approved_by_name",
            "approved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class DeploymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating deployments."""

    application_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Deployment
        fields = [
            "name",
            "application_id",
            "version",
            "target_ring",
        ]

    def validate_version(self, value: str) -> str:
        """Validate semantic version format."""
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", value):
            raise serializers.ValidationError("Version must be semantic (X.Y.Z)")
        return value

    def create(self, validated_data: dict) -> Deployment:
        """Create deployment with risk scoring."""
        from apps.policy_engine.services import calculate_risk_score

        application_id = validated_data.pop("application_id")
        application = Application.objects.get(id=application_id)

        deployment = Deployment(
            application=application,
            **validated_data,
        )

        # Calculate risk score
        deployment.risk_score = calculate_risk_score(deployment)
        deployment.save()

        return deployment
```

---

## View Layer

### ViewSet Pattern

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from apps.core.utils import apply_demo_filter
from .models import Deployment
from .serializers import (
    DeploymentListSerializer,
    DeploymentDetailSerializer,
    DeploymentCreateSerializer,
)

class DeploymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Deployment CRUD and actions."""

    queryset = Deployment.objects.select_related("application", "approved_by")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return serializer based on action."""
        if self.action == "list":
            return DeploymentListSerializer
        if self.action == "create":
            return DeploymentCreateSerializer
        return DeploymentDetailSerializer

    def get_queryset(self):
        """Filter queryset by demo mode and query params."""
        qs = super().get_queryset()

        # Apply demo filter
        qs = apply_demo_filter(qs, self.request)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by application
        app_id = self.request.query_params.get("application")
        if app_id:
            qs = qs.filter(application_id=app_id)

        # Filter by ring
        ring = self.request.query_params.get("ring")
        if ring:
            qs = qs.filter(target_ring=ring)

        return qs

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def approve(self, request, pk=None):
        """Approve a pending deployment."""
        deployment = self.get_object()

        if deployment.status != Deployment.Status.PENDING:
            return Response(
                {"error": "Only pending deployments can be approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = Deployment.Status.APPROVED
        deployment.approved_by = request.user
        deployment.approved_at = timezone.now()
        deployment.save()

        # Log audit event
        AuditLog.objects.create(
            action="deployment.approved",
            target_id=deployment.id,
            user=request.user,
            correlation_id=deployment.correlation_id,
        )

        return Response(DeploymentDetailSerializer(deployment).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reject(self, request, pk=None):
        """Reject a pending deployment."""
        deployment = self.get_object()
        reason = request.data.get("reason", "")

        if deployment.status != Deployment.Status.PENDING:
            return Response(
                {"error": "Only pending deployments can be rejected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = Deployment.Status.REJECTED
        deployment.rejection_reason = reason
        deployment.save()

        return Response(DeploymentDetailSerializer(deployment).data)
```

### Function-Based Views

```python
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.core.decorators import exempt_csrf_in_debug
from apps.core.throttling import StrictRateThrottle
from apps.core.utils import apply_demo_filter

@exempt_csrf_in_debug
@api_view(["POST"])
@throttle_classes([StrictRateThrottle])
@permission_classes([IsAuthenticated])
@transaction.atomic
def approve_deployment(request, correlation_id: str) -> Response:
    """
    Approve a deployment by correlation ID.

    POST /api/v1/deployments/{correlation_id}/approve/
    """
    deployment = get_object_or_404(
        apply_demo_filter(Deployment.objects.all(), request),
        correlation_id=correlation_id,
    )

    if deployment.status != Deployment.Status.PENDING:
        return Response(
            {"error": "Only pending deployments can be approved"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check CAB approval requirement
    if deployment.requires_cab_approval:
        cab_approval = CABApproval.objects.filter(
            deployment=deployment,
            status=CABApproval.Status.APPROVED,
        ).first()

        if not cab_approval:
            return Response(
                {"error": "CAB approval required for this deployment"},
                status=status.HTTP_403_FORBIDDEN,
            )

    deployment.status = Deployment.Status.APPROVED
    deployment.approved_by = request.user
    deployment.approved_at = timezone.now()
    deployment.save()

    # Use correlation ID from middleware
    logger = request.logger
    logger.info(f"Deployment approved: {deployment.name}")

    return Response(DeploymentDetailSerializer(deployment).data)
```

---

## URL Configuration

### Router-Based URLs

```python
# apps/deployments/urls.py
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"deployments", views.DeploymentViewSet, basename="deployment")

urlpatterns = router.urls
```

### Mixed URL Patterns

```python
# apps/cab_workflow/urls.py
from django.urls import path
from . import views

app_name = "cab_workflow"

urlpatterns = [
    # Function-based views
    path("pending/", views.list_pending_approvals, name="pending"),
    path("approvals/", views.list_approvals, name="list"),
    path("<uuid:correlation_id>/approve/", views.approve_deployment, name="approve"),
    path("<uuid:correlation_id>/reject/", views.reject_deployment, name="reject"),
]
```

### Main URL Configuration

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    # API v1
    path("api/v1/", include([
        path("deployments/", include("apps.deployments.urls")),
        path("cab/", include("apps.cab_workflow.urls", namespace="cab")),
        path("applications/", include("apps.applications.urls")),
        path("knowledge/", include("apps.knowledge.urls")),
    ])),

    # Admin
    path("admin/", admin.site.urls),
]
```

---

## Middleware

### Correlation ID Middleware

```python
# apps/core/middleware.py
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

class CorrelationIdMiddleware(MiddlewareMixin):
    """Inject correlation ID into request for audit trail."""

    HEADER_NAME = "X-Correlation-ID"

    def process_request(self, request):
        # Extract from header or generate new
        correlation_id = request.headers.get(self.HEADER_NAME)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.correlation_id = correlation_id

        # Create logger adapter with correlation context
        request.logger = logging.LoggerAdapter(
            logging.getLogger("apps"),
            {"correlation_id": correlation_id},
        )

    def process_response(self, request, response):
        # Add correlation ID to response headers
        if hasattr(request, "correlation_id"):
            response[self.HEADER_NAME] = request.correlation_id
        return response
```

---

## Demo Data Filtering

### Utility Function

```python
# apps/core/utils.py
from django.db.models import QuerySet
from django.http import HttpRequest

def apply_demo_filter(queryset: QuerySet, request: HttpRequest) -> QuerySet:
    """
    Filter queryset based on demo mode.

    Checks:
    1. X-Demo-Mode header
    2. ?demo=true query parameter
    3. Session demo mode
    """
    # Check header
    demo_mode = request.headers.get("X-Demo-Mode", "").lower() == "true"

    # Check query param
    if not demo_mode:
        demo_mode = request.GET.get("demo", "").lower() == "true"

    # Check session
    if not demo_mode:
        demo_mode = request.session.get("demo_mode", False)

    if demo_mode:
        return queryset.filter(is_demo=True)

    return queryset.filter(is_demo=False)
```

---

## Admin Configuration

```python
# apps/deployments/admin.py
from django.contrib import admin
from .models import Deployment

@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "application",
        "version",
        "status",
        "risk_score",
        "target_ring",
        "created_at",
    ]
    list_filter = ["status", "target_ring", "is_demo"]
    search_fields = ["name", "application__name", "correlation_id"]
    readonly_fields = ["correlation_id", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("application")
```

---

## Celery Tasks

```python
# apps/deployments/tasks.py
from celery import shared_task
from django.utils import timezone

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_deployment(self, deployment_id: str, correlation_id: str):
    """
    Process approved deployment through ring rollout.

    Retries on transient failures with exponential backoff.
    """
    from .models import Deployment
    from apps.connectors.services import publish_to_execution_plane

    try:
        deployment = Deployment.objects.get(id=deployment_id)

        # Update status
        deployment.status = Deployment.Status.IN_PROGRESS
        deployment.save()

        # Publish to execution plane
        result = publish_to_execution_plane(deployment, correlation_id)

        if result.success:
            deployment.status = Deployment.Status.COMPLETED
        else:
            deployment.status = Deployment.Status.FAILED
            deployment.failure_reason = result.error

        deployment.save()

    except TransientError as e:
        # Retry on transient errors
        raise self.retry(exc=e)

    except Exception as e:
        deployment.status = Deployment.Status.FAILED
        deployment.failure_reason = str(e)
        deployment.save()
        raise
```
