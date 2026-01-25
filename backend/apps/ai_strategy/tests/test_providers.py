# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for LLM providers (10 tests).
"""
from django.test import TestCase

from apps.ai_strategy.providers import LLMMessage, LLMProvider, MockLLMProvider


class MockProviderTests(TestCase):
    """Tests for MockLLMProvider."""

    def setUp(self):
        """Set up test provider."""
        self.provider = MockLLMProvider()

    def test_provider_initialization(self):
        """Test provider initializes correctly."""
        self.assertEqual(self.provider.get_provider_name(), "mock")
        self.assertEqual(self.provider.get_model_name(), "mock-gpt")

    def test_basic_completion(self):
        """Test basic completion generation."""
        messages = [LLMMessage(role="user", content="Hello, how are you?")]

        completion = self.provider.complete(messages)

        self.assertIsNotNone(completion.content)
        self.assertEqual(completion.provider, "mock")
        self.assertGreater(completion.tokens_used, 0)
        self.assertGreater(completion.confidence, 0.0)

    def test_classification_completion(self):
        """Test classification-specific completion."""
        messages = [LLMMessage(role="user", content="Classify this incident: System outage")]

        completion = self.provider.complete(messages)

        self.assertIn("Classification", completion.content)
        self.assertEqual(completion.confidence, 0.85)

    def test_remediation_completion(self):
        """Test remediation-specific completion."""
        messages = [LLMMessage(role="user", content="How do I fix this error?")]

        completion = self.provider.complete(messages)

        self.assertIn("remediation", completion.content)

    def test_call_count_tracking(self):
        """Test provider tracks call count."""
        initial_count = self.provider.call_count

        self.provider.complete([LLMMessage(role="user", content="Test")])
        self.assertEqual(self.provider.call_count, initial_count + 1)

        self.provider.complete([LLMMessage(role="user", content="Test 2")])
        self.assertEqual(self.provider.call_count, initial_count + 2)

    def test_health_check(self):
        """Test provider health check."""
        self.assertTrue(self.provider.health_check())

    def test_temperature_parameter(self):
        """Test temperature parameter is accepted."""
        messages = [LLMMessage(role="user", content="Test")]

        completion = self.provider.complete(messages, temperature=0.5)

        self.assertIsNotNone(completion)

    def test_max_tokens_parameter(self):
        """Test max_tokens parameter is accepted."""
        messages = [LLMMessage(role="user", content="Test")]

        completion = self.provider.complete(messages, max_tokens=100)

        self.assertIsNotNone(completion)

    def test_reasoning_included(self):
        """Test completion includes reasoning."""
        messages = [LLMMessage(role="user", content="Test")]

        completion = self.provider.complete(messages)

        self.assertIsNotNone(completion.reasoning)

    def test_metadata_included(self):
        """Test completion includes metadata."""
        messages = [LLMMessage(role="user", content="Test")]

        completion = self.provider.complete(messages)

        self.assertIsNotNone(completion.metadata)
        self.assertIn("call_count", completion.metadata)
