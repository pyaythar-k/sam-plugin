#!/usr/bin/env python3
"""
SAM Tracing Context - Distributed tracing across SAM skills.

Provides:
- Trace ID generation and propagation
- Span creation with parent-child relationships
- Event tracking within spans
- Trace export to JSON
"""

import json
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, OrderedDict


# Thread-local storage for current span
_current_span = threading.local()


@dataclass
class SpanEvent:
    """Event within a span."""

    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """
    Trace span representing a unit of work.

    Captures timing, attributes, and events for a single operation.
    """

    operation_name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    status: str = "ok"  # ok, error, internal_error

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        self.attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        """Set multiple attributes."""
        self.attributes.update(attributes)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        event = SpanEvent(
            name=name,
            timestamp=time.time(),
            attributes=attributes or {},
        )
        self.events.append(event)

    def end(self, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        End the span.

        Args:
            attributes: Optional attributes to add before ending
        """
        if self.end_time is not None:
            return  # Already ended

        self.end_time = time.time()
        if attributes:
            self.attributes.update(attributes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        duration_ms = None
        if self.end_time:
            duration_ms = round((self.end_time - self.start_time) * 1000, 2)

        return {
            "operation": self.operation_name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_ms": duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": [
                {
                    "name": e.name,
                    "timestamp": datetime.fromtimestamp(e.timestamp).isoformat(),
                    "attributes": e.attributes,
                }
                for e in self.events
            ],
        }

    def get_duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time:
            return round((self.end_time - self.start_time) * 1000, 2)
        return None


@dataclass
class Trace:
    """
    Complete trace containing multiple spans.

    Represents a full workflow execution across SAM skills.
    """

    trace_id: str
    root_operation: str
    spans: List[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: Span) -> None:
        """Add a span to the trace."""
        self.spans.append(span)

    def end(self) -> None:
        """End the trace."""
        self.end_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        duration_ms = None
        if self.end_time:
            duration_ms = round((self.end_time - self.start_time) * 1000, 2)

        return {
            "trace_id": self.trace_id,
            "root_operation": self.root_operation,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_ms": duration_ms,
            "span_count": len(self.spans),
            "attributes": self.attributes,
            "spans": [span.to_dict() for span in self.spans],
        }

    def get_span_by_id(self, span_id: str) -> Optional[Span]:
        """Get a span by its ID."""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None

    def get_span_hierarchy(self) -> List[Dict[str, Any]]:
        """
        Get spans organized in parent-child hierarchy.

        Returns:
            List of root spans with nested children
        """
        span_map = {s.span_id: s for s in self.spans}
        roots = []
        children_map: Dict[str, List[Dict]] = {s.span_id: [] for s in self.spans}

        # Build children map
        for span in self.spans:
            if span.parent_id and span.parent_id in children_map:
                children_map[span.parent_id].append(span.to_dict())
            else:
                roots.append(span.to_dict())

        # Add children to parent dicts
        def add_children(span_dict: Dict) -> None:
            span_id = span_dict.get("span_id")
            if span_id in children_map:
                span_dict["children"] = children_map[span_id]
                for child in span_dict["children"]:
                    add_children(child)

        for root in roots:
            add_children(root)

        return roots


class TracingContext:
    """
    Manage distributed tracing context across SAM skills.

    Provides thread-local span management and trace export.
    """

    def __init__(self, component: str, storage_dir: Optional[Path] = None):
        """
        Initialize tracing context.

        Args:
            component: Component name
            storage_dir: Directory for trace storage (defaults to .sam/traces/)
        """
        self.component = component
        self.storage_dir = storage_dir or Path(".sam/traces")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Active traces
        self._traces: Dict[str, Trace] = {}
        self._lock = threading.RLock()

    def start_trace(self, operation_name: str, trace_id: Optional[str] = None) -> tuple[str, Span]:
        """
        Start a new trace.

        Args:
            operation_name: Name of the root operation
            trace_id: Optional trace ID (auto-generated if not provided)

        Returns:
            Tuple of (trace_id, root_span)
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())[:8]

        span_id = str(uuid.uuid4())[:8]
        root_span = Span(
            operation_name=operation_name,
            trace_id=trace_id,
            span_id=span_id,
        )

        trace = Trace(
            trace_id=trace_id,
            root_operation=operation_name,
        )
        trace.add_span(root_span)

        with self._lock:
            self._traces[trace_id] = trace

        # Set as current span
        self._set_current_span(root_span)

        return trace_id, root_span

    def start_span(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent: Optional[Span] = None,
    ) -> Span:
        """
        Start a new span.

        Args:
            operation_name: Name of the operation
            trace_id: Trace ID (uses current trace if not provided)
            parent: Parent span (uses current span if not provided)

        Returns:
            New span
        """
        current_span = self._get_current_span()

        if not trace_id and current_span:
            trace_id = current_span.trace_id
        elif not trace_id:
            trace_id = str(uuid.uuid4())[:8]
            # Start new trace
            return self.start_span(operation_name, trace_id, parent)[1]

        parent_id = parent.span_id if parent else (current_span.span_id if current_span else None)

        span = Span(
            operation_name=operation_name,
            trace_id=trace_id,
            parent_id=parent_id,
        )

        # Add to trace
        with self._lock:
            if trace_id in self._traces:
                self._traces[trace_id].add_span(span)
            else:
                # Create new trace
                trace = Trace(trace_id=trace_id, root_operation=operation_name)
                trace.add_span(span)
                self._traces[trace_id] = trace

        # Set as current span
        self._set_current_span(span)

        return span

    def end_span(self, span: Span, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        End a span.

        Args:
            span: Span to end
            attributes: Optional attributes to add
        """
        span.end(attributes)

        # Update trace end time if this was the root span
        with self._lock:
            if span.trace_id in self._traces:
                trace = self._traces[span.trace_id]
                # Check if this is the root span
                if trace.spans and trace.spans[0].span_id == span.span_id:
                    trace.end()

        # Clear current span if it's this one
        if self._get_current_span() == span:
            parent_id = span.parent_id
            if parent_id:
                # Set parent as current
                for s in self._traces.get(span.trace_id, Trace(span.trace_id, "")).spans:
                    if s.span_id == parent_id:
                        self._set_current_span(s)
                        break
            else:
                self._clear_current_span()

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Get a trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace or None if not found
        """
        with self._lock:
            return self._traces.get(trace_id)

    def export_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a trace as dictionary.

        Args:
            trace_id: Trace ID

        Returns:
            Trace dictionary or None
        """
        trace = self.get_trace(trace_id)
        if trace:
            return trace.to_dict()
        return None

    def save_trace(self, trace_id: str) -> Optional[Path]:
        """
        Save a trace to disk.

        Args:
            trace_id: Trace ID

        Returns:
            Path to saved file or None
        """
        trace_dict = self.export_trace(trace_id)
        if not trace_dict:
            return None

        file_path = self.storage_dir / f"{trace_id}.json"
        with open(file_path, "w") as f:
            json.dump(trace_dict, f, indent=2)

        return file_path

    def save_all_traces(self) -> List[Path]:
        """Save all traces to disk."""
        paths = []
        with self._lock:
            for trace_id in list(self._traces.keys()):
                path = self.save_trace(trace_id)
                if path:
                    paths.append(path)
        return paths

    @staticmethod
    def _get_current_span() -> Optional[Span]:
        """Get current span from thread-local storage."""
        return getattr(_current_span, "value", None)

    @staticmethod
    def _set_current_span(span: Span) -> None:
        """Set current span in thread-local storage."""
        _current_span.value = span

    @staticmethod
    def _clear_current_span() -> None:
        """Clear current span from thread-local storage."""
        _current_span.value = None

    @staticmethod
    def get_current_trace_id() -> Optional[str]:
        """Get current trace ID."""
        span = TracingContext._get_current_span()
        return span.trace_id if span else None

    @staticmethod
    def get_current_span_id() -> Optional[str]:
        """Get current span ID."""
        span = TracingContext._get_current_span()
        return span.span_id if span else None

    @contextmanager
    def span(self, operation_name: str, **attributes):
        """
        Context manager for automatic span creation.

        Args:
            operation_name: Name of the operation
            **attributes: Attributes to add to span

        Yields:
            Span

        Example:
            with tracer.span("parse_spec"):
                parse_spec()
        """
        span = self.start_span(operation_name)
        span.set_attributes(attributes)

        try:
            yield span
        except Exception as e:
            span.status = "error"
            span.set_attribute("error", str(e))
            raise
        finally:
            self.end_span(span)


# Global tracer cache
_tracer_cache: Dict[str, TracingContext] = {}
_cache_lock = threading.Lock()


def get_tracer(component: str, storage_dir: Optional[Path] = None) -> TracingContext:
    """
    Get or create a TracingContext instance.

    Args:
        component: Component name
        storage_dir: Optional storage directory override

    Returns:
        TracingContext instance
    """
    with _cache_lock:
        if component not in _tracer_cache:
            _tracer_cache[component] = TracingContext(component, storage_dir)

        return _tracer_cache[component]


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID from any tracer."""
    return TracingContext.get_current_trace_id()


def get_current_span_id() -> Optional[str]:
    """Get current span ID from any tracer."""
    return TracingContext.get_current_span_id()


if __name__ == "__main__":
    # Demo
    tracer = TracingContext("sam-specs")

    # Start a trace
    trace_id, root_span = tracer.start_trace("generate_user_stories")
    root_span.set_attribute("feature", "user_auth")

    # Add child spans
    with tracer.span("read_feature_doc") as span:
        span.add_event("file_opened", {"file": "FEATURE.md"})

    with tracer.span("generate_stories") as span:
        span.set_attribute("stories_generated", 5)

        with tracer.span("verify_coverage") as span:
            span.set_attribute("coverage", "100%")

    # End root span
    tracer.end_span(root_span)

    # Export
    trace_dict = tracer.export_trace(trace_id)
    print(json.dumps(trace_dict, indent=2))

    # Save
    path = tracer.save_trace(trace_id)
    print(f"Saved trace to: {path}")
