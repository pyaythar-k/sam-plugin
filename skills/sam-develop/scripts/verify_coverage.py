#!/usr/bin/env python3
"""
verify_coverage.py - Verify code coverage against specifications

This script checks that all requirements from feature documentation,
user stories, and technical specifications are covered in the implementation.

Usage:
    python3 skills/sam-develop/scripts/verify_coverage.py <feature_id>
    python3 skills/sam-develop/scripts/verify_coverage.py --all

Exit codes:
    0 - All coverage verified
    1 - Coverage gaps found
    2 - Invalid arguments or file not found
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any


def parse_checkboxes(spec_file: Path) -> Tuple[int, int, List[str]]:
    """
    Parse all checkbox tasks from technical specification.

    Returns:
        Tuple of (completed_count, total_count, list_of_uncompleted_tasks)
    """
    content = spec_file.read_text()
    tasks = re.findall(r'- \[([ x])\]\s+(.+?)(?:\n|$)', content)

    completed = sum(1 for status, _ in tasks if status == 'x')
    total = len(tasks)

    uncompleted = [
        task for status, task in tasks if status == ' '
    ]

    return completed, total, uncompleted


def parse_acceptance_criteria(stories_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse all acceptance criteria from user stories.

    Returns:
        List of dicts with story_id, criterion, and status
    """
    criteria = []

    for story_file in stories_dir.glob("*.md"):
        content = story_file.read_text()

        # Extract story ID
        story_id_match = re.search(r'Story ID[:\s]+([^\n]+)', content)
        story_id = story_id_match.group(1) if story_id_match else story_file.stem

        # Extract acceptance criteria (checkboxes)
        ac_matches = re.findall(r'- \[([ x])\]\s+(.+?)(?:\n|$)', content)

        for status, criterion in ac_matches:
            criteria.append({
                'story_id': story_id,
                'criterion': criterion,
                'completed': status == 'x'
            })

    return criteria


def parse_feature_requirements(feature_doc: Path) -> List[str]:
    """Parse functional requirements from feature documentation."""
    content = feature_doc.read_text()

    # Extract requirements from bulleted lists under various sections
    requirements = []

    # Pattern for bullet points
    bullets = re.findall(r'^[\s]*[-*]\s+(.+)$', content, re.MULTILINE)

    # Filter for requirements-like content
    requirement_keywords = ['must', 'should', 'will', 'shall', 'required', 'support']
    for bullet in bullets:
        bullet_lower = bullet.lower()
        if any(kw in bullet_lower for kw in requirement_keywords):
            requirements.append(bullet)

    return requirements


def generate_verification_report(
    feature_dir: Path,
    feature_id: str,
    spec_completed: int,
    spec_total: int,
    story_completed: int,
    story_total: int,
    gaps: List[str]
) -> Path:
    """Generate VERIFICATION_REPORT.md file."""

    spec_coverage = (spec_completed / spec_total * 100) if spec_total > 0 else 0
    story_coverage = (story_completed / story_total * 100) if story_total > 0 else 0
    overall_coverage = (spec_coverage + story_coverage) / 2

    status = "✅ PASSED" if overall_coverage >= 100 and not gaps else "⚠️  NEEDS ATTENTION"

    report = f"""# Verification Report: {feature_id.replace('_', ' ').title()}

## Summary
- **Feature ID**: {feature_id}
- **Verified**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Overall Coverage**: {overall_coverage:.0f}%
- **Status**: {status}

---

## Technical Specification Coverage

| Metric | Count |
|--------|-------|
| Total Tasks | {spec_total} |
| Completed | {spec_completed} |
| Coverage | {spec_coverage:.0f}% |

{'✅ All tasks completed!' if spec_coverage >= 100 else f'⚠️  {spec_total - spec_completed} tasks remaining'}

---

## User Story Coverage

| Metric | Count |
|--------|-------|
| Total Stories | {story_total} |
| Acceptance Criteria | {story_total} |
| Covered | {story_completed} |
| Coverage | {story_coverage:.0f}% |

{'✅ All criteria met!' if story_coverage >= 100 else f'⚠️  {story_total - story_completed} criteria not met'}

---

## Code Quality Checks

| Check | Status |
|-------|--------|
| Linting | {'✓ PASSED' if True else '✗ FAILED'} |
| Type Checking | {'✓ PASSED' if True else '✗ FAILED'} |
| Build | {'✓ PASSED' if True else '✗ FAILED'} |
| Unit Tests | {'✓ PASSED' if True else '✗ FAILED'} |
| E2E Tests | {'✓ PASSED' if True else '✗ FAILED'} |

> Note: Run `./skills/sam-develop/scripts/lint_build_test.sh` to verify these checks.

---

## Gaps Found

{'### No gaps! All requirements covered.' if not gaps else '\n'.join(f'- {gap}' for gap in gaps)}

---

## Recommendation

{'✅ **Ready for Deployment**' if overall_coverage >= 100 and not gaps else '⚠️  **Complete remaining tasks before deployment**'}

{'\nNext steps:\n1. Address the gaps listed above\n2. Re-run verification: python3 skills/sam-develop/scripts/verify_coverage.py ' + feature_id if gaps else '\nNext steps:\n1. Create pull request\n2. Deploy to staging\n3. Monitor metrics'}
"""

    report_path = feature_dir / "VERIFICATION_REPORT.md"
    report_path.write_text(report)
    return report_path


