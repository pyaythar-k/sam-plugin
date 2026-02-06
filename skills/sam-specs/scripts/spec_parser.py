#!/usr/bin/env python3
"""
spec_parser.py - Parse technical specifications and extract task metadata

This script parses TECHNICAL_SPEC.md files and extracts checkbox metadata
including task IDs, line numbers, dependencies, and phase information for
generating TASKS.json registry files.

Usage:
    python3 skills/sam-specs/scripts/spec_parser.py <feature_dir>
    python3 skills/sam-specs/scripts/spec_parser.py .sam/001_user_auth

Output:
    Generates TASKS.json in the feature directory with extracted metadata
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class Task:
    """Represents a single task from the specification."""
    task_id: str
    title: str
    status: str  # "pending" or "completed"
    spec_file: str
    section_start: int
    section_end: int
    phase_id: str
    phase_name: str
    parent_task_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    story_mapping: Optional[str] = None
    completion_note: Optional[str] = None


@dataclass
class Phase:
    """Represents a phase with its tasks."""
    phase_id: str
    phase_name: str
    status: str  # "pending", "in_progress", or "completed"
    tasks: List[Task] = field(default_factory=list)


@dataclass
class Checkpoint:
    """Represents the current checkpoint state."""
    last_completed_task: Optional[str] = None
    last_checkpoint_time: Optional[str] = None
    iteration_count: int = 0
    current_phase: str = "1"
    active_tasks: List[str] = field(default_factory=list)
    quality_gate_last_passed: Optional[str] = None
    last_quality_gate_result: Dict[str, str] = field(default_factory=dict)


@dataclass
class TaskRegistry:
    """Complete task registry for a feature."""
    metadata: Dict[str, str] = field(default_factory=dict)
    phases: List[Phase] = field(default_factory=list)
    checkpoint: Checkpoint = field(default_factory=Checkpoint)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": self.metadata,
            "phases": [
                {
                    "phase_id": p.phase_id,
                    "phase_name": p.phase_name,
                    "status": p.status,
                    "tasks": [
                        {
                            "task_id": t.task_id,
                            "title": t.title,
                            "status": t.status,
                            "spec_file": t.spec_file,
                            "section_start": t.section_start,
                            "section_end": t.section_end,
                            "parent_task_id": t.parent_task_id,
                            "dependencies": t.dependencies,
                            "story_mapping": t.story_mapping,
                            "completion_note": t.completion_note
                        }
                        for t in p.tasks
                    ]
                }
                for p in self.phases
            ],
            "checkpoint": {
                "last_completed_task": self.checkpoint.last_completed_task,
                "last_checkpoint_time": self.checkpoint.last_checkpoint_time,
                "iteration_count": self.checkpoint.iteration_count,
                "current_phase": self.checkpoint.current_phase,
                "active_tasks": self.checkpoint.active_tasks,
                "quality_gate_last_passed": self.checkpoint.quality_gate_last_passed,
                "last_quality_gate_result": self.checkpoint.last_quality_gate_result
            }
        }


class SpecParser:
    """Parser for technical specification files."""

    def __init__(self, spec_file: Path, feature_id: str, feature_name: str):
        self.spec_file = spec_file
        self.feature_id = feature_id
        self.feature_name = feature_name
        self.content = ""
        self.lines: List[str] = []
        self.project_type = "unknown"  # NEW: Store project type

    def _get_project_type(self, feature_dir: Path) -> str:
        """
        Get project type from TASKS.json or detect from codebase.

        Priority:
        1. TASKS.json metadata.project_type (user override or previous classification)
        2. FEATURE_DOCUMENTATION.md project_type field
        3. Auto-detection via codebase_analyzer
        """
        # Check TASKS.json first
        tasks_file = feature_dir / "TASKS.json"
        if tasks_file.exists():
            try:
                data = json.loads(tasks_file.read_text())
                metadata = data.get("metadata", {})
                if "project_type" in metadata:
                    return metadata["project_type"]
            except (json.JSONDecodeError, KeyError):
                pass

        # Check FEATURE_DOCUMENTATION.md
        feat_doc = feature_dir / "FEATURE_DOCUMENTATION.md"
        if feat_doc.exists():
            content = feat_doc.read_text()
            for line in content.split('\n'):
                if 'project_type:' in line.lower():
                    value = line.split(':', 1)[1].strip().lower()
                    if value in ['baas-fullstack', 'frontend-only', 'full-stack', 'static-site']:
                        return value

        # Default to full-stack if unknown
        return "full-stack"

    def parse(self) -> TaskRegistry:
        """Parse the specification file and generate task registry."""
        self.content = self.spec_file.read_text()
        self.lines = self.content.split('\n')

        # Get project type (NEW)
        feature_dir = self.spec_file.parent
        self.project_type = self._get_project_type(feature_dir)

        registry = TaskRegistry()
        registry.metadata = {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "spec_version": "2.0",
            "total_tasks": "0",
            "completed_tasks": "0",
            "current_phase": "1",
            "project_type": self.project_type  # NEW: Include project type
        }

        # Parse phases and tasks
        phases = self._parse_phases()
        registry.phases = phases

        # Count total and completed tasks
        total_tasks = sum(len(p.tasks) for p in phases)
        completed_tasks = sum(
            sum(1 for t in p.tasks if t.status == "completed")
            for p in phases
        )

        registry.metadata["total_tasks"] = str(total_tasks)
        registry.metadata["completed_tasks"] = str(completed_tasks)

        # Set initial checkpoint
        if completed_tasks > 0:
            last_completed = self._find_last_completed_task(phases)
            registry.checkpoint.last_completed_task = last_completed
            registry.checkpoint.last_checkpoint_time = datetime.now().isoformat()

        return registry

    def _parse_phases(self) -> List[Phase]:
        """Parse all phases from the specification."""
        phases = []
        current_phase_id = "1"
        current_phase_name = ""
        current_phase: Optional[Phase] = None

        # Phase pattern: ## Phase X: Name
        phase_pattern = re.compile(r'^## Phase (\d+):\s*(.+)$')

        for line_num, line in enumerate(self.lines, 1):
            phase_match = phase_pattern.match(line)

            if phase_match:
                # Save previous phase
                if current_phase:
                    phases.append(current_phase)

                # Start new phase
                current_phase_id = phase_match.group(1)
                current_phase_name = phase_match.group(2)
                current_phase = Phase(
                    phase_id=current_phase_id,
                    phase_name=current_phase_name,
                    status="pending"
                )
            elif current_phase:
                # Check for tasks in current phase
                if line.strip().startswith('- [') and '**' in line:
                    task = self._parse_task(line, line_num, current_phase)
                    if task:
                        current_phase.tasks.append(task)

        # Save last phase
        if current_phase:
            phases.append(current_phase)

        # Update phase status based on tasks
        for phase in phases:
            if not phase.tasks:
                continue
            all_completed = all(t.status == "completed" for t in phase.tasks)
            any_completed = any(t.status == "completed" for t in phase.tasks)
            any_pending = any(t.status == "pending" for t in phase.tasks)

            if all_completed:
                phase.status = "completed"
            elif any_completed and any_pending:
                phase.status = "in_progress"
            else:
                phase.status = "pending"

        return phases

    def _parse_task(self, line: str, line_num: int, phase: Phase) -> Optional[Task]:
        """Parse a single task from a checkbox line."""
        # Pattern: - [x] **1.1 Task Title** or - [ ] **1.1 Task Title**
        task_match = re.match(r'-\s+\[([x ])\]\s+\*\*([\d.]+)\s+(.+?)\*\*(.*)', line)

        if not task_match:
            return None

        status_char = task_match.group(1)
        task_id = task_match.group(2)
        title = task_match.group(3).strip()
        rest = task_match.group(4).strip()

        # Find section end (next task or phase header)
        section_end = self._find_section_end(line_num)

        # Parse story mapping from rest of line
        story_mapping = None
        if "Maps to:" in rest:
            mapping_match = re.search(r'Maps to:\s*Story\s+(\S+)', rest)
            if mapping_match:
                story_mapping = mapping_match.group(1)

        # Check for completion note
        completion_note = None
        if "Completed:" in rest:
            note_match = re.search(r'Completed:\s*([\d-]+)', rest)
            if note_match:
                completion_note = note_match.group(1)

        return Task(
            task_id=task_id,
            title=title,
            status="completed" if status_char == 'x' else "pending",
            spec_file="TECHNICAL_SPEC.md",
            section_start=line_num,
            section_end=section_end,
            phase_id=phase.phase_id,
            phase_name=phase.phase_name,
            story_mapping=story_mapping,
            completion_note=completion_note
        )

    def _find_section_end(self, start_line: int) -> int:
        """Find the end line of a task section."""
        for i in range(start_line, len(self.lines)):
            line = self.lines[i]
            # Next task or phase header ends the section
            if line.strip().startswith('- [') and '**' in line:
                return i
            if line.strip().startswith('## Phase'):
                return i
        return len(self.lines)

    def _find_last_completed_task(self, phases: List[Phase]) -> Optional[str]:
        """Find the most recent completed task."""
        for phase in reversed(phases):
            for task in reversed(phase.tasks):
                if task.status == "completed":
                    return task.task_id
        return None


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 spec_parser.py <feature_dir>")
        print("Example: python3 spec_parser.py .sam/001_user_auth")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Find technical spec
    spec_file = feature_dir / "TECHNICAL_SPEC.md"

    if not spec_file.exists():
        print(f"Error: TECHNICAL_SPEC.md not found in {feature_dir}")
        sys.exit(1)

    # Extract feature info
    feature_id = feature_dir.name

    # Try to get feature name from spec
    spec_content = spec_file.read_text()
    name_match = re.search(r'# Technical Specification:\s*(.+)', spec_content)
    feature_name = name_match.group(1).strip() if name_match else feature_id.replace('_', ' ').title()

    # Parse specification
    print(f"Parsing specification: {spec_file}")
    parser = SpecParser(spec_file, feature_id, feature_name)
    registry = parser.parse()

    # Write TASKS.json
    output_file = feature_dir / "TASKS.json"
    with open(output_file, 'w') as f:
        json.dump(registry.to_dict(), f, indent=2)

    print(f"✓ Generated TASKS.json")
    print(f"  Features: {registry.metadata['feature_name']}")
    print(f"  Total Tasks: {registry.metadata['total_tasks']}")
    print(f"  Completed: {registry.metadata['completed_tasks']}")
    print(f"  Phases: {len(registry.phases)}")
    print(f"  Project Type: {registry.metadata.get('project_type', 'unknown')}")  # NEW

    for phase in registry.phases:
        print(f"    Phase {phase.phase_id} ({phase.phase_name}): {len(phase.tasks)} tasks [{phase.status}]")


if __name__ == "__main__":
    main()
