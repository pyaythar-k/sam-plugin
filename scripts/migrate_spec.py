#!/usr/bin/env python3
"""
migrate_spec.py - Migrate existing single-spec projects to modular format

This script migrates existing TECHNICAL_SPEC.md files to the new modular structure:
- Generates TASKS.json with task metadata
- Splits IMPLEMENTATION_TASKS.md into PHASE_*.md files
- Updates template references

Usage:
    python3 scripts/migrate_spec.py .sam/{feature}
    python3 scripts/migrate_spec.py .sam/001_user_auth --dry-run

Options:
    --dry-run    Show what would be done without making changes
    --force      Overwrite existing TASKS.json and phase files
"""

import sys
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional


def parse_spec_sections(spec_file: Path) -> List[dict]:
    """
    Parse specification file into sections.

    Returns:
        List of section dicts with name, content, line_start, line_end
    """
    content = spec_file.read_text()
    lines = content.split('\n')

    sections = []
    current_section = None
    section_start = 0

    for i, line in enumerate(lines):
        # Detect section headers
        if line.strip().startswith('#'):
            # Save previous section
            if current_section:
                current_section['line_end'] = i - 1
                current_section['content'] = '\n'.join(
                    lines[section_start:i]
                )
                sections.append(current_section)

            # Start new section
            level = len(re.match(r'^#+', line).group())
            title = line.strip('#').strip()
            current_section = {
                'level': level,
                'title': title,
                'line_start': i,
                'line_end': len(lines),
                'content': ''
            }
            section_start = i

    # Save last section
    if current_section:
        current_section['content'] = '\n'.join(lines[section_start:])
        sections.append(current_section)

    return sections


def extract_implementation_tasks(spec_file: Path) -> Tuple[str, List[dict]]:
    """
    Extract implementation tasks section from spec.

    Returns:
        Tuple of (main_spec_content, list_of_phase_sections)
    """
    content = spec_file.read_text()
    lines = content.split('\n')

    # Find Implementation Tasks section
    impl_start = -1
    impl_header_line = -1

    for i, line in enumerate(lines):
        if line.strip() == '# Implementation Tasks':
            impl_header_line = i
            impl_start = i
            break

    if impl_start == -1:
        # No implementation tasks found
        return content, []

    # Find phases within implementation tasks
    phases = []
    current_phase = None
    phase_start = impl_start

    for i in range(impl_start, len(lines)):
        line = lines[i]

        # Detect phase headers
        phase_match = re.match(r'^## Phase (\d+):\s*(.+)$', line)
        if phase_match:
            # Save previous phase
            if current_phase:
                current_phase['content'] = '\n'.join(
                    lines[phase_start:i]
                )
                phases.append(current_phase)

            # Start new phase
            phase_id = phase_match.group(1)
            phase_name = phase_match.group(2)
            current_phase = {
                'phase_id': phase_id,
                'phase_name': phase_name,
                'line_start': i,
                'content': ''
            }
            phase_start = i

    # Save last phase
    if current_phase:
        current_phase['content'] = '\n'.join(lines[phase_start:])
        phases.append(current_phase)

    # Remove implementation tasks from main spec
    main_spec = '\n'.join(lines[:impl_header_line])

    return main_spec, phases


