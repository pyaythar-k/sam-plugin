#!/usr/bin/env python3
"""
SAM Log Exporter - Optional integrations for external observability platforms.

Provides optional integrations with:
- Prometheus metrics export
- Sentry error tracking
- OpenTelemetry tracing export

These integrations are truly optional - the core observability system
works perfectly without them.
"""

import json
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


class LogExporter(ABC):
    """Abstract base class for log exporters."""

    @abstractmethod
    def export_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """Export logs to external platform."""
        pass

    @abstractmethod
    def export_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Export metrics to external platform."""
        pass

    @abstractmethod
    def export_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """Export errors to external platform."""
        pass


class ConsoleLogExporter(LogExporter):
    """Simple console exporter for testing."""

    def export_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """Print logs to console."""
        for log in logs[-10:]:  # Last 10
            print(f"[{log.get('timestamp', '')}] {log.get('level', '')}: {log.get('message', '')}")
        return True

    def export_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Print metrics to console."""
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
        return True

    def export_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """Print errors to console."""
        for error in errors[-5:]:  # Last 5
            print(f"Error: {error.get('error_type', '')}: {error.get('message', '')}")
        return True


class PrometheusLogExporter(LogExporter):
    """
    Export metrics to Prometheus Pushgateway.

    Requires: prometheus_client
    Installation: pip install prometheus_client
    """

    def __init__(self, pushgateway_url: str, job: str = "sam_workflow"):
        self.pushgateway_url = pushgateway_url
        self.job = job
        self._available = False

        try:
            from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
            self.CollectorRegistry = CollectorRegistry
            self.Gauge = Gauge
            self.push_to_gateway = push_to_gateway
            self._available = True
        except ImportError:
            print("Warning: prometheus_client not installed. Prometheus export disabled.", file=sys.stderr)

    def is_available(self) -> bool:
        """Check if exporter is available."""
        return self._available

    def export_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """Prometheus doesn't handle logs - skip."""
        return True

    def export_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Export metrics to Prometheus Pushgateway."""
        if not self.is_available():
            return False

        try:
            registry = self.CollectorRegistry()

            # Export counters
            for component, component_metrics in metrics.get("counters", {}).items():
                for metric_name, value in component_metrics.items():
                    g = self.Gauge(
                        f"sam_{component}_{metric_name}",
                        f"SAM {component} {metric_name}",
                        registry=registry
                    )
                    g.set(value)

            # Export gauges
            for component, component_metrics in metrics.get("gauges", {}).items():
                for metric_name, value in component_metrics.items():
                    g = self.Gauge(
                        f"sam_{component}_{metric_name}",
                        f"SAM {component} {metric_name}",
                        registry=registry
                    )
                    g.set(value)

            # Push to gateway
            self.push_to_gateway(
                self.pushgateway_url,
                job=self.job,
                registry=registry
            )

            return True

        except Exception as e:
            print(f"Error exporting to Prometheus: {e}", file=sys.stderr)
            return False

    def export_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """Export error count to Prometheus."""
        if not self.is_available():
            return False

        try:
            registry = self.CollectorRegistry()

            # Count errors by type
            error_counts: Dict[str, int] = {}
            for error in errors:
                error_type = error.get("error_type", "unknown")
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

            for error_type, count in error_counts.items():
                g = self.Gauge(
                    f"sam_errors_{error_type.lower()}",
                    f"SAM errors of type {error_type}",
                    registry=registry
                )
                g.set(count)

            # Push to gateway
            self.push_to_gateway(
                self.pushgateway_url,
                job=self.job,
                registry=registry
            )

            return True

        except Exception as e:
            print(f"Error exporting errors to Prometheus: {e}", file=sys.stderr)
            return False


class SentryLogExporter(LogExporter):
    """
    Export errors to Sentry.

    Requires: sentry-sdk
    Installation: pip install sentry-sdk
    """

    def __init__(self, dsn: str, environment: str = "development"):
        self.dsn = dsn
        self.environment = environment
        self._available = False

        try:
            import sentry_sdk
            self.sentry_sdk = sentry_sdk

            # Initialize Sentry
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                traces_sample_rate=0.1,  # 10% sampling for performance
            )
            self._available = True

        except ImportError:
            print("Warning: sentry-sdk not installed. Sentry export disabled.", file=sys.stderr)

    def is_available(self) -> bool:
        """Check if exporter is available."""
        return self._available

    def export_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """Sentry doesn't handle logs - skip."""
        return True

    def export_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Sentry doesn't handle metrics - skip."""
        return True

    def export_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """Export errors to Sentry."""
        if not self.is_available():
            return False

        try:
            for error in errors:
                # Send error to Sentry
                self.sentry_sdk.capture_exception(Exception(error.get("message", "Unknown error")))

            # Flush events
            self.sentry_sdk.flush()

            return True

        except Exception as e:
            print(f"Error exporting to Sentry: {e}", file=sys.stderr)
            return False


