#!/usr/bin/env python3
"""
SAM Observability CLI

Command-line interface for observability features:
- console: Interactive diagnostic console
- logs: Query and filter logs
- metrics: View metrics summary
- dashboard: Show status dashboard
- export: Export diagnostic bundle
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from skills.sam_observe.scripts.sam_logger import SamLogger
    from skills.sam_observe.scripts.metrics_collector import MetricsCollector
    from skills.sam_observe.scripts.tracing_context import TracingContext
    from skills.sam_observe.scripts.error_tracker import ErrorTracker
    from skills.sam_observe.scripts.observability_manager import ObservabilityManager
    from skills.shared.observability import initialize, get_logger, get_error_tracker
except ImportError:
    # Try relative imports
    try:
        from .sam_logger import SamLogger
        from .metrics_collector import MetricsCollector
        from .tracing_context import TracingContext
        from .error_tracker import ErrorTracker
        from .observability_manager import ObservabilityManager
    except ImportError:
        print("Error: Could not import observability modules", file=sys.stderr)
        sys.exit(1)


def cmd_console(args) -> int:
    """Interactive diagnostic console."""
    print("SAM Observability - Interactive Console")
    print("=" * 50)

    if args.component:
        print(f"Component filter: {args.component}")

    # Show menu
    print("\nAvailable commands:")
    print("  logs [filter]    - Query logs")
    print("  metrics          - View metrics")
    print("  traces [id]      - View traces")
    print("  errors           - View errors")
    print("  status           - Show system status")
    print("  export [path]    - Export diagnostic bundle")
    print("  quit             - Exit console")

    # Interactive loop
    try:
        while True:
            try:
                cmd = input("\n> ").strip().split()
                if not cmd:
                    continue

                if cmd[0] in ("quit", "exit", "q"):
                    break

                elif cmd[0] == "logs":
                    _query_logs(cmd[1:], args)

                elif cmd[0] == "metrics":
                    _show_metrics(args)

                elif cmd[0] == "traces":
                    _show_traces(cmd[1:], args)

                elif cmd[0] == "errors":
                    _show_errors(args)

                elif cmd[0] == "status":
                    _show_status(args)

                elif cmd[0] == "export":
                    path = cmd[1] if len(cmd) > 1 else None
                    _export_bundle(path, args)

                else:
                    print(f"Unknown command: {cmd[0]}")

            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_logs(args) -> int:
    """Query logs directly."""
    return _query_logs([], args)


def _query_logs(extra_args, args) -> int:
    """Query and display logs."""
    log_file = Path(".sam/logs/sam.log")

    if not log_file.exists():
        print("No log file found. Run SAM operations first.")
        return 0

    # Read and parse logs
    entries = []
    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                # Skip non-JSON lines (from text format)
                continue

    # Apply filters
    if args.component:
        entries = [e for e in entries if e.get("component") == args.component]

    if args.level:
        level_map = {"error": "ERROR", "warning": "WARNING", "info": "INFO", "debug": "DEBUG"}
        target_level = level_map.get(args.level.lower(), args.level.upper())
        entries = [e for e in entries if e.get("level") == target_level]

    if args.feature_id:
        entries = [e for e in entries if e.get("feature_id") == args.feature_id]

    # Limit results
    if args.limit:
        entries = entries[-args.limit:]

    # Display
    if not entries:
        print("No matching log entries found.")
        return 0

    print(f"\nFound {len(entries)} log entries:\n")
    for entry in entries:
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "")
        component = entry.get("component", "")
        message = entry.get("message", "")

        # Format
        level_color = {
            "ERROR": "\033[31m",  # Red
            "WARNING": "\033[33m",  # Yellow
            "INFO": "\033[32m",  # Green
            "DEBUG": "\033[36m",  # Cyan
        }.get(level, "")

        reset = "\033[0m"

        print(f"{timestamp} {level_color}[{level}]{reset} {component}: {message}")

        if args.verbose and entry.get("context"):
            print(f"  Context: {entry['context']}")

    return 0


def cmd_metrics(args) -> int:
    """Show metrics summary."""
    return _show_metrics(args)


def _show_metrics(args) -> int:
    """Display metrics summary."""
    metrics_dir = Path(".sam/metrics")

    if not metrics_dir.exists():
        print("No metrics found. Run SAM operations first.")
        return 0

    print("\n=== Metrics Summary ===\n")

    # Counters
    counters_file = metrics_dir / "counters.json"
    if counters_file.exists():
        with open(counters_file, "r") as f:
            counters = json.load(f)

        print("Counters:")
        for component, metrics in counters.items():
            print(f"\n  {component}:")
            for metric_name, tagged_values in metrics.items():
                if isinstance(tagged_values, dict):
                    total = sum(tagged_values.values()) if tagged_values else 0
                    print(f"    {metric_name}: {total}")

    # Gauges
    gauges_file = metrics_dir / "gauges.json"
    if gauges_file.exists():
        with open(gauges_file, "r") as f:
            gauges = json.load(f)

        print("\nGauges:")
        for component, metrics in gauges.items():
            print(f"\n  {component}:")
            for metric_name, tagged_values in metrics.items():
                if isinstance(tagged_values, dict):
                    # Show first value
                    for tags, value in tagged_values.items():
                        print(f"    {metric_name}: {value}")
                        break

    # Histograms
    histograms_file = metrics_dir / "histograms.json"
    if histograms_file.exists():
        with open(histograms_file, "r") as f:
            histograms = json.load(f)

        print("\nHistograms (timing):")
        for component, metrics in histograms.items():
            print(f"\n  {component}:")
            for metric_name, summaries in metrics.items():
                if isinstance(summaries, dict):
                    for tags, summary in summaries.items():
                        if isinstance(summary, dict):
                            print(f"    {metric_name}:")
                            print(f"      count: {summary.get('count', 0)}")
                            print(f"      p50: {summary.get('p50', 0):.1f}ms")
                            print(f"      p95: {summary.get('p95', 0):.1f}ms")
                            print(f"      p99: {summary.get('p99', 0):.1f}ms")
                        break

    return 0


def cmd_dashboard(args) -> int:
    """Show status dashboard."""
    return _show_status(args)


def _show_status(args) -> int:
    """Display observability status."""
    print("\n=== SAM Observability Status ===\n")

    # System status
    try:
        manager = ObservabilityManager.get_instance()
        status = manager.get_status()

        print("Configuration:")
        print(f"  Logging: {'enabled' if status['config']['logging']['enabled'] else 'disabled'}")
        print(f"    Level: {status['config']['logging']['level']}")
        print(f"  Metrics: {'enabled' if status['config']['metrics']['enabled'] else 'disabled'}")
        print(f"  Tracing: {'enabled' if status['config']['tracing']['enabled'] else 'disabled'}")
        print(f"    Sample rate: {status['config']['tracing']['sample_rate']}")
        print(f"  Errors: {'enabled' if status['config']['errors']['enabled'] else 'disabled'}")

        print("\nActive Components:")
        print(f"  Loggers: {status['components']['loggers']}")
        print(f"  Metrics collectors: {status['components']['metrics_collectors']}")
        print(f"  Tracers: {status['components']['tracers']}")

        if "errors" in status:
            print(f"\nError Statistics:")
            print(f"  Total errors: {status['errors']['total_errors']}")
            print(f"  Unique errors: {status['errors']['unique_errors']}")
            print(f"  Groups: {status['errors']['total_groups']}")

        if "traces" in status:
            print(f"\nTrace Statistics:")
            print(f"  Active traces: {status['traces']['active_traces']}")

    except RuntimeError:
        print("Observability system not initialized.")
        print("Run SAM operations to initialize.")

    # File storage status
    print("\nStorage Status:")
    for name, path in [
        ("Logs", ".sam/logs"),
        ("Metrics", ".sam/metrics"),
        ("Traces", ".sam/traces"),
        ("Errors", ".sam/errors"),
    ]:
        p = Path(path)
        if p.exists():
            files = list(p.rglob("*"))
            size = sum(f.stat().st_size for f in files if f.is_file())
            print(f"  {name}: {len([f for f in files if f.is_file()])} files, {size / 1024:.1f} KB")
        else:
            print(f"  {name}: not created yet")

    return 0


def cmd_export(args) -> int:
    """Export diagnostic bundle."""
    return _export_bundle(args.output, args)


def _export_bundle(output_path, args) -> int:
    """Create diagnostic bundle."""
    try:
        manager = ObservabilityManager.get_instance()
    except RuntimeError:
        print("Observability system not initialized.")
        return 1

    print("Creating diagnostic bundle...")

    bundle_path = manager.create_diagnostic_bundle(
        output_path=Path(output_path) if output_path else None
    )

    print(f"Bundle created: {bundle_path}")

    # Show bundle contents
    import zipfile
    with zipfile.ZipFile(bundle_path, "r") as zf:
        print("\nBundle contents:")
        for name in zf.namelist():
            print(f"  {name}")

    return 0


def cmd_init(args) -> int:
    """Initialize observability for project."""
    print("Initializing SAM Observability...")

    # Initialize manager
    manager = initialize(args.config)

    print("✓ Observability system initialized")
    print(f"✓ Config: {args.config if args.config else 'defaults'}")
    print(f"✓ Logging: {'enabled' if manager.config.logging.enabled else 'disabled'}")
    print(f"✓ Metrics: {'enabled' if manager.config.metrics.enabled else 'disabled'}")
    print(f"✓ Tracing: {'enabled' if manager.config.tracing.enabled else 'disabled'}")
    print(f"✓ Errors: {'enabled' if manager.config.errors.enabled else 'disabled'}")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sam-observe",
        description="SAM Observability CLI",
    )

    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=None,
        help="Path to configuration file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # console command
    console_parser = subparsers.add_parser("console", help="Interactive diagnostic console")
    console_parser.add_argument("--component", help="Filter by component")

    # logs command
    logs_parser = subparsers.add_parser("logs", help="Query logs")
    logs_parser.add_argument("--component", help="Filter by component")
    logs_parser.add_argument("--level", help="Filter by level (DEBUG, INFO, WARNING, ERROR)")
    logs_parser.add_argument("--feature-id", help="Filter by feature ID")
    logs_parser.add_argument("--limit", type=int, help="Limit results")
    logs_parser.add_argument("--verbose", "-v", action="store_true", help="Show context")

    # metrics command
    metrics_parser = subparsers.add_parser("metrics", help="View metrics")

    # dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Show status dashboard")

    # export command
    export_parser = subparsers.add_parser("export", help="Export diagnostic bundle")
    export_parser.add_argument("--output", "-o", help="Output path")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize observability")
    init_parser.add_argument("--config", "-c", type=Path, help="Config file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Route to command handler
    handlers = {
        "console": cmd_console,
        "logs": cmd_logs,
        "metrics": cmd_metrics,
        "dashboard": cmd_dashboard,
        "export": cmd_export,
        "init": cmd_init,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
