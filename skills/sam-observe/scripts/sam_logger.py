#!/usr/bin/env python3
"""
SAM Logger - Structured logging with JSON output and context enrichment.

Provides centralized logging with:
- JSON formatted output for machine parsing
- Human-readable console output (backward compatible)
- Context binding with child loggers
- Automatic trace/span ID propagation
- Dual output strategy (console + file)
"""

import json
import logging
import sys
import threading
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Optional


# Thread-local storage for trace/span context
_trace_context = threading.local()


@dataclass
class LogEntry:
    """Structured log entry."""

    timestamp: str
    level: str
    component: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    feature_id: Optional[str] = None
    task_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    exception: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "component": self.component,
            "feature_id": self.feature_id,
            "task_id": self.task_id,
            "message": self.message,
            "context": self.context,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "exception": self.exception,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class TextFormatter(logging.Formatter):
    """Human-readable log formatter for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def __init__(self, show_context: bool = True):
        super().__init__()
        self.show_context = show_context

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for human-readable output."""
        level = record.levelname
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]

        # Base format: [LEVEL] component: message
        parts = [
            f"{color}[{level}]{reset}",
            f"{getattr(record, 'component', 'unknown')}:",
            record.getMessage(),
        ]

        # Add context if present
        if self.show_context:
            context_parts = []
            if hasattr(record, "feature_id") and record.feature_id:
                context_parts.append(f"feature={record.feature_id}")
            if hasattr(record, "task_id") and record.task_id:
                context_parts.append(f"task={record.task_id}")

            if context_parts:
                parts.append(f"({', '.join(context_parts)})")

        # Add exception info if present
        if record.exc_info:
            parts.append("\n" + "".join(traceback.format_exception(*record.exc_info)))

        return " ".join(parts)


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=record.levelname,
            component=getattr(record, "component", "unknown"),
            message=record.getMessage(),
            context=getattr(record, "context", {}),
            feature_id=getattr(record, "feature_id", None),
            task_id=getattr(record, "task_id", None),
            trace_id=getattr(record, "trace_id", None) or self._get_trace_id(),
            span_id=getattr(record, "span_id", None) or self._get_span_id(),
        )

        # Add exception info if present
        if record.exc_info:
            entry.exception = "".join(traceback.format_exception(*record.exc_info))

        return entry.to_json()

    @staticmethod
    def _get_trace_id() -> Optional[str]:
        """Get current trace ID from thread-local storage."""
        return getattr(_trace_context, "trace_id", None)

    @staticmethod
    def _get_span_id() -> Optional[str]:
        """Get current span ID from thread-local storage."""
        return getattr(_trace_context, "span_id", None)


