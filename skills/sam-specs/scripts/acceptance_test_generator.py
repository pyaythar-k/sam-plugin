#!/usr/bin/env python3
"""
acceptance_test_generator.py - Generate acceptance tests for each task

This script reads TASKS.json and generates acceptance tests for each task
based on its story mapping. This enables shift-left verification where each
task is validated against its acceptance criteria immediately after implementation.

Usage:
    python3 skills/sam-specs/scripts/acceptance_test_generator.py <feature_dir>
    python3 skills/sam-specs/scripts/acceptance_test_generator.py .sam/001_user_auth

Output:
    Generates acceptance tests in .sam/{feature}/tests/acceptance/
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from stringcase import snakecase


class AcceptanceTestGenerator:
    """Generate acceptance tests from task specifications."""

    def __init__(self, feature_dir: Path):
        self.feature_dir = feature_dir
        self.tasks_file = feature_dir / "TASKS.json"
        self.scenarios_file = feature_dir / "SCENARIOS.json"
        self.tasks_data: Dict[str, Any] = {}
        self.scenarios_data: Dict[str, Any] = {}

    def load_data(self):
        """Load TASKS.json and SCENARIOS.json."""
        with open(self.tasks_file, 'r') as f:
            self.tasks_data = json.load(f)

        if self.scenarios_file.exists():
            with open(self.scenarios_file, 'r') as f:
                self.scenarios_data = json.load(f)

    def generate_all(self):
        """Generate acceptance tests for all tasks."""
        self.load_data()

        feature_id = self.tasks_data["metadata"]["feature_id"]
        feature_name = self.tasks_data["metadata"]["feature_name"]

        # Create tests directory
        tests_dir = self.feature_dir / "tests" / "acceptance"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate acceptance test file
        test_file = tests_dir / f"test_{snakecase(feature_name)}_acceptance.ts"

        content = self._generate_header(feature_name)
        content += self._generate_imports()

        # Generate tests for each phase
        for phase in self.tasks_data.get("phases", []):
            content += self._generate_phase_tests(phase)

        content += self._generate_footer()

        with open(test_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated acceptance tests: {test_file}")

        # Generate acceptance test status tracker
        self._generate_status_tracker(tests_dir)

    def _generate_header(self, feature_name: str) -> str:
        """Generate test file header."""
        return f'''/**
 * Auto-generated acceptance tests for task verification
 * Feature: {feature_name}
 * Generated: {datetime.now().isoformat()}
 *
 * These tests validate that each task meets its acceptance criteria.
 * Run after each task completion for shift-left verification.
 */

'''

    def _generate_imports(self) -> str:
        """Generate import statements."""
        return '''import {{ test, expect }} from '@jest/globals';
import {{ acceptTask, TaskResult }} from '../helpers/task-acceptance';

'''

    def _generate_phase_tests(self, phase: Dict[str, Any]) -> str:
        """Generate tests for a phase."""
        content = f"describe('Phase {phase['phase_id']}: {phase['phase_name']}', () => {{\n"

        # Generate tests for each task
        for task in phase.get("tasks", []):
            content += self._generate_task_test(task)

        content += "});\n\n"
        return content

    def _generate_task_test(self, task: Dict[str, Any]) -> str:
        """Generate acceptance test for a single task."""
        task_id = task["task_id"]
        title = task["title"]
        story_mapping = task.get("story_mapping", "")

        content = f"""
  describe('Task {task_id}: {title}', () => {{
    const taskId = '{task_id}';
"""

        # Add story mapping info
        if story_mapping:
            content += f"    const storyMapping = '{story_mapping}';\n"

        # Add acceptance criteria test
        content += """
    it('should meet all acceptance criteria', async () => {
      const result: TaskResult = await acceptTask(taskId);

      // Verify implementation exists
      expect(result.implemented).toBe(true);

      // Verify acceptance criteria pass
      expect(result.acceptanceCriteria.passed).toBe(true);
      expect(result.acceptanceCriteria.total).toBeGreaterThan(0);

      // Verify no blocking issues
      expect(result.blockingIssues).toEqual([]);
    });

    it('should pass quality gates', async () => {
      const result: TaskResult = await acceptTask(taskId);

      // Linting passes
      expect(result.qualityGates.linting).toBe('passed');

      // Type checking passes
      expect(result.qualityGates.typeCheck).toBe('passed');

      // Build succeeds
      expect(result.qualityGates.build).toBe('passed');
    });

    it('should have test coverage', async () => {
      const result: TaskResult = await acceptTask(taskId);

      // Tests exist for this task
      expect(result.tests.exists).toBe(true);

      // Tests pass
      expect(result.tests.passing).toBe(true);

      // Coverage meets threshold
      expect(result.tests.coverage).toBeGreaterThanOrEqual(80);
    });
  });
"""

        return content

    def _generate_footer(self) -> str:
        """Generate test file footer."""
        return """
/**
 * Task Acceptance Helper
 *
 * This helper function validates task completion:
 *
 * 1. Implementation exists (files created, code written)
 * 2. Acceptance criteria pass (scenarios from EXECUTABLE_SPEC.yaml)
 * 3. Quality gates pass (lint, type-check, build)
 * 4. Tests exist and pass with sufficient coverage
 *
 * Usage:
 *   const result = await acceptTask('1.1');
 *   if (result.acceptanceCriteria.passed) {
 *     // Task can be marked as [x]
 *   }
 */

async function acceptTask(taskId: string): Promise<TaskResult> {
  // Implementation in task-acceptance.ts
  return {} as TaskResult;
}
"""

    def _generate_status_tracker(self, tests_dir: Path):
        """Generate acceptance test status tracker."""
        tracker_file = tests_dir / "task-acceptance.ts"

        content = '''/**
 * Task Acceptance Helper Functions
 *
 * These functions help verify that tasks meet their acceptance criteria
 * before being marked as complete.
 */

export interface TaskResult {
  taskId: string;
  implemented: boolean;
  acceptanceCriteria: {
    passed: boolean;
    total: number;
    criteria: CriterionResult[];
  };
  qualityGates: {
    linting: 'passed' | 'failed' | 'skipped';
    typeCheck: 'passed' | 'failed' | 'skipped';
    build: 'passed' | 'failed' | 'skipped';
  };
  tests: {
    exists: boolean;
    passing: boolean;
    coverage: number;
  };
  blockingIssues: string[];
}

export interface CriterionResult {
  description: string;
  passed: boolean;
  error?: string;
}

/**
 * Validate that a task meets all acceptance criteria
 */
export async function acceptTask(taskId: string): Promise<TaskResult> {
  const result: TaskResult = {
    taskId,
    implemented: false,
    acceptanceCriteria: {
      passed: false,
      total: 0,
      criteria: []
    },
    qualityGates: {
      linting: 'skipped',
      typeCheck: 'skipped',
      build: 'skipped'
    },
    tests: {
      exists: false,
      passing: false,
      coverage: 0
    },
    blockingIssues: []
  };

  // Check implementation, acceptance criteria, quality gates, tests
  // Implementation details would go here

  return result;
}
'''

        with open(tracker_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated acceptance tracker: {tracker_file}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 acceptance_test_generator.py <feature_dir>")
        print("Example: python3 acceptance_test_generator.py .sam/001_user_auth")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Find tasks file
    tasks_file = feature_dir / "TASKS.json"

    if not tasks_file.exists():
        print(f"Error: TASKS.json not found in {feature_dir}")
        print("Hint: Run spec_parser.py first to generate TASKS.json")
        sys.exit(1)

    # Generate acceptance tests
    print(f"Generating acceptance tests from: {tasks_file}")
    generator = AcceptanceTestGenerator(feature_dir)
    generator.generate_all()

    print(f"\\n✓ Acceptance test generation complete!")
    print(f"  Output directory: {feature_dir / 'tests' / 'acceptance'}")


if __name__ == "__main__":
    main()
