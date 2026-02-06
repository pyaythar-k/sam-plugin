#!/usr/bin/env python3
"""
SAM Error Tracker - Capture, aggregate, and analyze errors.

Provides:
- Exception tracking with stack traces
- Error grouping by type and similarity
- Error frequency analysis
- Context preservation
- Error export to JSON
"""

import hashlib
import json
import sys
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


class ErrorSeverity(Enum):
    """Error severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorSummary:
    """Summary of an error occurrence."""

    error_id: str
    error_type: str
    message: str
    severity: str
    count: int
    first_seen: datetime
    last_seen: datetime
    stack_trace: str
    context: Dict[str, Any]
    group_id: str


@dataclass
class ErrorGroup:
    """Group of similar errors."""

    group_id: str
    error_type: str
    pattern: str
    count: int
    first_seen: datetime
    last_seen: datetime
    sample_errors: List[ErrorSummary]


class ErrorTracker:
    """
    Track, aggregate, and analyze errors.

    Thread-safe error tracking with grouping by similarity.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize error tracker.

        Args:
            storage_dir: Directory for error storage (defaults to .sam/errors/)
        """
        self.storage_dir = storage_dir or Path(".sam/errors")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self._errors: Dict[str, ErrorSummary] = {}
        self._groups: Dict[str, ErrorGroup] = {}
        self._lock = threading.RLock()

        # Load existing data
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing errors and groups from disk."""
        groups_file = self.storage_dir / "groups.json"
        if groups_file.exists():
            try:
                with open(groups_file, "r") as f:
                    groups_data = json.load(f)

                for group_id, group_data in groups_data.items():
                    self._groups[group_id] = ErrorGroup(
                        group_id=group_id,
                        error_type=group_data["error_type"],
                        pattern=group_data["pattern"],
                        count=group_data["count"],
                        first_seen=datetime.fromisoformat(group_data["first_seen"]),
                        last_seen=datetime.fromisoformat(group_data["last_seen"]),
                        sample_errors=[],
                    )
            except Exception as e:
                print(f"Warning: Failed to load error groups: {e}", file=sys.stderr)

    def _generate_error_id(self, error_type: str, message: str, stack_trace: str) -> str:
        """Generate unique error ID."""
        content = f"{error_type}:{message}:{stack_trace[:200]}"
        hash_obj = hashlib.md5(content.encode())
        return f"ERR_{hash_obj.hexdigest()[:12]}"

    def _generate_group_id(self, error_type: str, stack_pattern: str) -> str:
        """Generate group ID for similar errors."""
        content = f"{error_type}:{stack_pattern}"
        hash_obj = hashlib.md5(content.encode())
        return f"GRP_{hash_obj.hexdigest()[:12]}"

    def _get_stack_pattern(self, stack_trace: str) -> str:
        """Extract pattern from stack trace for grouping."""
        # Group by top-level function calls (first non-error line)
        lines = stack_trace.split("\n")
        for line in lines:
            if "File " in line and "line " in line:
                # Extract file and line
                parts = line.strip().split('"')
                if len(parts) >= 2:
                    return parts[1]  # File path
        return "unknown"

    def _save_error(self, error: ErrorSummary) -> None:
        """Save error to disk."""
        error_file = self.storage_dir / f"{error.error_id}.json"
        with open(error_file, "w") as f:
            error_dict = {
                **error.__dict__,
                "first_seen": error.first_seen.isoformat(),
                "last_seen": error.last_seen.isoformat(),
            }
            json.dump(error_dict, f, indent=2)

    def _save_groups(self) -> None:
        """Save error groups to disk."""
        groups_data = {}
        for group_id, group in self._groups.items():
            groups_data[group_id] = {
                "group_id": group.group_id,
                "error_type": group.error_type,
                "pattern": group.pattern,
                "count": group.count,
                "first_seen": group.first_seen.isoformat(),
                "last_seen": group.last_seen.isoformat(),
            }

        groups_file = self.storage_dir / "groups.json"
        with open(groups_file, "w") as f:
            json.dump(groups_data, f, indent=2, sort_keys=True)

    def track_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> str:
        """
        Track an exception.

        Args:
            exception: The exception to track
            context: Optional context dictionary
            severity: Error severity level

        Returns:
            Error ID
        """
        # Get exception details
        error_type = type(exception).__name__
        message = str(exception)
        stack_trace = "".join(traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__
        ))

        return self.track_error(
            message=message,
            error_type=error_type,
            stack_trace=stack_trace,
            context=context,
            severity=severity,
        )

    def track_error(
        self,
        message: str,
        error_type: str,
        stack_trace: str = "",
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> str:
        """
        Track an error.

        Args:
            message: Error message
            error_type: Type of error
            stack_trace: Stack trace (if available)
            context: Optional context dictionary
            severity: Error severity level

        Returns:
            Error ID
        """
        with self._lock:
            # Generate IDs
            error_id = self._generate_error_id(error_type, message, stack_trace)
            stack_pattern = self._get_stack_pattern(stack_trace)
            group_id = self._generate_group_id(error_type, stack_pattern)

            now = datetime.utcnow()

            # Update or create error
            if error_id in self._errors:
                error = self._errors[error_id]
                error.count += 1
                error.last_seen = now
                if context:
                    error.context.update(context)
            else:
                error = ErrorSummary(
                    error_id=error_id,
                    error_type=error_type,
                    message=message,
                    severity=severity.value,
                    count=1,
                    first_seen=now,
                    last_seen=now,
                    stack_trace=stack_trace,
                    context=context or {},
                    group_id=group_id,
                )
                self._errors[error_id] = error

            # Update or create group
            if group_id in self._groups:
                group = self._groups[group_id]
                group.count += 1
                group.last_seen = now
                if len(group.sample_errors) < 5:
                    group.sample_errors.append(error)
            else:
                group = ErrorGroup(
                    group_id=group_id,
                    error_type=error_type,
                    pattern=stack_pattern,
                    count=1,
                    first_seen=now,
                    last_seen=now,
                    sample_errors=[error],
                )
                self._groups[group_id] = group

            # Persist
            self._save_error(error)
            self._save_groups()

            return error_id

    def get_error(self, error_id: str) -> Optional[ErrorSummary]:
        """
        Get error by ID.

        Args:
            error_id: Error ID

        Returns:
            ErrorSummary or None
        """
        with self._lock:
            return self._errors.get(error_id)

    def get_error_group(self, group_id: str) -> Optional[ErrorGroup]:
        """
        Get error group by ID.

        Args:
            group_id: Group ID

        Returns:
            ErrorGroup or None
        """
        with self._lock:
            return self._groups.get(group_id)

    def get_error_groups(self) -> List[ErrorGroup]:
        """
        Get all error groups, sorted by frequency.

        Returns:
            List of ErrorGroup
        """
        with self._lock:
            return sorted(self._groups.values(), key=lambda g: g.count, reverse=True)

    def get_frequent_errors(self, limit: int = 10) -> List[ErrorSummary]:
        """
        Get most frequently occurring errors.

        Args:
            limit: Maximum number to return

        Returns:
            List of ErrorSummary
        """
        with self._lock:
            errors = sorted(self._errors.values(), key=lambda e: e.count, reverse=True)
            return errors[:limit]

    def get_recent_errors(self, limit: int = 10) -> List[ErrorSummary]:
        """
        Get most recent errors.

        Args:
            limit: Maximum number to return

        Returns:
            List of ErrorSummary
        """
        with self._lock:
            errors = sorted(
                self._errors.values(),
                key=lambda e: e.last_seen,
                reverse=True
            )
            return errors[:limit]

    def get_errors_by_type(self, error_type: str) -> List[ErrorSummary]:
        """
        Get all errors of a specific type.

        Args:
            error_type: Error type name

        Returns:
            List of ErrorSummary
        """
        with self._lock:
            return [e for e in self._errors.values() if e.error_type == error_type]

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get overall error statistics.

        Returns:
            Statistics dictionary
        """
        with self._lock:
            total_errors = sum(e.count for e in self._errors.values())
            unique_errors = len(self._errors)
            total_groups = len(self._groups)

            # Count by severity
            by_severity: Dict[str, int] = {}
            for error in self._errors.values():
                by_severity[error.severity] = by_severity.get(error.severity, 0) + error.count

            # Count by type
            by_type: Dict[str, int] = {}
            for error in self._errors.values():
                by_type[error.error_type] = by_type.get(error.error_type, 0) + error.count

            return {
                "total_errors": total_errors,
                "unique_errors": unique_errors,
                "total_groups": total_groups,
                "by_severity": by_severity,
                "by_type": dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
            }

    def export_errors(self) -> Dict[str, Any]:
        """
        Export all errors as dictionary.

        Returns:
            Dictionary with all errors and groups
        """
        with self._lock:
            return {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "stats": self.get_error_stats(),
                "errors": [
                    {
                        **e.__dict__,
                        "first_seen": e.first_seen.isoformat(),
                        "last_seen": e.last_seen.isoformat(),
                    }
                    for e in self._errors.values()
                ],
                "groups": [
                    {
                        **g.__dict__,
                        "first_seen": g.first_seen.isoformat(),
                        "last_seen": g.last_seen.isoformat(),
                        "sample_errors": [e.error_id for e in g.sample_errors],
                    }
                    for g in self._groups.values()
                ],
            }


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None
_tracker_lock = threading.Lock()


def get_error_tracker(storage_dir: Optional[Path] = None) -> ErrorTracker:
    """
    Get or create the global ErrorTracker instance.

    Args:
        storage_dir: Optional storage directory override

    Returns:
        ErrorTracker instance
    """
    global _error_tracker

    with _tracker_lock:
        if _error_tracker is None:
            _error_tracker = ErrorTracker(storage_dir)

        return _error_tracker


def track_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
) -> str:
    """
    Convenience function to track an exception.

    Args:
        exception: The exception to track
        context: Optional context dictionary
        severity: Error severity level

    Returns:
        Error ID
    """
    tracker = get_error_tracker()
    return tracker.track_exception(exception, context, severity)


def track_error(
    message: str,
    error_type: str,
    stack_trace: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Convenience function to track an error.

    Args:
        message: Error message
        error_type: Type of error
        stack_trace: Stack trace
        context: Optional context dictionary

    Returns:
        Error ID
    """
    tracker = get_error_tracker()
    return tracker.track_error(message, error_type, stack_trace, context)


if __name__ == "__main__":
    # Demo
    tracker = ErrorTracker()

    # Track some errors
    try:
        1 / 0
    except Exception as e:
        tracker.track_exception(e, context={"operation": "divide_test"})

    try:
        int("not a number")
    except Exception as e:
        tracker.track_exception(e, context={"operation": "parse_test"})

    try:
        [][0]
    except Exception as e:
        tracker.track_exception(e, context={"operation": "index_test"})

    # Get stats
    stats = tracker.get_error_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")

    # Get frequent errors
    frequent = tracker.get_frequent_errors()
    print(f"\nFrequent errors: {[e.error_type for e in frequent]}")

    # Get groups
    groups = tracker.get_error_groups()
    print(f"\nGroups: {len(groups)}")
    for group in groups[:3]:
        print(f"  {group.error_type}: {group.count} occurrences")
