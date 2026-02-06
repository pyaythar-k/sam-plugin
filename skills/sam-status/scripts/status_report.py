#!/usr/bin/env python3
"""
status_report.py - Generate SAM feature status report with observability integration

Scans all features in .sam/ and generates a comprehensive status report.
Enhanced with real-time metrics and performance data from observability system.

Usage:
    python3 skills/sam-status/scripts/status_report.py [feature_id]
    python3 skills/sam-status/scripts/status_report.py --all
    python3 skills/sam-status/scripts/status_report.py --metrics
    python3 skills/sam-status/scripts/status_report.py --watch
"""

import sys
import re
import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, TypedDict, Optional

# Observability integration
try:
    from skills.shared.observability import (
        get_logger,
        get_metrics,
        initialize,
    )
    from skills.sam_observe.scripts.observability_manager import ObservabilityManager
    HAS_OBSERVABILITY = True
except ImportError:
    HAS_OBSERVABILITY = False


class FeatureStatus(TypedDict):
    """Type dictionary for feature status structure."""
    id: str
    name: str
    phase: str
    progress: int
    icon: str
    stories: int
    tasks_completed: int
    tasks_total: int


def parse_checkboxes(spec_file: Path) -> Tuple[int, int]:
    """Parse checkbox completion from technical spec."""
    if not spec_file.exists():
        return 0, 0

    content = spec_file.read_text()
    tasks = re.findall(r'- \[([ x])\]', content)

    completed = sum(1 for status in tasks if status == 'x')
    total = len(tasks)

    return completed, total


def get_feature_status(feature_dir: Path, logger=None, metrics=None) -> FeatureStatus:
    """Determine the status of a feature."""
    feature_doc = feature_dir / "FEATURE_DOCUMENTATION.md"
    stories_dir = feature_dir / "USER_STORIES"
    spec_file = feature_dir / "TECHNICAL_SPEC.md"
    verification_report = feature_dir / "VERIFICATION_REPORT.md"
    tasks_file = feature_dir / "TASKS.json"

    feature_id = feature_dir.name

    status: FeatureStatus = {
        'id': feature_id,
        'name': feature_id.replace('_', ' ').title(),
        'phase': 'Unknown',
        'progress': 0,
        'icon': '❓',
        'stories': 0,
        'tasks_completed': 0,
        'tasks_total': 0,
    }

    # Log feature scan
    if logger:
        logger.debug("Scanning feature", feature_id=feature_id)

    # Count stories
    if stories_dir.exists():
        story_files = list(stories_dir.glob("*.md"))
        status['stories'] = len(story_files)

    # Try to get detailed info from TASKS.json first
    if tasks_file.exists():
        try:
            tasks_data = json.loads(tasks_file.read_text())
            metadata = tasks_data.get("metadata", {})
            status['tasks_total'] = int(metadata.get("total_tasks", 0))
            status['tasks_completed'] = int(metadata.get("completed_tasks", 0))

            if status['tasks_total'] > 0:
                status['progress'] = int((status['tasks_completed'] / status['tasks_total']) * 100)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback to checkbox parsing
            status['tasks_completed'], status['tasks_total'] = parse_checkboxes(spec_file)
    else:
        status['tasks_completed'], status['tasks_total'] = parse_checkboxes(spec_file)

    # Determine phase and status
    if verification_report.exists():
        status['phase'] = 'Completed'
        status['icon'] = '✅'
        status['progress'] = 100
    elif spec_file.exists():
        if status['progress'] == 100:
            status['phase'] = 'Verification'
            status['icon'] = '🔍'
        elif status['progress'] > 0:
            status['phase'] = 'Development'
            status['icon'] = '🚧'
        else:
            status['phase'] = 'Specs'
            status['icon'] = '📐'
    elif stories_dir.exists():
        status['phase'] = 'Stories'
        status['icon'] = '📝'
        status['progress'] = 20
    elif feature_doc.exists():
        status['phase'] = 'Discovery'
        status['icon'] = '📋'
        status['progress'] = 10

    # Log status determination
    if logger:
        logger.debug(
            "Feature status determined",
            feature_id=feature_id,
            phase=status['phase'],
            progress=status['progress']
        )

    # Track metrics
    if metrics:
        metrics.gauge(f"feature_{feature_id}_progress", status['progress'])
        metrics.increment(f"feature_{feature_id}_scan_count")

    return status


