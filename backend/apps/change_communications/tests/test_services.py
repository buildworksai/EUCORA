# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for Change Communications.
"""
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.change_communications.models import ChangeRecord, CommunicationTemplate
from apps.change_communications.services.template_renderer import RenderedTemplate, TemplateRenderer


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass", email="test@example.com")


@pytest.fixture
def change_record(db, user):
    """Create a test change record."""
    return ChangeRecord.objects.create(
        servicenow_number="CHG0012345",
        servicenow_sys_id="abc123",
        change_type="normal",
        short_description="Update Microsoft Office",
        description="Deploy Office 365 update to all workstations",
        risk_level="low",
        impact="low",
        planned_start=timezone.now(),
        planned_end=timezone.now() + timedelta(hours=4),
        requested_by=user,
    )


@pytest.fixture
def template(db):
    """Create a test template."""
    return CommunicationTemplate.objects.create(
        name="Deployment Scheduled",
        event_type="scheduled",
        channel="email",
        subject_template="[EUCORA] Change ${change_number} Scheduled: ${short_description}",
        body_template="""
A change has been scheduled.

**Change Details:**
- Change Number: ${change_number}
- Description: ${short_description}
- Risk Level: ${risk_level}
- Planned Start: ${planned_start}
- Planned End: ${planned_end}

Contact: ${contact_email|support@example.com}
""",
    )


class TestTemplateRenderer:
    """Tests for TemplateRenderer."""

    def test_build_context(self, change_record):
        """Test building context from change record."""
        renderer = TemplateRenderer()
        context = renderer.build_context(change_record)

        assert context["change_number"] == "CHG0012345"
        assert context["short_description"] == "Update Microsoft Office"
        assert context["risk_level"] == "low"
        assert "planned_start" in context

    def test_render_template(self, template, change_record):
        """Test rendering a template."""
        renderer = TemplateRenderer()
        context = renderer.build_context(change_record)
        rendered = renderer.render(template, context)

        assert isinstance(rendered, RenderedTemplate)
        assert "CHG0012345" in rendered.subject
        assert "Update Microsoft Office" in rendered.subject
        assert "CHG0012345" in rendered.body
        assert "low" in rendered.body

    def test_default_values(self, db, change_record):
        """Test default value substitution."""
        template = CommunicationTemplate.objects.create(
            name="Test Default",
            event_type="scheduled",
            channel="email",
            subject_template="Test ${missing_var|DEFAULT}",
            body_template="Value: ${another_missing|fallback}",
        )

        renderer = TemplateRenderer()
        context = renderer.build_context(change_record)
        rendered = renderer.render(template, context)

        assert "DEFAULT" in rendered.subject
        assert "fallback" in rendered.body

    def test_missing_variable_no_default(self, db, change_record):
        """Test missing variable without default."""
        template = CommunicationTemplate.objects.create(
            name="Test Missing",
            event_type="scheduled",
            channel="email",
            subject_template="Test ${nonexistent}",
            body_template="Body",
        )

        renderer = TemplateRenderer()
        context = renderer.build_context(change_record)
        rendered = renderer.render(template, context)

        # Empty string when no default
        assert rendered.subject == "Test "

    def test_variables_used_tracking(self, template, change_record):
        """Test tracking of used variables."""
        renderer = TemplateRenderer()
        context = renderer.build_context(change_record)
        rendered = renderer.render(template, context)

        assert "change_number" in rendered.variables_used
        assert "short_description" in rendered.variables_used
        assert "planned_start" in rendered.variables_used

    def test_render_string(self):
        """Test rendering a raw string."""
        renderer = TemplateRenderer()
        renderer._context = {"name": "Test", "value": "123"}

        result = renderer.render_string("Name: ${name}, Value: ${value}")
        assert result == "Name: Test, Value: 123"

    def test_preview(self, template):
        """Test template preview with sample data."""
        renderer = TemplateRenderer()
        rendered = renderer.preview(template)

        assert "CHG0012345" in rendered.subject
        assert "Sample App" in rendered.body or "CHG0012345" in rendered.body

    def test_preview_with_custom_context(self, template):
        """Test preview with custom context."""
        renderer = TemplateRenderer()
        custom_context = {
            "change_number": "CHG9999999",
            "short_description": "Custom Test",
            "risk_level": "high",
            "planned_start": "2026-06-01 10:00",
            "planned_end": "2026-06-01 14:00",
        }
        rendered = renderer.preview(template, custom_context)

        assert "CHG9999999" in rendered.subject
        assert "Custom Test" in rendered.subject
        assert "high" in rendered.body

    def test_get_available_variables(self):
        """Test getting available variables list."""
        variables = TemplateRenderer.get_available_variables()

        assert len(variables) > 0
        assert any(v["name"] == "change_number" for v in variables)
        assert any(v["name"] == "application_name" for v in variables)

        # Check structure
        for var in variables:
            assert "name" in var
            assert "description" in var

    def test_nested_context_access(self):
        """Test nested dictionary access."""
        renderer = TemplateRenderer()
        renderer._context = {
            "app": {
                "name": "MyApp",
                "version": "1.0.0",
            }
        }

        result = renderer.render_string("App: ${app.name} v${app.version}")
        assert result == "App: MyApp v1.0.0"

    def test_special_characters(self, db, change_record):
        """Test handling of special characters."""
        change_record.short_description = "Update <App> & 'Config'"
        change_record.save()

        template = CommunicationTemplate.objects.create(
            name="Special Chars",
            event_type="scheduled",
            channel="email",
            subject_template="${short_description}",
            body_template="${short_description}",
        )

        renderer = TemplateRenderer()
        context = renderer.build_context(change_record)
        rendered = renderer.render(template, context)

        assert "<App>" in rendered.subject
        assert "'Config'" in rendered.body
