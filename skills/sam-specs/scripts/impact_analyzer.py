#!/usr/bin/env python3
"""
impact_analyzer.py - Dependency analysis and impact visualization

This script analyzes task dependencies from TASKS.json and generates:
- Impact reports for specific tasks or stories
- Mermaid dependency graphs
- Ripple effect analysis

Usage:
    python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --task 2.1.3
    python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --story 001
    python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --visualize
    python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --task 1.1 --report

Output:
    Generates impact analysis reports and Mermaid diagrams
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict


@dataclass
class ImpactReport:
    """Impact analysis report."""
    target: str
    target_type: str  # "task" or "story"
    direct_impact: List[Dict[str, str]] = field(default_factory=list)
    transitive_impact: List[Dict[str, str]] = field(default_factory=list)
    affected_stories: List[Dict[str, str]] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    risk_level: str = "medium"  # "low", "medium", "high"
    mermaid_graph: str = ""
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TaskInfo:
    """Information about a task."""
    task_id: str
    title: str
    status: str
    phase_id: str
    phase_name: str
    parent_task_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    story_mapping: Optional[str] = None
    spec_file: str = ""


class ImpactAnalyzer:
    """Analyze impact of changes using TASKS.json dependencies."""

    def __init__(self, feature_dir: Path):
        self.feature_dir = feature_dir
        self.tasks_file = feature_dir / "TASKS.json"
        self.data: Dict[str, Any] = {}
        self.tasks: Dict[str, TaskInfo] = {}
        self.dependents: Dict[str, Set[str]] = {}  # Reverse dependency map

    def load_tasks(self):
        """Load tasks from TASKS.json."""
        with open(self.tasks_file, 'r') as f:
            self.data = json.load(f)

        # Build task index
        for phase in self.data.get("phases", []):
            phase_id = phase["phase_id"]
            phase_name = phase["phase_name"]

            for task_data in phase.get("tasks", []):
                task = TaskInfo(
                    task_id=task_data["task_id"],
                    title=task_data["title"],
                    status=task_data["status"],
                    phase_id=phase_id,
                    phase_name=phase_name,
                    parent_task_id=task_data.get("parent_task_id"),
                    dependencies=task_data.get("dependencies", []),
                    story_mapping=task_data.get("story_mapping"),
                    spec_file=task_data.get("spec_file", "")
                )
                self.tasks[task.task_id] = task

        # Build dependents map (reverse dependencies)
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id not in self.dependents:
                    self.dependents[dep_id] = set()
                self.dependents[dep_id].add(task_id)

    def analyze_task_impact(self, task_id: str) -> ImpactReport:
        """Analyze impact of changing a specific task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self.tasks[task_id]
        report = ImpactReport(
            target=task_id,
            target_type="task"
        )

        # Direct impact - tasks that depend on this one
        direct_dependents = self.dependents.get(task_id, set())
        for dep_id in sorted(direct_dependents):
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                report.direct_impact.append({
                    "id": dep_id,
                    "name": dep_task.title,
                    "status": dep_task.status,
                    "phase": dep_task.phase_name
                })

        # Transitive impact - cascading dependencies
        transitive = set()
        for dep_id in direct_dependents:
            transitive.update(self.get_transitive_dependents(dep_id))

        for trans_id in sorted(transitive):
            if trans_id != task_id and trans_id in self.tasks:
                trans_task = self.tasks[trans_id]
                report.transitive_impact.append({
                    "id": trans_id,
                    "name": trans_task.title,
                    "status": trans_task.status,
                    "phase": trans_task.phase_name
                })

        # Affected stories
        affected_story_ids = set()
        if task.story_mapping:
            affected_story_ids.add(task.story_mapping)

        for dep_id in direct_dependents | transitive:
            if dep_id in self.tasks and self.tasks[dep_id].story_mapping:
                affected_story_ids.add(self.tasks[dep_id].story_mapping)

        for story_id in sorted(affected_story_ids):
            report.affected_stories.append({
                "story_id": story_id,
                "impact": "direct" if task.story_mapping == story_id else "indirect"
            })

        # Affected files
        report.affected_files = self._get_affected_files(task_id, direct_dependents, transitive)

        # Calculate risk level
        report.risk_level = self._calculate_risk_level(report)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report, task)

        # Generate Mermaid graph
        report.mermaid_graph = self._generate_mermaid_for_task(task_id)

        return report

    def analyze_story_impact(self, story_id: str) -> ImpactReport:
        """Analyze impact of changing a user story."""
        report = ImpactReport(
            target=story_id,
            target_type="story"
        )

        # Find all tasks that map to this story
        story_tasks = [
            (task_id, task) for task_id, task in self.tasks.items()
            if task.story_mapping == story_id
        ]

        if not story_tasks:
            return report

        # Collect all impacted tasks
        all_impacted = set()
        direct_impact = set()

        for task_id, task in story_tasks:
            direct_impact.add(task_id)
            all_impacted.add(task_id)

            # Add dependents
            for dep_id in self.dependents.get(task_id, set()):
                direct_impact.add(dep_id)
                all_impacted.add(dep_id)

            # Add transitive
            for dep_id in list(direct_impact):
                all_impacted.update(self.get_transitive_dependents(dep_id))

        # Build report
        for task_id in sorted(direct_impact):
            if task_id in self.tasks:
                task = self.tasks[task_id]
                report.direct_impact.append({
                    "id": task_id,
                    "name": task.title,
                    "status": task.status,
                    "phase": task.phase_name
                })

        for task_id in sorted(all_impacted - direct_impact):
            if task_id in self.tasks:
                task = self.tasks[task_id]
                report.transitive_impact.append({
                    "id": task_id,
                    "name": task.title,
                    "status": task.status,
                    "phase": task.phase_name
                })

        report.affected_stories.append({
            "story_id": story_id,
            "impact": "direct"
        })

        report.risk_level = self._calculate_risk_level(report)
        report.mermaid_graph = self._generate_mermaid_for_story(story_id, story_tasks)
        report.recommendations = self._generate_story_recommendations(report, story_id)

        return report

    def get_transitive_dependencies(self, task_id: str) -> Set[str]:
        """Get all transitive dependencies for a task."""
        visited = set()
        to_visit = [task_id]

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue

            visited.add(current)

            if current in self.tasks:
                for dep_id in self.tasks[current].dependencies:
                    if dep_id not in visited:
                        to_visit.append(dep_id)

        return visited - {task_id}

    def get_transitive_dependents(self, task_id: str) -> Set[str]:
        """Get all tasks that transitively depend on this task."""
        visited = set()
        to_visit = [task_id]

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue

            visited.add(current)

            for dep_id in self.dependents.get(current, set()):
                if dep_id not in visited:
                    to_visit.append(dep_id)

        return visited - {task_id}

    def _get_affected_files(self, task_id: str, direct: Set[str], transitive: Set[str]) -> List[str]:
        """Get list of files affected by task changes."""
        files = set()

        # Add spec file for the task
        if task_id in self.tasks:
            spec_file = self.tasks[task_id].spec_file
            if spec_file:
                files.add(f".sam/{self.feature_dir.name}/{spec_file}")

        # Add files for dependent tasks
        for dep_id in direct | transitive:
            if dep_id in self.tasks:
                spec_file = self.tasks[dep_id].spec_file
                if spec_file:
                    files.add(f".sam/{self.feature_dir.name}/{spec_file}")

        return sorted(files)

    def _calculate_risk_level(self, report: ImpactReport) -> str:
        """Calculate risk level based on impact."""
        total_impact = len(report.direct_impact) + len(report.transitive_impact)

        if total_impact == 0:
            return "low"

        # Check for completed tasks that would need to be re-verified
        completed_impact = sum(
            1 for item in report.direct_impact + report.transitive_impact
            if item.get("status") == "completed"
        )

        if completed_impact > 3:
            return "high"
        elif completed_impact > 0 or total_impact > 5:
            return "medium"
        else:
            return "low"

    def _generate_recommendations(self, report: ImpactReport, task: TaskInfo) -> List[str]:
        """Generate recommendations for handling the impact."""
        recommendations = []

        if not report.direct_impact and not report.transitive_impact:
            recommendations.append("✓ No dependent tasks - this change is isolated")
            return recommendations

        completed_count = sum(
            1 for item in report.direct_impact + report.transitive_impact
            if item.get("status") == "completed"
        )

        if completed_count > 0:
            recommendations.append(f"⚠️ {completed_count} completed task(s) may need re-verification")

        if report.risk_level == "high":
            recommendations.append("🔴 High risk impact - consider creating a new feature branch")
            recommendations.append("🔴 Schedule regression testing for affected components")
        elif report.risk_level == "medium":
            recommendations.append("🟡 Medium risk impact - verify dependent functionality")
        else:
            recommendations.append("🟢 Low risk impact - standard testing should suffice")

        # Specific recommendations based on dependencies
        if len(report.direct_impact) > 3:
            recommendations.append("📋 Consider updating multiple related tasks together")

        if report.affected_stories:
            recommendations.append(f"📖 Affected {len(report.affected_stories)} user story(ies) - verify acceptance criteria")

        return recommendations

    def _generate_story_recommendations(self, report: ImpactReport, story_id: str) -> List[str]:
        """Generate recommendations for story-level impact."""
        recommendations = []

        recommendations.append(f"📖 Review user story {story_id} for requirement changes")

        completed_count = sum(
            1 for item in report.direct_impact + report.transitive_impact
            if item.get("status") == "completed"
        )

        if completed_count > 0:
            recommendations.append(f"⚠️ {completed_count} implemented task(s) may be affected")

        if report.risk_level == "high":
            recommendations.append("🔴 Consider reverting story changes and re-issuing")

        return recommendations

    def _generate_mermaid_for_task(self, task_id: str) -> str:
        """Generate Mermaid graph for task impact."""
        lines = ["graph TD"]

        # Add the target task
        lines.append(f"    {task_id.replace('.', '_')}[{task_id}: {self.tasks[task_id].title}]")
        lines.append(f"    style {task_id.replace('.', '_')} fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px")

        # Add direct dependents
        direct = self.dependents.get(task_id, set())
        for dep_id in sorted(direct):
            if dep_id in self.tasks:
                node_id = dep_id.replace('.', '_')
                lines.append(f"    {node_id}[{dep_id}: {self.tasks[dep_id].title}]")
                lines.append(f"    {task_id.replace('.', '_')} -->|direct| {node_id}")
                lines.append(f"    style {node_id} fill:#ffd43b,stroke:#fab005,stroke-width:2px")

        # Add transitive dependents
        transitive = set()
        for dep_id in direct:
            transitive.update(self.get_transitive_dependents(dep_id))

        for trans_id in sorted(transitive - direct):
            if trans_id in self.tasks:
                node_id = trans_id.replace('.', '_')
                lines.append(f"    {node_id}[{trans_id}: {self.tasks[trans_id].title}]")
                # Find connection path
                for dep_id in direct:
                    if trans_id in self.get_transitive_dependents(dep_id):
                        lines.append(f"    {dep_id.replace('.', '_')} -.->|transitive| {node_id}")
                        break
                lines.append(f"    style {node_id} fill:#d3f9d8,stroke:#37b24d,stroke-width:1px")

        return "\n".join(lines)

    def _generate_mermaid_for_story(self, story_id: str, story_tasks: List[Tuple[str, TaskInfo]]) -> str:
        """Generate Mermaid graph for story impact."""
        lines = ["graph TD"]
        lines.append(f"    Story_{story_id}[Story {story_id}]")
        lines.append(f"    style Story_{story_id} fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px")

        for task_id, task in story_tasks:
            node_id = task_id.replace('.', '_')
            lines.append(f"    {node_id}[{task_id}: {task.title}]")
            lines.append(f"    Story_{story_id} -->|maps to| {node_id}")

            # Add dependents
            for dep_id in self.dependents.get(task_id, set()):
                if dep_id in self.tasks:
                    dep_node_id = dep_id.replace('.', '_')
                    lines.append(f"    {dep_node_id}[{dep_id}: {self.tasks[dep_id].title}]")
                    lines.append(f"    {node_id} -->|dependent| {dep_node_id}")

        return "\n".join(lines)

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies in the task graph using DFS with three-color marking.

        A circular dependency (deadlock) occurs when:
        - Task A depends on Task B
        - Task B depends on Task C
        - Task C depends on Task A (directly or transitively)

        This prevents parallel execution and causes the system to hang.

        Returns:
            List of cycles, where each cycle is a list of task IDs in order
        """
        # Three-state marking for cycle detection
        # WHITE (0): Not visited
        # GRAY (1): Visiting (in current DFS path)
        # BLACK (2): Visited (fully processed)
        WHITE, GRAY, BLACK = 0, 1, 2

        color = {task_id: WHITE for task_id in self.tasks}
        cycles: List[List[str]] = []
        parent: Dict[str, Optional[str]] = {}

        def dfs_cycle_detect(task_id: str, path: List[str]) -> bool:
            """DFS to detect cycles, returns True if cycle found."""
            color[task_id] = GRAY
            path.append(task_id)

            # Check all dependencies
            for dep_id in self.tasks[task_id].dependencies:
                if dep_id not in self.tasks:
                    continue  # Skip invalid dependencies

                if color[dep_id] == GRAY:
                    # Found a cycle - extract it from the path
                    cycle_start_idx = path.index(dep_id)
                    cycle = path[cycle_start_idx:] + [dep_id]
                    cycles.append(cycle)
                    return True
                elif color[dep_id] == WHITE:
                    if dfs_cycle_detect(dep_id, path):
                        return True

            color[task_id] = BLACK
            path.pop()
            return False

        # Run DFS from each unvisited node
        for task_id in self.tasks:
            if color[task_id] == WHITE:
                dfs_cycle_detect(task_id, [])

        return cycles

    def analyze_blocking_chains(self) -> Dict[str, List[str]]:
        """
        Analyze blocking chains to identify which tasks are blocking others.

        Returns:
            Dictionary mapping blocker task ID to list of blocked task IDs
        """
        blocking_chains: Dict[str, List[str]] = {}

        for task_id, task in self.tasks.items():
            if task.status != "completed":
                # Check which incomplete tasks are blocking this one
                for dep_id in task.dependencies:
                    if dep_id in self.tasks:
                        dep_task = self.tasks[dep_id]
                        if dep_task.status != "completed":
                            if dep_id not in blocking_chains:
                                blocking_chains[dep_id] = []
                            blocking_chains[dep_id].append(task_id)

        return blocking_chains

    def suggest_cycle_resolution(self, cycle: List[str]) -> List[str]:
        """
        Suggest resolutions for a detected circular dependency.

        Args:
            cycle: List of task IDs forming a cycle

        Returns:
            List of resolution suggestions
        """
        suggestions = []

        suggestions.append(f"🔴 Circular dependency detected: {' → '.join(cycle)}")
        suggestions.append("")
        suggestions.append("Possible resolutions:")
        suggestions.append(f"  1. Break the cycle at {cycle[-1]}:")
        suggestions.append(f"     - Remove dependency from {cycle[-1]} to {cycle[0]}")
        suggestions.append(f"     - Or mark {cycle[0]} as completed if it's actually done")
        suggestions.append("")
        suggestions.append("  2. Refactor to extract shared dependency:")
        suggestions.append("     - Create a new task for shared functionality")
        suggestions.append("     - Make both tasks depend on the new task")
        suggestions.append("")
        suggestions.append("  3. Merge tasks into a single task:")
        suggestions.append(f"     - Combine {', '.join(cycle)} into one task")
        suggestions.append("")
        suggestions.append("  4. Review if dependencies are correctly specified:")
        suggestions.append("     - Some 'dependencies' may be order preferences, not hard requirements")

        return suggestions

    def generate_full_dependency_graph(self, highlight_cycles: bool = False) -> str:
        """
        Generate complete Mermaid dependency graph.

        Args:
            highlight_cycles: If True, highlight circular dependencies in red
        """
        lines = ["graph TD"]
        lines.append("    subgraph Phases")

        # Group by phase
        phase_groups = {}
        for task_id, task in self.tasks.items():
            phase_key = f"Phase_{task.phase_id}"
            if phase_key not in phase_groups:
                phase_groups[phase_key] = []
            phase_groups[phase_key].append(task)

        for phase_key, tasks in sorted(phase_groups.items()):
            phase_name = tasks[0].phase_name if tasks else ""
            lines.append(f"        subgraph {phase_key}[{phase_name}]")

            for task in tasks:
                node_id = task.task_id.replace('.', '_')
                status_color = "#51cf66" if task.status == "completed" else "#868e96"
                lines.append(f"            {node_id}[{task.task_id}: {task.title}]")
                lines.append(f"            style {node_id} fill:{status_color},stroke:#228be6,stroke-width:1px")

            lines.append("        end")

        lines.append("    end")

        # Detect cycles if highlighting is requested
        cycle_tasks = set()
        if highlight_cycles:
            cycles = self.detect_cycles()
            for cycle in cycles:
                cycle_tasks.update(cycle)

        # Add dependencies
        for task_id, task in self.tasks.items():
            node_id = task_id.replace('.', '_')
            for dep_id in task.dependencies:
                if dep_id in self.tasks:
                    dep_node_id = dep_id.replace('.', '_')
                    # Highlight cycle edges in red
                    if highlight_cycles and task_id in cycle_tasks and dep_id in cycle_tasks:
                        lines.append(f"    {dep_node_id} ==>|CYCLE| {node_id}")
                        lines.append(f"    style {node_id} stroke:#ff0000,stroke-width:3px")
                        lines.append(f"    style {dep_node_id} stroke:#ff0000,stroke-width:3px")
                    else:
                        lines.append(f"    {dep_node_id} -->|depends| {node_id}")

        return "\n".join(lines)

    def generate_impact_report(self, target: str, target_type: str = "task") -> str:
        """Generate markdown impact analysis report."""
        if target_type == "task":
            report = self.analyze_task_impact(target)
        else:
            report = self.analyze_story_impact(target)

        template = self._load_report_template()
        return self._fill_template(template, report)

    def _load_report_template(self) -> str:
        """Load impact report template."""
        template_file = Path(__file__).parent.parent.parent.parent / "templates" / "IMPACT_REPORT_TEMPLATE.md"
        if template_file.exists():
            return template_file.read_text()
        return self._get_default_template()

    def _get_default_template(self) -> str:
        """Get default impact report template."""
        return """# Impact Analysis Report

