"""
SAM Shared Observability Module

This module provides convenient access to all observability components
for use across SAM skills.

Usage:
    from skills.shared.observability import (
        get_logger,
        get_metrics,
        get_tracer,
        get_error_tracker,
        initialize,
        shutdown,
        observe,
        timed,
        catch_and_track,
    )

    # Initialize (call once at startup)
    initialize()

    # Get components
    logger = get_logger("sam-specs", feature_id="user_auth")
    metrics = get_metrics("sam-specs")

    # Use decorators
    @observe()
    @timed("operation_duration")
    def my_function():
        ...
"""

import functools
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

# Import observability components
try:
    from skills.sam_observe.sam_logger import (
        SamLogger,
        get_logger as _get_logger,
        set_trace_context,
        get_trace_context,
    )
    from skills.sam_observe.metrics_collector import (
        MetricsCollector,
        get_metrics as _get_metrics,
        timed as _timed_decorator,
    )
    from skills.sam_observe.tracing_context import (
        TracingContext,
        Span,
        get_tracer as _get_tracer,
        get_current_trace_id,
        get_current_span_id,
    )
    from skills.sam_observe.error_tracker import (
        ErrorTracker,
        ErrorSeverity,
        get_error_tracker as _get_error_tracker,
        track_exception as _track_exception,
    )
    from skills.sam_observe.observability_manager import (
        ObservabilityManager,
        initialize_observability,
        shutdown_observability,
        get_manager,
    )
except ImportError:
    # Fallback for development/testing
    try:
        # Try relative imports
        from ...sam_observe.scripts.sam_logger import (
            SamLogger,
            get_logger as _get_logger,
        )
        from ...sam_observe.scripts.metrics_collector import (
            MetricsCollector,
            get_metrics as _get_metrics,
        )
        from ...sam_observe.scripts.tracing_context import (
            TracingContext,
            Span,
            get_tracer as _get_tracer,
        )
        from ...sam_observe.scripts.error_tracker import (
            ErrorTracker,
            ErrorSeverity,
            get_error_tracker as _get_error_tracker,
        )
        from ...sam_observe.scripts.observability_manager import (
            ObservabilityManager,
            initialize_observability,
            shutdown_observability,
            get_manager,
        )
    except ImportError:
        # For standalone module usage
        import sam_logger
        import metrics_collector
        import tracing_context
        import error_tracker
        import observability_manager

        SamLogger = sam_logger.SamLogger
        MetricsCollector = metrics_collector.MetricsCollector
        TracingContext = tracing_context.TracingContext
        Span = tracing_context.Span
        ErrorTracker = error_tracker.ErrorTracker
        ErrorSeverity = error_tracker.ErrorSeverity
        ObservabilityManager = observability_manager.ObservabilityManager

        _get_logger = sam_logger.get_logger
        _get_metrics = metrics_collector.get_metrics
        _get_tracer = tracing_context.get_tracer
        _get_error_tracker = error_tracker.get_error_tracker
        initialize_observability = observability_manager.initialize_observability
        shutdown_observability = observability_manager.shutdown_observability
        get_manager = observability_manager.get_manager


F = TypeVar("F", bound=Callable[..., Any])


# ============================================================================
# Public API - Component Access
# ============================================================================

def initialize(config_path: Optional[Path] = None) -> ObservabilityManager:
    """
    Initialize the observability system.

    Call this once at application startup.

    Args:
        config_path: Optional path to configuration file

    Returns:
        ObservabilityManager instance

    Example:
        initialize()
        # or
        initialize(config_path=Path("config/observability.yaml"))
    """
    return initialize_observability(config_path)


def shutdown() -> None:
    """
    Shutdown the observability system.

    Call this at application shutdown to flush all data.
    """
    shutdown_observability()


def get_logger(component: str, **context) -> SamLogger:
    """
    Get or create a logger for a component.

    Args:
        component: Component name (e.g., "sam-specs", "sam-develop")
        **context: Default context (feature_id, task_id, etc.)

    Returns:
        SamLogger instance

    Example:
        logger = get_logger("sam-specs", feature_id="user_auth")
        logger.info("Specification parsed", tasks_found=42)
    """
    if ObservabilityManager.is_initialized():
        return get_manager().get_logger(component, **context)
    return _get_logger(component, **context)


def get_metrics(component: str) -> MetricsCollector:
    """
    Get or create a metrics collector for a component.

    Args:
        component: Component name

    Returns:
        MetricsCollector instance

    Example:
        metrics = get_metrics("sam-specs")
        metrics.increment("tasks_completed")
        with metrics.start_timer("operation_duration"):
            do_work()
    """
    if ObservabilityManager.is_initialized():
        return get_manager().get_metrics(component)
    return _get_metrics(component)


def get_tracer(component: str) -> TracingContext:
    """
    Get or create a tracer for a component.

    Args:
        component: Component name

    Returns:
        TracingContext instance

    Example:
        tracer = get_tracer("sam-specs")
        with tracer.span("parse_spec"):
            parse_spec()
    """
    if ObservabilityManager.is_initialized():
        return get_manager().get_tracer(component)
    return _get_tracer(component)


def get_error_tracker() -> ErrorTracker:
    """
    Get the global error tracker.

    Returns:
        ErrorTracker instance

    Example:
        tracker = get_error_tracker()
        try:
            risky_operation()
        except Exception as e:
            tracker.track_exception(e, context={"operation": "risky"})
    """
    if ObservabilityManager.is_initialized():
        return get_manager().get_error_tracker()
    return _get_error_tracker()


# ============================================================================
# Decorators
# ============================================================================

