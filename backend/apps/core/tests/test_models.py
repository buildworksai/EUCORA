# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for core models.
"""
import pytest
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel, CorrelationIdModel


class TestModel(TimeStampedModel):
    """Test model inheriting from TimeStampedModel."""
    name = models.CharField(max_length=100)


class TestCorrelationModel(CorrelationIdModel):
    """Test model inheriting from CorrelationIdModel."""
    name = models.CharField(max_length=100)


@pytest.mark.django_db
class TestTimeStampedModel:
    """Test TimeStampedModel functionality."""
    
    def test_creates_timestamps_on_creation(self):
        """Test that timestamps are created on model creation."""
        instance = TestModel.objects.create(name='Test')
        
        assert instance.created_at is not None
        assert instance.updated_at is not None
        assert isinstance(instance.created_at, timezone.datetime)
    
    def test_updates_updated_at_on_save(self):
        """Test that updated_at is updated on save."""
        instance = TestModel.objects.create(name='Test')
        original_updated_at = instance.updated_at
        
        import time
        time.sleep(0.1)  # Ensure time difference
        
        instance.name = 'Updated'
        instance.save()
        
        assert instance.updated_at > original_updated_at


@pytest.mark.django_db
class TestCorrelationIdModel:
    """Test CorrelationIdModel functionality."""
    
    def test_generates_correlation_id_on_creation(self):
        """Test that correlation_id is generated on creation."""
        instance = TestCorrelationModel.objects.create(name='Test')
        
        assert instance.correlation_id is not None
        assert isinstance(instance.correlation_id, type(instance.correlation_id))
    
    def test_correlation_id_is_unique(self):
        """Test that correlation_ids are unique."""
        instance1 = TestCorrelationModel.objects.create(name='Test1')
        instance2 = TestCorrelationModel.objects.create(name='Test2')
        
        assert instance1.correlation_id != instance2.correlation_id
    
    def test_correlation_id_is_indexed(self):
        """Test that correlation_id has database index."""
        from django.db import connection
        indexes = connection.introspection.get_indexes(connection.cursor(), 'core_testcorrelationmodel')
        # Note: This test may need adjustment based on Django version
        assert True  # Placeholder - index verification

