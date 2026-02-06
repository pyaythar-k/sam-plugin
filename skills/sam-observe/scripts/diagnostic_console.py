#!/usr/bin/env python3
"""
SAM Diagnostic Console - Interactive inspection tool.

Provides interactive console for querying logs, metrics, traces, and errors.
"""

import json
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from skills.sam_observe.scripts.sam_logger import SamLogger
    from skills.sam_observe.scripts.metrics_collector import MetricsCollector, MetricSummary
    from skills.sam_observe.scripts.tracing_context import TracingContext, Trace
    from skills.sam_observe.scripts.error_tracker import ErrorTracker, ErrorSummary
    from skills.sam_observe.scripts.observability_manager import ObservabilityManager
except ImportError:
    from sam_logger import SamLogger
    from metrics_collector import MetricsCollector, MetricSummary
    from tracing_context import TracingContext, Trace
    from error_tracker import ErrorTracker, ErrorSummary
    from observability_manager import ObservabilityManager


class LogFilter:
    """Filter for log queries."""

    def __init__(
        self,
        component: Optional[str] = None,
        level: Optional[str] = None,
        feature_id: Optional[str] = None,
        task_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        message_contains: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        self.component = component
        self.level = level
        self.feature_id = feature_id
        self.task_id = task_id
        self.trace_id = trace_id
        self.message_contains = message_contains
        self.start_time = start_time
        self.end_time = end_time

    def matches(self, entry: Dict[str, Any]) -> bool:
        """Check if log entry matches filter."""
        if self.component and entry.get("component") != self.component:
            return False

        if self.level and entry.get("level") != self.level.upper():
            return False

        if self.feature_id and entry.get("feature_id") != self.feature_id:
            return False

        if self.task_id and entry.get("task_id") != self.task_id:
            return False

        if self.trace_id and entry.get("trace_id") != self.trace_id:
            return False

        if self.message_contains and self.message_contains.lower() not in entry.get("message", "").lower():
            return False

        if self.start_time or self.end_time:
            try:
                entry_time = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", ""))
                if self.start_time and entry_time < self.start_time:
                    return False
                if self.end_time and entry_time > self.end_time:
                    return False
            except (ValueError, TypeError):
                pass

        return True


class MetricData:
    """Container for metric data points."""

    def __init__(self, name: str, values: List[float], timestamps: List[float], tags: Optional[Dict] = None):
        self.name = name
        self.values = values
        self.timestamps = timestamps
        self.tags = tags or {}

    def get_summary(self) -> MetricSummary:
        """Get statistical summary."""
        if not self.values:
            return None

        sorted_values = sorted(self.values)
        count = len(sorted_values)

        from skills.sam_observe.scripts.metrics_collector import MetricSummary
        return MetricSummary(
            count=count,
            min=sorted_values[0],
            max=sorted_values[-1],
            mean=sum(sorted_values) / count,
            p50=sorted_values[int(count * 0.5)],
            p95=sorted_values[int(count * 0.95)] if count >= 20 else sorted_values[-1],
            p99=sorted_values[int(count * 0.99)] if count >= 100 else sorted_values[-1],
        )


class DashboardView:
    """Dashboard view of observability data."""

    def __init__(
        self,
        log_entries: List[Dict],
        metrics_summary: Dict[str, Any],
        recent_errors: List[ErrorSummary],
        recent_traces: List[Trace],
    ):
        self.log_entries = log_entries
        self.metrics_summary = metrics_summary
        self.recent_errors = recent_errors
        self.recent_traces = recent_traces

    def display(self) -> str:
        """Generate dashboard display."""
        lines = []
        lines.append("=" * 80)
        lines.append("SAM OBSERVABILITY DASHBOARD")
        lines.append("=" * 80)
        lines.append("")

        # Recent logs
        lines.append("Recent Logs:")
        lines.append("-" * 40)
        for entry in self.log_entries[:10]:
            timestamp = entry.get("timestamp", "")[:19]
            level = entry.get("level", "")
            component = entry.get("component", "")
            message = entry.get("message", "")[:60]

            lines.append(f"  {timestamp} [{level}] {component}: {message}")

        lines.append("")

        # Metrics summary
        lines.append("Metrics Summary:")
        lines.append("-" * 40)
        for component, metrics in self.metrics_summary.items():
            lines.append(f"  {component}:")
            for metric_name, value in metrics.items():
                lines.append(f"    {metric_name}: {value}")

        lines.append("")

        # Recent errors
        lines.append(f"Recent Errors (last {len(self.recent_errors)}):")
        lines.append("-" * 40)
        for error in self.recent_errors[:10]:
            lines.append(f"  [{error.error_type}] {error.message[:60]}")
            lines.append(f"    Count: {error.count} | Last: {error.last_seen.strftime('%Y-%m-%d %H:%M')}")

        lines.append("")

        # Recent traces
        lines.append(f"Recent Traces (last {len(self.recent_traces)}):")
        lines.append("-" * 40)
        for trace in self.recent_traces[:10]:
            duration = trace.end_time - trace.start_time if trace.end_time else 0
            lines.append(f"  {trace.trace_id}: {trace.root_operation}")
            lines.append(f"    Spans: {len(trace.spans)} | Duration: {duration:.2f}s")

        return "\n".join(lines)


class DiagnosticConsole:
    """
    Interactive console for inspecting observability data.

    Provides commands for querying logs, metrics, traces, and errors.
    """

    def __init__(self, log_dir: Optional[Path] = None, metrics_dir: Optional[Path] = None):
        """
        Initialize diagnostic console.

        Args:
            log_dir: Directory for log files
            metrics_dir: Directory for metrics files
        """
        self.log_dir = log_dir or Path(".sam/logs")
        self.metrics_dir = metrics_dir or Path(".sam/metrics")
        self.running = False

    def query_logs(
        self,
        filter: LogFilter,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query logs with optional filter.

        Args:
            filter: LogFilter to apply
            limit: Maximum number of entries to return

        Returns:
            List of log entry dictionaries
        """
        log_file = self.log_dir / "sam.log"

        if not log_file.exists():
            return []

        entries = []
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    if filter.matches(entry):
                        entries.append(entry)
                        if len(entries) >= limit:
                            break
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    continue

        return entries

    def query_metrics(
        self,
        metric_names: Optional[List[str]] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
    ) -> List[MetricData]:
        """
        Query metrics data.

        Args:
            metric_names: List of metric names to query (None = all)
            time_range: Optional (start, end) datetime tuple

        Returns:
            List of MetricData
        """
        results = []

        # Query histograms
        histograms_file = self.metrics_dir / "histograms.json"
        if histograms_file.exists():
            with open(histograms_file, "r") as f:
                histograms = json.load(f)

            for component, metrics in histograms.items():
                for metric_name, summaries in metrics.items():
                    if metric_names and metric_name not in metric_names:
                        continue

                    for tags_str, summary in summaries.items():
                        if isinstance(summary, dict):
                            results.append(MetricData(
                                name=f"{component}.{metric_name}",
                                values=[summary.get("mean", 0)],
                                timestamps=[],
                                tags=json.loads(tags_str) if tags_str else {},
                            ))

        return results

    def query_traces(self, trace_id: Optional[str] = None) -> List[Trace]:
        """
        Query traces.

        Args:
            trace_id: Specific trace ID to query (None = all recent)

        Returns:
            List of Trace objects
        """
        traces_dir = Path(".sam/traces")

        if not traces_dir.exists():
            return []

        traces = []

        if trace_id:
            # Load specific trace
            trace_file = traces_dir / f"{trace_id}.json"
            if trace_file.exists():
                with open(trace_file, "r") as f:
                    trace_dict = json.load(f)

                trace = Trace(
                    trace_id=trace_dict["trace_id"],
                    root_operation=trace_dict["root_operation"],
                )
                traces.append(trace)
        else:
            # Load all traces
            for trace_file in traces_dir.glob("*.json"):
                try:
                    with open(trace_file, "r") as f:
                        trace_dict = json.load(f)

                    trace = Trace(
                        trace_id=trace_dict["trace_id"],
                        root_operation=trace_dict["root_operation"],
                    )
                    traces.append(trace)
                except (json.JSONDecodeError, KeyError):
                    continue

        # Sort by time (most recent first)
        traces.sort(key=lambda t: t.start_time, reverse=True)

        return traces

    def show_dashboard(self) -> DashboardView:
        """
        Generate dashboard view.

        Returns:
            DashboardView instance
        """
        # Get recent logs
        log_filter = LogFilter()
        log_entries = self.query_logs(log_filter, limit=20)

        # Get metrics summary
        metrics_summary = self._get_metrics_summary()

        # Get recent errors
        error_tracker = None
        try:
            error_tracker = ObservabilityManager.get_instance().get_error_tracker()
            recent_errors = error_tracker.get_recent_errors(limit=10)
        except RuntimeError:
            recent_errors = []

        # Get recent traces
        recent_traces = self.query_traces()[:10]

        return DashboardView(
            log_entries=log_entries,
            metrics_summary=metrics_summary,
            recent_errors=recent_errors,
            recent_traces=recent_traces,
        )

    def export_diagnostic_bundle(self, output_path: Path) -> None:
        """
        Export diagnostic bundle.

        Args:
            output_path: Path for output zip file
        """
        try:
            manager = ObservabilityManager.get_instance()
            manager.create_diagnostic_bundle(output_path)
        except RuntimeError:
            print("Observability system not initialized.", file=sys.stderr)

    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for dashboard."""
        summary = {}

        # Load counters
        counters_file = self.metrics_dir / "counters.json"
        if counters_file.exists():
            with open(counters_file, "r") as f:
                counters = json.load(f)

            for component, metrics in counters.items():
                summary[component] = {}
                for metric_name, tagged_values in metrics.items():
                    if isinstance(tagged_values, dict):
                        total = sum(tagged_values.values())
                        summary[component][metric_name] = total

        return summary

    def interactive(self) -> None:
        """Start interactive console loop."""
        self.running = True

        print("\n" + "=" * 60)
        print("SAM DIAGNOSTIC CONSOLE")
        print("=" * 60)
        print("\nCommands:")
        print("  logs [filter]      - Query logs (filters: --component, --level, --limit)")
        print("  metrics            - Show metrics summary")
        print("  traces [id]        - Show traces")
        print("  errors             - Show recent errors")
        print("  dashboard          - Show full dashboard")
        print("  export [path]      - Export diagnostic bundle")
        print("  help               - Show this help")
        print("  quit               - Exit console")
        print("\n")

        while self.running:
            try:
                cmd_input = input("diagnostic> ").strip()

                if not cmd_input:
                    continue

                parts = cmd_input.split()
                command = parts[0].lower()
                args = parts[1:]

                if command in ("quit", "exit", "q"):
                    print("Goodbye!")
                    break

                elif command == "help":
                    self._show_help()

                elif command == "logs":
                    self._cmd_logs(args)

                elif command == "metrics":
                    self._cmd_metrics(args)

                elif command == "traces":
                    self._cmd_traces(args)

                elif command == "errors":
                    self._cmd_errors(args)

                elif command == "dashboard":
                    self._cmd_dashboard(args)

                elif command == "export":
                    self._cmd_export(args)

                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")

            except EOFError:
                print("\nGoodbye!")
                break
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                print(f"Error: {e}")

    def _show_help(self) -> None:
        """Show help text."""
        print("\nAvailable Commands:")
        print("\n  logs [options]")
        print("    Query and display log entries")
        print("    Options:")
        print("      --component NAME    Filter by component")
        print("      --level LVL         Filter by level (DEBUG, INFO, WARNING, ERROR)")
        print("      --limit N           Limit results")
        print("\n  metrics")
        print("    Show metrics summary")
        print("\n  traces [id]")
        print("    Show traces (optional specific trace ID)")
        print("\n  errors")
        print("    Show recent errors")
        print("\n  dashboard")
        print("    Show full dashboard view")
        print("\n  export [path]")
        print("    Export diagnostic bundle")
        print("\n  quit")
        print("    Exit console\n")

    def _cmd_logs(self, args: List[str]) -> None:
        """Handle logs command."""
        component = None
        level = None
        limit = 20

        i = 0
        while i < len(args):
            if args[i] == "--component" and i + 1 < len(args):
                component = args[i + 1]
                i += 2
            elif args[i] == "--level" and i + 1 < len(args):
                level = args[i + 1]
                i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1])
                i += 2
            else:
                i += 1

        filter = LogFilter(component=component, level=level)
        entries = self.query_logs(filter, limit)

        if not entries:
            print("No matching log entries found.")
            return

        print(f"\nFound {len(entries)} log entries:\n")
        for entry in entries:
            timestamp = entry.get("timestamp", "")[:19]
            lvl = entry.get("level", "")
            comp = entry.get("component", "")
            msg = entry.get("message", "")

            print(f"  {timestamp} [{lvl}] {comp}: {msg}")

    def _cmd_metrics(self, args: List[str]) -> None:
        """Handle metrics command."""
        data = self.query_metrics()

        if not data:
            print("No metrics found.")
            return

        print("\nMetrics:\n")
        for metric in data:
            print(f"  {metric.name}")
            if metric.values:
                summary = metric.get_summary()
                if summary:
                    print(f"    Count: {summary.count}")
                    print(f"    Mean: {summary.mean:.2f}")
                    print(f"    P95: {summary.p95:.2f}")

    def _cmd_traces(self, args: List[str]) -> None:
        """Handle traces command."""
        trace_id = args[0] if args else None

        traces = self.query_traces(trace_id)

        if not traces:
            print("No traces found.")
            return

        print(f"\nFound {len(traces)} traces:\n")
        for trace in traces:
            duration = (trace.end_time - trace.start_time) if trace.end_time else 0
            print(f"  {trace.trace_id}: {trace.root_operation}")
            print(f"    Spans: {len(trace.spans)} | Duration: {duration:.2f}s")

    def _cmd_errors(self, args: List[str]) -> None:
        """Handle errors command."""
        try:
            tracker = ObservabilityManager.get_instance().get_error_tracker()
            errors = tracker.get_recent_errors(limit=20)

            if not errors:
                print("No errors found.")
                return

            print(f"\nRecent errors:\n")
            for error in errors:
                print(f"  [{error.error_type}] {error.message[:60]}")
                print(f"    Count: {error.count} | Last: {error.last_seen.strftime('%Y-%m-%d %H:%M')}")

        except RuntimeError:
            print("Observability system not initialized.")

    def _cmd_dashboard(self, args: List[str]) -> None:
        """Handle dashboard command."""
        dashboard = self.show_dashboard()
        print("\n" + dashboard.display())

    def _cmd_export(self, args: List[str]) -> None:
        """Handle export command."""
        output = args[0] if args else None

        if output:
            self.export_diagnostic_bundle(Path(output))
        else:
            self.export_diagnostic_bundle(Path(".sam/diagnostic_bundle.zip"))


def main() -> int:
    """Main entry point."""
    console = DiagnosticConsole()
    console.interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