def get_feature_metrics(feature_id: str) -> Optional[Dict]:
    """Get observability metrics for a feature if available."""
    if not HAS_OBSERVABILITY:
        return None

    try:
        manager = ObservabilityManager.get_instance()
        status = manager.get_status()

        metrics_data = {
            "parse_p95_ms": None,
            "error_count": 0,
        }

        # Get metrics summary
        if "metrics_sample" in status:
            metrics_summary = status["metrics_sample"]
            # Extract parse timing if available
            if "histograms" in metrics_summary:
                parse_hist = metrics_summary["histograms"].get("spec_parse_duration", {})
                if parse_hist and "p95" in parse_hist:
                    metrics_data["parse_p95_ms"] = parse_hist["p95"]

        # Get error count from error tracker
        try:
            tracker = manager.get_error_tracker()
            errors = tracker.get_errors_by_type(f"{feature_id}*")
            metrics_data["error_count"] = len(errors)
        except Exception:
            pass

        return metrics_data
    except RuntimeError:
        return None


def print_enhanced_status(feature: FeatureStatus, show_metrics: bool = False):
    """Print enhanced status with performance metrics."""
    progress_bar = "█" * (feature['progress'] // 5) + "░" * (20 - feature['progress'] // 5)
    print(f"{feature['icon']} {feature['id']}")
    print(f"  Phase: {feature['phase']} ({feature['progress']}%)")
    print(f"  [{progress_bar}]")

    if feature['phase'] == 'Development':
        print(f"  ├─ Tasks: {feature['tasks_completed']}/{feature['tasks_total']} complete")
        remaining = feature['tasks_total'] - feature['tasks_completed']
        if remaining > 0:
            print(f"  ├─ Pending: {remaining}")

    # Add metrics if requested and available
    if show_metrics:
        metrics = get_feature_metrics(feature['id'])
        if metrics:
            if metrics.get('parse_p95_ms'):
                print(f"  ├─ Performance: P95 parse: {metrics['parse_p95_ms']:.0f}ms")
            if metrics.get('error_count', 0) > 0:
                print(f"  └─ ⚠️  Errors: {metrics['error_count']}")

    print()


def print_terminal_summary(features: List[FeatureStatus], show_metrics: bool = False):
    """Print a terminal-friendly summary."""
    print("\n" + "=" * 60)
    print("  SAM Feature Status Report")
    print("=" * 60 + "\n")

    counts = {
        'Discovery': sum(1 for f in features if f['phase'] == 'Discovery'),
        'Stories': sum(1 for f in features if f['phase'] == 'Stories'),
        'Specs': sum(1 for f in features if f['phase'] == 'Specs'),
        'Development': sum(1 for f in features if f['phase'] == 'Development'),
        'Verification': sum(1 for f in features if f['phase'] == 'Verification'),
        'Completed': sum(1 for f in features if f['phase'] == 'Completed'),
    }

    print(f"📊 Overview")
    print(f"  Total Features:    {len(features)}")
    print(f"  In Discovery:      {counts['Discovery']}")
    print(f"  In Stories:        {counts['Stories']}")
    print(f"  In Specs:          {counts['Specs']}")
    print(f"  In Development:    {counts['Development']}")
    print(f"  In Verification:   {counts['Verification']}")
    print(f"  Completed:         {counts['Completed']}")

    # Show observability status if available
    if HAS_OBSERVABILITY and show_metrics:
        try:
            manager = ObservabilityManager.get_instance()
            obs_status = manager.get_status()
            if obs_status.get('config', {}).get('logging', {}).get('enabled'):
                print(f"\n🔍 Observability: Enabled")
        except RuntimeError:
            pass

    print("\n" + "-" * 60 + "\n")

    for feature in features:
        print_enhanced_status(feature, show_metrics)


def generate_status_report(features: List[FeatureStatus]) -> str:
    """Generate the status report markdown."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Count by phase
    counts = {
        'Discovery': sum(1 for f in features if f['phase'] == 'Discovery'),
        'Stories': sum(1 for f in features if f['phase'] == 'Stories'),
        'Specs': sum(1 for f in features if f['phase'] == 'Specs'),
        'Development': sum(1 for f in features if f['phase'] == 'Development'),
        'Verification': sum(1 for f in features if f['phase'] == 'Verification'),
        'Completed': sum(1 for f in features if f['phase'] == 'Completed'),
    }

    report = f"""# SAM Feature Status Report

Generated: {now}

---

## Summary

| Metric | Count |
|--------|-------|
| Total Features | {len(features)} |
| In Discovery | {counts['Discovery']} |
| In Stories | {counts['Stories']} |
| In Specs | {counts['Specs']} |
| In Development | {counts['Development']} |
| In Verification | {counts['Verification']} |
| Completed | {counts['Completed']} |

---

## Feature Details

"""

    for feature in features:
        report += f"""### {feature['id']}

**Status**: {feature['icon']} {feature['phase']}
**Progress**: {feature['progress']}%

**Details**:
- Stories: {feature['stories']}
- Spec Tasks: {feature['tasks_completed']}/{feature['tasks_total']}

"""
        if feature['phase'] == 'Development' and feature['tasks_total'] > 0:
            remaining = feature['tasks_total'] - feature['tasks_completed']
            report += f"- Remaining: {remaining} tasks\n\n"

    return report


def watch_mode(interval: int = 5, show_metrics: bool = False):
    """Run status report in watch mode with auto-refresh."""
    try:
        while True:
            # Clear screen
            print("\033[2J\033[H", end="")

            # Generate status
            sam_dir = Path(".sam")
            if sam_dir.exists():
                feature_dirs = sorted([d for d in sam_dir.iterdir() if d.is_dir()])
                features = [get_feature_status(d) for d in feature_dirs]
                print_terminal_summary(features, show_metrics)

            print(f"\nRefreshing every {interval}s... (Ctrl+C to exit)")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch mode stopped.")


def main():
    parser = argparse.ArgumentParser(description='Generate SAM status report')
    parser.add_argument('feature_id', nargs='?', help='Specific feature ID')
    parser.add_argument('--all', action='store_true', help='Show all features')
    parser.add_argument('--metrics', '-m', action='store_true', help='Show performance metrics')
    parser.add_argument('--watch', '-w', action='store_true', help='Watch mode (auto-refresh)')
    parser.add_argument('--interval', type=int, default=5, help='Watch mode refresh interval (seconds)')
    args = parser.parse_args()

    # Initialize observability
    logger = None
    metrics = None
    if HAS_OBSERVABILITY:
        try:
            initialize()
            logger = get_logger("sam-status")
            metrics = get_metrics("sam-status")
            metrics.increment("status_report_invocations")
        except Exception:
            pass

    if args.watch:
        watch_mode(args.interval, args.metrics)
        return

    sam_dir = Path(".sam")

    if not sam_dir.exists():
        print("❌ .sam/ directory not found")
        if logger:
            logger.error("SAM directory not found")
        sys.exit(1)

    # Get feature directories
    if args.feature_id:
        feature_dirs = [sam_dir / args.feature_id]
        if not feature_dirs[0].exists():
            print(f"❌ Feature not found: {args.feature_id}")
            if logger:
                logger.error("Feature not found", feature_id=args.feature_id)
            sys.exit(1)
    else:
        feature_dirs = sorted([d for d in sam_dir.iterdir() if d.is_dir()])

    if not feature_dirs:
        print("❌ No features found in .sam/")
        if logger:
            logger.warning("No features found")
        sys.exit(1)

    # Get status for each feature
    features = [get_feature_status(d, logger, metrics) for d in feature_dirs]

    # Print terminal summary
    print_terminal_summary(features, args.metrics)

    # Generate markdown report
    report = generate_status_report(features)
    report_path = sam_dir / "STATUS.md"
    report_path.write_text(report)

    print(f"Full report saved to: {report_path}")

    if logger:
        logger.info(
            "Status report generated",
            features_count=len(features),
            output_path=str(report_path)
        )


if __name__ == "__main__":
    main()
