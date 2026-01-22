# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
OpenTelemetry distributed tracing configuration.

Implements correlation ID propagation across:
- HTTP requests (inbound/outbound)
- Celery tasks
- Database queries
- External API calls

Exports traces to OTLP endpoint for analysis.
"""
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagate import set_global_textmap
import os
import logging

logger = logging.getLogger(__name__)


def init_tracing(service_name: str = "eucora-control-plane"):
    """
    Initialize OpenTelemetry tracing with OTLP exporter.
    
    Args:
        service_name: Service name for traces
    
    Environment Variables:
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
        OTEL_ENABLED: Enable/disable tracing (default: true)
    """
    if not os.getenv("OTEL_ENABLED", "true").lower() == "true":
        logger.info("OpenTelemetry tracing disabled")
        return
    
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        # Initialize trace provider
        trace_provider = TracerProvider(resource=resource)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=True,
        )
        
        # Add batch processor for efficient export
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set global trace provider
        trace.set_tracer_provider(trace_provider)
        
        # Configure propagator for correlation ID across services
        set_global_textmap(CompositePropagator([TraceContextTextMapPropagator()]))
        
        # Instrument Django
        DjangoInstrumentor().instrument()
        
        # Instrument Celery
        CeleryInstrumentor().instrument()
        
        # Instrument HTTP requests
        RequestsInstrumentor().instrument()
        
        logger.info(
            "OpenTelemetry tracing initialized",
            extra={
                "service": service_name,
                "endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            }
        )
        
    except Exception as exc:
        logger.error(f"Failed to initialize OpenTelemetry tracing: {exc}", exc_info=True)


def init_metrics(service_name: str = "eucora-control-plane"):
    """
    Initialize OpenTelemetry metrics with OTLP exporter.
    
    Args:
        service_name: Service name for metrics
    
    Environment Variables:
        OTEL_METRICS_ENABLED: Enable/disable metrics (default: true)
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint
    """
    if not os.getenv("OTEL_METRICS_ENABLED", "true").lower() == "true":
        logger.info("OpenTelemetry metrics disabled")
        return
    
    try:
        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
        })
        
        # Initialize metric exporter
        metric_exporter = OTLPMetricExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=True,
        )
        
        # Initialize meter provider with periodic reader
        # Export metrics every 60 seconds
        metric_reader = PeriodicExportingMetricReader(exporter=metric_exporter)
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        
        # Set global meter provider
        metrics.set_meter_provider(meter_provider)
        
        logger.info(
            "OpenTelemetry metrics initialized",
            extra={"service": service_name}
        )
        
    except Exception as exc:
        logger.error(f"Failed to initialize OpenTelemetry metrics: {exc}", exc_info=True)


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance for a module.
    
    Args:
        name: Module name (e.g., __name__)
    
    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """
    Get a meter instance for metrics.
    
    Args:
        name: Module name (e.g., __name__)
    
    Returns:
        Meter instance
    """
    return metrics.get_meter(name)
