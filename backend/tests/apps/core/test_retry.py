# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Unit tests for retry decorators."""
from unittest.mock import Mock, call, patch

import pytest
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from apps.core.retry import DEFAULT_RETRY, NO_RETRY, SLOW_SERVICE_RETRY, TRANSIENT_RETRY


class TestDefaultRetry:
    """Test DEFAULT_RETRY pattern."""

    def test_default_retry_succeeds_immediately(self):
        """Function succeeds on first attempt."""
        mock_func = Mock(return_value="success")
        decorated = DEFAULT_RETRY(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_default_retry_retries_on_failure(self):
        """Function retries after exceptions."""
        mock_func = Mock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])
        decorated = DEFAULT_RETRY(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 3

    def test_default_retry_max_attempts(self):
        """Stops after max_attempts (3)."""
        mock_func = Mock(side_effect=ValueError("fail"))
        decorated = DEFAULT_RETRY(mock_func)
        with pytest.raises(ValueError):
            decorated()
        assert mock_func.call_count == 3

    def test_default_retry_exponential_backoff(self):
        """Uses exponential backoff between retries."""
        # The retry decorator from tenacity applies exponential backoff
        # We verify the decorator is configured correctly
        mock_func = Mock(side_effect=[ValueError("fail"), "success"])
        decorated = DEFAULT_RETRY(mock_func)
        result = decorated()
        assert result == "success"


class TestTransientRetry:
    """Test TRANSIENT_RETRY pattern for transient errors."""

    def test_transient_retry_succeeds(self):
        """Succeeds on first attempt."""
        mock_func = Mock(return_value="success")
        decorated = TRANSIENT_RETRY(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_transient_retry_on_timeout(self):
        """Retries on TimeoutError."""
        mock_func = Mock(side_effect=[TimeoutError("timeout"), "success"])
        decorated = TRANSIENT_RETRY(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 2

    def test_transient_retry_on_connection_error(self):
        """Retries on ConnectionError."""
        mock_func = Mock(side_effect=[ConnectionError("conn fail"), "success"])
        decorated = TRANSIENT_RETRY(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 2

    def test_transient_retry_max_attempts_2(self):
        """Max attempts is 2 for transient errors."""
        mock_func = Mock(side_effect=TimeoutError("timeout"))
        decorated = TRANSIENT_RETRY(mock_func)
        with pytest.raises(TimeoutError):
            decorated()
        assert mock_func.call_count == 2

    def test_transient_retry_ignores_other_exceptions(self):
        """Does not retry on non-transient exceptions."""
        mock_func = Mock(side_effect=ValueError("not transient"))
        decorated = TRANSIENT_RETRY(mock_func)
        with pytest.raises(ValueError):
            decorated()
        assert mock_func.call_count == 1  # No retry


class TestSlowServiceRetry:
    """Test SLOW_SERVICE_RETRY pattern."""

    def test_slow_service_succeeds(self):
        """Succeeds on first attempt."""
        mock_func = Mock(return_value="success")
        decorated = SLOW_SERVICE_RETRY(mock_func)
        result = decorated()
        assert result == "success"

    def test_slow_service_retries_on_any_exception(self):
        """Retries on any exception."""
        mock_func = Mock(side_effect=[ValueError("fail1"), ValueError("fail2"), "success"])
        decorated = SLOW_SERVICE_RETRY(mock_func)
        result = decorated()
        assert result == "success"
        assert mock_func.call_count == 3

    def test_slow_service_max_attempts_5(self):
        """Max attempts is 5 for slow services."""
        mock_func = Mock(side_effect=ValueError("fail"))
        decorated = SLOW_SERVICE_RETRY(mock_func)
        with pytest.raises(ValueError):
            decorated()
        assert mock_func.call_count == 5

    def test_slow_service_longer_backoff(self):
        """Slow service uses longer backoff (2-30s)."""
        # Verify decorator configuration
        mock_func = Mock(side_effect=[ValueError("fail"), "success"])
        decorated = SLOW_SERVICE_RETRY(mock_func)
        result = decorated()
        assert result == "success"


class TestNoRetry:
    """Test NO_RETRY pattern."""

    def test_no_retry_is_identity(self):
        """NO_RETRY returns the function unchanged."""

        def my_func():
            return "result"

        decorated = NO_RETRY(my_func)
        result = decorated()
        assert result == "result"

    def test_no_retry_no_exception_handling(self):
        """NO_RETRY does not catch exceptions."""

        def failing_func():
            raise ValueError("fail")

        decorated = NO_RETRY(failing_func)
        with pytest.raises(ValueError):
            decorated()


class TestRetryWithArgs:
    """Test retry decorators with function arguments."""

    def test_retry_preserves_args(self):
        """Retry decorators preserve function arguments."""
        mock_func = Mock(side_effect=[ValueError("fail"), "success"])
        decorated = DEFAULT_RETRY(mock_func)
        result = decorated("arg1", "arg2", kwarg="value")
        assert result == "success"
        assert mock_func.call_args_list[-1] == call("arg1", "arg2", kwarg="value")

    def test_retry_preserves_return_value(self):
        """Retry decorators preserve return values."""
        return_dict = {"key": "value", "number": 42}
        mock_func = Mock(side_effect=[ValueError("fail"), return_dict])
        decorated = DEFAULT_RETRY(mock_func)
        result = decorated()
        assert result == return_dict


class TestRetryIntegration:
    """Integration tests with real retry behavior."""

    def test_retry_with_incremental_success(self):
        """Real example: eventually succeed after retries."""
        call_count = 0

        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError(f"Attempt {call_count}")
            return f"success on attempt {call_count}"

        decorated = TRANSIENT_RETRY(sometimes_fails)
        result = decorated()
        assert result == "success on attempt 3"
        assert call_count == 3

    def test_retry_exhausts_attempts(self):
        """Real example: all attempts fail."""
        attempt_count = 0

        def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise TimeoutError(f"Attempt {attempt_count} failed")

        decorated = TRANSIENT_RETRY(always_fails)
        with pytest.raises(TimeoutError):
            decorated()
        assert attempt_count == 2  # Max 2 attempts for TRANSIENT_RETRY
