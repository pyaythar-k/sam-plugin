#!/usr/bin/env python3
"""
SAM Observability Manager - Central coordinator for all observability components.

Provides:
- Singleton access to logging, metrics, tracing, and error tracking
- Centralized initialization and configuration
- Diagnostic bundle creation
- Flush and shutdown coordination
"""

import json
import shutil
import sys
import tempfile
import threading
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Import observability components
try:
    from skills.sam_observe.sam_logger import SamLogger, get_logger, set_trace_context
    from skills.sam_observe.metrics_collector import MetricsCollector, get_metrics, flush_all_metrics
    from skills.sam_observe.tracing_context import TracingContext, Span
    from skills.sam_observe.error_tracker import ErrorTracker, get_error_tracker
    from skills.sam_observe.config_loader import ConfigLoader, ObservabilityConfig
except ImportError:
    # For standalone testing
    from sam_logger import SamLogger, get_logger
    from metrics_collector import MetricsCollector, get_metrics
    from tracing_context import TracingContext, Span
    from error_tracker import ErrorTracker, get_error_tracker
    from config_loader import ConfigLoader, ObservabilityConfig


@dataclass
class ObservabilityComponents:
    """Container for all observability components."""

    logger: SamLogger
    metrics: MetricsCollector
    tracer: TracingContext
    error_tracker: ErrorTracker


class ObservabilityManager:
    """
    Central coordinator for all observability components.

    Provides singleton access to logging, metrics, tracing, and error tracking
    with unified initialization and shutdown.
    """

    _instance: Optional['ObservabilityManager'] = None
    _instance_lock = threading.Lock()
    _initialized = False

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize observability manager.

        Args:
            config_path: Optional path to configuration file
        """
        if ObservabilityManager._initialized:
            return

        # Load configuration
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load()

        # Initialize components
        self._initialize_components()

        # Component registries
        self._loggers: Dict[str, SamLogger] = {}
        self._metrics_collectors: Dict[str, MetricsCollector] = {}
        self._tracers: Dict[str, TracingContext] = {}

        # Error tracker (singleton)
        self._error_tracker: Optional[ErrorTracker] = None

        ObservabilityManager._initialized = True

    def _initialize_components(self) -> None:
        """Initialize core observability components."""
        # Initialize logging
        if self.config.logging.enabled:
            log_dir = Path(self.config.logging.file_path).parent
            SamLogger.initialize(
                log_dir=log_dir,
                level=self.config.logging.level,
            )

        # Initialize error tracker storage
        if self.config.errors.enabled:
            error_dir = Path(self.config.errors.storage_path)
            error_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metrics storage
        if self.config.metrics.enabled:
            metrics_dir = Path(self.config.metrics.storage_path)
            metrics_dir.mkdir(parents=True, exist_ok=True)

        # Initialize tracing storage
        if self.config.tracing.enabled:
            tracing_dir = Path(self.config.tracing.storage_path)
            tracing_dir.mkdir(parents=True, exist_ok=True)

    def get_logger(self, component: str, **context) -> SamLogger:
        """
        Get or create a logger for a component.

        Args:
            component: Component name (e.g., "sam-specs")
            **context: Default context (feature_id, task_id, etc.)

        Returns:
            SamLogger instance
        """
        cache_key = (component, tuple(sorted(context.items())))

        if cache_key not in self._loggers:
            logger = SamLogger(component, **context)

            # Apply component-specific log level
            component_level = self.config.logging.component_levels.get(component)
            if component_level:
                logger._logger.setLevel(getattr(__import__("logging"), component_level.upper()))

            self._loggers[cache_key] = logger

        return self._loggers[cache_key]

    def get_metrics(self, component: str) -> MetricsCollector:
        """
        Get or create a metrics collector for a component.

        Args:
            component: Component name

        Returns:
            MetricsCollector instance
        """
        if component not in self._metrics_collectors:
            storage_dir = Path(self.config.metrics.storage_path)
            self._metrics_collectors[component] = MetricsCollector(component, storage_dir)

        return self._metrics_collectors[component]

    def get_tracer(self, component: str) -> TracingContext:
        """
        Get or create a tracer for a component.

        Args:
            component: Component name

        Returns:
            TracingContext instance
        """
        if component not in self._tracers:
            storage_dir = Path(self.config.tracing.storage_path)
            self._tracers[component] = TracingContext(component, storage_dir)

        return self._tracers[component]

    def get_error_tracker(self) -> ErrorTracker:
        """
        Get the global error tracker.

        Returns:
            ErrorTracker instance
        """
        if self._error_tracker is None:
            storage_dir = Path(self.config.errors.storage_path)
            self._error_tracker = ErrorTracker(storage_dir)

        return self._error_tracker

    def get_components(self, component: str, **context) -> ObservabilityComponents:
        """
        Get all observability components for a component.

        Args:
            component: Component name
            **context: Context for logger

        Returns:
            ObservabilityComponents container
        """
        return ObservabilityComponents(
            logger=self.get_logger(component, **context),
            metrics=self.get_metrics(component),
            tracer=self.get_tracer(component),
            error_tracker=self.get_error_tracker(),
        )

    def flush(self) -> None:
        """Flush all buffered data to disk."""
        # Flush metrics
        for collector in self._metrics_collectors.values():
            collector.flush()

        # Flush traces
        for tracer in self._tracers.values():
            tracer.save_all_traces()

        # Flush log handlers
        if self.config.logging.enabled:
            for logger in self._loggers.values():
                for handler in logger._logger.handlers:
                    handler.flush()

    def shutdown(self) -> None:
        """Shutdown all observability components."""
        self.flush()

        # Close file handlers
        if self.config.logging.enabled:
            for logger in self._loggers.values():
                for handler in logger._logger.handlers:
                    handler.close()

    def create_diagnostic_bundle(self, output_path: Optional[Path] = None) -> Path:
        """
        Create a diagnostic bundle containing logs, metrics, traces, and errors.

        Args:
            output_path: Optional output path (defaults to timestamped zip file)

        Returns:
            Path to created bundle
        """
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = Path(f".sam/diagnostic_bundle_{timestamp}.zip")

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy logs
            logs_src = Path(".sam/logs")
            if logs_src.exists():
                shutil.copytree(logs_src, temp_path / "logs")

            # Copy metrics
            metrics_src = Path(".sam/metrics")
            if metrics_src.exists():
                shutil.copytree(metrics_src, temp_path / "metrics")

            # Copy traces
            traces_src = Path(".sam/traces")
            if traces_src.exists():
                shutil.copytree(traces_src, temp_path / "traces")

            # Copy errors
            errors_src = Path(".sam/errors")
            if errors_src.exists():
                shutil.copytree(errors_src, temp_path / "errors")

            # Add configuration
            config_data = {
                "logging": {
                    "level": self.config.logging.level,
                    "enabled": self.config.logging.enabled,
                },
                "metrics": {
                    "enabled": self.config.metrics.enabled,
                },
                "tracing": {
                    "enabled": self.config.tracing.enabled,
                    "sample_rate": self.config.tracing.sample_rate,
                },
                "errors": {
                    "enabled": self.config.errors.enabled,
                },
            }
            with open(temp_path / "config.json", "w") as f:
                json.dump(config_data, f, indent=2)

            # Add system info
            import platform
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "timestamp": time.time(),
            }
            with open(temp_path / "system_info.json", "w") as f:
                json.dump(system_info, f, indent=2)

            # Create zip file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zipf.write(file_path, arcname)

        return output_path

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all observability components.

        Returns:
            Status dictionary
        """
        status = {
            "config": {
                "logging": {
                    "enabled": self.config.logging.enabled,
                    "level": self.config.logging.level,
                },
                "metrics": {
                    "enabled": self.config.metrics.enabled,
                },
                "tracing": {
                    "enabled": self.config.tracing.enabled,
                    "sample_rate": self.config.tracing.sample_rate,
                },
                "errors": {
                    "enabled": self.config.errors.enabled,
                },
            },
            "components": {
                "loggers": len(self._loggers),
                "metrics_collectors": len(self._metrics_collectors),
                "tracers": len(self._tracers),
            },
        }

        # Add error stats
        if self._error_tracker:
            status["errors"] = self._error_tracker.get_error_stats()

        # Add metrics summary (first component)
        if self._metrics_collectors:
            first_collector = next(iter(self._metrics_collectors.values()))
            status["metrics_sample"] = {
                "counters": len(first_collector._counters),
                "gauges": len(first_collector._gauges),
                "histograms": len(first_collector._histograms),
            }

        # Add traces summary (first tracer)
        if self._tracers:
            first_tracer = next(iter(self._tracers.values()))
            status["traces"] = {
                "active_traces": len(first_tracer._traces),
            }

        return status

    @classmethod
    def get_instance(cls) -> 'ObservabilityManager':
        """
        Get the singleton ObservabilityManager instance.

        Returns:
            ObservabilityManager instance

        Raises:
            RuntimeError: If not initialized
        """
        if cls._instance is None:
            raise RuntimeError("ObservabilityManager not initialized. Call initialize() first.")
        return cls._instance

    @classmethod
    def initialize(cls, config_path: Optional[Path] = None) -> 'ObservabilityManager':
        """
        Initialize the singleton ObservabilityManager.

        Args:
            config_path: Optional path to configuration file

        Returns:
            ObservabilityManager instance
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(config_path)
        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if ObservabilityManager has been initialized."""
        return cls._instance is not None


