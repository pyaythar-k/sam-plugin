#!/usr/bin/env python3
"""
verification_linker.py - Task-to-verification linking for traceability

This script links tasks to their verification methods (tests, checks) and
generates traceability matrices showing requirements through implementation
to tests.

Usage:
    python3 verification_linker.py .sam/{feature} --discover
    python3 verification_linker.py .sam/{feature} --task 2.1.3 --status
    python3 verification_linker.py .sam/{feature} --matrix > traceability.md
    python3 verification_linker.py .sam/{feature} --find-gaps
    python3 verification_linker.py .sam/{feature} --verify 2.1.3

Output:
    Updates TASKS.json with verification_methods
    Generates traceability matrix
    Lists verification gaps
"""

import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class VerificationMethod:
    """A verification method for a task."""
    method_id: str
    method_type: str  # "unit_test", "integration_test", "e2e_test", "contract_test", "manual_check"
    name: str
    file_path: str
    line_range: Tuple[int, int]
    coverage: List[str]  # What this verifies (requirements, acceptance criteria)
    status: str  # "passed", "failed", "skipped", "pending"
    last_run: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["line_range"] = list(self.line_range)  # Convert tuple to list
        return data


@dataclass
class TaskVerification:
    """Verification status for a task."""
    task_id: str
    verification_methods: List[VerificationMethod] = field(default_factory=list)
    overall_status: str = "pending"  # "verified", "failed", "partial", "pending"
    verified_criteria: List[str] = field(default_factory=list)
    unverified_criteria: List[str] = field(default_factory=list)
    last_verified: Optional[str] = None
    coverage_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["verification_methods"] = [m.to_dict() for m in self.verification_methods]
        return data


@dataclass
class TraceabilityMatrix:
    """Traceability matrix for requirements-to-tests."""
    task_id: str
    task_title: str
    requirement: str
    acceptance_criteria: List[str]
    verification_methods: List[str]
    coverage_percentage: float
    gaps: List[str] = field(default_factory=list)