def observe(operation_name: Optional[str] = None, component: Optional[str] = None):
    """
    Decorator to observe a function with logging and tracing.

    Adds:
    - Function entry/exit logging
    - Span creation for tracing
    - Error tracking if exception occurs

    Args:
        operation_name: Name for the operation (defaults to function name)
        component: Component name (inferred from module if not provided)

    Example:
        @observe()
        def parse_spec(feature_dir):
            # Automatically logged and traced
            ...
    """
    def decorator(func: F) -> F:
        # Infer component from module
        inferred_component = component
        if inferred_component is None:
            module = func.__module__
            inferred_component = module.split(".")[-1] if "." in module else "unknown"

        op_name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(inferred_component)
            tracer = get_tracer(inferred_component)

            # Log entry
            logger.info(f"Starting: {op_name}", function=func.__name__)

            # Create span
            span = tracer.start_span(op_name)

            try:
                result = func(*args, **kwargs)

                # Log success
                logger.info(f"Completed: {op_name}", function=func.__name__)

                return result

            except Exception as e:
                # Log error
                logger.error(f"Failed: {op_name}", exception=e, function=func.__name__)

                # Track error
                tracker = get_error_tracker()
                tracker.track_exception(e, context={
                    "function": func.__name__,
                    "operation": op_name,
                })

                raise

            finally:
                # End span
                tracer.end_span(span)

        return wrapper
    return decorator


def timed(metric_name: Optional[str] = None, component: Optional[str] = None):
    """
    Decorator to time function execution.

    Records execution time in metrics.

    Args:
        metric_name: Name for the timing metric (defaults to function_name + "_duration")
        component: Component name (inferred from module if not provided)

    Example:
        @timed()
        def parse_spec(feature_dir):
            # Execution time recorded
            ...
    """
    def decorator(func: F) -> F:
        # Infer component from module
        inferred_component = component
        if inferred_component is None:
            module = func.__module__
            inferred_component = module.split(".")[-1] if "." in module else "unknown"

        name = metric_name or f"{func.__name__}_duration"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics(inferred_component)
            with metrics.start_timer(name):
                return func(*args, **kwargs)

        return wrapper
    return decorator


def catch_and_track(
    error_message: Optional[str] = None,
    component: Optional[str] = None,
    re_raise: bool = True,
):
    """
    Decorator to catch exceptions and track them.

    Exceptions are tracked in the error tracker and can be optionally re-raised.

    Args:
        error_message: Custom error message (defaults to function name + " failed")
        component: Component name (inferred from module if not provided)
        re_raise: Whether to re-raise the exception (default: True)

    Example:
        @catch_and_track(re_raise=False)
        def risky_operation():
            # Exceptions tracked but not raised
            ...
    """
    def decorator(func: F) -> F:
        # Infer component from module
        inferred_component = component
        if inferred_component is None:
            module = func.__module__
            inferred_component = module.split(".")[-1] if "." in module else "unknown"

        message = error_message or f"{func.__name__} failed"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(inferred_component)
            tracker = get_error_tracker()

            try:
                return func(*args, **kwargs)

            except Exception as e:
                # Log error
                logger.error(message, exception=e, function=func.__name__)

                # Track error
                tracker.track_exception(e, context={
                    "function": func.__name__,
                    "component": inferred_component,
                })

                # Re-raise if requested
                if re_raise:
                    raise

                return None

        return wrapper
    return decorator


# ============================================================================
# Context Managers
# ============================================================================

class observe_context:
    """
    Context manager for observing a block of code.

    Similar to @observe decorator but for code blocks.

    Example:
        with observe_context("parse_operation", "sam-specs"):
            parse_spec()
    """

    def __init__(self, operation_name: str, component: str):
        self.operation_name = operation_name
        self.component = component
        self.logger: Optional[SamLogger] = None
        self.tracer: Optional[TracingContext] = None
        self.span: Optional[Span] = None

    def __enter__(self):
        self.logger = get_logger(self.component)
        self.tracer = get_tracer(self.component)

        self.logger.info(f"Starting: {self.operation_name}")
        self.span = self.tracer.start_span(self.operation_name)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Failed: {self.operation_name}", exception=exc_val)

            tracker = get_error_tracker()
            tracker.track_exception(exc_val, context={
                "operation": self.operation_name,
                "component": self.component,
            })

            self.tracer.end_span(self.span)
            return False  # Re-raise exception

        self.logger.info(f"Completed: {self.operation_name}")
        self.tracer.end_span(self.span)
        return True


# ============================================================================
# Convenience Functions
# ============================================================================

def flush() -> None:
    """Flush all observability data to disk."""
    if ObservabilityManager.is_initialized():
        get_manager().flush()


def create_diagnostic_bundle(output_path: Optional[Path] = None) -> Path:
    """Create a diagnostic bundle containing all observability data."""
    if ObservabilityManager.is_initialized():
        return get_manager().create_diagnostic_bundle(output_path)
    raise RuntimeError("ObservabilityManager not initialized")


# Export public API
__all__ = [
    # Component access
    "initialize",
    "shutdown",
    "get_logger",
    "get_metrics",
    "get_tracer",
    "get_error_tracker",
    # Decorators
    "observe",
    "timed",
    "catch_and_track",
    # Context managers
    "observe_context",
    # Utilities
    "flush",
    "create_diagnostic_bundle",
    # Types
    "SamLogger",
    "MetricsCollector",
    "TracingContext",
    "Span",
    "ErrorTracker",
    "ErrorSeverity",
    "ObservabilityManager",
    # Tracing utilities
    "get_current_trace_id",
    "get_current_span_id",
]