# Convenience functions for global access

def get_manager() -> ObservabilityManager:
    """
    Get the global ObservabilityManager.

    Returns:
        ObservabilityManager instance

    Raises:
        RuntimeError: If not initialized
    """
    return ObservabilityManager.get_instance()


def initialize_observability(config_path: Optional[Path] = None) -> ObservabilityManager:
    """
    Initialize global observability system.

    Args:
        config_path: Optional path to configuration file

    Returns:
        ObservabilityManager instance
    """
    return ObservabilityManager.initialize(config_path)


def shutdown_observability() -> None:
    """Shutdown global observability system."""
    if ObservabilityManager.is_initialized():
        get_manager().shutdown()


def create_diagnostic_bundle(output_path: Optional[Path] = None) -> Path:
    """
    Create a diagnostic bundle.

    Args:
        output_path: Optional output path

    Returns:
        Path to created bundle
    """
    return get_manager().create_diagnostic_bundle(output_path)


if __name__ == "__main__":
    # Demo
    print("Initializing ObservabilityManager...")
    manager = ObservabilityManager.initialize()

    print("\nGetting components...")
    logger = manager.get_logger("sam-specs", feature_id="demo")
    metrics = manager.get_metrics("sam-specs")
    tracer = manager.get_tracer("sam-specs")

    logger.info("Test log message", test_value=123)
    metrics.increment("test_counter")
    trace_id, root_span = tracer.start_trace("demo_operation")

    print("\nStatus:")
    status = manager.get_status()
    print(json.dumps(status, indent=2))

    print("\nFlushing...")
    manager.flush()

    print("\nCreating diagnostic bundle...")
    bundle_path = manager.create_diagnostic_bundle()
    print(f"Bundle created: {bundle_path}")

    print("\nShutting down...")
    manager.shutdown()
