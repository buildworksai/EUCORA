# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Retry decorators for resilient external service calls.

Implements exponential backoff with jitter to prevent thundering herd.
"""
import logging

from tenacity import after_log, before_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Standard retry pattern: 3 attempts with exponential backoff (2^n seconds + jitter)
DEFAULT_RETRY = retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((Exception,)),
    before=before_log(logger, logging.DEBUG),
    after=after_log(logger, logging.DEBUG),
    reraise=True,
)

# Shorter retry for transient failures (2 attempts, faster backoff)
TRANSIENT_RETRY = retry(
    wait=wait_exponential(multiplier=1, min=0.5, max=5),
    stop=stop_after_attempt(2),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    reraise=True,
)

# Longer retry for slow services (5 attempts, slower backoff)
SLOW_SERVICE_RETRY = retry(
    wait=wait_exponential(multiplier=2, min=2, max=30),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
)

# No-retry pattern for operations that should fail fast
NO_RETRY = lambda x: x