def generate_tasks_json(spec_file: Path, feature_id: str) -> dict:
    """
    Generate TASKS.json by parsing checkboxes.

    This is a simplified version that delegates to spec_parser.py
    """
    # Import the spec_parser module
    import importlib.util

    parser_path = Path(__file__).parent.parent / 'skills' / 'sam-specs' / 'scripts' / 'spec_parser.py'

    spec = importlib.util.spec_from_file_location("spec_parser", parser_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load spec from {parser_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    parser = module.SpecParser(spec_file, feature_id, feature_id.replace('_', ' ').title())
    registry = parser.parse()

    return registry.to_dict()


def migrate_feature(
    feature_dir: Path,
    dry_run: bool = False,
    force: bool = False
) -> bool:
    """Migrate a single feature to modular format."""

    print(f"\n{'='*60}")
    print(f"Migrating Feature: {feature_dir.name}")
    print(f"{'='*60}\n")

    spec_file = feature_dir / "TECHNICAL_SPEC.md"

    if not spec_file.exists():
        print(f"❌ TECHNICAL_SPEC.md not found in {feature_dir}")
        return False

    # Check if already migrated
    tasks_file = feature_dir / "TASKS.json"
    if tasks_file.exists() and not force:
        print(f"⚠ TASKS.json already exists. Use --force to overwrite.")
        return False

    impl_dir = feature_dir / "IMPLEMENTATION_TASKS"
    if impl_dir.exists() and not force:
        print(f"⚠ IMPLEMENTATION_TASKS/ already exists. Use --force to overwrite.")
        return False

    print(f"Step 1: Parsing TECHNICAL_SPEC.md...")
    main_spec, phases = extract_implementation_tasks(spec_file)

    print(f"  Found {len(phases)} phases")
    for phase in phases:
        print(f"    Phase {phase['phase_id']}: {phase['phase_name']}")

    if dry_run:
        print(f"\n🔍 DRY RUN - Would make these changes:")
        print(f"  1. Create TASKS.json")
        print(f"  2. Create IMPLEMENTATION_TASKS/ directory")
        print(f"  3. Create {len(phases)} PHASE_*.md files")
        print(f"  4. Update TECHNICAL_SPEC.md (remove implementation tasks)")
        return True

    print(f"\nStep 2: Generating TASKS.json...")
    feature_id = feature_dir.name
    tasks_data = generate_tasks_json(spec_file, feature_id)

    with open(tasks_file, 'w') as f:
        json.dump(tasks_data, f, indent=2)

    print(f"  ✓ Created TASKS.json")
    print(f"    Total tasks: {tasks_data['metadata']['total_tasks']}")
    print(f"    Completed: {tasks_data['metadata']['completed_tasks']}")

    print(f"\nStep 3: Creating IMPLEMENTATION_TASKS/ directory...")
    impl_dir.mkdir(exist_ok=True)

    # Create IMPLEMENTATION_TASKS.md with summaries
    impl_summary = "# Implementation Tasks\n\n"
    impl_summary += f"**Feature**: {feature_id}\n"
    impl_summary += f"**Total Phases**: {len(phases)}\n\n"
    impl_summary += "## Phase Overview\n\n"

    for phase in phases:
        phase_file = impl_dir / f"PHASE_{phase['phase_id']}_{phase['phase_name'].upper().replace(' ', '_')}.md"
        impl_summary += f"- [Phase {phase['phase_id']}: {phase['phase_name']}]({phase_file.name})\n"

        # Write individual phase file
        phase_content = f"# Phase {phase['phase_id']}: {phase['phase_name']}\n\n"
        phase_content += phase['content']

        with open(phase_file, 'w') as f:
            f.write(phase_content)

        print(f"  ✓ Created {phase_file.name}")

    with open(impl_dir / "IMPLEMENTATION_TASKS.md", 'w') as f:
        f.write(impl_summary)

    print(f"  ✓ Created IMPLEMENTATION_TASKS.md")

    print(f"\nStep 4: Updating TECHNICAL_SPEC.md...")
    # Backup original
    backup_file = spec_file.with_suffix('.md.backup')
    shutil.copy(spec_file, backup_file)
    print(f"  ✓ Backed up to {backup_file.name}")

    # Write updated main spec
    with open(spec_file, 'w') as f:
        f.write(main_spec)

    # Add reference to implementation tasks
    with open(spec_file, 'a') as f:
        f.write("\n---\n\n")
        f.write("# Implementation Tasks\n\n")
        f.write("Detailed implementation tasks have been moved to modular files:\n\n")
        f.write("See: [IMPLEMENTATION_TASKS/](IMPLEMENTATION_TASKS/)\n\n")
        for phase in phases:
            phase_name = f"PHASE_{phase['phase_id']}_{phase['phase_name'].upper().replace(' ', '_')}.md"
            f.write(f"- [Phase {phase['phase_id']}: {phase['phase_name']}]({phase_name})\n")

    print(f"  ✓ Updated TECHNICAL_SPEC.md")

    print(f"\n{'='*60}")
    print(f"✅ Migration Complete!")
    print(f"{'='*60}")
    print(f"\nChanges:")
    print(f"  • Created: TASKS.json")
    print(f"  • Created: IMPLEMENTATION_TASKS/")
    print(f"  • Created: {len(phases)} phase files")
    print(f"  • Updated: TECHNICAL_SPEC.md")
    print(f"  • Backup: {backup_file.name}")
    print(f"\nNext steps:")
    print(f"  1. Review the changes")
    print(f"  2. Test with: /sam-develop {feature_id}")
    print(f"  3. If issues: restore from backup")

    return True


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Migrate existing SAM specs to modular format'
    )
    parser.add_argument(
        'feature_dir',
        type=Path,
        help='Feature directory (e.g., .sam/001_user_auth)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing TASKS.json and phase files'
    )

    args = parser.parse_args()

    if not args.feature_dir.exists():
        print(f"❌ Error: Feature directory not found: {args.feature_dir}")
        sys.exit(1)

    success = migrate_feature(
        args.feature_dir,
        dry_run=args.dry_run,
        force=args.force
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
