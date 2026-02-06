#!/usr/bin/env python3
"""
code_task_mapper.py - Bidirectional code-to-task mapping for traceability

This script provides comprehensive traceability between source code and tasks
by mapping code artifacts (files, functions, classes, endpoints) to their
implementing tasks through multiple discovery strategies.

Usage:
    python3 code_task_mapper.py .sam/{feature} --scan
    python3 code_task_mapper.py .sam/{feature} --map-file src/api/users.ts --line 45
    python3 code_task_mapper.py .sam/{feature} --task 2.1.3 --show-code
    python3 code_task_mapper.py .sam/{feature} --detect-new --baseline main~1
    python3 code_task_mapper.py .sam/{feature} --export-mappings > mappings.json

Output:
    Updates TASKS.json with code_mappings field
    Generates code-to-task mapping reports
"""

import sys
import json
import re
import ast
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field, asdict


@dataclass
class CodeMapping:
    """Maps a code artifact to its implementing task."""
    file_path: str
    task_id: str
    mapping_type: str  # "file", "function", "class", "endpoint"
    name: str  # Function/class name or endpoint path
    line_start: int
    line_end: int
    confidence: float = 1.0  # 0.0-1.0, based on discovery method
    discovery_method: str = "unknown"  # "annotation", "git_blame", "heuristic", "manual"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TaskCodeMap:
    """Aggregate code mappings for a task."""
    task_id: str
    files: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    total_lines: int = 0
    total_mappings: int = 0
    confidence_score: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def calculate_confidence(self) -> float:
        """Calculate overall confidence based on mappings."""
        if not self.total_mappings:
            return 0.0

        # Weight mapping types by reliability
        weights = {
            "annotation": 1.0,      # Explicit @task annotation
            "git_blame": 0.9,       # Commit message analysis
            "endpoint": 0.85,       # API route registration
            "heuristic": 0.6,       # Directory/file patterns
            "manual": 1.0           # Manual override
        }

        return min(1.0, sum(weights.get(m, 0.5) for m in []) / self.total_mappings)


