#!/usr/bin/env python
"""Quick test script to create deployments and record metrics."""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import uuid

from django.contrib.auth.models import User

from apps.core.metrics import record_deployment
from apps.deployment_intents.models import DeploymentIntent

# Get or create test user
user, _ = User.objects.get_or_create(username="testuser", defaults={"is_staff": True, "is_superuser": True})

# Create multiple deployments to test metrics recording
print("Creating test deployments and recording metrics...")
for i in range(3):
    deployment = DeploymentIntent.objects.create(
        app_name=f"TestApp{i}",
        version="1.0.0",
        target_ring="LAB",
        evidence_pack_id=uuid.uuid4(),
        submitter=user,
        requires_cab_approval=False,
        status="COMPLETED",
        risk_score=25,
    )

    # Record metrics
    record_deployment(status="COMPLETED", ring="LAB", app_name=f"TestApp{i}", requires_cab=False, duration=float(i + 1))

    print(f"✓ Created deployment {i+1}: {deployment.app_name}")

print("\n✓ All test deployments created and metrics recorded")
print("Wait 30 seconds for Prometheus to scrape metrics, then check:")
print("  - Metrics endpoint: http://localhost:8000/api/v1/metrics/")
print("  - Prometheus: http://localhost:9090/api/v1/query?query=deployment_total")
print("  - Grafana: http://localhost:3000")