**Target**: {{TARGET_TYPE}} {{TARGET_ID}}
**Generated**: {{TIMESTAMP}}
**Risk Level**: {{RISK_LEVEL}}

---

## Direct Impact

The following items are directly affected:

| Type | ID | Name | Status |
|------|----|----|--------|
{{DIRECT_IMPACT_ROWS}}

---

## Transitive Impact

The following items are indirectly affected:

| Type | ID | Name | Status |
|------|----|----|--------|
{{TRANSITIVE_IMPACT_ROWS}}

---

## Affected Stories

| Story ID | Impact |
|----------|--------|
{{STORY_ROWS}}

---

## Affected Files

```
{{FILE_TREE}}
```

---

## Dependency Graph

```mermaid
{{MERMAID_GRAPH}}
```

---

## Recommendations

{{RECOMMENDATIONS}}
"""

    def _fill_template(self, template: str, report: ImpactReport) -> str:
        """Fill template with report data."""
        # Generate direct impact rows
        direct_rows = []
        for item in report.direct_impact:
            direct_rows.append(f"| {report.target_type} | {item['id']} | {item['name']} | {item['status']} |")
        direct_rows_str = "\n".join(direct_rows) if direct_rows else "| - | - | No direct impact | - |"

        # Generate transitive impact rows
        transitive_rows = []
        for item in report.transitive_impact:
            transitive_rows.append(f"| {report.target_type} | {item['id']} | {item['name']} | {item['status']} |")
        transitive_rows_str = "\n".join(transitive_rows) if transitive_rows else "| - | - | No transitive impact | - |"

        # Generate story rows
        story_rows = []
        for story in report.affected_stories:
            story_rows.append(f"| {story['story_id']} | {story['impact']} |")
        story_rows_str = "\n".join(story_rows) if story_rows else "| - | - |"

        # Generate file tree
        file_tree = "\n".join(report.affected_files) if report.affected_files else "No affected files"

        # Generate recommendations
        recommendations_str = "\n".join(f"- {rec}" for rec in report.recommendations) if report.recommendations else "- No specific recommendations"

        # Fill template
        return template.replace("{{TARGET_TYPE}}", report.target_type.capitalize()) \
            .replace("{{TARGET_ID}}", report.target) \
            .replace("{{TIMESTAMP}}", report.timestamp) \
            .replace("{{RISK_LEVEL}}", report.risk_level.upper()) \
            .replace("{{DIRECT_IMPACT_ROWS}}", direct_rows_str) \
            .replace("{{TRANSITIVE_IMPACT_ROWS}}", transitive_rows_str) \
            .replace("{{STORY_ROWS}}", story_rows_str) \
            .replace("{{FILE_TREE}}", file_tree) \
            .replace("{{MERMAID_GRAPH}}", report.mermaid_graph) \
            .replace("{{RECOMMENDATIONS}}", recommendations_str)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 impact_analyzer.py <feature_dir> [--task <id> | --story <id> | --visualize | --check-cycles] [--report] [--output <file>]")
        print("Examples:")
        print("  python3 impact_analyzer.py .sam/001_user_auth --task 2.1.3")
        print("  python3 impact_analyzer.py .sam/001_user_auth --story 001")
        print("  python3 impact_analyzer.py .sam/001_user_auth --visualize")
        print("  python3 impact_analyzer.py .sam/001_user_auth --task 1.1 --report")
        print("  python3 impact_analyzer.py .sam/001_user_auth --check-cycles")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    output_file = None
    generate_report = False
    visualize = False
    check_cycles = False
    target_type = None
    target_id = None

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--task":
            target_type = "task"
            target_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--story":
            target_type = "story"
            target_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--visualize":
            visualize = True
            i += 1
        elif sys.argv[i] == "--check-cycles":
            check_cycles = True
            i += 1
        elif sys.argv[i] == "--report":
            generate_report = True
            i += 1
        elif sys.argv[i] == "--output":
            output_file = Path(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    tasks_file = feature_dir / "TASKS.json"
    if not tasks_file.exists():
        print(f"Error: TASKS.json not found in {feature_dir}")
        print("Hint: Run spec_parser.py first to generate TASKS.json")
        sys.exit(1)

    # Analyze
    analyzer = ImpactAnalyzer(feature_dir)
    analyzer.load_tasks()

    # Check for circular dependencies (deadlock detection)
    if check_cycles:
        print(f"\n🔍 Checking for circular dependencies in {feature_dir.name}...")
        print("=" * 60)

        cycles = analyzer.detect_cycles()

        if cycles:
            print(f"\n❌ Found {len(cycles)} circular dependency/cycles:\n")
            for idx, cycle in enumerate(cycles, 1):
                print(f"Cycle {idx}: {' → '.join(cycle)}")
                print()
                suggestions = analyzer.suggest_cycle_resolution(cycle)
                for suggestion in suggestions:
                    print(f"  {suggestion}")
                print()
                print("-" * 60)

            # Generate visualization with cycles highlighted
            if output_file:
                graph = analyzer.generate_full_dependency_graph(highlight_cycles=True)
                with open(output_file, 'w') as f:
                    f.write(graph)
                print(f"\n📊 Generated graph with highlighted cycles: {output_file}")
                print("   View at: https://mermaid.live/")
            else:
                graph = analyzer.generate_full_dependency_graph(highlight_cycles=True)
                print("\n📊 Mermaid graph (cycles highlighted in red):")
                print(graph)
                print("\nView at: https://mermaid.live/")

            sys.exit(1)
        else:
            print("✅ No circular dependencies detected!")
            print("   The task graph is acyclic and safe for parallel execution.")
            sys.exit(0)

    elif visualize:
        # Generate full dependency graph
        graph = analyzer.generate_full_dependency_graph()

        if output_file:
            with open(output_file, 'w') as f:
                f.write(graph)
            print(f"✓ Generated dependency graph: {output_file}")
        else:
            print("Mermaid Dependency Graph:")
            print(graph)
            print("\nView at: https://mermaid.live/")

    elif target_id and target_type:
        report = analyzer.analyze_task_impact(target_id) if target_type == "task" else analyzer.analyze_story_impact(target_id)

        print(f"\n📊 Impact Analysis: {target_type.capitalize()} {target_id}")
        print(f"   Risk Level: {report.risk_level.upper()}")
        print(f"   Direct Impact: {len(report.direct_impact)} item(s)")
        print(f"   Transitive Impact: {len(report.transitive_impact)} item(s)")
        print(f"   Affected Stories: {len(report.affected_stories)}")

        if generate_report or output_file:
            report_text = analyzer.generate_impact_report(target_id, target_type)

            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                print(f"\n✓ Generated impact report: {output_file}")
            else:
                report_file = feature_dir / f"IMPACT_REPORT_{target_id.replace('.', '_')}.md"
                with open(report_file, 'w') as f:
                    f.write(report_text)
                print(f"\n✓ Generated impact report: {report_file}")

        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  {rec}")

    else:
        print("Error: Please specify --task, --story, --visualize, or --check-cycles")
        sys.exit(1)


if __name__ == "__main__":
    main()
