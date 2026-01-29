# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for Application Portfolio models.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.application_portfolio.models import (
    Application,
    ApplicationDependency,
    ApplicationHealth,
    ApplicationStatus,
    ApplicationVersion,
    ArtifactStatus,
    ComplianceStatus,
    DeploymentIntent,
    DeploymentMetric,
    DeploymentStatus,
    HealthStatus,
    PackageArtifact,
    PackageType,
    PlatformType,
    Publisher,
    RingLevel,
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def publisher(db):
    """Create a test publisher."""
    return Publisher.objects.create(
        name="Test Publisher",
        identifier="com.testpublisher",
        website="https://testpublisher.com",
        is_verified=True,
        trust_score=Decimal("0.85"),
    )


@pytest.fixture
def application(db, publisher, user):
    """Create a test application."""
    return Application.objects.create(
        name="Test Application",
        identifier="com.testpublisher.testapp",
        publisher=publisher,
        description="A test application",
        category="Productivity",
        tags=["test", "productivity"],
        owner=user,
        status=ApplicationStatus.PUBLISHED,
        supported_platforms=[PlatformType.WINDOWS, PlatformType.MACOS],
        risk_score=35,
    )


@pytest.fixture
def version(db, application):
    """Create a test application version."""
    return ApplicationVersion.objects.create(
        application=application,
        version="1.0.0",
        version_code=100,
        release_notes="Initial release",
        is_latest=True,
    )


@pytest.fixture
def artifact(db, version, user):
    """Create a test package artifact."""
    return PackageArtifact.objects.create(
        version=version,
        platform=PlatformType.WINDOWS,
        architecture="x64",
        package_type=PackageType.INTUNEWIN,
        file_name="testapp-1.0.0.intunewin",
        file_size=10485760,
        file_hash_sha256="a" * 64,
        storage_ref="artifacts/testapp/1.0.0/testapp-1.0.0.intunewin",
        is_signed=True,
        signature_type="authenticode",
        status=ArtifactStatus.READY,
        uploaded_by=user,
    )


@pytest.fixture
def deployment(db, artifact, user):
    """Create a test deployment intent."""
    return DeploymentIntent.objects.create(
        artifact=artifact,
        target_ring=RingLevel.RING_1,
        target_scope={"groups": ["pilot-users"]},
        target_device_count=100,
        status=DeploymentStatus.DRAFT,
        risk_score=35,
        created_by=user,
    )


# =============================================================================
# PUBLISHER TESTS
# =============================================================================


@pytest.mark.django_db
class TestPublisher:
    """Tests for Publisher model."""

    def test_create_publisher(self, publisher):
        """Test publisher creation."""
        assert publisher.name == "Test Publisher"
        assert publisher.identifier == "com.testpublisher"
        assert publisher.is_verified is True
        assert publisher.trust_score == Decimal("0.85")
        assert publisher.is_active is True

    def test_publisher_str(self, publisher):
        """Test publisher string representation."""
        assert str(publisher) == "Test Publisher"

    def test_publisher_unique_identifier(self, db, publisher):
        """Test publisher identifier uniqueness."""
        with pytest.raises(IntegrityError):
            Publisher.objects.create(
                name="Another Publisher",
                identifier="com.testpublisher",  # Duplicate
            )


# =============================================================================
# APPLICATION TESTS
# =============================================================================


@pytest.mark.django_db
class TestApplication:
    """Tests for Application model."""

    def test_create_application(self, application, publisher):
        """Test application creation."""
        assert application.name == "Test Application"
        assert application.identifier == "com.testpublisher.testapp"
        assert application.publisher == publisher
        assert application.status == ApplicationStatus.PUBLISHED
        assert application.risk_score == 35
        assert PlatformType.WINDOWS in application.supported_platforms

    def test_application_str(self, application):
        """Test application string representation."""
        assert str(application) == "Test Application (com.testpublisher.testapp)"

    def test_application_unique_identifier(self, db, application, publisher):
        """Test application identifier uniqueness."""
        with pytest.raises(IntegrityError):
            Application.objects.create(
                name="Another App",
                identifier="com.testpublisher.testapp",  # Duplicate
                publisher=publisher,
            )

    def test_latest_version_property(self, application, version):
        """Test latest_version property."""
        assert application.latest_version == version

    def test_platform_count_property(self, application):
        """Test platform_count property."""
        assert application.platform_count == 2


# =============================================================================
# VERSION TESTS
# =============================================================================


@pytest.mark.django_db
class TestApplicationVersion:
    """Tests for ApplicationVersion model."""

    def test_create_version(self, version, application):
        """Test version creation."""
        assert version.version == "1.0.0"
        assert version.version_code == 100
        assert version.application == application
        assert version.is_latest is True

    def test_version_str(self, version):
        """Test version string representation."""
        assert str(version) == "Test Application v1.0.0"

    def test_version_uniqueness(self, db, application, version):
        """Test version uniqueness per application."""
        with pytest.raises(IntegrityError):
            ApplicationVersion.objects.create(
                application=application,
                version="1.0.0",  # Duplicate
            )

    def test_only_one_latest_version(self, db, application, version):
        """Test that only one version can be latest."""
        # Create a new version marked as latest
        new_version = ApplicationVersion.objects.create(
            application=application,
            version="2.0.0",
            is_latest=True,
        )

        # Refresh from database
        version.refresh_from_db()

        # Old version should no longer be latest
        assert version.is_latest is False
        assert new_version.is_latest is True


# =============================================================================
# ARTIFACT TESTS
# =============================================================================


