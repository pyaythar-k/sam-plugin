#!/usr/bin/env python3
"""
status_report.py - Generate SAM feature status report

Scans all features in .sam/ and generates a comprehensive status report.

Usage:
    python3 skills/sam-status/scripts/status_report.py [feature_id]
    python3 skills/sam-status/scripts/status_report.py --all
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, TypedDict


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


def get_feature_status(feature_dir: Path) -> FeatureStatus:
    """Determine the status of a feature."""
    feature_doc = feature_dir / "FEATURE_DOCUMENTATION.md"
    stories_dir = feature_dir / "USER_STORIES"
    spec_file = feature_dir / "TECHNICAL_SPEC.md"
    verification_report = feature_dir / "VERIFICATION_REPORT.md"

    status: FeatureStatus = {
        'id': feature_dir.name,
        'name': feature_dir.name.replace('_', ' ').title(),
        'phase': 'Unknown',
        'progress': 0,
        'icon': '❓',
        'stories': 0,
        'tasks_completed': 0,
        'tasks_total': 0,
    }

    # Count stories
    if stories_dir.exists():
        story_files = list(stories_dir.glob("*.md"))
        status['stories'] = len(story_files)

    # Parse spec checkboxes
    status['tasks_completed'], status['tasks_total'] = parse_checkboxes(spec_file)

    # Determine phase and status
    if verification_report.exists():
        status['phase'] = 'Completed'
        status['icon'] = '✅'
        status['progress'] = 100
    elif spec_file.exists():
        completed, total = status['tasks_completed'], status['tasks_total']
        if total > 0:
            status['progress'] = int((completed / total) * 100)

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
        status['progress'] = 20  # Arbitrary progress for stories phase
    elif feature_doc.exists():
        status['phase'] = 'Discovery'
        status['icon'] = '📋'
        status['progress'] = 10

    return status


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


def print_terminal_summary(features: List[FeatureStatus]):
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
    print("\n" + "-" * 60 + "\n")

    for feature in features:
        progress_bar = "█" * (feature['progress'] // 5) + "░" * (20 - feature['progress'] // 5)
        print(f"{feature['icon']} {feature['id']}")
        print(f"  Status: {feature['phase']} ({feature['progress']}%)")
        print(f"  [{progress_bar}]")

        if feature['phase'] == 'Development':
            print(f"  Tasks: {feature['tasks_completed']}/{feature['tasks_total']} complete")

        print()


def main():
    parser = argparse.ArgumentParser(description='Generate SAM status report')
    parser.add_argument('feature_id', nargs='?', help='Specific feature ID')
    parser.add_argument('--all', action='store_true', help='Show all features')
    args = parser.parse_args()

    sam_dir = Path(".sam")

    if not sam_dir.exists():
        print("❌ .sam/ directory not found")
        sys.exit(1)

    # Get feature directories
    if args.feature_id:
        feature_dirs = [sam_dir / args.feature_id]
        if not feature_dirs[0].exists():
            print(f"❌ Feature not found: {args.feature_id}")
            sys.exit(1)
    else:
        feature_dirs = sorted([d for d in sam_dir.iterdir() if d.is_dir()])

    if not feature_dirs:
        print("❌ No features found in .sam/")
        sys.exit(1)

    # Get status for each feature
    features = [get_feature_status(d) for d in feature_dirs]

    # Print terminal summary
    print_terminal_summary(features)

    # Generate markdown report
    report = generate_status_report(features)
    report_path = sam_dir / "STATUS.md"
    report_path.write_text(report)

    print(f"Full report saved to: {report_path}")


if __name__ == "__main__":
    main()