@dataclass
class NewCodeDetection:
    """Result of new code detection since baseline."""
    baseline_commit: str
    new_mappings: List[CodeMapping] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    total_new_lines: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CodeTaskMapper:
    """Manages bidirectional code-to-task mapping."""

    # Task annotation patterns in different languages
    ANNOTATION_PATTERNS = {
        "python": [
            r"#\s*@task\s+([\d.]+)",           # # @task 1.2.3
            r"#\s*task:\s*([\d.]+)",           # # task: 1.2.3
            r'"""\s*@task\s+([\d.]+)',         # """ @task 1.2.3
        ],
        "javascript": [
            r"//\s*@task\s+([\d.]+)",          # // @task 1.2.3
            r"//\s*task:\s*([\d.]+)",          # // task: 1.2.3
            r"/\*\s*@task\s+([\d.]+)\s*\*/",   # /* @task 1.2.3 */
        ],
        "typescript": [
            r"//\s*@task\s+([\d.]+)",          # // @task 1.2.3
            r"//\s*task:\s*([\d.]+)",          # // task: 1.2.3
        ],
        "rust": [
            r"//\s*@task\s+([\d.]+)",          # // @task 1.2.3
            r"//!\s*@task\s+([\d.]+)",         # //! @task 1.2.3
        ],
        "go": [
            r"//\s*@task\s+([\d.]+)",          # // @task 1.2.3
        ]
    }

    # Commit message patterns for git blame
    COMMIT_PATTERNS = [
        r"feat(?:ute)?(?:\(|:)\s*(?:task\s+)?([\d.]+)",  # feat: task 1.2.3
        r"fix(?:\(|:)\s*(?:task\s+)?([\d.]+)",           # fix: task 1.2.3
        r"implement\s+task\s+([\d.]+)",                   # implement task 1.2.3
        r"complete\s+task\s+([\d.]+)",                    # complete task 1.2.3
        r"\[([\d.]+)\]",                                  # [1.2.3]
    ]

    # Directory structure patterns
    DIRECTORY_PATTERNS = [
        r"features?[/_-]?(\d+)[/_-]",                     # features/001 or feature-001
        r"task[/_-]?(\d+[.\d]*)",                         # task/1.2.3
        r"(?:phase|p)[_-]?(\d+)[/_-]",                    # phase_1 or p-1
    ]

    # API endpoint detection patterns
    ENDPOINT_PATTERNS = {
        "express": [
            r"(?:router\.)?(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        ],
        "fastapi": [
            r"@(?:router\.)?(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
            r"app\.(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        ],
        "flask": [
            r"@(?:router\.)?(?:route)\s*\(\s*['\"]([^'\"]+)['\"]",
        ],
        "next": [
            r"export\s+(?:async\s+)?function\s+(?:GET|POST|PUT|DELETE|PATCH)",
        ]
    }

    def __init__(self, feature_dir: Path, project_dir: Path):
        """Initialize the mapper.

        Args:
            feature_dir: Path to .sam/{feature} directory containing TASKS.json
            project_dir: Path to project root containing source code
        """
        self.feature_dir = feature_dir
        self.project_dir = project_dir
        self.tasks_file = feature_dir / "TASKS.json"
        self.mappings: Dict[str, List[CodeMapping]] = {}  # task_id -> mappings
        self.file_index: Dict[str, CodeMapping] = {}      # file_path -> mapping
        self.reverse_index: Dict[str, Set[str]] = {}      # file_path -> task_ids

        # Load existing data
        self._load_tasks()

    def _load_tasks(self):
        """Load tasks from TASKS.json."""
        if not self.tasks_file.exists():
            return

        with open(self.tasks_file, 'r') as f:
            data = json.load(f)

        # Build task index
        self.tasks: Dict[str, Dict] = {}
        for phase in data.get("phases", []):
            for task in phase.get("tasks", []):
                self.tasks[task["task_id"]] = task

        # Load existing mappings
        self.mappings = data.get("code_mappings", {})

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
        }
        return ext_map.get(file_path.suffix.lower(), "unknown")

    def _extract_from_annotations(self, file_path: Path) -> List[CodeMapping]:
        """Extract task annotations from source code.

        Args:
            file_path: Path to source file

        Returns:
            List of CodeMapping objects from annotations
        """
        mappings = []
        language = self._detect_language(file_path)
        patterns = self.ANNOTATION_PATTERNS.get(language, [])

        if not patterns:
            return mappings

        try:
            content = file_path.read_text()
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        task_id = match.group(1)
                        # Normalize task ID
                        if not task_id.startswith(("1", "2", "3", "4", "5")):
                            # Try to infer phase prefix
                            task_id = self._normalize_task_id(task_id)

                        mappings.append(CodeMapping(
                            file_path=str(file_path.relative_to(self.project_dir)),
                            task_id=task_id,
                            mapping_type="file",  # Default, will be refined
                            name=file_path.name,
                            line_start=line_num,
                            line_end=line_num,
                            confidence=1.0,
                            discovery_method="annotation"
                        )))

        except (UnicodeDecodeError, IOError):
            pass  # Skip binary or unreadable files

        return mappings

    def _extract_from_git_blame(self, file_path: Path) -> List[CodeMapping]:
        """Extract task mappings from git blame.

        Analyzes commit messages to find task IDs that implemented
        specific lines of code.

        Args:
            file_path: Path to source file

        Returns:
            List of CodeMapping objects from git blame
        """
        mappings = []

        try:
            # Run git blame with porcelain format
            result = subprocess.run(
                ["git", "blame", "--porcelain", str(file_path)],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return mappings

            # Parse git blame output
            output = result.stdout
            current_commit = None
            current_summary = None

            for line in output.splitlines():
                if line.startswith("\t"):
                    # This is a code line, current_commit has the info
                    if current_summary:
                        # Check commit summary for task patterns
                        for pattern in self.COMMIT_PATTERNS:
                            match = re.search(pattern, current_summary)
                            if match:
                                task_id = match.group(1)
                                mappings.append(CodeMapping(
                                    file_path=str(file_path.relative_to(self.project_dir)),
                                    task_id=task_id,
                                    mapping_type="file",
                                    name=file_path.name,
                                    line_start=0,  # Git blame doesn't give us line numbers easily
                                    line_end=0,
                                    confidence=0.9,
                                    discovery_method="git_blame"
                                ))
                                break  # Use first match
                    current_summary = None
                elif line.startswith("summary "):
                    current_summary = line[8:]
                elif not line.startswith(("\t", "author ", "author-time ",
                                           "committer ", "committer-time ",
                                           "filename ")):
                    current_commit = line.split()[0] if line else None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return mappings

    def _extract_from_directory_structure(self, file_path: Path) -> List[CodeMapping]:
        """Extract task mappings from directory structure.

        Uses heuristics like:
        - src/features/001-user-auth/ -> task 1.1
        - components/task-2-1-3/ -> task 2.1.3

        Args:
            file_path: Path to source file

        Returns:
            List of CodeMapping objects from directory structure
        """
        mappings = []
        relative_path = str(file_path.relative_to(self.project_dir))

        for pattern in self.DIRECTORY_PATTERNS:
            match = re.search(pattern, relative_path)
            if match:
                task_number = match.group(1)

                # Convert directory number to task ID
                # 001 -> 1.1, 002 -> 1.2, etc. (default phase 1)
                if len(task_number) == 3 and task_number.isdigit():
                    num = int(task_number)
                    task_id = f"1.{num}"
                else:
                    task_id = self._normalize_task_id(task_number)

                mappings.append(CodeMapping(
                    file_path=relative_path,
                    task_id=task_id,
                    mapping_type="file",
                    name=file_path.name,
                    line_start=1,
                    line_end=self._count_lines(file_path),
                    confidence=0.6,
                    discovery_method="heuristic"
                ))
                break

        return mappings

    def _extract_from_endpoints(self, file_path: Path) -> List[CodeMapping]:
        """Extract task mappings from API endpoint definitions.

        Detects API routes and maps them to tasks based on naming
        or nearby annotations.

        Args:
            file_path: Path to source file

        Returns:
            List of CodeMapping objects from endpoint definitions
        """
        mappings = []
        language = self._detect_language(file_path)

        # Get appropriate patterns based on language/framework
        framework_patterns = []
        if language in ["javascript", "typescript"]:
            content = file_path.read_text()
            # Detect framework
            if "express" in content.lower() or "router" in content.lower():
                framework_patterns = self.ENDPOINT_PATTERNS.get("express", [])
            elif "fastapi" in content.lower():
                framework_patterns = self.ENDPOINT_PATTERNS.get("fastapi", [])
            elif "next" in content.lower():
                framework_patterns = self.ENDPOINT_PATTERNS.get("next", [])
        elif language == "python":
            content = file_path.read_text()
            if "fastapi" in content.lower():
                framework_patterns = self.ENDPOINT_PATTERNS.get("fastapi", [])
            elif "flask" in content.lower():
                framework_patterns = self.ENDPOINT_PATTERNS.get("flask", [])

        try:
            content = file_path.read_text()
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                for pattern in framework_patterns:
                    match = re.search(pattern, line)
                    if match:
                        endpoint_path = match.group(1)

                        # Try to extract task ID from endpoint path or nearby
                        task_id = self._extract_task_from_endpoint(endpoint_path, lines, line_num)

                        if task_id:
                            mappings.append(CodeMapping(
                                file_path=str(file_path.relative_to(self.project_dir)),
                                task_id=task_id,
                                mapping_type="endpoint",
                                name=endpoint_path,
                                line_start=line_num,
                                line_end=line_num,
                                confidence=0.85,
                                discovery_method="endpoint"
                            ))

        except (UnicodeDecodeError, IOError):
            pass

        return mappings

    def _extract_task_from_endpoint(self, endpoint: str, lines: List[str], line_num: int) -> Optional[str]:
        """Extract task ID from endpoint path or nearby code.

        Args:
            endpoint: The API endpoint path
            lines: All lines in the file
            line_num: Current line number

        Returns:
            Task ID if found, None otherwise
        """
        # Check endpoint path for task hints
        # /users/001 -> task 1.1
        match = re.search(r"/(\d+)(?:/|$)", endpoint)
        if match:
            num = int(match.group(1))
            if num < 100:
                return f"1.{num}"

        # Check nearby lines for annotations
        context_start = max(0, line_num - 3)
        context_end = min(len(lines), line_num + 2)

        for i in range(context_start, context_end):
            for pattern in self.ANNOTATION_PATTERNS.get("javascript", []):
                match = re.search(pattern, lines[i])
                if match:
                    return match.group(1)

        return None

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            return len(file_path.read_text().splitlines())
        except (UnicodeDecodeError, IOError):
            return 0

    def _normalize_task_id(self, task_id: str) -> str:
        """Normalize task ID to standard format.

        Args:
            task_id: Raw task ID from any source

        Returns:
            Normalized task ID (e.g., "1.2.3")
        """
        # Remove leading zeros
        parts = task_id.split(".")
        normalized = ".".join(str(int(p)) if p.isdigit() else p for p in parts)

        # Ensure it starts with a phase number
        if not normalized[0].isdigit():
            normalized = "1." + normalized

        return normalized

    def scan_codebase(self, extensions: Optional[Set[str]] = None) -> Dict[str, List[CodeMapping]]:
        """Scan entire codebase and generate mappings.

        Args:
            extensions: Set of file extensions to scan (e.g., {".py", ".ts"})
                       If None, scans all source files

        Returns:
            Dictionary mapping task_id to list of CodeMapping objects
        """
        if extensions is None:
            extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java", ".kt"}

        all_mappings = []

        # Scan project directory
        for file_path in self.project_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                # Skip node_modules, .git, etc.
                if any(skip in file_path.parts for skip in ["node_modules", ".git", "target", "build", "dist"]):
                    continue

                # Try all discovery methods
                mappings = []

                # 1. Check for annotations (highest priority)
                mappings.extend(self._extract_from_annotations(file_path))

                # 2. Check for endpoints
                mappings.extend(self._extract_from_endpoints(file_path))

                # 3. Check git blame
                mappings.extend(self._extract_from_git_blame(file_path))

                # 4. Check directory structure (lowest priority)
                mappings.extend(self._extract_from_directory_structure(file_path))

                # Deduplicate mappings by task_id and method
                unique_mappings = self._deduplicate_mappings(mappings)
                all_mappings.extend(unique_mappings)

        # Group by task_id
        mappings_by_task: Dict[str, List[CodeMapping]] = {}
        for mapping in all_mappings:
            if mapping.task_id not in mappings_by_task:
                mappings_by_task[mapping.task_id] = []
            mappings_by_task[mapping.task_id].append(mapping)

        self.mappings = mappings_by_task
        return mappings_by_task

    def _deduplicate_mappings(self, mappings: List[CodeMapping]) -> List[CodeMapping]:
        """Deduplicate mappings, keeping highest confidence for each task.

        Args:
            mappings: List of potentially duplicate mappings

        Returns:
            Deduplicated list
        """
        by_task: Dict[str, CodeMapping] = {}

        for mapping in mappings:
            key = (mapping.task_id, mapping.file_path, mapping.mapping_type)
            if key not in by_task or mapping.confidence > by_task[key].confidence:
                by_task[key] = mapping

        return list(by_task.values())

    def map_code_to_task(self, file_path: str, line_number: int) -> Optional[str]:
        """Map specific code location to implementing task.

        Args:
            file_path: Path to source file (relative or absolute)
            line_number: Line number in the file

        Returns:
            Task ID if found, None otherwise
        """
        # Normalize path
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_dir / file_path

        relative_path = str(path.relative_to(self.project_dir))

        # Check direct file mappings
        for task_id, mappings in self.mappings.items():
            for mapping in mappings:
                if mapping.file_path == relative_path:
                    if mapping.line_start <= line_number <= mapping.line_end:
                        return task_id

        # Check if any tasks map to this file
        if relative_path in self.reverse_index:
            task_ids = list(self.reverse_index[relative_path])
            return task_ids[0] if task_ids else None

        return None

    def get_task_code_map(self, task_id: str) -> TaskCodeMap:
        """Get all code implementing a specific task.

        Args:
            task_id: Task identifier

        Returns:
            TaskCodeMap with all code for this task
        """
        mappings = self.mappings.get(task_id, [])

        code_map = TaskCodeMap(
            task_id=task_id,
            total_mappings=len(mappings),
            total_lines=sum(m.line_end - m.line_start + 1 for m in mappings)
        )

        for mapping in mappings:
            if mapping.mapping_type == "file":
                code_map.files.append(mapping.file_path)
            elif mapping.mapping_type == "function":
                code_map.functions.append(mapping.name)
            elif mapping.mapping_type == "class":
                code_map.classes.append(mapping.name)
            elif mapping.mapping_type == "endpoint":
                code_map.endpoints.append(mapping.name)

        # Remove duplicates
        code_map.files = list(set(code_map.files))
        code_map.functions = list(set(code_map.functions))
        code_map.classes = list(set(code_map.classes))
        code_map.endpoints = list(set(code_map.endpoints))

        # Calculate confidence
        code_map.confidence_score = code_map.calculate_confidence()

        return code_map

    def detect_new_code(self, baseline_commit: str) -> NewCodeDetection:
        """Detect new code added since baseline commit.

        Args:
            baseline_commit: Git commit hash or reference to compare against

        Returns:
            NewCodeDetection with new code mappings
        """
        detection = NewCodeDetection(baseline_commit=baseline_commit)

        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{baseline_commit}..HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return detection

            changed_files = result.stdout.strip().splitlines()
            detection.modified_files = [f for f in changed_files if f]

            # Check each changed file for new task mappings
            for file_path in changed_files:
                full_path = self.project_dir / file_path
                if not full_path.exists():
                    continue

                # Scan for new annotations
                new_mappings = []
                new_mappings.extend(self._extract_from_annotations(full_path))
                new_mappings.extend(self._extract_from_endpoints(full_path))

                # Filter to only mappings not in existing self.mappings
                for mapping in new_mappings:
                    exists = any(
                        m.file_path == mapping.file_path and
                        m.task_id == mapping.task_id
                        for m in self.mappings.get(mapping.task_id, [])
                    )
                    if not exists:
                        detection.new_mappings.append(mapping)

            detection.total_new_lines = sum(
                m.line_end - m.line_start + 1 for m in detection.new_mappings
            )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return detection

    def update_tasks_json(self):
        """Update TASKS.json with code mappings."""
        # Load existing data
        with open(self.tasks_file, 'r') as f:
            data = json.load(f)

        # Add code_mappings section
        data["code_mappings"] = {
            "last_scan": datetime.now().isoformat(),
            "total_mappings": sum(len(m) for m in self.mappings.values()),
            "mappings_by_task": {
                task_id: [m.to_dict() for m in mappings]
                for task_id, mappings in self.mappings.items()
            }
        }

        # Update individual tasks with their mappings
        for phase in data.get("phases", []):
            for task in phase.get("tasks", []):
                task_id = task["task_id"]
                if task_id in self.mappings:
                    task["code_mappings"] = [m.to_dict() for m in self.mappings[task_id]]

        # Write back
        with open(self.tasks_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_report(self) -> str:
        """Generate a code-to-task mapping report.

        Returns:
            Markdown report
        """
        lines = [
            "# Code-to-Task Mapping Report",
            "",
            f"**Generated**: {datetime.now().isoformat()}",
            f"**Total Mappings**: {sum(len(m) for m in self.mappings.values())}",
            f"**Tasks with Code**: {len(self.mappings)}",
            "",
            "## Mappings by Task",
            ""
        ]

        for task_id in sorted(self.mappings.keys()):
            code_map = self.get_task_code_map(task_id)
            lines.append(f"### Task {task_id}")
            lines.append(f"**Confidence**: {code_map.confidence_score:.0%}")
            lines.append(f"**Total Mappings**: {code_map.total_mappings}")
            lines.append(f"**Total Lines**: {code_map.total_lines}")

            if code_map.files:
                lines.append(f"**Files** ({len(code_map.files)}):")
                for f in sorted(code_map.files):
                    lines.append(f"  - `{f}`")

            if code_map.functions:
                lines.append(f"**Functions** ({len(code_map.functions)}):")
                for fn in sorted(code_map.functions):
                    lines.append(f"  - `{fn}`")

            if code_map.classes:
                lines.append(f"**Classes** ({len(code_map.classes)}):")
                for cls in sorted(code_map.classes):
                    lines.append(f"  - `{cls}`")

            if code_map.endpoints:
                lines.append(f"**Endpoints** ({len(code_map.endpoints)}):")
                for ep in sorted(code_map.endpoints):
                    lines.append(f"  - `{ep}`")

            lines.append("")

        return "\n".join(lines)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 code_task_mapper.py <feature_dir> [--scan] [--map-file <file> --line <n>] [--task <id> --show-code] [--detect-new --baseline <commit>] [--export-mappings]")
        print("Examples:")
        print("  python3 code_task_mapper.py .sam/001_feature --scan")
        print("  python3 code_task_mapper.py .sam/001_feature --map-file src/api/users.ts --line 45")
        print("  python3 code_task_mapper.py .sam/001_feature --task 2.1.3 --show-code")
        print("  python3 code_task_mapper.py .sam/001_feature --detect-new --baseline main~1")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    # Determine project directory (parent of .sam or current dir)
    if feature_dir.name.startswith(".sam"):
        project_dir = feature_dir.parent.parent
    else:
        project_dir = Path.cwd()

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    tasks_file = feature_dir / "TASKS.json"
    if not tasks_file.exists():
        print(f"Error: TASKS.json not found in {feature_dir}")
        sys.exit(1)

    mapper = CodeTaskMapper(feature_dir, project_dir)

    # Parse command line arguments
    scan = False
    map_file = None
    line_number = None
    show_task = None
    detect_new = False
    baseline = None
    export_mappings = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--scan":
            scan = True
            i += 1
        elif sys.argv[i] == "--map-file" and i + 1 < len(sys.argv):
            map_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--line" and i + 1 < len(sys.argv):
            line_number = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--task" and i + 1 < len(sys.argv):
            show_task = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--show-code":
            # Implicit with --task
            i += 1
        elif sys.argv[i] == "--detect-new":
            detect_new = True
            i += 1
        elif sys.argv[i] == "--baseline" and i + 1 < len(sys.argv):
            baseline = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--export-mappings":
            export_mappings = True
            i += 1
        else:
            i += 1

    # Execute requested action
    if scan:
        print(f"Scanning codebase: {project_dir}")
        print("=" * 60)

        mappings = mapper.scan_codebase()
        print(f"✓ Found {len(mappings)} tasks with code mappings")

        mapper.update_tasks_json()
        print(f"✓ Updated TASKS.json")

        # Print summary
        for task_id, task_mappings in sorted(mappings.items()):
            print(f"  Task {task_id}: {len(task_mappings)} mappings")

        print(f"\n✓ Total mappings: {sum(len(m) for m in mappings.values())}")

    elif map_file and line_number:
        task_id = mapper.map_code_to_task(map_file, line_number)
        if task_id:
            print(f"Task: {task_id}")
        else:
            print(f"No task found for {map_file}:{line_number}")
            sys.exit(1)

    elif show_task:
        code_map = mapper.get_task_code_map(show_task)
        print(f"\nTask {show_task} Code Map:")
        print(f"  Total Mappings: {code_map.total_mappings}")
        print(f"  Total Lines: {code_map.total_lines}")
        print(f"  Confidence: {code_map.confidence_score:.0%}")
        print(f"\n  Files: {len(code_map.files)}")
        for f in sorted(code_map.files):
            print(f"    - {f}")
        print(f"  Functions: {len(code_map.functions)}")
        for fn in sorted(code_map.functions):
            print(f"    - {fn}")
        print(f"  Classes: {len(code_map.classes)}")
        for cls in sorted(code_map.classes):
            print(f"    - {cls}")
        print(f"  Endpoints: {len(code_map.endpoints)}")
        for ep in sorted(code_map.endpoints):
            print(f"    - {ep}")

    elif detect_new and baseline:
        print(f"Detecting new code since {baseline}...")
        detection = mapper.detect_new_code(baseline)

        print(f"\nNew Code Detection Report:")
        print(f"  Modified Files: {len(detection.modified_files)}")
        print(f"  New Mappings: {len(detection.new_mappings)}")
        print(f"  Total New Lines: {detection.total_new_lines}")

        if detection.new_mappings:
            print(f"\n  New Mappings:")
            for mapping in detection.new_mappings:
                print(f"    - {mapping.task_id}: {mapping.file_path}:{mapping.line_start}")

    elif export_mappings:
        # Export all mappings as JSON
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "mappings": {
                task_id: [m.to_dict() for m in mappings]
                for task_id, mappings in mapper.mappings.items()
            }
        }
        print(json.dumps(export_data, indent=2))

    else:
        print("Error: Please specify an action (--scan, --map-file, --task, --detect-new, or --export-mappings)")
        sys.exit(1)


if __name__ == "__main__":
    main()