class OpenTelemetryLogExporter(LogExporter):
    """
    Export traces to OpenTelemetry-compatible backends.

    Requires: opentelemetry-sdk, opentelemetry-api
    Installation: pip install opentelemetry-sdk opentelemetry-api
    """

    def __init__(self, endpoint: str = "http://localhost:4317"):
        self.endpoint = endpoint
        self._available = False

        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            # Setup trace provider
            trace.set_tracer_provider(TracerProvider())
            tracer_provider = trace.get_tracer_provider()

            # Setup OTLP exporter
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            self.trace = trace
            self._available = True

        except ImportError:
            print("Warning: OpenTelemetry packages not installed. OTLP export disabled.", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to initialize OpenTelemetry: {e}", file=sys.stderr)

    def is_available(self) -> bool:
        """Check if exporter is available."""
        return self._available

    def export_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """OpenTelemetry doesn't handle logs directly - skip."""
        return True

    def export_metrics(self, metrics: Dict[str, Any]) -> bool:
        """OpenTelemetry metrics require additional setup - skip for now."""
        return True

    def export_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """Errors are already captured in traces - skip."""
        return True


def get_exporter(exporter_type: str, **config) -> Optional[LogExporter]:
    """
    Factory function to create log exporters.

    Args:
        exporter_type: Type of exporter (prometheus, sentry, otlp, console)
        **config: Configuration for the exporter

    Returns:
        LogExporter instance or None if type not recognized
    """
    exporters = {
        "prometheus": lambda: PrometheusLogExporter(
            pushgateway_url=config.get("pushgateway_url", "localhost:9091"),
            job=config.get("job", "sam_workflow"),
        ),
        "sentry": lambda: SentryLogExporter(
            dsn=config.get("dsn", ""),
            environment=config.get("environment", "development"),
        ),
        "otlp": lambda: OpenTelemetryLogExporter(
            endpoint=config.get("endpoint", "http://localhost:4317"),
        ),
        "console": lambda: ConsoleLogExporter(),
    }

    exporter_factory = exporters.get(exporter_type.lower())
    if exporter_factory:
        return exporter_factory()

    return None


if __name__ == "__main__":
    # Demo
    print("Testing log exporters...\n")

    # Console exporter (always available)
    console = get_exporter("console")
    print("Console Exporter:")
    console.export_metrics({"counters": {"test": 123}})
    console.export_errors([{"error_type": "TestError", "message": "Test error message"}])

    # Test other exporters (may fail if packages not installed)
    for exporter_type in ["prometheus", "sentry", "otlp"]:
        print(f"\n{exporter_type.capitalize()} Exporter:")
        exporter = get_exporter(exporter_type)
        if exporter and hasattr(exporter, "is_available") and exporter.is_available():
            print(f"  ✓ Available")
        else:
            print(f"  ✗ Not available (install required packages)")
