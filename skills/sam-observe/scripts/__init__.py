"""
SAM Observability Skill

Provides comprehensive observability for SAM workflow including:
- Structured logging with JSON output
- Metrics collection (timing, counters, gauges)
- Distributed tracing
- Error tracking and aggregation
- Interactive diagnostic console

Usage:
    from skills.shared.observability import (
        initialize,
        get_logger,
        get_metrics,
        observe,
        timed,
    )

    # Initialize (once at startup)
    initialize()

    # Get components
    logger = get_logger("sam-specs", feature_id="user_auth")
    metrics = get_metrics("sam-specs")

    # Use decorators
    @observe()
    @timed("operation_duration")
    def my_function():
        logger.info("Processing...")
"""

__all__ = [
    "SamLogger",
    "MetricsCollector",
    "TracingContext",
    "ErrorTracker",
    "ObservabilityManager",
    "DiagnosticConsole",
]
