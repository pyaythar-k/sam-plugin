#!/usr/bin/env python3
"""
SAM Metrics Collector - Track performance metrics and operation counts.

Provides:
- Timing measurements (histograms)
- Counters for event tracking
- Gauges for current values
- Percentile calculations (p50, p95, p99)
- Periodic persistence to disk
"""

import json
import math
import sys
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple


@dataclass
class MetricSummary:
    """Statistical summary of a metric."""

    count: int
    min: float
    max: float
    mean: float
    p50: float
    p95: float
    p99: float


@dataclass
class MetricValue:
    """Single metric value with tags and timestamp."""

    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """
    Collect and aggregate performance metrics.

    Thread-safe metrics collection with in-memory aggregation
    and periodic persistence to disk.
    """

    def __init__(self, component: str, storage_dir: Optional[Path] = None):
        """
        Initialize metrics collector.

        Args:
            component: Component name (e.g., "sam-specs")
            storage_dir: Directory for metrics storage (defaults to .sam/metrics/)
        """
        self.component = component
        self.storage_dir = storage_dir or Path(".sam/metrics")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self._counters: Dict[str, Dict[Tuple, int]] = defaultdict(lambda: defaultdict(int))
        self._gauges: Dict[str, Dict[Tuple, float]] = defaultdict(dict)
        self._histograms: Dict[str, Dict[Tuple, List[float]]] = defaultdict(lambda: defaultdict(list))

        self._lock = threading.RLock()
        self._dirty = False
        self._last_flush = time.time()

    def _make_tags_key(self, tags: Optional[Dict[str, str]]) -> Tuple:
        """Convert tags dict to hashable tuple."""
        if not tags:
            return ()
        return tuple(sorted(tags.items()))

    def increment(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.

        Args:
            metric_name: Name of the counter
            value: Amount to increment (default: 1)
            tags: Optional tags for grouping
        """
        with self._lock:
            tags_key = self._make_tags_key(tags)
            self._counters[metric_name][tags_key] += value
            self._dirty = True

    def decrement(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Decrement a counter metric.

        Args:
            metric_name: Name of the counter
            value: Amount to decrement (default: 1)
            tags: Optional tags for grouping
        """
        self.increment(metric_name, -value, tags)

    def gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric value.

        Args:
            metric_name: Name of the gauge
            value: Current value
            tags: Optional tags for grouping
        """
        with self._lock:
            tags_key = self._make_tags_key(tags)
            self._gauges[metric_name][tags_key] = value
            self._dirty = True

    def histogram(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a value in a histogram (for timing distributions).

        Args:
            metric_name: Name of the histogram
            value: Value to record
            tags: Optional tags for grouping
        """
        with self._lock:
            tags_key = self._make_tags_key(tags)
            self._histograms[metric_name][tags_key].append(value)
            self._dirty = True

    @contextmanager
    def start_timer(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> Iterator[None]:
        """
        Context manager for timing operations.

        Args:
            metric_name: Name for the timing metric
            tags: Optional tags

        Yields:
            None

        Example:
            with metrics.start_timer("operation_duration"):
                do_work()
        """
        start = time.time()

        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            self.histogram(metric_name, duration_ms, tags)

    def get_counter(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """
        Get current counter value.

        Args:
            metric_name: Name of the counter
            tags: Optional tags

        Returns:
            Current counter value
        """
        with self._lock:
            tags_key = self._make_tags_key(tags)
            return self._counters.get(metric_name, {}).get(tags_key, 0)

    def get_gauge(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """
        Get current gauge value.

        Args:
            metric_name: Name of the gauge
            tags: Optional tags

        Returns:
            Current gauge value or None if not set
        """
        with self._lock:
            tags_key = self._make_tags_key(tags)
            return self._gauges.get(metric_name, {}).get(tags_key)

    def get_summary(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> Optional[MetricSummary]:
        """
        Get statistical summary for a histogram.

        Args:
            metric_name: Name of the histogram
            tags: Optional tags

        Returns:
            MetricSummary or None if no data
        """
        with self._lock:
            tags_key = self._make_tags_key(tags)
            values = self._histograms.get(metric_name, {}).get(tags_key, [])

            if not values:
                return None

            sorted_values = sorted(values)
            count = len(sorted_values)

            return MetricSummary(
                count=count,
                min=sorted_values[0],
                max=sorted_values[-1],
                mean=sum(sorted_values) / count,
                p50=sorted_values[int(count * 0.5)],
                p95=sorted_values[int(count * 0.95)] if count >= 20 else sorted_values[-1],
                p99=sorted_values[int(count * 0.99)] if count >= 100 else sorted_values[-1],
            )

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics as dictionary.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            export = {
                "component": self.component,
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "counters": {},
                "gauges": {},
                "histograms": {},
            }

            # Export counters
            for name, tagged_counters in self._counters.items():
                export["counters"][name] = {}
                for tags_key, value in tagged_counters.items():
                    tags = dict(tags_key) if tags_key else {}
                    tag_str = json.dumps(tags, sort_keys=True)
                    export["counters"][name][tag_str] = value

            # Export gauges
            for name, tagged_gauges in self._gauges.items():
                export["gauges"][name] = {}
                for tags_key, value in tagged_gauges.items():
                    tags = dict(tags_key) if tags_key else {}
                    tag_str = json.dumps(tags, sort_keys=True)
                    export["gauges"][name][tag_str] = value

            # Export histogram summaries
            for name, tagged_histograms in self._histograms.items():
                export["histograms"][name] = {}
                for tags_key, values in tagged_histograms.items():
                    tags = dict(tags_key) if tags_key else {}
                    tag_str = json.dumps(tags, sort_keys=True)
                    summary = self.get_summary(name, tags)
                    if summary:
                        export["histograms"][name][tag_str] = {
                            "count": summary.count,
                            "min": summary.min,
                            "max": summary.max,
                            "mean": summary.mean,
                            "p50": summary.p50,
                            "p95": summary.p95,
                            "p99": summary.p99,
                        }

            return export

    def flush(self, force: bool = False) -> None:
        """
        Flush metrics to disk.

        Args:
            force: Force flush even if not dirty
        """
        with self._lock:
            if not self._dirty and not force:
                return

            export = self.export_metrics()

            # Write to separate files by metric type
            counters_file = self.storage_dir / "counters.json"
            gauges_file = self.storage_dir / "gauges.json"
            histograms_file = self.storage_dir / "histograms.json"

            # Load existing and merge
            for file_path, metric_type in [
                (counters_file, "counters"),
                (gauges_file, "gauges"),
                (histograms_file, "histograms"),
            ]:
                existing = {}
                if file_path.exists():
                    with open(file_path, "r") as f:
                        existing = json.load(f)

                # Update with current data
                if self.component not in existing:
                    existing[self.component] = {}

                existing[self.component].update(export[metric_type])

                # Write back
                with open(file_path, "w") as f:
                    json.dump(existing, f, indent=2, sort_keys=True)

            self._dirty = False
            self._last_flush = time.time()

    def reset(self) -> None:
        """Reset all metrics (clear in-memory storage)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._dirty = True


# Global metrics collector cache
_metrics_cache: Dict[str, MetricsCollector] = {}
_cache_lock = threading.Lock()


def get_metrics(component: str, storage_dir: Optional[Path] = None) -> MetricsCollector:
    """
    Get or create a MetricsCollector instance.

    Args:
        component: Component name (e.g., "sam-specs")
        storage_dir: Optional storage directory override

    Returns:
        MetricsCollector instance
    """
    with _cache_lock:
        if component not in _metrics_cache:
            _metrics_cache[component] = MetricsCollector(component, storage_dir)

        return _metrics_cache[component]


def flush_all_metrics() -> None:
    """Flush all metrics collectors to disk."""
    with _cache_lock:
        for collector in _metrics_cache.values():
            collector.flush()


def timed(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """
    Decorator to time function execution.

    Args:
        metric_name: Name for the timing metric
        tags: Optional tags

    Returns:
        Decorator function

    Example:
        @timed("spec_parse_duration")
        def parse_spec(feature_dir):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get component from function's module
            module = func.__module__
            component = module.split(".")[-1] if "." in module else "unknown"

            metrics = get_metrics(component)
            with metrics.start_timer(metric_name, tags):
                return func(*args, **kwargs)

        return wrapper
    return decorator


if __name__ == "__main__":
    # Demo
    collector = MetricsCollector("sam-specs")

    # Counters
    collector.increment("tasks_completed")
    collector.increment("tasks_completed", tags={"status": "success"})
    collector.increment("tasks_completed", tags={"status": "failed"})

    # Gauges
    collector.gauge("active_tasks", 5)
    collector.gauge("memory_usage_mb", 234.5)

    # Histograms
    for duration in [100, 150, 200, 250, 300, 1000]:
        collector.histogram("task_duration_ms", duration)

    # Get summary
    summary = collector.get_summary("task_duration_ms")
    print(f"Duration summary: {summary}")

    # Timer context manager
    with collector.start_timer("demo_operation"):
        time.sleep(0.1)

    # Export
    export = collector.export_metrics()
    print(json.dumps(export, indent=2))

    # Flush
    collector.flush()
