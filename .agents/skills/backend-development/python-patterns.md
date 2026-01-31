# Python Patterns Reference

Advanced Python patterns for EUCORA backend development.

---

## Type Annotations

### Standard Patterns

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union, Callable, TypeVar, Generic

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from apps.core.models import User

T = TypeVar("T")

# Function signatures
def process_items(items: list[str], limit: int = 10) -> dict[str, int]:
    ...

# Optional values
def get_user(user_id: str) -> User | None:
    ...

# Callable types
def apply_transform(data: list[T], transform: Callable[[T], T]) -> list[T]:
    ...

# Generic classes
class Repository(Generic[T]):
    def get(self, id: str) -> T | None:
        ...

    def list(self) -> list[T]:
        ...
```

### Django-Specific Types

```python
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

def get_deployments(request: HttpRequest) -> QuerySet[Deployment]:
    return Deployment.objects.filter(owner=request.user)

def deployment_view(request: HttpRequest, pk: int) -> HttpResponse:
    deployment = get_object_or_404(Deployment, pk=pk)
    return render(request, "deployment.html", {"deployment": deployment})
```

---

## Error Handling

### Custom Exception Hierarchy

```python
class EUCORAError(Exception):
    """Base exception for EUCORA platform."""

    def __init__(self, message: str, code: str, correlation_id: str | None = None):
        self.message = message
        self.code = code
        self.correlation_id = correlation_id
        super().__init__(message)


class ValidationError(EUCORAError):
    """Raised when input validation fails."""
    pass


class PolicyViolationError(EUCORAError):
    """Raised when an action violates platform policy."""
    pass


class TransientError(EUCORAError):
    """Raised for retryable errors (network, rate limits)."""
    pass


class PermanentError(EUCORAError):
    """Raised for non-retryable errors."""
    pass
```

### Error Classification Pattern

```python
from enum import Enum
from dataclasses import dataclass

class ErrorClass(str, Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    POLICY_VIOLATION = "policy_violation"

@dataclass
class ClassifiedError:
    original: Exception
    classification: ErrorClass
    should_retry: bool
    correlation_id: str

def classify_error(error: Exception, correlation_id: str) -> ClassifiedError:
    """Classify error for appropriate handling."""

    if isinstance(error, (TimeoutError, ConnectionError)):
        return ClassifiedError(error, ErrorClass.TRANSIENT, True, correlation_id)

    if isinstance(error, PermissionError):
        return ClassifiedError(error, ErrorClass.POLICY_VIOLATION, False, correlation_id)

    return ClassifiedError(error, ErrorClass.PERMANENT, False, correlation_id)
```

---

## Async Patterns

### Async Context Manager

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

@asynccontextmanager
async def database_transaction() -> AsyncIterator[Connection]:
    """Async context manager for database transactions."""
    conn = await get_connection()
    try:
        await conn.begin()
        yield conn
        await conn.commit()
    except Exception:
        await conn.rollback()
        raise
    finally:
        await conn.close()

# Usage
async def create_deployment(data: dict) -> Deployment:
    async with database_transaction() as conn:
        deployment = await Deployment.objects.acreate(**data)
        await AuditLog.objects.acreate(
            action="create",
            target_id=deployment.id,
        )
        return deployment
```

### Concurrent Execution

```python
import asyncio
from typing import Coroutine, Any

async def gather_with_errors(
    *coros: Coroutine[Any, Any, Any],
    max_concurrent: int = 10,
) -> list[Any]:
    """Run coroutines concurrently with error handling."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited(coro: Coroutine) -> Any:
        async with semaphore:
            return await coro

    results = await asyncio.gather(
        *(limited(c) for c in coros),
        return_exceptions=True,
    )

    # Raise first exception if any
    for result in results:
        if isinstance(result, Exception):
            raise result

    return results
```

---

## Dataclasses and Pydantic

### Dataclass with Validation

```python
from dataclasses import dataclass, field
from typing import Self

@dataclass
class RiskScore:
    """Immutable risk score with validation."""

    value: float
    factors: list[str] = field(default_factory=list)
    model_version: str = "v1.0"

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"Risk score must be 0-100, got {self.value}")

    @property
    def requires_cab(self) -> bool:
        return self.value > 50

    @property
    def risk_level(self) -> str:
        if self.value <= 30:
            return "low"
        elif self.value <= 70:
            return "medium"
        return "high"

    @classmethod
    def from_factors(cls, factors: dict[str, float], weights: dict[str, float]) -> Self:
        """Create risk score from weighted factors."""
        score = sum(factors.get(k, 0) * v for k, v in weights.items())
        return cls(value=min(100, max(0, score)), factors=list(factors.keys()))
```

### Pydantic for API Validation

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID

class DeploymentRequest(BaseModel):
    """Request model for creating deployments."""

    application_id: UUID
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    target_ring: int = Field(ge=0, le=4)
    schedule: datetime | None = None
    correlation_id: UUID

    @field_validator("schedule")
    @classmethod
    def schedule_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v and v <= datetime.now():
            raise ValueError("Schedule must be in the future")
        return v

class DeploymentResponse(BaseModel):
    """Response model for deployment operations."""

    id: UUID
    status: str
    risk_score: float
    created_at: datetime
    correlation_id: UUID

    class Config:
        from_attributes = True  # Enable ORM mode
```

---

## Logging Patterns

### Structured Logging Setup

```python
import logging
import json
from typing import Any

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def get_logger(name: str, correlation_id: str | None = None) -> logging.LoggerAdapter:
    """Get logger with optional correlation ID context."""
    logger = logging.getLogger(name)
    extra = {"correlation_id": correlation_id} if correlation_id else {}
    return logging.LoggerAdapter(logger, extra)

# Usage
logger = get_logger(__name__, correlation_id="abc-123")
logger.info("Processing deployment", extra={"deployment_id": "xyz"})
```

---

## Retry Patterns

### Exponential Backoff

```python
import asyncio
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (TransientError,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for retry with exponential backoff."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        await asyncio.sleep(delay)

            raise last_exception

        return wrapper

    return decorator

# Usage
@retry_with_backoff(max_attempts=5, base_delay=2.0)
async def call_external_api(url: str) -> dict:
    response = await http_client.get(url)
    if response.status_code >= 500:
        raise TransientError("Server error")
    return response.json()
```

---

## Testing Utilities

### Factory Pattern for Test Data

```python
from typing import Any
import factory
from factory.django import DjangoModelFactory

class DeploymentFactory(DjangoModelFactory):
    """Factory for creating test Deployment instances."""

    class Meta:
        model = Deployment

    name = factory.Faker("company")
    status = DeploymentStatus.PENDING
    risk_score = factory.Faker("pydecimal", min_value=0, max_value=100, right_digits=2)
    correlation_id = factory.Faker("uuid4")
    is_demo = False

    @factory.lazy_attribute
    def application(self) -> Application:
        return ApplicationFactory()

# Usage in tests
def test_deployment_approval():
    deployment = DeploymentFactory(status=DeploymentStatus.PENDING)

    result = approve_deployment(deployment)

    assert result.status == DeploymentStatus.APPROVED
```

### Async Test Fixtures

```python
import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def deployment() -> Deployment:
    """Create deployment for async tests."""
    return await Deployment.objects.acreate(
        name="Test Deployment",
        status=DeploymentStatus.PENDING,
    )

@pytest.mark.asyncio
async def test_semantic_search(deployment: Deployment):
    # Index the deployment
    await index_deployment(deployment)

    # Search
    results = await semantic_search("test deployment")

    assert len(results) > 0
    assert results[0]["source_id"] == str(deployment.id)
```
