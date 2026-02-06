#!/usr/bin/env python3
"""
task_registry.py - Task registry management for SAM workflow

This script manages TASKS.json files including reading, writing, updating
task status, and checkpoint management. It provides utilities for sam-develop
to efficiently track progress and resume work.

Usage:
    python3 skills/sam-develop/scripts/task_registry.py read <feature_dir>
    python3 skills/sam-develop/scripts/task_registry.py update <feature_dir> <task_id> --status completed
    python3 skills/sam-develop/scripts/task_registry.py checkpoint <feature_dir>
    python3 skills/sam-develop/scripts/task_registry.py resume <feature_dir>
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class TaskInfo:
    """Lightweight task information from registry."""
    task_id: str
    title: str
    status: str
    phase_id: str
    spec_file: str
    section_start: int
    section_end: int
    dependencies: List[str] = field(default_factory=list)
    # Phase 4: Validation & Verification fields
    code_mappings: List[Dict[str, Any]] = field(default_factory=list)
    verification_methods: List[Dict[str, Any]] = field(default_factory=list)
    verification_status: str = "pending"  # "verified", "failed", "partial", "pending"
    verified_at: Optional[str] = None
    verification_coverage: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskInfo':
        """Create from dictionary."""
        return cls(
            task_id=data.get('task_id', ''),
            title=data.get('title', ''),
            status=data.get('status', 'pending'),
            phase_id=data.get('phase_id', '1'),
            spec_file=data.get('spec_file', 'TECHNICAL_SPEC.md'),
            section_start=data.get('section_start', 0),
            section_end=data.get('section_end', 0),
            dependencies=data.get('dependencies', []),
            # Phase 4 fields
            code_mappings=data.get('code_mappings', []),
            verification_methods=data.get('verification_methods', []),
            verification_status=data.get('verification_status', 'pending'),
            verified_at=data.get('verified_at'),
            verification_coverage=data.get('verification_coverage', 0.0)
        )


@dataclass
class PhaseInfo:
    """Lightweight phase information from registry."""
    phase_id: str
    phase_name: str
    status: str
    tasks: List[TaskInfo] = field(default_factory=list)
    # Phase 4: Phase gate result
    gate_result: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'PhaseInfo':
        """Create from dictionary."""
        tasks = [TaskInfo.from_dict(t) for t in data.get('tasks', [])]
        return cls(
            phase_id=data.get('phase_id', ''),
            phase_name=data.get('phase_name', ''),
            status=data.get('status', 'pending'),
            tasks=tasks,
            gate_result=data.get('gate_result')
        )

    def get_pending_tasks(self) -> List[TaskInfo]:
        """Get all pending tasks in this phase."""
        return [t for t in self.tasks if t.status == 'pending']

    def get_completed_tasks(self) -> List[TaskInfo]:
        """Get all completed tasks in this phase."""
        return [t for t in self.tasks if t.status == 'completed']


@dataclass
class CheckpointInfo:
    """Checkpoint information for resumption."""
    last_completed_task: Optional[str] = None
    last_checkpoint_time: Optional[str] = None
    iteration_count: int = 0
    current_phase: str = "1"
    active_tasks: List[str] = field(default_factory=list)
    quality_gate_last_passed: Optional[str] = None
    last_quality_gate_result: Dict[str, str] = field(default_factory=dict)
    coverage_last_checked: Optional[str] = None
    coverage_percentage: Optional[float] = None
    coverage_trend: List[Dict[str, Any]] = field(default_factory=list)
    # CI/CD metadata fields (Phase 3)
    last_ci_run: Optional[str] = None
    ci_environment: Optional[str] = None
    ci_job_id: Optional[str] = None
    ci_workflow: Optional[str] = None
    ci_status: Optional[str] = None
    ci_metadata: Dict[str, Any] = field(default_factory=dict)
    # Phase 4: Validation & Verification fields
    phase_gate_status: Optional[Dict[str, Any]] = None
    conflict_detection: Optional[Dict[str, Any]] = None
    verification_status: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'CheckpointInfo':
        """Create from dictionary."""
        return cls(
            last_completed_task=data.get('last_completed_task'),
            last_checkpoint_time=data.get('last_checkpoint_time'),
            iteration_count=data.get('iteration_count', 0),
            current_phase=data.get('current_phase', '1'),
            active_tasks=data.get('active_tasks', []),
            quality_gate_last_passed=data.get('quality_gate_last_passed'),
            last_quality_gate_result=data.get('last_quality_gate_result', {}),
            coverage_last_checked=data.get('coverage_last_checked'),
            coverage_percentage=data.get('coverage_percentage'),
            coverage_trend=data.get('coverage_trend', []),
            # CI/CD metadata
            last_ci_run=data.get('last_ci_run'),
            ci_environment=data.get('ci_environment'),
            ci_job_id=data.get('ci_job_id'),
            ci_workflow=data.get('ci_workflow'),
            ci_status=data.get('ci_status'),
            ci_metadata=data.get('ci_metadata', {}),
            # Phase 4 fields
            phase_gate_status=data.get('phase_gate_status'),
            conflict_detection=data.get('conflict_detection'),
            verification_status=data.get('verification_status')
        )


class TaskRegistry:
    """Manager for TASKS.json operations."""

    def __init__(self, feature_dir: Path):
        self.feature_dir = feature_dir
        self.registry_file = feature_dir / "TASKS.json"
        self._data: Dict[str, Any] = {}
        self._phases: List[PhaseInfo] = []

    def load(self) -> bool:
        """Load the registry file. Returns True if successful."""
        if not self.registry_file.exists():
            return False

        try:
            with open(self.registry_file, 'r') as f:
                self._data = json.load(f)

            # Parse phases
            self._phases = [
                PhaseInfo.from_dict(p)
                for p in self._data.get('phases', [])
            ]
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to load registry: {e}")
            return False

    def save(self):
        """Save the registry file."""
        # Update phase data from internal state
        self._data['phases'] = [
            {
                'phase_id': p.phase_id,
                'phase_name': p.phase_name,
                'status': p.status,
                'gate_result': p.gate_result,  # Phase 4 field
                'tasks': [
                    {
                        'task_id': t.task_id,
                        'title': t.title,
                        'status': t.status,
                        'spec_file': t.spec_file,
                        'section_start': t.section_start,
                        'section_end': t.section_end,
                        'parent_task_id': None,
                        'dependencies': t.dependencies,
                        'story_mapping': None,
                        'completion_note': None,
                        # Phase 4 fields
                        'code_mappings': t.code_mappings,
                        'verification_methods': t.verification_methods,
                        'verification_status': t.verification_status,
                        'verified_at': t.verified_at,
                        'verification_coverage': t.verification_coverage
                    }
                    for t in p.tasks
                ]
            }
            for p in self._phases
        ]

        # Update metadata counts
        total_tasks = sum(len(p.tasks) for p in self._phases)
        completed_tasks = sum(
            sum(1 for t in p.tasks if t.status == 'completed')
            for p in self._phases
        )

        self._data.setdefault('metadata', {})['total_tasks'] = str(total_tasks)
        self._data['metadata']['completed_tasks'] = str(completed_tasks)

        with open(self.registry_file, 'w') as f:
            json.dump(self._data, f, indent=2)

    def get_phases(self) -> List[PhaseInfo]:
        """Get all phases."""
        return self._phases

    def get_current_phase(self) -> Optional[PhaseInfo]:
        """Get the current phase (first incomplete phase)."""
        checkpoint = CheckpointInfo.from_dict(
            self._data.get('checkpoint', {})
        )
        current_phase_id = checkpoint.current_phase

        for phase in self._phases:
            if phase.phase_id == current_phase_id:
                return phase

        # Fallback: first incomplete phase
        for phase in self._phases:
            if phase.status != 'completed':
                return phase

        return None

    def get_pending_tasks(self, phase_id: Optional[str] = None) -> List[TaskInfo]:
        """Get pending tasks, optionally filtered by phase."""
        if phase_id:
            for phase in self._phases:
                if phase.phase_id == phase_id:
                    return phase.get_pending_tasks()
            return []

        # Get all pending tasks
        pending = []
        for phase in self._phases:
            pending.extend(phase.get_pending_tasks())
        return pending

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Find a task by ID."""
        for phase in self._phases:
            for task in phase.tasks:
                if task.task_id == task_id:
                    return task
        return None

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status. Returns True if successful."""
        for phase in self._phases:
            for task in phase.tasks:
                if task.task_id == task_id:
                    task.status = status
                    return True
        return False

    def update_checkpoint(
        self,
        last_completed_task: Optional[str] = None,
        iteration_count: Optional[int] = None,
        quality_gate_results: Optional[Dict[str, str]] = None
    ):
        """Update checkpoint information."""
        checkpoint = self._data.setdefault('checkpoint', {})

        if last_completed_task:
            checkpoint['last_completed_task'] = last_completed_task
            checkpoint['last_checkpoint_time'] = datetime.now().isoformat()

        if iteration_count is not None:
            checkpoint['iteration_count'] = iteration_count

        if quality_gate_results:
            checkpoint['quality_gate_last_passed'] = datetime.now().isoformat()
            checkpoint['last_quality_gate_result'] = quality_gate_results

    def get_checkpoint(self) -> CheckpointInfo:
        """Get checkpoint information."""
        return CheckpointInfo.from_dict(
            self._data.get('checkpoint', {})
        )

    def get_parallel_limit(self) -> int:
        """Get maximum parallel subagents from environment or default."""
        return int(os.environ.get('SAM_MAX_PARALLEL_SUBAGENTS', '3'))

    def get_coverage_summary(self) -> Dict[str, Any]:
        """Get quick coverage summary from registry."""
        total_tasks = sum(len(p.tasks) for p in self._phases)
        completed_tasks = sum(
            sum(1 for t in p.tasks if t.status == 'completed')
            for p in self._phases
        )

        metadata = self._data.get('metadata', {})
        checkpoint = self._data.get('checkpoint', {})

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'coverage_percent': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'current_phase': metadata.get('current_phase', '1'),
            'last_completed_task': checkpoint.get('last_completed_task'),
            'iteration_count': checkpoint.get('iteration_count', 0),
            'project_type': metadata.get('project_type', 'unknown')  # NEW
        }

    def get_phase_structure(self, project_type: str) -> List[str]:
        """
        Return phase IDs based on project type.

        Args:
            project_type: One of 'baas-fullstack', 'frontend-only', 'full-stack', 'static-site'

        Returns:
            List of phase IDs for the project type
        """
        structures = {
            "baas-fullstack": ["1", "2", "3", "4", "5"],
            "frontend-only": ["1", "2", "3", "4"],
            "full-stack": ["1", "2", "3", "4", "5"],
            "static-site": ["1", "2", "3", "4"]
        }
        return structures.get(project_type, structures["full-stack"])

    def get_project_type(self) -> str:
        """Get the project type from metadata."""
        return self._data.get('metadata', {}).get('project_type', 'unknown')


def print_registry_info(registry: TaskRegistry):
    """Print registry information for CLI."""
    print("\n" + "="*60)
    print("Task Registry Information")
    print("="*60)

    metadata = registry._data.get('metadata', {})
    print(f"\nFeature: {metadata.get('feature_name', 'Unknown')}")
    print(f"Feature ID: {metadata.get('feature_id', 'Unknown')}")
    print(f"Project Type: {metadata.get('project_type', 'unknown')}")  # NEW

    summary = registry.get_coverage_summary()
    print(f"\nProgress: {summary['completed_tasks']}/{summary['total_tasks']} tasks")
    print(f"Coverage: {summary['coverage_percent']:.0f}%")
    print(f"Current Phase: {summary['current_phase']}")
    print(f"Iterations: {summary['iteration_count']}")

    checkpoint = registry.get_checkpoint()
    if checkpoint.last_completed_task:
        print(f"Last Completed: {checkpoint.last_completed_task}")
        print(f"Last Checkpoint: {checkpoint.last_checkpoint_time}")

    print("\nPhases:")
    for phase in registry.get_phases():
        pending = len(phase.get_pending_tasks())
        completed = len(phase.get_completed_tasks())
        total = len(phase.tasks)
        print(f"  Phase {phase.phase_id} ({phase.phase_name}):")
        print(f"    Status: {phase.status}")
        print(f"    Tasks: {completed}/{total} complete, {pending} pending")


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  task_registry.py read <feature_dir>")
        print("  task_registry.py update <feature_dir> <task_id> --status <completed|pending>")
        print("  task_registry.py checkpoint <feature_dir> [--task <task_id>]")
        print("  task_registry.py resume <feature_dir>")
        sys.exit(1)

    command = sys.argv[1]
    feature_dir = Path(sys.argv[2])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    registry = TaskRegistry(feature_dir)

    if command == "read":
        if not registry.load():
            print(f"Error: TASKS.json not found in {feature_dir}")
            sys.exit(1)
        print_registry_info(registry)

    elif command == "update":
        if len(sys.argv) < 5:
            print("Error: update command requires task_id and --status")
            sys.exit(1)

        task_id = sys.argv[3]
        status = sys.argv[5] if sys.argv[4] == "--status" else "pending"

        if not registry.load():
            print(f"Error: TASKS.json not found in {feature_dir}")
            sys.exit(1)

        if registry.update_task_status(task_id, status):
            registry.save()
            print(f"✓ Updated task {task_id} to {status}")
        else:
            print(f"Error: Task {task_id} not found")
            sys.exit(1)

    elif command == "checkpoint":
        task_id = None
        if "--task" in sys.argv:
            idx = sys.argv.index("--task")
            task_id = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

        if not registry.load():
            print(f"Error: TASKS.json not found in {feature_dir}")
            sys.exit(1)

        # Get current iteration count
        checkpoint = registry.get_checkpoint()
        iteration_count = checkpoint.iteration_count + 1

        registry.update_checkpoint(last_completed_task=task_id, iteration_count=iteration_count)
        registry.save()
        print(f"✓ Checkpoint saved (iteration {iteration_count})")

    elif command == "resume":
        if not registry.load():
            print(f"Error: TASKS.json not found in {feature_dir}")
            sys.exit(1)

        checkpoint = registry.get_checkpoint()
        summary = registry.get_coverage_summary()

        print("\nResume Information:")
        print(f"  Last Completed: {checkpoint.last_completed_task or 'None'}")
        print(f"  Current Phase: {summary['current_phase']}")
        print(f"  Progress: {summary['completed_tasks']}/{summary['total_tasks']} ({summary['coverage_percent']:.0f}%)")

        if checkpoint.active_tasks:
            print(f"  Active Tasks: {', '.join(checkpoint.active_tasks)}")

        # Show pending tasks in current phase
        current_phase = registry.get_current_phase()
        if current_phase:
            pending = current_phase.get_pending_tasks()[:5]  # Show first 5
            print(f"\nNext Tasks (Phase {current_phase.phase_id}):")
            for task in pending:
                print(f"  - {task.task_id}: {task.title}")

    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