@pytest.mark.django_db
class TestPackageArtifact:
    """Tests for PackageArtifact model."""

    def test_create_artifact(self, artifact, version):
        """Test artifact creation."""
        assert artifact.version == version
        assert artifact.platform == PlatformType.WINDOWS
        assert artifact.package_type == PackageType.INTUNEWIN
        assert artifact.status == ArtifactStatus.READY
        assert artifact.is_signed is True

    def test_artifact_str(self, artifact):
        """Test artifact string representation."""
        assert "Test Application v1.0.0" in str(artifact)
        assert "windows" in str(artifact)

    def test_has_vulnerabilities_property(self, artifact):
        """Test has_vulnerabilities property."""
        assert artifact.has_vulnerabilities is False

        artifact.vulnerability_count_critical = 1
        artifact.save()
        assert artifact.has_vulnerabilities is True

    def test_total_vulnerabilities_property(self, artifact):
        """Test total_vulnerabilities property."""
        artifact.vulnerability_count_critical = 1
        artifact.vulnerability_count_high = 2
        artifact.vulnerability_count_medium = 5
        artifact.vulnerability_count_low = 10
        artifact.save()

        assert artifact.total_vulnerabilities == 18


# =============================================================================
# DEPLOYMENT TESTS
# =============================================================================


@pytest.mark.django_db
class TestDeploymentIntent:
    """Tests for DeploymentIntent model."""

    def test_create_deployment(self, deployment, artifact):
        """Test deployment creation."""
        assert deployment.artifact == artifact
        assert deployment.target_ring == RingLevel.RING_1
        assert deployment.status == DeploymentStatus.DRAFT
        assert deployment.risk_score == 35
        assert deployment.target_device_count == 100

    def test_deployment_str(self, deployment):
        """Test deployment string representation."""
        assert "ring_1" in str(deployment)
        assert "draft" in str(deployment)

    def test_deployment_scope(self, deployment):
        """Test deployment target scope."""
        assert "groups" in deployment.target_scope
        assert "pilot-users" in deployment.target_scope["groups"]


# =============================================================================
# METRIC TESTS
# =============================================================================


@pytest.mark.django_db
class TestDeploymentMetric:
    """Tests for DeploymentMetric model."""

    def test_create_metric(self, db, deployment):
        """Test metric creation."""
        metric = DeploymentMetric.objects.create(
            deployment=deployment,
            devices_targeted=100,
            devices_succeeded=95,
            devices_failed=5,
            success_rate=Decimal("95.00"),
        )

        assert metric.deployment == deployment
        assert metric.devices_targeted == 100
        assert metric.success_rate == Decimal("95.00")

    def test_metric_str(self, db, deployment):
        """Test metric string representation."""
        metric = DeploymentMetric.objects.create(
            deployment=deployment,
            devices_targeted=100,
        )
        assert "metrics" in str(metric)


# =============================================================================
# HEALTH TESTS
# =============================================================================


@pytest.mark.django_db
class TestApplicationHealth:
    """Tests for ApplicationHealth model."""

    def test_create_health(self, db, application):
        """Test health snapshot creation."""
        health = ApplicationHealth.objects.create(
            application=application,
            health_status=HealthStatus.HEALTHY,
            total_installations=1000,
            healthy_installations=950,
            unhealthy_installations=50,
            compliance_status=ComplianceStatus.COMPLIANT,
            compliance_score=Decimal("95.00"),
        )

        assert health.application == application
        assert health.health_status == HealthStatus.HEALTHY
        assert health.compliance_status == ComplianceStatus.COMPLIANT

    def test_health_str(self, db, application):
        """Test health string representation."""
        health = ApplicationHealth.objects.create(
            application=application,
            health_status=HealthStatus.HEALTHY,
        )
        assert application.name in str(health)
        assert "health" in str(health)


# =============================================================================
# DEPENDENCY TESTS
# =============================================================================


@pytest.mark.django_db
class TestApplicationDependency:
    """Tests for ApplicationDependency model."""

    def test_create_dependency(self, db, publisher, user):
        """Test dependency creation."""
        app1 = Application.objects.create(
            name="App One",
            identifier="com.test.app1",
            publisher=publisher,
        )
        app2 = Application.objects.create(
            name="App Two",
            identifier="com.test.app2",
            publisher=publisher,
        )

        dep = ApplicationDependency.objects.create(
            application=app1,
            depends_on=app2,
            dependency_type="runtime",
            min_version="1.0.0",
            is_required=True,
        )

        assert dep.application == app1
        assert dep.depends_on == app2
        assert dep.is_required is True

    def test_dependency_str(self, db, publisher):
        """Test dependency string representation."""
        app1 = Application.objects.create(
            name="App One",
            identifier="com.test.appone",
            publisher=publisher,
        )
        app2 = Application.objects.create(
            name="App Two",
            identifier="com.test.apptwo",
            publisher=publisher,
        )

        dep = ApplicationDependency.objects.create(
            application=app1,
            depends_on=app2,
        )
        assert "App One" in str(dep)
        assert "App Two" in str(dep)

    def test_dependency_uniqueness(self, db, publisher):
        """Test dependency uniqueness."""
        app1 = Application.objects.create(
            name="App A",
            identifier="com.test.appa",
            publisher=publisher,
        )
        app2 = Application.objects.create(
            name="App B",
            identifier="com.test.appb",
            publisher=publisher,
        )

        ApplicationDependency.objects.create(
            application=app1,
            depends_on=app2,
        )

        with pytest.raises(IntegrityError):
            ApplicationDependency.objects.create(
                application=app1,
                depends_on=app2,  # Duplicate
            )
