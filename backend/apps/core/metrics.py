# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Prometheus metrics instrumentation.

Implements custom metrics for:
- Deployment success/failure rates
- Risk score distribution
- Time-to-compliance tracking
- Circuit breaker state changes
- Task execution times
- HTTP response latencies

In multiprocess mode, metrics are stored in files in PROMETHEUS_MULTIPROC_DIR.
When Prometheus scrapes the metrics endpoint, MultiProcessCollector aggregates
all worker process metrics from the shared directory.
"""
import logging

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Deployment Metrics
deployment_total = Counter(
    "deployment_total", "Total deployments by status and ring", ["status", "ring", "app_name", "requires_cab"]
)

deployment_duration_seconds = Histogram(
    "deployment_duration_seconds",
    "Deployment execution time in seconds",
    ["ring", "app_name", "status"],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800),
)

deployment_time_to_compliance_seconds = Gauge(
    "deployment_time_to_compliance_seconds", "Time from Ring 1 to compliance across all rings", ["ring", "app_name"]
)

# Risk Score Metrics
risk_score = Histogram(
    "risk_score_distribution",
    "Distribution of deployment risk scores",
    ["requires_cab"],
    buckets=(10, 25, 50, 75, 90, 100),
)

# Ring Promotion Metrics
ring_promotion_total = Counter(
    "ring_promotion_total", "Ring promotions by from_ring, to_ring, and status", ["from_ring", "to_ring", "status"]
)

promotion_gate_success_rate = Gauge("promotion_gate_success_rate", "Success rate for ring promotion gates", ["ring"])

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    "circuit_breaker_state", "Circuit breaker state: 0=CLOSED, 1=OPEN, 2=HALF_OPEN", ["service", "connector_type"]
)

circuit_breaker_failures = Counter(
    "circuit_breaker_failures_total",
    "Total failures triggering circuit breaker",
    ["service", "connector_type", "error_type"],
)

# Celery Task Metrics
celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution time",
    ["task_name", "status"],
    buckets=(0.1, 0.5, 1, 5, 10, 30, 60, 300),
)

celery_task_retries_total = Counter("celery_task_retries_total", "Celery task retries", ["task_name", "retry_number"])

# HTTP Metrics
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint", "status"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_total = Counter(
    "http_requests_total", "HTTP requests by method, endpoint, and status", ["method", "endpoint", "status"]
)

# Database Metrics
db_connection_pool_size = Gauge("db_connection_pool_size", "Database connection pool current size")

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query execution time",
    ["query_type"],
    buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 5.0),
)

# Connector Metrics
connector_health = Gauge("connector_health", "Connector health status: 1=healthy, 0=unhealthy", ["connector_type"])

connector_operation_duration_seconds = Histogram(
    "connector_operation_duration_seconds",
    "Connector operation latency",
    ["connector_type", "operation", "status"],
    buckets=(0.1, 0.5, 1, 5, 10, 30, 60, 300),
)


def record_deployment(status: str, ring: str, app_name: str, requires_cab: bool, duration: float):
    """
    Record deployment metrics.

    Args:
        status: 'success' or 'failed'
        ring: Ring name (LAB, CANARY, PILOT, DEPARTMENT, GLOBAL)
        app_name: Application name
        requires_cab: Whether CAB approval was required
        duration: Execution time in seconds
    """
    deployment_total.labels(status=status, ring=ring, app_name=app_name, requires_cab=str(requires_cab)).inc()

    deployment_duration_seconds.labels(ring=ring, app_name=app_name, status=status).observe(duration)


def record_risk_score(score: int, requires_cab: bool):
    """Record risk score distribution."""
    risk_score.labels(requires_cab=str(requires_cab)).observe(score)


def record_ring_promotion(from_ring: str, to_ring: str, status: str):
    """Record ring promotion attempt."""
    ring_promotion_total.labels(from_ring=from_ring, to_ring=to_ring, status=status).inc()


def update_promotion_gate_rate(ring: str, success_rate: float):
    """Update promotion gate success rate."""
    promotion_gate_success_rate.labels(ring=ring).set(success_rate)


def update_circuit_breaker_state(service: str, connector_type: str, state: int):
    """
    Update circuit breaker state.

    Args:
        service: Service name
        connector_type: Connector type (intune, jamf, sccm, etc.)
        state: 0=CLOSED, 1=OPEN, 2=HALF_OPEN
    """
    circuit_breaker_state.labels(service=service, connector_type=connector_type).set(state)


def record_circuit_breaker_failure(service: str, connector_type: str, error_type: str):
    """Record circuit breaker failure."""
    circuit_breaker_failures.labels(service=service, connector_type=connector_type, error_type=error_type).inc()


def record_celery_task(task_name: str, status: str, duration: float, retry_count: int = 0):
    """
    Record Celery task metrics.

    Args:
        task_name: Task name
        status: 'success' or 'failed'
        duration: Execution time in seconds
        retry_count: Number of retries
    """
    celery_task_duration_seconds.labels(task_name=task_name, status=status).observe(duration)

    if retry_count > 0:
        celery_task_retries_total.labels(task_name=task_name, retry_number=str(retry_count)).inc()


def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """
    Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()

    http_request_duration_seconds.labels(method=method, endpoint=endpoint, status=str(status_code)).observe(duration)


def record_db_query(query_type: str, duration: float):
    """
    Record database query metrics.

    Args:
        query_type: Type of query (select, insert, update, delete)
        duration: Query execution time in seconds
    """
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def update_connector_health(connector_type: str, is_healthy: bool):
    """
    Update connector health status.

    Args:
        connector_type: Connector type
        is_healthy: True if healthy, False otherwise
    """
    connector_health.labels(connector_type=connector_type).set(1 if is_healthy else 0)


def record_connector_operation(connector_type: str, operation: str, status: str, duration: float):
    """
    Record connector operation metrics.

    Args:
        connector_type: Connector type
        operation: Operation name (deploy, query, remediate)
        status: 'success' or 'failed'
        duration: Operation duration in seconds
    """
    connector_operation_duration_seconds.labels(
        connector_type=connector_type, operation=operation, status=status
    ).observe(duration)