class SamLogger:
    """
    Structured logger with context enrichment and dual output.

    Maintains backward compatibility by outputting to console in text format
    while also writing JSON to file for machine parsing.
    """

    # Class-level configuration
    _log_dir: Optional[Path] = None
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False

    @classmethod
    def initialize(cls, log_dir: Optional[Path] = None, level: str = "INFO"):
        """
        Initialize the logging system.

        Args:
            log_dir: Directory for JSON log files (defaults to .sam/logs/)
            level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if cls._initialized:
            return

        cls._log_dir = log_dir or Path(".sam/logs")
        cls._log_dir.mkdir(parents=True, exist_ok=True)

        # Create root logger
        root_logger = logging.getLogger("sam")
        root_logger.setLevel(getattr(logging, level.upper()))
        root_logger.handlers.clear()

        # Console handler (text format)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(TextFormatter())
        console_handler.setLevel(logging.INFO)  # Less verbose on console
        root_logger.addHandler(console_handler)

        # File handler (JSON format)
        log_file = cls._log_dir / "sam.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(file_handler)

        cls._initialized = True

    def __init__(
        self,
        component: str,
        feature_id: Optional[str] = None,
        task_id: Optional[str] = None,
        level: str = "INFO",
    ):
        """
        Create a new SamLogger instance.

        Args:
            component: Component name (e.g., "sam-specs", "sam-develop")
            feature_id: Optional feature identifier
            task_id: Optional task identifier
            level: Log level for this logger
        """
        if not SamLogger._initialized:
            SamLogger.initialize()

        self.component = component
        self.feature_id = feature_id
        self.task_id = task_id

        # Get or create Python logger
        logger_name = f"sam.{component}"
        if logger_name not in self._loggers:
            self._loggers[logger_name] = logging.getLogger(logger_name)

        self._logger = self._loggers[logger_name]
        self._context: Dict[str, Any] = {}

    def _log(
        self,
        level: int,
        message: str,
        **context,
    ) -> None:
        """
        Internal logging method.

        Args:
            level: Python logging level constant
            message: Log message
            **context: Additional context key-value pairs
        """
        # Merge instance context with call context
        merged_context = {**self._context, **context}

        # Create log record with extra attributes
        extra = {
            "component": self.component,
            "feature_id": self.feature_id,
            "task_id": self.task_id,
            "context": merged_context,
        }

        # Add trace/span IDs if available
        trace_id = getattr(_trace_context, "trace_id", None)
        if trace_id:
            extra["trace_id"] = trace_id

        span_id = getattr(_trace_context, "span_id", None)
        if span_id:
            extra["span_id"] = span_id

        self._logger.log(level, message, extra=extra)

    def info(self, message: str, **context) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **context)

    def warning(self, message: str, **context) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **context)

    def error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        **context,
    ) -> None:
        """
        Log error message.

        Args:
            message: Error message
            exception: Optional exception to include
            **context: Additional context
        """
        if exception:
            self._logger.error(
                message,
                exc_info=(type(exception), exception, exception.__traceback__),
                extra={
                    "component": self.component,
                    "feature_id": self.feature_id,
                    "task_id": self.task_id,
                    "context": {**self._context, **context},
                },
            )
        else:
            self._log(logging.ERROR, message, **context)

    def debug(self, message: str, **context) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **context)

    def critical(self, message: str, **context) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **context)

    def with_context(self, **kwargs) -> "SamLogger":
        """
        Create a child logger with additional context.

        Args:
            **kwargs: Context key-value pairs to add

        Returns:
            New SamLogger instance with merged context
        """
        child = SamLogger(self.component, self.feature_id, self.task_id)
        child._context = {**self._context, **kwargs}
        return child

    @contextmanager
    def timed(self, operation_name: str) -> Iterator[None]:
        """
        Context manager for timing operations.

        Args:
            operation_name: Name of the operation being timed

        Yields:
            None
        """
        import time

        self.info(f"Starting: {operation_name}")
        start = time.time()

        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            self.info(
                f"Completed: {operation_name}",
                operation=operation_name,
                duration_ms=round(duration_ms, 2),
            )


# Global logger instances cache
_logger_cache: Dict[str, SamLogger] = {}
_cache_lock = threading.Lock()


def get_logger(component: str, **context) -> SamLogger:
    """
    Get or create a SamLogger instance.

    Args:
        component: Component name (e.g., "sam-specs", "sam-develop")
        **context: Default context (feature_id, task_id, etc.)

    Returns:
        SamLogger instance
    """
    cache_key = (component, tuple(sorted(context.items())))

    with _cache_lock:
        if cache_key not in _logger_cache:
            _logger_cache[cache_key] = SamLogger(component, **context)

        return _logger_cache[cache_key]


def set_trace_context(trace_id: str, span_id: Optional[str] = None) -> None:
    """
    Set trace context for current thread.

    Args:
        trace_id: Trace ID
        span_id: Optional span ID
    """
    _trace_context.trace_id = trace_id
    if span_id:
        _trace_context.span_id = span_id


def clear_trace_context() -> None:
    """Clear trace context for current thread."""
    _trace_context.trace_id = None
    _trace_context.span_id = None


def get_trace_context() -> tuple[Optional[str], Optional[str]]:
    """
    Get current trace context.

    Returns:
        Tuple of (trace_id, span_id)
    """
    return (
        getattr(_trace_context, "trace_id", None),
        getattr(_trace_context, "span_id", None),
    )


if __name__ == "__main__":
    # Demo
    SamLogger.initialize()

    logger = get_logger("sam-specs", feature_id="user_auth", task_id="3.2")

    logger.info("Starting specification parse", file="TECHNICAL_SPEC.md")

    with logger.timed("parse_operation"):
        logger.debug("Reading file contents")
        logger.info("Found 42 tasks", tasks_found=42)

    child_logger = logger.with_context(subtask="validation")
    child_logger.info("Validation complete")

    try:
        raise ValueError("Demo error")
    except Exception as e:
        logger.error("Parse failed", exception=e)