class VerificationLinker:
    """Links tasks to verification methods."""

    # Test patterns for extracting task IDs
    TEST_PATTERNS = [
        r"test[_-]?task[_-]?([\d.]+)",           # test_task_1_2_3
        r"test[_-]?(\d+[_-]\d+[_-]?\d*)",       # test_1_2_3
        r"task[_-]?(\d+[_-]\d+[_-]?\d*)[_-]?test",  # task_1_2_3_test
        r"spec[_-]?task[_-]?([\d.]+)",           # spec_task_1.2.3
        r"it[_-]?task[_-]?([\d.]+)",             # it_task_1.2.3
    ]

    # Verification annotation patterns
    VERIFICATION_PATTERNS = [
        r"@verifies\s+task\s+([\d.]+)",          # @verifies task 1.2.3
        r"@verifies\s+([\d.]+)",                 # @verifies 1.2.3
        r"#\s*verifies:\s*task\s+([\d.]+)",      # verifies: task 1.2.3
        r"//\s*verifies:\s*task\s+([\d.]+)",     # verifies: task 1.2.3
    ]

    # Test directory patterns
    TEST_DIRECTORIES = [
        "tests", "test", "__tests__", "spec", "specs",
        "test/unit", "test/integration", "test/e2e",
        "tests/unit", "tests/integration", "tests/e2e",
        "__tests__/unit", "__tests__/integration",
    ]

    # Test file extensions
    TEST_EXTENSIONS = {
        ".test.ts", ".test.tsx", ".test.js", ".test.jsx",
        ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx",
        "_test.ts", "_test.tsx", "_test.js", "_test.jsx",
        "_spec.ts", "_spec.tsx", "_spec.js", "_spec.jsx",
        ".test.py", "_test.py",
        "_test.rb", ".test.rb",
    }

    def __init__(self, feature_dir: Path, project_dir: Path):
        """Initialize the verification linker.

        Args:
            feature_dir: Path to .sam/{feature} directory
            project_dir: Path to project root
        """
        self.feature_dir = feature_dir
        self.project_dir = project_dir
        self.tasks_file = feature_dir / "TASKS.json"

        # Load tasks
        self.tasks: Dict[str, Dict] = {}
        self.specs: Dict[str, Path] = {}  # task_id -> spec file
        self._load_tasks()

        # Discovered verification methods
        self.verification_methods: Dict[str, List[VerificationMethod]] = defaultdict(list)
        self.test_tasks: Dict[str, Set[str]] = defaultdict(set)  # test_file -> task_ids
        self.task_tests: Dict[str, Set[str]] = defaultdict(set)  # task_id -> test_files

    def _load_tasks(self):
        """Load tasks from TASKS.json."""
        if not self.tasks_file.exists():
            raise FileNotFoundError(f"TASKS.json not found in {self.feature_dir}")

        with open(self.tasks_file, 'r') as f:
            data = json.load(f)

        for phase in data.get("phases", []):
            for task in phase.get("tasks", []):
                task_id = task["task_id"]
                self.tasks[task_id] = task

                # Store spec file path
                spec_file = task.get("spec_file", "TECHNICAL_SPEC.md")
                full_spec_path = self.feature_dir / spec_file
                if full_spec_path.exists():
                    self.specs[task_id] = full_spec_path

    def discover_verification_methods(self) -> Dict[str, List[VerificationMethod]]:
        """Discover all verification methods in the codebase.

        Returns:
            Dictionary mapping task_id to list of VerificationMethod objects
        """
        # Find all test files
        test_files = self._find_test_files()

        for test_file in test_files:
            self._parse_test_file(test_file)

        # Group by task
        for test_file, task_ids in self.test_tasks.items():
            for task_id in task_ids:
                self.task_tests[task_id].add(test_file)

        # Build verification methods for each task
        for task_id in self.tasks:
            methods = self._build_verification_methods(task_id)
            self.verification_methods[task_id] = methods

        return dict(self.verification_methods)

    def _find_test_files(self) -> List[Path]:
        """Find all test files in the project.

        Returns:
            List of test file paths
        """
        test_files = []

        # Check common test directories
        for test_dir in self.TEST_DIRECTORIES:
            test_path = self.project_dir / test_dir
            if test_path.exists():
                for ext in self.TEST_EXTENSIONS:
                    test_files.extend(test_path.rglob(f"*{ext}"))

        # Also check for test files anywhere in the project
        for ext in self.TEST_EXTENSIONS:
            test_files.extend(self.project_dir.rglob(f"*{ext}"))

        # Remove duplicates and sort
        test_files = sorted(set(test_files))

        # Filter out node_modules and similar
        test_files = [
            f for f in test_files
            if not any(skip in f.parts for skip in ["node_modules", ".git", "dist", "build"])
        ]

        return test_files

    def _parse_test_file(self, test_file: Path):
        """Parse a test file to find task references.

        Args:
            test_file: Path to test file
        """
        try:
            content = test_file.read_text()
            lines = content.splitlines()

            # Check filename for task hints
            filename_task = self._extract_task_from_filename(test_file)

            # Scan each test block
            test_blocks = self._extract_test_blocks(content, test_file.suffix)

            for block in test_blocks:
                # Check test name for task ID
                task_id = self._extract_task_from_test_name(block["name"])

                # Check test body for verification annotations
                if not task_id:
                    task_id = self._extract_task_from_annotations(block["body"])

                # Fall back to filename task
                if not task_id and filename_task:
                    task_id = filename_task

                if task_id:
                    # Determine test type
                    test_type = self._infer_test_type(test_file)

                    # Create verification method
                    method = VerificationMethod(
                        method_id=f"{test_file.stem}#{block['name'][:30]}",
                        method_type=test_type,
                        name=block["name"],
                        file_path=str(test_file.relative_to(self.project_dir)),
                        line_range=(block["line_start"], block["line_end"]),
                        coverage=[],  # Will be filled by parse_test_descriptions
                        status="pending"
                    )

                    self.verification_methods[task_id].append(method)
                    self.test_tasks[str(test_file.relative_to(self.project_dir))].add(task_id)

        except (UnicodeDecodeError, IOError):
            pass

    def _extract_task_from_filename(self, test_file: Path) -> Optional[str]:
        """Extract task ID from test filename.

        Args:
            test_file: Path to test file

        Returns:
            Task ID if found, None otherwise
        """
        name = test_file.stem.lower()

        # Check for task patterns
        for pattern in self.TEST_PATTERNS:
            match = re.search(pattern, name)
            if match:
                task_str = match.group(1).replace("_", ".")
                return self._normalize_task_id(task_str)

        return None

    def _extract_test_blocks(self, content: str, file_ext: str) -> List[Dict]:
        """Extract individual test blocks from test file content.

        Args:
            content: Test file content
            file_ext: File extension

        Returns:
            List of test block dicts with name, body, line numbers
        """
        blocks = []
        lines = content.splitlines()

        if file_ext in [".ts", ".tsx", ".js", ".jsx"]:
            blocks.extend(self._extract_jest_blocks(lines))
        elif file_ext == ".py":
            blocks.extend(self._extract_pytest_blocks(lines))
        elif file_ext in [".rb"]:
            blocks.extend(self._extract_rspec_blocks(lines))

        return blocks

    def _extract_jest_blocks(self, lines: List[str]) -> List[Dict]:
        """Extract test blocks from Jest/Jasmine style tests.

        Args:
            lines: File lines

        Returns:
            List of test blocks
        """
        blocks = []
        current_block = None
        brace_depth = 0

        for i, line in enumerate(lines, 1):
            # Detect test start
            match = re.search(r"(?:it|test|describe)\s*\(\s*['\"]([^'\"]+)['\"]", line)
            if match and current_block is None:
                current_block = {
                    "name": match.group(1),
                    "body": [],
                    "line_start": i,
                    "line_end": i
                }
                brace_depth = line.count("{") - line.count("}")
                continue

            # Track block body
            if current_block:
                current_block["body"].append(line)
                brace_depth += line.count("{") - line.count("}")

                # Check if block ended
                if brace_depth == 0:
                    current_block["line_end"] = i
                    blocks.append(current_block)
                    current_block = None

        return blocks

    def _extract_pytest_blocks(self, lines: List[str]) -> List[Dict]:
        """Extract test blocks from pytest style tests.

        Args:
            lines: File lines

        Returns:
            List of test blocks
        """
        blocks = []

        for i, line in enumerate(lines, 1):
            # Look for def test_ or async def test_
            match = re.search(r"(?:async\s+)?def\s+(test_\w+)", line)
            if match:
                # Find the end of the function (next def or end of file)
                end_line = i
                for j in range(i, len(lines)):
                    if j > i and re.search(r"^\s*def\s+", lines[j]):
                        end_line = j - 1
                        break
                    end_line = j + 1

                blocks.append({
                    "name": match.group(1),
                    "body": lines[i:end_line],
                    "line_start": i,
                    "line_end": end_line
                })

        return blocks

    def _extract_rspec_blocks(self, lines: List[str]) -> List[Dict]:
        """Extract test blocks from RSpec style tests.

        Args:
            lines: File lines

        Returns:
            List of test blocks
        """
        blocks = []

        for i, line in enumerate(lines, 1):
            # Look for it or specify blocks
            match = re.search(r"(it|specify)\s+['\"]([^'\"]+)['\"]", line)
            if match:
                # Find the end of the block
                end_line = i + 1
                for j in range(i + 1, len(lines)):
                    if re.search(r"^\s*end\s*$", lines[j]):
                        end_line = j
                        break

                blocks.append({
                    "name": match.group(2),
                    "body": lines[i:end_line + 1],
                    "line_start": i,
                    "line_end": end_line
                })

        return blocks

    def _extract_task_from_test_name(self, test_name: str) -> Optional[str]:
        """Extract task ID from test name.

        Args:
            test_name: Test name/description

        Returns:
            Task ID if found, None otherwise
        """
        test_name_lower = test_name.lower()

        for pattern in self.TEST_PATTERNS:
            match = re.search(pattern, test_name_lower)
            if match:
                task_str = match.group(1).replace("_", ".")
                return self._normalize_task_id(task_str)

        return None

    def _extract_task_from_annotations(self, test_body: List[str]) -> Optional[str]:
        """Extract task ID from verification annotations in test body.

        Args:
            test_body: Test body lines

        Returns:
            Task ID if found, None otherwise
        """
        for line in test_body[:20]:  # Check first 20 lines
            for pattern in self.VERIFICATION_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    return self._normalize_task_id(match.group(1))

        return None

    def _normalize_task_id(self, task_id: str) -> str:
        """Normalize task ID to standard format.

        Args:
            task_id: Raw task ID

        Returns:
            Normalized task ID
        """
        # Replace underscores/hyphens with dots
        normalized = task_id.replace("_", ".").replace("-", ".")

        # Remove leading zeros
        parts = normalized.split(".")
        normalized = ".".join(str(int(p)) if p.isdigit() else p for p in parts)

        return normalized

    def _infer_test_type(self, test_file: Path) -> str:
        """Infer test type from file path.

        Args:
            test_file: Path to test file

        Returns:
            Test type: "unit_test", "integration_test", "e2e_test", "contract_test"
        """
        path_str = str(test_file).lower()

        if "e2e" in path_str or "end-to-end" in path_str:
            return "e2e_test"
        elif "integration" in path_str:
            return "integration_test"
        elif "contract" in path_str:
            return "contract_test"
        else:
            return "unit_test"

    def _build_verification_methods(self, task_id: str) -> List[VerificationMethod]:
        """Build verification methods list for a task.

        Args:
            task_id: Task ID

        Returns:
            List of VerificationMethod objects
        """
        methods = self.verification_methods.get(task_id, [])

        # Add manual checks if needed
        task = self.tasks.get(task_id, {})
        if not task:
            return methods

        # Check if task has acceptance criteria that need manual verification
        spec_file = self.specs.get(task_id)
        if spec_file:
            acceptance_criteria = self._extract_acceptance_criteria(spec_file, task_id)
            if acceptance_criteria and not methods:
                # Add manual check placeholder
                methods.append(VerificationMethod(
                    method_id=f"manual_{task_id}",
                    method_type="manual_check",
                    name=f"Manual verification for {task_id}",
                    file_path="",
                    line_range=(0, 0),
                    coverage=acceptance_criteria,
                    status="pending"
                ))

        return methods

    def _extract_acceptance_criteria(self, spec_file: Path, task_id: str) -> List[str]:
        """Extract acceptance criteria for a task from spec file.

        Args:
            spec_file: Path to spec file
            task_id: Task ID

        Returns:
            List of acceptance criteria strings
        """
        try:
            content = spec_file.read_text()

            # Look for task section
            task_pattern = rf"##*\s*Task\s+{re.escape(task_id)}\b"
            task_match = re.search(task_pattern, content, re.IGNORECASE)

            if not task_match:
                return []

            # Extract section content
            start_pos = task_match.start()
            # Find next task section or end of file
            next_task = re.search(r"\n##+\s*Task\s+\d", content[start_pos + 1:])
            if next_task:
                end_pos = start_pos + 1 + next_task.start()
            else:
                end_pos = len(content)

            section_content = content[start_pos:end_pos]

            # Extract acceptance criteria
            ac_pattern = r"(?:Acceptance Criteria|AC):\s*\n((?:\s*-\s*[^\n]+\n)*)"
            ac_match = re.search(ac_pattern, section_content, re.IGNORECASE)

            if ac_match:
                criteria_text = ac_match.group(1)
                criteria = [
                    line.strip().lstrip("-").strip()
                    for line in criteria_text.splitlines()
                    if line.strip()
                ]
                return criteria

        except (UnicodeDecodeError, IOError):
            pass

        return []

    def link_task_to_tests(self, task_id: str) -> TaskVerification:
        """Get verification status for a specific task.

        Args:
            task_id: Task ID

        Returns:
            TaskVerification with verification status
        """
        methods = self.verification_methods.get(task_id, [])

        # Get acceptance criteria
        spec_file = self.specs.get(task_id)
        acceptance_criteria = []
        if spec_file:
            acceptance_criteria = self._extract_acceptance_criteria(spec_file, task_id)

        # Collect covered criteria
        covered = set()
        for method in methods:
            covered.update(method.coverage)

        verified_criteria = list(covered)
        unverified_criteria = [ac for ac in acceptance_criteria if ac not in covered]

        # Determine overall status
        if not methods:
            overall_status = "pending"
        elif all(m.status == "passed" for m in methods):
            overall_status = "verified"
        elif any(m.status == "failed" for m in methods):
            overall_status = "failed"
        else:
            overall_status = "partial"

        # Calculate coverage
        total_criteria = len(acceptance_criteria)
        coverage_percentage = (len(covered) / total_criteria * 100) if total_criteria > 0 else 0

        return TaskVerification(
            task_id=task_id,
            verification_methods=methods,
            overall_status=overall_status,
            verified_criteria=verified_criteria,
            unverified_criteria=unverified_criteria,
            coverage_percentage=coverage_percentage
        )

    def parse_test_descriptions(self) -> Dict[str, List[str]]:
        """Parse test descriptions to extract requirement references.

        Returns:
            Dictionary mapping task_id to list of covered requirements
        """
        # This would parse test descriptions for requirement references
        # For now, return empty dict
        return {}

    def generate_traceability_matrix(self) -> List[TraceabilityMatrix]:
        """Generate traceability matrix for all tasks.

        Returns:
            List of TraceabilityMatrix objects
        """
        matrix = []

        for task_id, task in sorted(self.tasks.items()):
            verification = self.link_task_to_tests(task_id)

            # Get requirement from task
            # (This would normally come from user story)
            requirement = f"Task {task_id}: {task.get('title', '')}"

            # Get acceptance criteria
            spec_file = self.specs.get(task_id)
            acceptance_criteria = []
            if spec_file:
                acceptance_criteria = self._extract_acceptance_criteria(spec_file, task_id)

            # Get verification methods
            verification_methods = [
                f"{m.method_type}: {m.name}"
                for m in verification.verification_methods
            ]

            # Identify gaps
            gaps = verification.unverified_criteria

            matrix.append(TraceabilityMatrix(
                task_id=task_id,
                task_title=task.get('title', ''),
                requirement=requirement,
                acceptance_criteria=acceptance_criteria,
                verification_methods=verification_methods,
                coverage_percentage=verification.coverage_percentage,
                gaps=gaps
            ))

        return matrix

    def find_verification_gaps(self) -> List[str]:
        """Find tasks with missing or incomplete verification.

        Returns:
            List of gap descriptions
        """
        gaps = []

        for task_id, task in sorted(self.tasks.items()):
            verification = self.link_task_to_tests(task_id)

            if not verification.verification_methods:
                gaps.append(f"❌ Task {task_id}: No verification methods found")
            elif verification.overall_status == "pending":
                gaps.append(f"⏳ Task {task_id}: Verification not run")
            elif verification.overall_status == "failed":
                gaps.append(f"❌ Task {task_id}: Verification failed")
            elif verification.coverage_percentage < 100:
                gaps.append(f"⚠️ Task {task_id}: {verification.coverage_percentage:.0f}% coverage ({len(verification.unverified_criteria)} criteria uncovered)")

        return gaps

    def update_tasks_json(self):
        """Update TASKS.json with verification methods."""
        with open(self.tasks_file, 'r') as f:
            data = json.load(f)

        # Update each task with verification methods
        for phase in data.get("phases", []):
            for task in phase.get("tasks", []):
                task_id = task["task_id"]
                verification = self.link_task_to_tests(task_id)

                # Add verification methods
                task["verification_methods"] = [
                    m.to_dict() for m in verification.verification_methods
                ]

                # Add verification status
                task["verification_status"] = verification.overall_status
                task["verified_at"] = verification.last_verified
                task["verification_coverage"] = verification.coverage_percentage

        # Add verification summary to checkpoint
        checkpoint = data.setdefault("checkpoint", {})

        # Calculate overall verification status
        total_tasks = len(self.tasks)
        verified_tasks = sum(
            1 for task_id in self.tasks
            if self.link_task_to_tests(task_id).overall_status == "verified"
        )

        checkpoint["verification_status"] = {
            "total_tasks": total_tasks,
            "verified_tasks": verified_tasks,
            "verification_percentage": (verified_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "last_scan": datetime.now().isoformat()
        }

        # Write back
        with open(self.tasks_file, 'w') as f:
            json.dump(data, f, indent=2)

    def run_verification(self, task_id: str) -> TaskVerification:
        """Run verification for a specific task.

        Args:
            task_id: Task ID

        Returns:
            TaskVerification with updated status
        """
        verification = self.link_task_to_tests(task_id)

        if not verification.verification_methods:
            return verification

        # Run tests for this task
        test_files = self.task_tests.get(task_id, set())

        if not test_files:
            return verification

        # Run the test framework
        all_passed = True
        last_run = None

        for test_file in test_files:
            result = self._run_test_file(test_file)
            last_run = result.get("timestamp")

            # Update method statuses
            for method in verification.verification_methods:
                if method.file_path == test_file:
                    method.status = result.get("status", "failed")
                    method.last_run = last_run

                    if method.status != "passed":
                        all_passed = False

        # Update overall status
        if all_passed:
            verification.overall_status = "verified"
        elif any(m.status == "failed" for m in verification.verification_methods):
            verification.overall_status = "failed"
        else:
            verification.overall_status = "partial"

        verification.last_verified = last_run

        return verification

    def _run_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run a specific test file.

        Args:
            test_file: Path to test file

        Returns:
            Result dict with status and timestamp
        """
        try:
            # Determine test framework
            full_path = self.project_dir / test_file

            if full_path.suffix in [".ts", ".tsx", ".js", ".jsx"]:
                # Try Jest/Vitest
                result = subprocess.run(
                    ["npm", "test", "--", test_file, "--passWithNoTests"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                status = "passed" if result.returncode == 0 else "failed"
            elif full_path.suffix == ".py":
                # Try pytest
                result = subprocess.run(
                    ["python", "-m", "pytest", str(full_path), "-v"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                status = "passed" if result.returncode == 0 else "failed"
            else:
                status = "skipped"

            return {
                "status": status,
                "timestamp": datetime.now().isoformat()
            }

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "status": "skipped",
                "timestamp": datetime.now().isoformat()
            }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 verification_linker.py <feature_dir> [--discover] [--task <id> --status] [--matrix] [--find-gaps] [--verify <id>]")
        print("Examples:")
        print("  python3 verification_linker.py .sam/001_feature --discover")
        print("  python3 verification_linker.py .sam/001_feature --task 2.1.3 --status")
        print("  python3 verification_linker.py .sam/001_feature --matrix > traceability.md")
        print("  python3 verification_linker.py .sam/001_feature --find-gaps")
        print("  python3 verification_linker.py .sam/001_feature --verify 2.1.3")
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

    linker = VerificationLinker(feature_dir, project_dir)

    # Parse arguments
    discover = False
    check_task = None
    show_matrix = False
    find_gaps = False
    verify_task = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--discover":
            discover = True
            i += 1
        elif sys.argv[i] == "--task" and i + 1 < len(sys.argv):
            check_task = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--status":
            # Implicit with --task
            i += 1
        elif sys.argv[i] == "--matrix":
            show_matrix = True
            i += 1
        elif sys.argv[i] == "--find-gaps":
            find_gaps = True
            i += 1
        elif sys.argv[i] == "--verify" and i + 1 < len(sys.argv):
            verify_task = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Execute
    if discover:
        print("Discovering verification methods...")
        print("=" * 60)

        methods = linker.discover_verification_methods()

        print(f"Found verification methods for {len(methods)} tasks:")

        for task_id, task_methods in sorted(methods.items()):
            if task_methods:
                print(f"\nTask {task_id}: {len(task_methods)} methods")
                for method in task_methods:
                    print(f"  - [{method.method_type}] {method.name}")
            else:
                print(f"\nTask {task_id}: No verification methods")

        linker.update_tasks_json()
        print(f"\n✓ Updated TASKS.json")

    elif check_task:
        verification = linker.link_task_to_tests(check_task)

        print(f"\nVerification Status for Task {check_task}:")
        print(f"  Overall: {verification.overall_status.upper()}")
        print(f"  Coverage: {verification.coverage_percentage:.0f}%")
        print(f"  Methods: {len(verification.verification_methods)}")

        if verification.verification_methods:
            print(f"\n  Verification Methods:")
            for method in verification.verification_methods:
                print(f"    - [{method.method_type}] {method.name}")
                print(f"      Status: {method.status}")
                if method.coverage:
                    print(f"      Covers: {', '.join(method.coverage[:2])}")

        if verification.unverified_criteria:
            print(f"\n  Unverified Criteria:")
            for criteria in verification.unverified_criteria:
                print(f"    - {criteria}")

    elif show_matrix:
        print("# Traceability Matrix")
        print(f"Generated: {datetime.now().isoformat()}")
        print()

        matrix = linker.generate_traceability_matrix()

        # Table header
        print("| Task | Requirement | AC Covered | Verification Methods | Coverage |")
        print("|------|-------------|------------|----------------------|----------|")

        for row in matrix:
            ac_count = f"{len(row.acceptance_criteria) - len(row.gaps)}/{len(row.acceptance_criteria)}"
            methods = ", ".join(m[:20] + ["..."] if len(m) > 1 else m for m in row.verification_methods)
            print(f"| {row.task_id} | {row.task_title[:40]} | {ac_count} | {methods[:50]} | {row.coverage_percentage:.0f}% |")

        # Print gaps section
        gaps = linker.find_verification_gaps()
        if gaps:
            print("\n## Verification Gaps")
            for gap in gaps:
                print(f"- {gap}")

    elif find_gaps:
        print("Verification Gaps:")
        print("=" * 60)

        gaps = linker.find_verification_gaps()

        if gaps:
            for gap in gaps:
                print(f"  {gap}")
            print(f"\nTotal gaps: {len(gaps)}")
        else:
            print("  ✅ No verification gaps found!")

    elif verify_task:
        print(f"Running verification for task {verify_task}...")
        print("=" * 60)

        verification = linker.run_verification(verify_task)

        print(f"\nVerification Result: {verification.overall_status.upper()}")

        if verification.verification_methods:
            print(f"\nMethods:")
            for method in verification.verification_methods:
                status_icon = "✅" if method.status == "passed" else "❌" if method.status == "failed" else "⏳"
                print(f"  {status_icon} [{method.method_type}] {method.name}")

        # Update TASKS.json
        linker.update_tasks_json()

        sys.exit(0 if verification.overall_status == "verified" else 1)

    else:
        print("Error: Please specify an action")
        sys.exit(1)


if __name__ == "__main__":
    main()
