"""OpenTelemetry distributed tracing setup.

Provides:
- Automatic span creation for FastAPI requests
- Manual span instrumentation for components
- Trace context propagation across async boundaries
- Export to OTLP endpoint (Jaeger, Honeycomb, etc.)

Usage:
    from src.observability.tracing import trace_async, get_tracer

    tracer = get_tracer(__name__)

    @trace_async("component_operation")
    async def my_function():
        pass
"""

import functools
from typing import Callable, Optional
from contextlib import contextmanager

from src.config.settings import get_settings

# OpenTelemetry imports (gracefully handle if not installed)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore


settings = get_settings()

# Global tracer provider
_tracer_provider: Optional["TracerProvider"] = None


def setup_tracing(service_name: str = "goassist") -> None:
    """Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for trace identification
    """
    if not OTEL_AVAILABLE:
        print("OpenTelemetry not installed. Tracing disabled.")
        return

    global _tracer_provider

    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name
    })

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(_tracer_provider)

    # Configure OTLP exporter (if endpoint provided)
    if settings.otel_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_endpoint,
            insecure=True,  # Use insecure for local dev (configure TLS for prod)
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        _tracer_provider.add_span_processor(span_processor)

    # Set B3 propagation format (compatible with most tracers)
    set_global_textmap(B3MultiFormat())


def instrument_fastapi(app) -> None:
    """Instrument FastAPI application with automatic tracing.

    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        return

    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str):
    """Get a tracer for the given module/component.

    Args:
        name: Tracer name (usually __name__)

    Returns:
        Tracer instance or no-op if OTel not available
    """
    if not OTEL_AVAILABLE or not trace:
        return NoOpTracer()

    return trace.get_tracer(name)


def trace_async(span_name: str, attributes: Optional[dict] = None):
    """Decorator for tracing async functions.

    Args:
        span_name: Name of the span
        attributes: Optional span attributes

    Usage:
        @trace_async("llm_generate")
        async def generate_response(prompt: str):
            pass
    """
    def decorator(func: Callable):
        if not OTEL_AVAILABLE:
            return func  # Pass-through if OTel not available

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)

                # Add function args as attributes (careful with PII)
                if kwargs:
                    span.set_attribute("function.kwargs_count", len(kwargs))

                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        return wrapper
    return decorator


def trace_sync(span_name: str, attributes: Optional[dict] = None):
    """Decorator for tracing synchronous functions.

    Args:
        span_name: Name of the span
        attributes: Optional span attributes
    """
    def decorator(func: Callable):
        if not OTEL_AVAILABLE:
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        return wrapper
    return decorator


@contextmanager
def trace_span(span_name: str, attributes: Optional[dict] = None):
    """Context manager for creating a trace span.

    Args:
        span_name: Name of the span
        attributes: Optional span attributes

    Usage:
        with trace_span("tts_synthesis", {"model": "xtts-v2"}):
            audio = await synthesize(text)
    """
    if not OTEL_AVAILABLE:
        yield
        return

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            span.set_attributes(attributes)
        yield span


class NoOpTracer:
    """No-op tracer when OpenTelemetry is not available."""

    @contextmanager
    def start_as_current_span(self, name: str, *args, **kwargs):
        """No-op span context manager."""
        yield self

    def set_attributes(self, attributes: dict):
        """No-op set attributes."""
        pass

    def record_exception(self, exception: Exception):
        """No-op record exception."""
        pass

    def set_status(self, status):
        """No-op set status."""
        pass


# Export commonly used functions
__all__ = [
    "setup_tracing",
    "instrument_fastapi",
    "get_tracer",
    "trace_async",
    "trace_sync",
    "trace_span",
]
