#!/usr/bin/env python3
"""
conflict_detector.py - Cross-task conflict detection

This script detects conflicts between parallel task implementations before
they cause issues in production. It identifies resource conflicts (files,
endpoints, database schemas) and logic conflicts (duplicates, type mismatches).

Usage:
    python3 conflict_detector.py .sam/{feature} --detect
    python3 conflict_detector.py .sam/{feature} --resource-conflicts
    python3 conflict_detector.py .sam/{feature} --logic-conflicts
    python3 conflict_detector.py .sam/{feature} --task 2.1.3 --check-conflicts
    python3 conflict_detector.py .sam/{feature} --report > conflicts.md
    python3 conflict_detector.py .sam/{feature} --check-cycles

Output:
    JSON report with conflicts, severity levels, and resolution recommendations
    Updates TASKS.json checkpoint with conflict status
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class ResourceConflict:
    """Conflict over shared resource."""
    conflict_id: str
    conflict_type: str  # "file", "endpoint", "database", "component", "env_var"
    resource_id: str  # File path, API route, table name, etc.
    task_ids: List[str]
    severity: str  # "critical", "major", "minor"
    description: str
    resolution: str
    evidence: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LogicConflict:
    """Incompatible implementations or logic."""
    conflict_id: str
    conflict_type: str  # "incompatible_types", "duplicate_implementation", "breaking_change"
    task_ids: List[str]
    severity: str
    description: str
    evidence: List[str] = field(default_factory=list)
    resolution: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ConflictReport:
    """Comprehensive conflict analysis report."""
    resource_conflicts: List[ResourceConflict] = field(default_factory=list)
    logic_conflicts: List[LogicConflict] = field(default_factory=list)
    total_conflicts: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    has_blocking_conflicts: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_resource_conflict(self, conflict: ResourceConflict):
        """Add a resource conflict and update statistics."""
        self.resource_conflicts.append(conflict)
        self.total_conflicts += 1
        self.by_severity[conflict.severity] = self.by_severity.get(conflict.severity, 0) + 1
        if conflict.severity == "critical":
            self.has_blocking_conflicts = True

    def add_logic_conflict(self, conflict: LogicConflict):
        """Add a logic conflict and update statistics."""
        self.logic_conflicts.append(conflict)
        self.total_conflicts += 1
        self.by_severity[conflict.severity] = self.by_severity.get(conflict.severity, 0) + 1
        if conflict.severity == "critical":
            self.has_blocking_conflicts = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ConflictDetector:
    """Detect conflicts between parallel task implementations."""

    # File extension groups for conflict detection
    SOURCE_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java", ".kt",
        ".cpp", ".c", ".h", ".hpp", ".cs", ".swift", ".rb", ".php"
    }

    # API endpoint patterns
    ENDPOINT_PATTERNS = {
        "express": r"(?:router\.)?(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        "fastapi": r"@(?:router\.)?(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        "flask": r"@(?:router\.)?(?:route)\s*\(\s*['\"]([^'\"]+)['\"]",
        "django": r"path\s*\(\s*['\"]([^'\"]+)['\"]",
    }

    # Database table name patterns
    TABLE_PATTERNS = [
        r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?['\"`]?(\w+)['\"`]?",
        r"ALTER TABLE\s+['\"`]?(\w+)['\"`]?",
        r"DROP TABLE\s+(?:IF EXISTS\s+)?['\"`]?(\w+)['\"`]?",
        r"Table\s*\(\s*['\"]([^'\"]+)['\"]",  # SQLAlchemy
        r"@Table\b\s*\(\s*name\s*=\s*['\"]([^'\"]+)['\"]",  # TypeORM
    ]

    # Component name patterns
    COMPONENT_PATTERNS = [
        r"(?:function|const|class)\s+(\w+Component)",  # React
        r"@Component\s*\(\s*name:\s*['\"]([^'\"]+)['\"]",  # Vue
        r"@Component\b",  # Angular
        r"export default function (\w+)",  # React functional
    ]

    def __init__(self, feature_dir: Path, project_dir: Path):
        """Initialize the conflict detector.

        Args:
            feature_dir: Path to .sam/{feature} directory containing TASKS.json
            project_dir: Path to project root containing source code
        """
        self.feature_dir = feature_dir
        self.project_dir = project_dir
        self.tasks_file = feature_dir / "TASKS.json"

        # Load tasks and build mappings
        self.tasks: Dict[str, Dict] = {}
        self.task_files: Dict[str, Set[str]] = defaultdict(set)
        self.file_tasks: Dict[str, Set[str]] = defaultdict(set)
        self.task_endpoints: Dict[str, Set[str]] = defaultdict(set)
        self.endpoint_tasks: Dict[str, Set[str]] = defaultdict(set)
        self.task_tables: Dict[str, Set[str]] = defaultdict(set)
        self.table_tasks: Dict[str, Set[str]] = defaultdict(set)

        self._load_tasks()
        self._build_mappings()

    def _load_tasks(self):
        """Load tasks from TASKS.json."""
        if not self.tasks_file.exists():
            return

        with open(self.tasks_file, 'r') as f:
            data = json.load(f)

        # Build task index
        for phase in data.get("phases", []):
            for task in phase.get("tasks", []):
                self.tasks[task["task_id"]] = task

    def _build_mappings(self):
        """Build task-to-resource and resource-to-task mappings.

        Uses code_mappings from TASKS.json if available, otherwise
        scans the codebase.
        """
        # Check if code_mappings exist in TASKS.json
        with open(self.tasks_file, 'r') as f:
            data = json.load(f)

        code_mappings = data.get("code_mappings", {}).get("mappings_by_task", {})

        if code_mappings:
            # Use existing mappings
            for task_id, mappings in code_mappings.items():
                for mapping in mappings:
                    file_path = mapping.get("file_path", "")
                    mapping_type = mapping.get("mapping_type", "file")

                    self.task_files[task_id].add(file_path)
                    self.file_tasks[file_path].add(task_id)

                    if mapping_type == "endpoint":
                        endpoint = mapping.get("name", "")
                        self.task_endpoints[task_id].add(endpoint)
                        self.endpoint_tasks[endpoint].add(task_id)

            # Scan for database tables separately
            self._scan_database_tables()
        else:
            # Full scan required
            self._scan_codebase()

    def _scan_codebase(self):
        """Scan codebase for file, endpoint, and table references."""
        # Import here to avoid circular import
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "sam-develop" / "scripts"))
        try:
            from code_task_mapper import CodeTaskMapper

            mapper = CodeTaskMapper(self.feature_dir, self.project_dir)
            mappings = mapper.scan_codebase()

            for task_id, task_mappings in mappings.items():
                for mapping in task_mappings:
                    file_path = mapping.file_path
                    self.task_files[task_id].add(file_path)
                    self.file_tasks[file_path].add(task_id)

                    if mapping.mapping_type == "endpoint":
                        self.task_endpoints[task_id].add(mapping.name)
                        self.endpoint_tasks[mapping.name].add(task_id)
        except ImportError:
            pass

        # Scan for database tables
        self._scan_database_tables()

    def _scan_database_tables(self):
        """Scan database files for table references."""
        # Common database file locations
        db_dirs = [
            self.project_dir / "migrations",
            self.project_dir / "migrate",
            self.project_dir / "database",
            self.project_dir / "db",
            self.project_dir / "prisma",
            self.project_dir / "drizzle",
        ]

        for db_dir in db_dirs:
            if not db_dir.exists():
                continue

            # Find all migration files
            for file_path in db_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                if file_path.suffix not in {".sql", ".js", ".ts", ".py", ".prisma"}:
                    continue

                self._extract_tables_from_file(file_path)

    def _extract_tables_from_file(self, file_path: Path):
        """Extract table references from a file.

        Args:
            file_path: Path to database file
        """
        try:
            content = file_path.read_text()

            # Find all table references
            for pattern in self.TABLE_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1)

                    # Map to task using file location
                    # Try to infer task from directory structure
                    task_id = self._infer_task_from_path(file_path)
                    if task_id:
                        self.task_tables[task_id].add(table_name)
                        self.table_tasks[table_name].add(task_id)

        except (UnicodeDecodeError, IOError):
            pass

    def _infer_task_from_path(self, file_path: Path) -> Optional[str]:
        """Infer task ID from file path.

        Args:
            file_path: Path to source file

        Returns:
            Task ID if inferred, None otherwise
        """
        relative_path = str(file_path.relative_to(self.project_dir))

        # Check for task annotations
        try:
            content = file_path.read_text()
            for line in content.splitlines()[:20]:  # Check first 20 lines
                match = re.search(r'@task\s+([\d.]+)', line)
                if match:
                    return match.group(1)
        except (UnicodeDecodeError, IOError):
            pass

        # Check directory structure
        match = re.search(r'/(\d+)/', relative_path)
        if match:
            num = int(match.group(1))
            return f"1.{num}"

        return None

    def detect_resource_conflicts(self) -> List[ResourceConflict]:
        """Detect all resource conflicts.

        Returns:
            List of ResourceConflict objects
        """
        conflicts = []

        # Detect file conflicts
        conflicts.extend(self.detect_file_conflicts())

        # Detect endpoint conflicts
        conflicts.extend(self.detect_endpoint_conflicts())

        # Detect database conflicts
        conflicts.extend(self.detect_database_conflicts())

        # Detect component conflicts
        conflicts.extend(self.detect_component_conflicts())

        return conflicts

    def detect_file_conflicts(self) -> List[ResourceConflict]:
        """Detect conflicts where multiple tasks modify the same file.

        Returns:
            List of file ResourceConflict objects
        """
        conflicts = []

        for file_path, task_ids in self.file_tasks.items():
            if len(task_ids) > 1:
                # Filter to only tasks that are not completed
                active_tasks = [
                    t for t in task_ids
                    if self.tasks.get(t, {}).get("status") != "completed"
                ]

                if len(active_tasks) > 1:
                    # Determine severity based on file type
                    severity = self._assess_file_conflict_severity(file_path)

                    # Generate conflict ID
                    conflict_id = f"file_{hash(file_path) % 10000:04d}"

                    # Build description
                    task_list = ", ".join(sorted(active_tasks))
                    description = (
                        f"Multiple tasks ({task_list}) are modifying the same file. "
                        f"This will cause merge conflicts."
                    )

                    # Build resolution
                    resolution = self._suggest_file_conflict_resolution(active_tasks, file_path)

                    # Gather evidence
                    evidence = [
                        f"File: {file_path}",
                        f"Conflicting tasks: {task_list}",
                        f"Total tasks accessing this file: {len(task_ids)}"
                    ]

                    conflicts.append(ResourceConflict(
                        conflict_id=conflict_id,
                        conflict_type="file",
                        resource_id=file_path,
                        task_ids=sorted(active_tasks),
                        severity=severity,
                        description=description,
                        resolution=resolution,
                        evidence=evidence
                    ))

        return conflicts

    def _assess_file_conflict_severity(self, file_path: str) -> str:
        """Assess severity of file conflict based on file type.

        Args:
            file_path: Path to file

        Returns:
            Severity level: "critical", "major", or "minor"
        """
        path = Path(file_path).lower()

        # Critical: Core configuration and entry points
        if any(name in path.parts for name in ["package.json", "pom.xml", "build.gradle", "cargo.toml"]):
            return "critical"

        # Critical: Main entry points
        if path.name in ["index.ts", "index.js", "main.ts", "main.js", "app.ts", "app.js", "server.ts", "server.js"]:
            return "critical"

        # Major: Configuration files
        if path.suffix in [".config.js", ".config.ts", ".json", ".yaml", ".yml", ".toml"]:
            return "major"

        # Major: Type definitions
        if path.suffix in [".d.ts"]:
            return "major"

        # Minor: Regular source files
        if path.suffix in self.SOURCE_EXTENSIONS:
            return "minor"

        return "minor"

    def _suggest_file_conflict_resolution(self, task_ids: List[str], file_path: str) -> str:
        """Suggest resolution for file conflict.

        Args:
            task_ids: List of conflicting task IDs
            file_path: Path to conflicting file

        Returns:
            Resolution suggestion
        """
        # Check if file is module/index file
        path = Path(file_path)
        if path.name in ["index.ts", "index.js", "mod.rs", "__init__.py"]:
            return (
                "This is a module index file. Consider refactoring to have "
                "each task export from its own module, then import into a "
                "central index."
            )

        # Check if file is large
        try:
            full_path = self.project_dir / file_path
            if full_path.exists() and len(full_path.read_text()) > 500:
                return (
                    "File is large. Consider splitting into smaller modules "
                    "by feature/task, or create a shared utility module."
                )
        except (IOError, UnicodeDecodeError):
            pass

        return (
            "Sequential execution recommended. Complete one task's changes "
            f"before starting the next. Tasks: {', '.join(sorted(task_ids))}"
        )

    def detect_endpoint_conflicts(self) -> List[ResourceConflict]:
        """Detect conflicts where multiple tasks define the same API endpoint.

        Returns:
            List of endpoint ResourceConflict objects
        """
        conflicts = []

        for endpoint, task_ids in self.endpoint_tasks.items():
            if len(task_ids) > 1:
                active_tasks = [
                    t for t in task_ids
                    if self.tasks.get(t, {}).get("status") != "completed"
                ]

                if len(active_tasks) > 1:
                    conflict_id = f"endpoint_{hash(endpoint) % 10000:04d}"

                    description = (
                        f"Multiple tasks are defining the same API endpoint: {endpoint}. "
                        "This will cause runtime conflicts."
                    )

                    resolution = (
                        "Choose one task to own this endpoint. Other tasks should "
                        "either use different endpoints or call this one's implementation."
                    )

                    evidence = [
                        f"Endpoint: {endpoint}",
                        f"Conflicting tasks: {', '.join(sorted(active_tasks))}"
                    ]

                    conflicts.append(ResourceConflict(
                        conflict_id=conflict_id,
                        conflict_type="endpoint",
                        resource_id=endpoint,
                        task_ids=sorted(active_tasks),
                        severity="critical",
                        description=description,
                        resolution=resolution,
                        evidence=evidence
                    ))

        return conflicts

    def detect_database_conflicts(self) -> List[ResourceConflict]:
        """Detect conflicts where multiple tasks modify the same database table.

        Returns:
            List of database ResourceConflict objects
        """
        conflicts = []

        for table, task_ids in self.table_tasks.items():
            if len(task_ids) > 1:
                active_tasks = [
                    t for t in task_ids
                    if self.tasks.get(t, {}).get("status") != "completed"
                ]

                if len(active_tasks) > 1:
                    conflict_id = f"db_{hash(table) % 10000:04d}"

                    description = (
                        f"Multiple tasks are modifying database table: {table}. "
                        "This may cause migration conflicts."
                    )

                    resolution = (
                        "Coordinate table changes. Create a shared migration or "
                        "decide which task owns schema changes."
                    )

                    evidence = [
                        f"Table: {table}",
                        f"Conflicting tasks: {', '.join(sorted(active_tasks))}"
                    ]

                    conflicts.append(ResourceConflict(
                        conflict_id=conflict_id,
                        conflict_type="database",
                        resource_id=table,
                        task_ids=sorted(active_tasks),
                        severity="major",
                        description=description,
                        resolution=resolution,
                        evidence=evidence
                    ))

        return conflicts

    def detect_component_conflicts(self) -> List[ResourceConflict]:
        """Detect conflicts where multiple tasks implement the same component.

        Returns:
            List of component ResourceConflict objects
        """
        conflicts = []

        # Scan for component definitions
        component_tasks: Dict[str, Set[str]] = defaultdict(set)

        for file_path in self.project_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in {".tsx", ".jsx", ".vue", ".svelte"}:
                continue

            try:
                content = file_path.read_text()

                # Find component definitions
                for pattern in self.COMPONENT_PATTERNS:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        component_name = match.group(1)

                        # Infer task
                        task_id = self._infer_task_from_path(file_path)
                        if task_id:
                            component_tasks[component_name].add(task_id)

            except (UnicodeDecodeError, IOError):
                pass

        # Find conflicts
        for component, task_ids in component_tasks.items():
            if len(task_ids) > 1:
                active_tasks = [
                    t for t in task_ids
                    if self.tasks.get(t, {}).get("status") != "completed"
                ]

                if len(active_tasks) > 1:
                    conflict_id = f"component_{hash(component) % 10000:04d}"

                    description = (
                        f"Multiple tasks are implementing component: {component}. "
                        "This may cause naming conflicts."
                    )

                    resolution = (
                        "Rename components to include task context or extract "
                        "shared component to a common location."
                    )

                    conflicts.append(ResourceConflict(
                        conflict_id=conflict_id,
                        conflict_type="component",
                        resource_id=component,
                        task_ids=sorted(active_tasks),
                        severity="minor",
                        description=description,
                        resolution=resolution
                    ))

        return conflicts

    def detect_logic_conflicts(self) -> List[LogicConflict]:
        """Detect all logic conflicts.

        Returns:
            List of LogicConflict objects
        """
        conflicts = []

        # Detect duplicate implementations
        conflicts.extend(self.detect_duplicate_implementations())

        # Detect type incompatibilities
        conflicts.extend(self.detect_type_incompatibilities())

        # Detect breaking changes
        conflicts.extend(self.detect_breaking_changes())

        return conflicts

    def detect_duplicate_implementations(self) -> List[LogicConflict]:
        """Detect duplicate implementations of the same functionality.

        Returns:
            List of LogicConflict objects for duplicates
        """
        conflicts = []

        # Look for similar function/class names across tasks
        implementation_map: Dict[str, Set[str]] = defaultdict(set)

        for file_path in self.project_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in self.SOURCE_EXTENSIONS:
                continue

            # Skip common directories
            if any(skip in file_path.parts for skip in ["node_modules", ".git", "target", "build"]):
                continue

            task_id = self._infer_task_from_path(file_path)
            if not task_id:
                continue

            try:
                content = file_path.read_text()

                # Find function/class definitions
                patterns = [
                    r"(?:function|def|class|const)\s+(\w+)",
                    r"(?:interface|type)\s+(\w+)",
                    r"export\s+(?:default\s+)?(?:class|function|const)\s+(\w+)",
                ]

                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        name = match.group(1)

                        # Filter out common names
                        if len(name) < 4 or name in ["main", "init", "setup", "test"]:
                            continue

                        implementation_map[name].add(task_id)

            except (UnicodeDecodeError, IOError):
                pass

        # Find duplicates
        for name, task_ids in implementation_map.items():
            if len(task_ids) > 1:
                # Check if implementations are actually similar
                if self._are_similar_implementations(name, list(task_ids)):
                    active_tasks = [
                        t for t in task_ids
                        if self.tasks.get(t, {}).get("status") != "completed"
                    ]

                    if len(active_tasks) > 1:
                        conflict_id = f"duplicate_{hash(name) % 10000:04d}"

                        description = (
                            f"Multiple tasks implement similar functionality: {name}. "
                            "This may indicate duplicate work."
                        )

                        resolution = (
                            "Consolidate implementations into a shared utility or "
                            "clarify task boundaries to avoid overlap."
                        )

                        conflicts.append(LogicConflict(
                            conflict_id=conflict_id,
                            conflict_type="duplicate_implementation",
                            task_ids=sorted(active_tasks),
                            severity="minor",
                            description=description,
                            resolution=resolution,
                            evidence=[f"Function/Class: {name}", f"Tasks: {', '.join(sorted(active_tasks))}"]
                        ))

        return conflicts

    def _are_similar_implementations(self, name: str, task_ids: List[str]) -> bool:
        """Check if implementations with the same name are actually similar.

        Args:
            name: Function/class name
            task_ids: List of task IDs

        Returns:
            True if implementations are similar
        """
        # For now, assume same name = similar implementation
        # A more sophisticated version would compare AST structures
        return True

    def detect_type_incompatibilities(self) -> List[LogicConflict]:
        """Detect type incompatibilities between tasks.

        Returns:
            List of LogicConflict objects for type issues
        """
        conflicts = []

        # This would require type checking integration
        # For now, return empty list

        return conflicts

    def detect_breaking_changes(self) -> List[LogicConflict]:
        """Detect breaking changes between tasks.

        Returns:
            List of LogicConflict objects for breaking changes
        """
        conflicts = []

        # Look for function signature changes in shared interfaces
        # This would require git diff analysis

        return conflicts

    def check_cycles_with_conflicts(self) -> List[List[str]]:
        """Check for circular dependencies involving conflicting tasks.

        Returns:
            List of cycles (each cycle is a list of task IDs)
        """
        # Import impact analyzer for cycle detection
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "sam-specs" / "scripts"))
        try:
            from impact_analyzer import ImpactAnalyzer

            analyzer = ImpactAnalyzer(self.feature_dir)
            analyzer.load_tasks()

            # Get cycles
            cycles = analyzer.detect_cycles()

            # Filter cycles to only those involving conflicts
            conflict_cycles = []

            # Build set of all conflicting task IDs
            conflicting_tasks = set()
            for rc in self.detect_resource_conflicts():
                conflicting_tasks.update(rc.task_ids)
            for lc in self.detect_logic_conflicts():
                conflicting_tasks.update(lc.task_ids)

            # Filter cycles
            for cycle in cycles:
                if any(task in conflicting_tasks for task in cycle):
                    conflict_cycles.append(cycle)

            return conflict_cycles

        except ImportError:
            return []

    def generate_conflict_report(self) -> ConflictReport:
        """Generate comprehensive conflict report.

        Returns:
            ConflictReport with all detected conflicts
        """
        report = ConflictReport()

        # Detect all conflicts
        resource_conflicts = self.detect_resource_conflicts()
        for conflict in resource_conflicts:
            report.add_resource_conflict(conflict)

        logic_conflicts = self.detect_logic_conflicts()
        for conflict in logic_conflicts:
            report.add_logic_conflict(conflict)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: ConflictReport) -> List[str]:
        """Generate recommendations based on conflicts.

        Args:
            report: Conflict report

        Returns:
            List of recommendations
        """
        recommendations = []

        if report.has_blocking_conflicts:
            recommendations.append(
                "🔴 CRITICAL conflicts detected. Address these before proceeding with parallel execution."
            )

        # Count by type
        file_count = sum(1 for c in report.resource_conflicts if c.conflict_type == "file")
        endpoint_count = sum(1 for c in report.resource_conflicts if c.conflict_type == "endpoint")
        db_count = sum(1 for c in report.resource_conflicts if c.conflict_type == "database")

        if file_count > 3:
            recommendations.append(
                f"📁 {file_count} file conflicts detected. Consider refactoring to reduce coupling."
            )

        if endpoint_count > 0:
            recommendations.append(
                f"🔌 {endpoint_count} endpoint conflicts detected. Coordinate API design across tasks."
            )

        if db_count > 0:
            recommendations.append(
                f"🗄️ {db_count} database conflicts detected. Plan schema changes together."
            )

        # Check for cycles
        cycles = self.check_cycles_with_conflicts()
        if cycles:
            recommendations.append(
                f"🔄 {len(cycles)} circular dependencies involving conflicting tasks detected."
            )
            recommendations.append(
                "   Break cycles by removing unnecessary dependencies or merging tasks."
            )

        return recommendations

    def check_conflicts_for_task(self, task_id: str) -> ConflictReport:
        """Check conflicts for a specific task.

        Args:
            task_id: Task to check

        Returns:
            ConflictReport for this task
        """
        report = ConflictReport()

        # Check resource conflicts
        for conflict in self.detect_resource_conflicts():
            if task_id in conflict.task_ids:
                report.add_resource_conflict(conflict)

        # Check logic conflicts
        for conflict in self.detect_logic_conflicts():
            if task_id in conflict.task_ids:
                report.add_logic_conflict(conflict)

        report.recommendations = self._generate_recommendations(report)

        return report

    def update_tasks_json(self, report: ConflictReport):
        """Update TASKS.json checkpoint with conflict status.

        Args:
            report: Conflict report to save
        """
        with open(self.tasks_file, 'r') as f:
            data = json.load(f)

        # Update checkpoint
        checkpoint = data.setdefault("checkpoint", {})
        checkpoint["conflict_detection"] = {
            "last_scan": report.timestamp,
            "total_conflicts": report.total_conflicts,
            "by_severity": report.by_severity,
            "has_blocking": report.has_blocking_conflicts
        }

        # Write back
        with open(self.tasks_file, 'w') as f:
            json.dump(data, f, indent=2)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 conflict_detector.py <feature_dir> [--detect] [--resource-conflicts] [--logic-conflicts] [--task <id> --check-conflicts] [--report] [--check-cycles]")
        print("Examples:")
        print("  python3 conflict_detector.py .sam/001_feature --detect")
        print("  python3 conflict_detector.py .sam/001_feature --resource-conflicts")
        print("  python3 conflict_detector.py .sam/001_feature --task 2.1.3 --check-conflicts")
        print("  python3 conflict_detector.py .sam/001_feature --report > conflicts.md")
        print("  python3 conflict_detector.py .sam/001_feature --check-cycles")
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

    tasks_file = feature_dir / "TASKS.json"
    if not tasks_file.exists():
        print(f"Error: TASKS.json not found in {feature_dir}")
        sys.exit(1)

    detector = ConflictDetector(feature_dir, project_dir)

    # Parse arguments
    detect_all = False
    resource_only = False
    logic_only = False
    check_task = None
    generate_report = False
    check_cycles = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--detect":
            detect_all = True
            i += 1
        elif sys.argv[i] == "--resource-conflicts":
            resource_only = True
            i += 1
        elif sys.argv[i] == "--logic-conflicts":
            logic_only = True
            i += 1
        elif sys.argv[i] == "--task" and i + 1 < len(sys.argv):
            check_task = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--check-conflicts":
            # Implicit with --task
            i += 1
        elif sys.argv[i] == "--report":
            generate_report = True
            i += 1
        elif sys.argv[i] == "--check-cycles":
            check_cycles = True
            i += 1
        else:
            i += 1

    # Execute
    if check_cycles:
        print(f"\n🔍 Checking for circular dependencies with conflicts...")
        print("=" * 60)

        cycles = detector.check_cycles_with_conflicts()

        if cycles:
            print(f"\n❌ Found {len(cycles)} cycle(s) involving conflicting tasks:\n")
            for idx, cycle in enumerate(cycles, 1):
                print(f"Cycle {idx}: {' → '.join(cycle)}")
            print(f"\n⚠️ These cycles prevent parallel execution.")
            print(f"   Break cycles by removing dependencies or merging tasks.")
            sys.exit(1)
        else:
            print("✅ No circular dependencies detected!")
            sys.exit(0)

    elif check_task:
        print(f"\n🔍 Checking conflicts for task {check_task}...")
        print("=" * 60)

        report = detector.check_conflicts_for_task(check_task)

        print(f"\nConflicts for Task {check_task}:")
        print(f"  Total: {report.total_conflicts}")
        print(f"  By Severity: {report.by_severity}")
        print(f"  Blocking: {report.has_blocking_conflicts}")

        if report.resource_conflicts:
            print(f"\n  Resource Conflicts ({len(report.resource_conflicts)}):")
            for conflict in report.resource_conflicts:
                print(f"    - [{conflict.severity.upper()}] {conflict.conflict_type}: {conflict.resource_id}")
                print(f"      {conflict.description}")

        if report.logic_conflicts:
            print(f"\n  Logic Conflicts ({len(report.logic_conflicts)}):")
            for conflict in report.logic_conflicts:
                print(f"    - [{conflict.severity.upper()}] {conflict.conflict_type}")
                print(f"      {conflict.description}")

        if report.recommendations:
            print(f"\n  Recommendations:")
            for rec in report.recommendations:
                print(f"    {rec}")

        # Update TASKS.json
        detector.update_tasks_json(report)

    elif detect_all:
        print(f"\n🔍 Detecting conflicts...")
        print("=" * 60)

        report = detector.generate_conflict_report()

        print(f"\nConflict Detection Results:")
        print(f"  Total Conflicts: {report.total_conflicts}")
        print(f"  Resource Conflicts: {len(report.resource_conflicts)}")
        print(f"  Logic Conflicts: {len(report.logic_conflicts)}")
        print(f"  By Severity: {report.by_severity}")
        print(f"  Blocking: {report.has_blocking_conflicts}")

        if report.resource_conflicts:
            print(f"\n  Resource Conflicts ({len(report.resource_conflicts)}):")
            for conflict in report.resource_conflicts:
                print(f"    - [{conflict.severity.upper()}] {conflict.conflict_type}: {conflict.resource_id}")
                print(f"      Tasks: {', '.join(conflict.task_ids)}")

        if report.logic_conflicts:
            print(f"\n  Logic Conflicts ({len(report.logic_conflicts)}):")
            for conflict in report.logic_conflicts:
                print(f"    - [{conflict.severity.upper()}] {conflict.conflict_type}")
                print(f"      Tasks: {', '.join(conflict.task_ids)}")

        if report.recommendations:
            print(f"\n  Recommendations:")
            for rec in report.recommendations:
                print(f"    {rec}")

        # Update TASKS.json
        detector.update_tasks_json(report)

        if generate_report:
            print(f"\n📄 Generating detailed report...")
            report_text = _generate_markdown_report(report, feature_dir.name)
            print(report_text)

    elif resource_only:
        conflicts = detector.detect_resource_conflicts()
        print(f"\nResource Conflicts: {len(conflicts)}")
        for conflict in conflicts:
            print(f"  - [{conflict.severity.upper()}] {conflict.conflict_type}: {conflict.resource_id}")
            print(f"    Tasks: {', '.join(conflict.task_ids)}")

    elif logic_only:
        conflicts = detector.detect_logic_conflicts()
        print(f"\nLogic Conflicts: {len(conflicts)}")
        for conflict in conflicts:
            print(f"  - [{conflict.severity.upper()}] {conflict.conflict_type}")
            print(f"    Tasks: {', '.join(conflict.task_ids)}")
            print(f"    {conflict.description}")

    else:
        print("Error: Please specify an action (--detect, --resource-conflicts, --logic-conflicts, --task, --check-cycles)")
        sys.exit(1)


def _generate_markdown_report(report: ConflictReport, feature_name: str) -> str:
    """Generate markdown conflict report.

    Args:
        report: Conflict report
        feature_name: Feature name for title

    Returns:
        Markdown report
    """
    lines = [
        "# Conflict Detection Report",
        "",
        f"**Feature**: {feature_name}",
        f"**Generated**: {report.timestamp}",
        f"**Total Conflicts**: {report.total_conflicts}",
        "",
        "## Summary",
        "",
        f"- **Resource Conflicts**: {len(report.resource_conflicts)}",
        f"- **Logic Conflicts**: {len(report.logic_conflicts)}",
        f"- **By Severity**:",
    ]

    for severity, count in sorted(report.by_severity.items()):
        emoji = "🔴" if severity == "critical" else "🟡" if severity == "major" else "🟢"
        lines.append(f"  - {emoji} {severity.capitalize()}: {count}")

    lines.extend([
        "",
        f"**Blocking Conflicts**: {'Yes ❌' if report.has_blocking_conflicts else 'No ✅'}",
        "",
        "## Resource Conflicts",
        ""
    ])

    if report.resource_conflicts:
        for conflict in report.resource_conflicts:
            emoji = "🔴" if conflict.severity == "critical" else "🟡" if conflict.severity == "major" else "🟢"
            lines.extend([
                f"### {emoji} {conflict.conflict_type.upper()}: {conflict.resource_id}",
                "",
                f"**Conflict ID**: `{conflict.conflict_id}`",
                f"**Severity**: {conflict.severity.upper()}",
                f"**Tasks**: {', '.join(f'`{t}`' for t in conflict.task_ids)}",
                "",
                f"**Description**: {conflict.description}",
                "",
                f"**Resolution**: {conflict.resolution}",
                ""
            ])

            if conflict.evidence:
                lines.append("**Evidence**:")
                for evidence in conflict.evidence:
                    lines.append(f"  - {evidence}")
                lines.append("")
    else:
        lines.append("✅ No resource conflicts detected.")
        lines.append("")

    lines.extend([
        "## Logic Conflicts",
        ""
    ])

    if report.logic_conflicts:
        for conflict in report.logic_conflicts:
            emoji = "🔴" if conflict.severity == "critical" else "🟡" if conflict.severity == "major" else "🟢"
            lines.extend([
                f"### {emoji} {conflict.conflict_type.replace('_', ' ').title()}",
                "",
                f"**Conflict ID**: `{conflict.conflict_id}`",
                f"**Severity**: {conflict.severity.upper()}",
                f"**Tasks**: {', '.join(f'`{t}`' for t in conflict.task_ids)}",
                "",
                f"**Description**: {conflict.description}",
                "",
                f"**Resolution**: {conflict.resolution}",
                ""
            ])
    else:
        lines.append("✅ No logic conflicts detected.")
        lines.append("")

    lines.extend([
        "## Recommendations",
        ""
    ])

    if report.recommendations:
        for rec in report.recommendations:
            lines.append(f"- {rec}")
    else:
        lines.append("- No conflicts detected. Good to go!")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
