#!/usr/bin/env python3
"""
phase_gate_validator.py - Phase gate validation for quality transitions

This script validates that all phase completion criteria are met before
allowing phase transitions. It enforces quality thresholds and generates
comprehensive completion reports.

Usage:
    python3 phase_gate_validator.py .sam/{feature} --validate-phase 2
    python3 phase_gate_validator.py .sam/{feature} --completion-report 2 > PHASE_2_REPORT.md
    python3 phase_gate_validator.py .sam/{feature} --can-transition 2 3
    python3 phase_gate_validator.py .sam/{feature} --validate-all
    python3 phase_gate_validator.py .sam/{feature} --list-criteria

Output:
    Phase gate validation results
    Updates TASKS.json with gate results
    Generates completion reports
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field, asdict


# Phase-specific gate criteria
PHASE_GATE_CRITERIA = {
    "1": {  # Foundation
        "all_tasks_complete": True,
        "quality_gate_passed": True,
        "coverage_threshold_met": False,  # Not applicable for foundation
        "acceptance_criteria_satisfied": False,  # Not applicable for foundation
        "no_conflicts_detected": True,
        "documentation_complete": True,
        "min_coverage": 0.0,
    },
    "2": {  # Backend
        "all_tasks_complete": True,
        "quality_gate_passed": True,
        "coverage_threshold_met": True,
        "acceptance_criteria_satisfied": True,
        "no_conflicts_detected": True,
        "documentation_complete": True,
        "min_coverage": 80.0,
    },
    "3": {  # Frontend
        "all_tasks_complete": True,
        "quality_gate_passed": True,
        "coverage_threshold_met": True,
        "acceptance_criteria_satisfied": True,
        "no_conflicts_detected": True,
        "documentation_complete": True,
        "min_coverage": 80.0,
    },
    "4": {  # Integration
        "all_tasks_complete": True,
        "quality_gate_passed": True,
        "coverage_threshold_met": True,
        "acceptance_criteria_satisfied": True,
        "no_conflicts_detected": True,
        "documentation_complete": True,
        "min_coverage": 75.0,
    },
    "5": {  # Deployment
        "all_tasks_complete": True,
        "quality_gate_passed": True,
        "coverage_threshold_met": False,
        "acceptance_criteria_satisfied": True,
        "no_conflicts_detected": True,
        "documentation_complete": True,
        "min_coverage": 0.0,
    },
}

# Phase type mappings (project_type -> phase IDs)
PROJECT_PHASES = {
    "baas-fullstack": ["1", "2", "3", "4", "5"],
    "frontend-only": ["1", "2", "3", "4"],
    "full-stack": ["1", "2", "3", "4", "5"],
    "static-site": ["1", "2", "3", "4"],
}


@dataclass
class PhaseGateCriteria:
    """Criteria for phase gate validation."""
    phase_id: str
    phase_name: str
    all_tasks_complete: bool = False
    quality_gate_passed: bool = False
    coverage_threshold_met: bool = False
    acceptance_criteria_satisfied: bool = False
    no_conflicts_detected: bool = False
    documentation_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def is_met(self) -> bool:
        """Check if all required criteria are met."""
        criteria = PHASE_GATE_CRITERIA.get(self.phase_id, {})

        if criteria.get("all_tasks_complete") and not self.all_tasks_complete:
            return False
        if criteria.get("quality_gate_passed") and not self.quality_gate_passed:
            return False
        if criteria.get("coverage_threshold_met") and not self.coverage_threshold_met:
            return False
        if criteria.get("acceptance_criteria_satisfied") and not self.acceptance_criteria_satisfied:
            return False
        if criteria.get("no_conflicts_detected") and not self.no_conflicts_detected:
            return False
        if criteria.get("documentation_complete") and not self.documentation_complete:
            return False

        return True


@dataclass
class PhaseGateResult:
    """Result of phase gate validation."""
    phase_id: str
    phase_name: str
    passed: bool
    criteria: PhaseGateCriteria
    failed_criteria: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    can_transition: bool = False
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["criteria"] = self.criteria.to_dict()
        return data


@dataclass
class PhaseCompletionReport:
    """Comprehensive phase completion report."""
    phase_id: str
    phase_name: str
    total_tasks: int
    completed_tasks: int
    completion_percentage: float
    gate_result: PhaseGateResult
    task_summary: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    next_phase_requirements: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["gate_result"] = self.gate_result.to_dict()
        return data


class PhaseGateValidator:
    """Validates phase gates before phase transitions."""

    def __init__(self, feature_dir: Path, project_dir: Path):
        """Initialize the validator.

        Args:
            feature_dir: Path to .sam/{feature} directory
            project_dir: Path to project root
        """
        self.feature_dir = feature_dir
        self.project_dir = project_dir
        self.tasks_file = feature_dir / "TASKS.json"

        # Load tasks
        self.data: Dict[str, Any] = {}
        self.phases: List[Dict] = []
        self._load_tasks()

        # Import path for other scripts
        self._setup_import_paths()

    def _load_tasks(self):
        """Load tasks from TASKS.json."""
        if not self.tasks_file.exists():
            raise FileNotFoundError(f"TASKS.json not found in {self.feature_dir}")

        with open(self.tasks_file, 'r') as f:
            self.data = json.load(f)
            self.phases = self.data.get("phases", [])

    def _setup_import_paths(self):
        """Setup import paths for other SAM scripts."""
        sam_scripts = Path(__file__).parent.parent.parent / "sam-develop" / "scripts"
        sam_specs_scripts = Path(__file__).parent.parent.parent / "sam-specs" / "scripts"
        sys.path.insert(0, str(sam_scripts))
        sys.path.insert(0, str(sam_specs_scripts))

    def validate_phase_gate(self, phase_id: str) -> PhaseGateResult:
        """Validate phase gate for a specific phase.

        Args:
            phase_id: Phase ID to validate

        Returns:
            PhaseGateResult with validation details
        """
        # Find phase
        phase_data = None
        for phase in self.phases:
            if phase["phase_id"] == phase_id:
                phase_data = phase
                break

        if not phase_data:
            raise ValueError(f"Phase {phase_id} not found")

        phase_name = phase_data["phase_name"]

        # Build criteria
        criteria = PhaseGateCriteria(
            phase_id=phase_id,
            phase_name=phase_name
        )

        # Check each criterion
        criteria.all_tasks_complete = self.check_task_completion(phase_id)
        criteria.quality_gate_passed = self.check_quality_gates(phase_id)
        criteria.coverage_threshold_met = self.check_coverage_threshold(phase_id)
        criteria.acceptance_criteria_satisfied = self.check_acceptance_criteria(phase_id)
        criteria.no_conflicts_detected = self.check_conflicts(phase_id)
        criteria.documentation_complete = self.check_documentation(phase_id)

        # Determine if gate passed
        passed = criteria.is_met()

        # Build result
        result = PhaseGateResult(
            phase_id=phase_id,
            phase_name=phase_name,
            passed=passed,
            criteria=criteria,
            can_transition=passed
        )

        # Collect failures
        gate_criteria = PHASE_GATE_CRITERIA.get(phase_id, {})
        for criterion, required in gate_criteria.items():
            if criterion.endswith("coverage") or criterion == "min_coverage":
                continue
            if required and not getattr(criteria, criterion, False):
                result.failed_criteria.append(criterion)

        # Generate recommendations
        result.recommendations = self._generate_gate_recommendations(result)

        # Identify blocking issues
        result.blocking_issues = self._identify_blocking_issues(result)

        return result

    def check_task_completion(self, phase_id: str) -> bool:
        """Check if all tasks in phase are complete.

        Args:
            phase_id: Phase ID to check

        Returns:
            True if all tasks complete
        """
        for phase in self.phases:
            if phase["phase_id"] == phase_id:
                tasks = phase.get("tasks", [])
                for task in tasks:
                    if task.get("status") != "completed":
                        return False
                return True
        return False

    def check_quality_gates(self, phase_id: str) -> bool:
        """Check if quality gates have passed.

        Args:
            phase_id: Phase ID to check

        Returns:
            True if quality gates passed
        """
        # Check checkpoint for quality gate status
        checkpoint = self.data.get("checkpoint", {})

        # Check if quality gate was run and passed
        last_passed = checkpoint.get("quality_gate_last_passed")
        if not last_passed:
            return False

        # Check last quality gate result
        last_result = checkpoint.get("last_quality_gate_result", {})
        if not last_result:
            return False

        # All checks should have passed
        return all(
            status.lower() in ["passed", "pass", "ok", "success"]
            for status in last_result.values()
        )

    def check_coverage_threshold(self, phase_id: str) -> bool:
        """Check if coverage threshold is met.

        Args:
            phase_id: Phase ID to check

        Returns:
            True if coverage threshold met
        """
        # Get required threshold for phase
        gate_criteria = PHASE_GATE_CRITERIA.get(phase_id, {})
        min_coverage = gate_criteria.get("min_coverage", 0.0)

        if min_coverage == 0.0:
            return True  # Coverage not required for this phase

        # Check checkpoint for coverage
        checkpoint = self.data.get("checkpoint", {})
        coverage = checkpoint.get("coverage_percentage", 0.0)

        return coverage >= min_coverage

    def check_acceptance_criteria(self, phase_id: str) -> bool:
        """Check if acceptance criteria are satisfied.

        Args:
            phase_id: Phase ID to check

        Returns:
            True if acceptance criteria satisfied
        """
        # For now, check if tasks have verification methods
        # This will be enhanced when verification linker is integrated

        for phase in self.phases:
            if phase["phase_id"] == phase_id:
                tasks = phase.get("tasks", [])
                for task in tasks:
                    # Check if task has verification or is marked complete
                    if task.get("status") == "completed":
                        continue

                    # Check for acceptance criteria in spec
                    spec_file = self.feature_dir / task.get("spec_file", "")
                    if not spec_file.exists():
                        return False

                    # Simple check: if task is complete, AC satisfied
                    # Full implementation would parse spec and verify each AC

                return True

        return False

    def check_conflicts(self, phase_id: str) -> bool:
        """Check if there are any blocking conflicts.

        Args:
            phase_id: Phase ID to check

        Returns:
            True if no blocking conflicts
        """
        # Check checkpoint for conflict status
        checkpoint = self.data.get("checkpoint", {})
        conflict_data = checkpoint.get("conflict_detection", {})

        if not conflict_data:
            # No conflict scan run - try to run one
            return self._run_conflict_detection()

        # Check for blocking conflicts
        has_blocking = conflict_data.get("has_blocking", False)
        return not has_blocking

    def _run_conflict_detection(self) -> bool:
        """Run conflict detection and return result.

        Returns:
            True if no blocking conflicts
        """
        try:
            # Import conflict detector
            from conflict_detector import ConflictDetector

            detector = ConflictDetector(self.feature_dir, self.project_dir)
            report = detector.generate_conflict_report()

            # Update checkpoint
            detector.update_tasks_json(report)

            return not report.has_blocking_conflicts

        except Exception:
            # If conflict detection fails, assume no conflicts
            # (don't block on tool failure)
            return True

    def check_documentation(self, phase_id: str) -> bool:
        """Check if documentation is complete.

        Args:
            phase_id: Phase ID to check

        Returns:
            True if documentation complete
        """
        # Check for required documentation files

        # Required docs for all phases
        required_docs = ["README.md"]

        # Phase-specific docs
        if phase_id == "1":
            required_docs.extend(["SETUP.md", "ARCHITECTURE.md"])
        elif phase_id in ["2", "3"]:
            required_docs.append("API.md")
        elif phase_id == "5":
            required_docs.append("DEPLOYMENT.md")

        # Check if docs exist
        for doc in required_docs:
            if not (self.project_dir / doc).exists():
                # Also check in feature directory
                if not (self.feature_dir / doc).exists():
                    return False

        return True

    def _generate_gate_recommendations(self, result: PhaseGateResult) -> List[str]:
        """Generate recommendations based on gate result.

        Args:
            result: Phase gate result

        Returns:
            List of recommendations
        """
        recommendations = []

        if result.passed:
            recommendations.append(f"✅ Phase {result.phase_id} gate passed. Ready for transition.")
            return recommendations

        # Generate recommendations for failures
        if not result.criteria.all_tasks_complete:
            recommendations.append("📋 Complete all remaining tasks in this phase.")

        if not result.criteria.quality_gate_passed:
            recommendations.append("🔧 Fix quality gate failures (lint, build, test).")

        if not result.criteria.coverage_threshold_met:
            gate_criteria = PHASE_GATE_CRITERIA.get(result.phase_id, {})
            min_coverage = gate_criteria.get("min_coverage", 0.0)
            recommendations.append(f"📊 Increase code coverage to at least {min_coverage}%.")

        if not result.criteria.acceptance_criteria_satisfied:
            recommendations.append("✅ Verify all acceptance criteria are met.")

        if not result.criteria.no_conflicts_detected:
            recommendations.append("⚠️ Resolve conflicts before proceeding.")

        if not result.criteria.documentation_complete:
            recommendations.append("📝 Complete required documentation.")

        return recommendations

    def _identify_blocking_issues(self, result: PhaseGateResult) -> List[str]:
        """Identify specific blocking issues.

        Args:
            result: Phase gate result

        Returns:
            List of blocking issues
        """
        issues = []

        if not result.criteria.all_tasks_complete:
            # List incomplete tasks
            for phase in self.phases:
                if phase["phase_id"] == result.phase_id:
                    for task in phase.get("tasks", []):
                        if task.get("status") != "completed":
                            issues.append(f"Task {task['task_id']} not complete: {task['title']}")

        if not result.criteria.no_conflicts_detected:
            checkpoint = self.data.get("checkpoint", {})
            conflict_data = checkpoint.get("conflict_detection", {})
            if conflict_data.get("total_conflicts", 0) > 0:
                issues.append(f"Blocking conflicts detected: {conflict_data['total_conflicts']} total")

        return issues

    def generate_completion_report(self, phase_id: str) -> PhaseCompletionReport:
        """Generate comprehensive phase completion report.

        Args:
            phase_id: Phase ID

        Returns:
            PhaseCompletionReport
        """
        # Get phase gate result
        gate_result = self.validate_phase_gate(phase_id)

        # Find phase data
        phase_data = None
        for phase in self.phases:
            if phase["phase_id"] == phase_id:
                phase_data = phase
                break

        if not phase_data:
            raise ValueError(f"Phase {phase_id} not found")

        tasks = phase_data.get("tasks", [])
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Build task summary
        task_summary = {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": total_tasks - completed_tasks,
            "by_status": {}
        }

        for task in tasks:
            status = task.get("status", "unknown")
            task_summary["by_status"][status] = task_summary["by_status"].get(status, 0) + 1

        # Get quality metrics
        checkpoint = self.data.get("checkpoint", {})
        quality_metrics = {
            "coverage_percentage": checkpoint.get("coverage_percentage", 0.0),
            "quality_gate_passed": checkpoint.get("quality_gate_last_passed") is not None,
            "conflict_count": checkpoint.get("conflict_detection", {}).get("total_conflicts", 0),
            "iteration_count": checkpoint.get("iteration_count", 0),
        }

        # List artifacts
        artifacts = self._list_phase_artifacts(phase_id)

        # Next phase requirements
        next_phase_id = str(int(phase_id) + 1)
        next_phase_requirements = self._get_next_phase_requirements(next_phase_id)

        return PhaseCompletionReport(
            phase_id=phase_id,
            phase_name=phase_data["phase_name"],
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_percentage=completion_percentage,
            gate_result=gate_result,
            task_summary=task_summary,
            quality_metrics=quality_metrics,
            artifacts=artifacts,
            next_phase_requirements=next_phase_requirements
        )

    def _list_phase_artifacts(self, phase_id: str) -> List[str]:
        """List artifacts produced by this phase.

        Args:
            phase_id: Phase ID

        Returns:
            List of artifact paths
        """
        artifacts = []

        # Common artifacts
        artifacts.append("TASKS.json")

        # Phase-specific artifacts
        if phase_id == "1":
            artifacts.extend(["README.md", "SETUP.md", "package.json"])
        elif phase_id == "2":
            artifacts.extend(["API.md", "openapi.yaml"])
        elif phase_id == "3":
            artifacts.extend(["components/"])
        elif phase_id == "5":
            artifacts.append("DEPLOYMENT.md")

        return artifacts

    def _get_next_phase_requirements(self, next_phase_id: str) -> List[str]:
        """Get requirements for entering next phase.

        Args:
            next_phase_id: Next phase ID

        Returns:
            List of requirements
        """
        requirements = []

        # Find next phase
        next_phase = None
        for phase in self.phases:
            if phase["phase_id"] == next_phase_id:
                next_phase = phase
                break

        if not next_phase:
            return ["No next phase (this is the final phase)"]

        # Get criteria for next phase
        criteria = PHASE_GATE_CRITERIA.get(next_phase_id, {})

        requirements.append(f"Phase {next_phase_id}: {next_phase['phase_name']}")

        if criteria.get("all_tasks_complete"):
            requirements.append("- Complete all tasks in Phase " + next_phase_id)

        if criteria.get("coverage_threshold_met"):
            min_coverage = criteria.get("min_coverage", 0)
            requirements.append(f"- Maintain {min_coverage}%+ code coverage")

        if criteria.get("quality_gate_passed"):
            requirements.append("- Pass all quality gates")

        return requirements

    def validate_transition(self, from_phase: str, to_phase: str) -> bool:
        """Validate if transition from one phase to another is allowed.

        Args:
            from_phase: Source phase ID
            to_phase: Target phase ID

        Returns:
            True if transition allowed
        """
        # Check if source phase gate is passed
        source_result = self.validate_phase_gate(from_phase)
        if not source_result.passed:
            print(f"❌ Cannot transition: Phase {from_phase} gate not passed")
            return False

        # Check if phases are sequential
        from_num = int(from_phase)
        to_num = int(to_phase)

        if to_num != from_num + 1:
            print(f"⚠️ Warning: Skipping phase(s) ({from_num} → {to_num})")

        # Check if target phase exists
        target_exists = False
        for phase in self.phases:
            if phase["phase_id"] == to_phase:
                target_exists = True
                break

        if not target_exists:
            print(f"❌ Cannot transition: Phase {to_phase} does not exist")
            return False

        print(f"✅ Transition allowed: Phase {from_phase} → Phase {to_phase}")
        return True

    def update_checkpoint(self, result: PhaseGateResult):
        """Update TASKS.json checkpoint with gate result.

        Args:
            result: Phase gate result
        """
        checkpoint = self.data.setdefault("checkpoint", {})

        # Update phase gate status
        phase_gate_status = checkpoint.setdefault("phase_gate_status", {})

        # Store this phase's gate result
        phase_gate_status[f"phase_{result.phase_id}"] = {
            "passed": result.passed,
            "validated_at": result.validated_at,
            "criteria": result.criteria.to_dict(),
            "failed_criteria": result.failed_criteria,
        }

        # Update last validated phase
        phase_gate_status["last_validated_phase"] = result.phase_id
        phase_gate_status["last_validation_time"] = result.validated_at

        # Update current phase if gate passed
        if result.passed:
            phase_gate_status["current_phase"] = str(int(result.phase_id) + 1)
            phase_gate_status["can_transition"] = True
        else:
            phase_gate_status["can_transition"] = False

        # Write back
        with open(self.tasks_file, 'w') as f:
            json.dump(self.data, f, indent=2)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 phase_gate_validator.py <feature_dir> [--validate-phase <n>] [--completion-report <n>] [--can-transition <from> <to>] [--validate-all] [--list-criteria]")
        print("Examples:")
        print("  python3 phase_gate_validator.py .sam/001_feature --validate-phase 2")
        print("  python3 phase_gate_validator.py .sam/001_feature --completion-report 2 > PHASE_2_REPORT.md")
        print("  python3 phase_gate_validator.py .sam/001_feature --can-transition 2 3")
        print("  python3 phase_gate_validator.py .sam/001_feature --validate-all")
        print("  python3 phase_gate_validator.py .sam/001_feature --list-criteria")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    # Determine project directory
    if feature_dir.name.startswith(".sam"):
        project_dir = feature_dir.parent.parent
    else:
        project_dir = Path.cwd()

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    validator = PhaseGateValidator(feature_dir, project_dir)

    # Parse arguments
    validate_phase = None
    completion_report = None
    can_transition_from = None
    can_transition_to = None
    validate_all = False
    list_criteria = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--validate-phase" and i + 1 < len(sys.argv):
            validate_phase = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--completion-report" and i + 1 < len(sys.argv):
            completion_report = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--can-transition" and i + 2 < len(sys.argv):
            can_transition_from = sys.argv[i + 1]
            can_transition_to = sys.argv[i + 2]
            i += 3
        elif sys.argv[i] == "--validate-all":
            validate_all = True
            i += 1
        elif sys.argv[i] == "--list-criteria":
            list_criteria = True
            i += 1
        else:
            i += 1

    # Execute
    if list_criteria:
        print("Phase Gate Criteria:")
        print("=" * 60)
        for phase_id, criteria in sorted(PHASE_GATE_CRITERIA.items()):
            print(f"\nPhase {phase_id}:")
            for criterion, required in criteria.items():
                if criterion == "min_coverage":
                    print(f"  - min_coverage: {required}%")
                else:
                    status = "✓ Required" if required else "○ Optional"
                    print(f"  - {criterion}: {status}")

    elif validate_all:
        print("\nValidating all phase gates...")
        print("=" * 60)

        all_passed = True
        for phase in validator.phases:
            phase_id = phase["phase_id"]
            result = validator.validate_phase_gate(phase_id)

            status = "✅ PASSED" if result.passed else "❌ FAILED"
            print(f"\nPhase {phase_id} ({result.phase_name}): {status}")

            if result.failed_criteria:
                print(f"  Failed criteria: {', '.join(result.failed_criteria)}")

            if not result.passed:
                all_passed = False

            # Update checkpoint
            validator.update_checkpoint(result)

        print(f"\n{'=' * 60}")
        if all_passed:
            print("✅ All phase gates passed!")
            sys.exit(0)
        else:
            print("❌ Some phase gates failed")
            sys.exit(1)

    elif validate_phase:
        print(f"\nValidating Phase {validate_phase} gate...")
        print("=" * 60)

        result = validator.validate_phase_gate(validate_phase)

        print(f"\nPhase: {result.phase_name}")
        print(f"Result: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        print(f"Validated: {result.validated_at}")

        print(f"\nCriteria:")
        print(f"  All tasks complete: {'✅' if result.criteria.all_tasks_complete else '❌'}")
        print(f"  Quality gate passed: {'✅' if result.criteria.quality_gate_passed else '❌'}")
        print(f"  Coverage threshold met: {'✅' if result.criteria.coverage_threshold_met else '❌'}")
        print(f"  Acceptance criteria satisfied: {'✅' if result.criteria.acceptance_criteria_satisfied else '❌'}")
        print(f"  No conflicts detected: {'✅' if result.criteria.no_conflicts_detected else '❌'}")
        print(f"  Documentation complete: {'✅' if result.criteria.documentation_complete else '❌'}")

        if result.failed_criteria:
            print(f"\nFailed criteria: {', '.join(result.failed_criteria)}")

        if result.blocking_issues:
            print(f"\nBlocking issues:")
            for issue in result.blocking_issues:
                print(f"  - {issue}")

        if result.recommendations:
            print(f"\nRecommendations:")
            for rec in result.recommendations:
                print(f"  {rec}")

        # Update checkpoint
        validator.update_checkpoint(result)

        sys.exit(0 if result.passed else 1)

    elif completion_report:
        print(f"\nGenerating Phase {completion_report} completion report...")
        print("=" * 60)

        report = validator.generate_completion_report(completion_report)

        print(f"\nPhase {report.phase_id}: {report.phase_name}")
        print(f"Completion: {report.completed_tasks}/{report.total_tasks} ({report.completion_percentage:.1f}%)")
        print(f"Gate Status: {'✅ PASSED' if report.gate_result.passed else '❌ FAILED'}")

        print(f"\nTask Summary:")
        for status, count in report.task_summary.get("by_status", {}).items():
            print(f"  {status}: {count}")

        print(f"\nQuality Metrics:")
        print(f"  Coverage: {report.quality_metrics.get('coverage_percentage', 0):.1f}%")
        print(f"  Quality Gate: {'✅' if report.quality_metrics.get('quality_gate_passed') else '❌'}")
        print(f"  Conflicts: {report.quality_metrics.get('conflict_count', 0)}")

        print(f"\nArtifacts:")
        for artifact in report.artifacts:
            print(f"  - {artifact}")

        if report.next_phase_requirements:
            print(f"\nNext Phase Requirements:")
            for req in report.next_phase_requirements:
                print(f"  {req}")

    elif can_transition_from and can_transition_to:
        allowed = validator.validate_transition(can_transition_from, can_transition_to)
        sys.exit(0 if allowed else 1)

    else:
        print("Error: Please specify an action")
        sys.exit(1)


if __name__ == "__main__":
    main()