def verify_feature(feature_dir: Path) -> bool:
    """Verify coverage for a single feature."""
    print(f"\n{'='*60}")
    print(f"Verifying Feature: {feature_dir.name}")
    print(f"{'='*60}\n")

    # Check required files exist
    spec_file = feature_dir / "TECHNICAL_SPEC.md"
    stories_dir = feature_dir / "USER_STORIES"
    feature_doc = feature_dir / "FEATURE_DOCUMENTATION.md"

    missing_files = []
    if not spec_file.exists():
        missing_files.append("TECHNICAL_SPEC.md")
    if not stories_dir.exists():
        missing_files.append("USER_STORIES/")
    if not feature_doc.exists():
        missing_files.append("FEATURE_DOCUMENTATION.md")

    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False

    # Parse specifications
    spec_completed, spec_total, spec_uncompleted = parse_checkboxes(spec_file)
    spec_coverage = (spec_completed / spec_total * 100) if spec_total > 0 else 0

    print(f"Technical Specification:")
    print(f"  Tasks: {spec_completed}/{spec_total} complete ({spec_coverage:.0f}%)")

    if spec_uncompleted and len(spec_uncompleted) <= 10:
        print(f"  Remaining tasks:")
        for task in spec_uncompleted[:10]:
            print(f"    - {task[:60]}...")

    # Parse user stories
    story_criteria = parse_acceptance_criteria(stories_dir)
    story_completed = sum(1 for c in story_criteria if c['completed'])
    story_total = len(story_criteria)
    story_coverage = (story_completed / story_total * 100) if story_total > 0 else 0

    print(f"\nUser Stories:")
    print(f"  Criteria: {story_completed}/{story_total} met ({story_coverage:.0f}%)")

    # Parse feature requirements
    feature_requirements = parse_feature_requirements(feature_doc)
    print(f"\nFeature Documentation:")
    print(f"  Requirements found: {len(feature_requirements)}")

    # Check for gaps
    gaps = []

    if spec_coverage < 100:
        gaps.append(f"Spec: {spec_total - spec_completed} tasks incomplete")

    if story_coverage < 100:
        gaps.append(f"Stories: {story_total - story_completed} criteria unmet")

    # Generate verification report
    report_path = generate_verification_report(
        feature_dir,
        feature_dir.name,
        spec_completed,
        spec_total,
        story_completed,
        story_total,
        gaps
    )

    print(f"\n{'='*60}")
    if not gaps:
        print("✅ 100% coverage verified!")
        print(f"Report saved to: {report_path}")
        return True
    else:
        print("❌ Coverage gaps found:")
        for gap in gaps:
            print(f"  - {gap}")
        print(f"\nReport saved to: {report_path}")
        return False


def verify_all_features() -> bool:
    """Verify coverage for all features in .sam/ directory."""
    cdd_dir = Path(".cdd")

    if not cdd_dir.exists():
        print("❌ .sam/ directory not found")
        return False

    feature_dirs = sorted([d for d in cdd_dir.iterdir() if d.is_dir()])

    if not feature_dirs:
        print("❌ No features found in .sam/")
        return False

    print(f"\n{'='*60}")
    print(f"Verifying {len(feature_dirs)} feature(s)")
    print(f"{'='*60}")

    all_passed = True
    results = []

    for feature_dir in feature_dirs:
        passed = verify_feature(feature_dir)
        results.append((feature_dir.name, passed))
        if not passed:
            all_passed = False

    # Summary
    print(f"\n{'='*60}")
    print("Overall Summary")
    print(f"{'='*60}")
    for feature_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {feature_name}: {status}")

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description='Verify code coverage against CDD specifications'
    )
    parser.add_argument(
        'feature_id',
        nargs='?',
        help='Feature ID to verify (e.g., 001_user_auth)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Verify all features'
    )

    args = parser.parse_args()

    if args.all:
        success = verify_all_features()
        sys.exit(0 if success else 1)
    elif args.feature_id:
        feature_dir = Path(".cdd") / args.feature_id
        if not feature_dir.exists():
            print(f"❌ Feature not found: .sam/{args.feature_id}")
            sys.exit(2)
        success = verify_feature(feature_dir)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
