#!/usr/bin/env python3
"""
test_generator.py - Generate test files from executable specifications

This script reads SCENARIOS.json (parsed from EXECUTABLE_SPEC.yaml) and generates
test files in various formats: Jest, Cucumber (Gherkin), or Pytest.

Usage:
    python3 skills/sam-specs/scripts/test_generator.py <feature_dir> [--framework jest|cucumber|pytest]
    python3 skills/sam-specs/scripts/test_generator.py .sam/001_user_auth --framework jest

Output:
    Generates test files in the feature's tests/ directory
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from stringcase import snakecase, camelcase

# Import context resolver for variable interpolation
try:
    from context_resolver import ContextResolver
    CONTEXT_RESOLVER_AVAILABLE = True
except ImportError:
    CONTEXT_RESOLVER_AVAILABLE = False


class TestGenerator:
    """Generate test files from scenario specifications."""

    def __init__(self, scenarios_file: Path, framework: str = "jest", use_context: bool = True):
        self.scenarios_file = scenarios_file
        self.framework = framework.lower()
        self.feature_dir = scenarios_file.parent
        self.data: Dict[str, Any] = {}
        self.use_context = use_context and CONTEXT_RESOLVER_AVAILABLE
        self.context_resolver: Optional[ContextResolver] = None

        if self.use_context:
            self.context_resolver = ContextResolver(self.feature_dir)
            try:
                self.context_resolver.load_context()
            except Exception as e:
                # Context loading is optional - log warning and continue
                print(f"  ⚠ Could not load context: {e}")
                self.use_context = False

    def load_scenarios(self):
        """Load scenarios from SCENARIOS.json."""
        with open(self.scenarios_file, 'r') as f:
            self.data = json.load(f)

    def resolve_context(self, template: str) -> str:
        """
        Resolve {{VARIABLE}} placeholders in a template string.

        Args:
            template: String containing potential placeholders

        Returns:
            String with placeholders resolved (if context available)
        """
        if self.use_context and self.context_resolver:
            return self.context_resolver.resolve_string(template)
        return template

    def generate_all(self):
        """Generate all test files."""
        self.load_scenarios()

        if self.framework == "jest":
            self._generate_jest_tests()
        elif self.framework == "cucumber":
            self._generate_cucumber_tests()
        elif self.framework == "pytest":
            self._generate_pytest_tests()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def _generate_jest_tests(self):
        """Generate Jest test files from scenarios."""
        feature_id = self.data["metadata"]["feature_id"]
        feature_name = self.data["metadata"]["feature_name"]

        # Create tests directory
        tests_dir = self.feature_dir / "tests" / "jest"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate main test file
        test_file = tests_dir / f"{snakecase(feature_name)}.test.ts"

        content = self._generate_jest_header()
        content += self._generate_jest_scenarios()
        content += self._generate_jest_contract_tests()
        content += self._generate_jest_footer()

        with open(test_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Jest tests: {test_file}")

        # Generate test utilities
        self._generate_jest_utils(tests_dir)

    def _generate_jest_header(self) -> str:
        """Generate Jest test file header."""
        return f'''/**
 * Auto-generated test file from executable specification
 * Feature: {self.data["metadata"]["feature_name"]}
 * Generated: {datetime.now().isoformat()}
 */

import {{ request }} from '@/tests/setup';
import {{ TestContext }} from '@/types/test';

'''

    def _generate_jest_scenarios(self) -> str:
        """Generate Jest test cases from scenarios."""
        content = "describe('Executable Scenarios', () => {\n"

        for scenario in self.data.get("scenarios", []):
            content += self._generate_jest_scenario(scenario)

        content += "});\n\n"
        return content

    def _generate_jest_scenario(self, scenario: Dict[str, Any]) -> str:
        """Generate a single Jest scenario test."""
        scenario_name = camelcase(scenario["name"])

        content = f"""
  describe('{scenario["name"]}', () => {{
    let context: TestContext;

    beforeEach(async () => {{
      context = {{}};

'''

        # Generate Given steps (setup)
        for given_step in scenario.get("given", []):
            content += self._generate_jest_given(given_step)

        # Generate When step (action)
        for when_step in scenario.get("when", []):
            content += self._generate_jest_when(when_step)

        content += "    });\n\n"

        # Generate Then steps (assertions)
        for then_step in scenario.get("then", []):
            content += self._generate_jest_then(then_step)

        content += "  });\n"

        return content

    def _generate_jest_given(self, step: Dict[str, Any]) -> str:
        """Generate Jest code for a Given step."""
        description = step["description"]
        content = f"      // Given: {description}\n"

        for setup_action in step.get("setup", []):
            action = setup_action["action"]
            target = setup_action["target"]

            if action == "truncate_table":
                content += f"      await truncateTable('{target}');\n"
            elif action == "mock_service":
                content += f"      mockService('{target}');\n"
            elif action == "seed_database":
                data = setup_action.get("data", {})
                content += f"      await seedDatabase('{target}', {json.dumps(data)});\n"

        return content

    def _generate_jest_when(self, step: Dict[str, Any]) -> str:
        """Generate Jest code for a When step."""
        description = step["description"]
        action = step["action"]

        content = f"\n      // When: {description}\n"
        content += f"      context.response = await request(app)\n"

        method = action["method"].lower()
        endpoint = action["endpoint"]
        content += f"        .{method}('{endpoint}')\n"

        # Add headers
        headers = action.get("headers", {})
        for key, value in headers.items():
            content += f"        .set('{key}', '{value}')\n"

        # Add body
        body = action.get("body", {})
        if body:
            content += f"        .send({json.dumps(body)});\n"
        else:
            content += "        .send();\n"

        return content

    def _generate_jest_then(self, step: Dict[str, Any]) -> str:
        """Generate Jest code for a Then step."""
        description = step["description"]
        assertion = step["assertion"]

        content = f"\n    it('{description}', async () => {{\n"

        assertion_type = assertion["type"]
        expected = assertion["expected"]
        comparison = assertion["comparison"]

        if assertion_type == "status_code":
            content += f"      expect(context.response.status).toBe({expected});\n"

        elif assertion_type == "json_path":
            path = assertion["path"]
            if comparison == "exists":
                content += f"      expect(context.response.body{self._json_path_to_js(path)}).toBeDefined();\n"
            elif comparison == "equals":
                content += f"      expect(context.response.body{self._json_path_to_js(path)}).toBe('{expected}');\n"

        elif assertion_type == "database_query":
            query = assertion["query"]
            if comparison == "equals":
                content += f"      const result = await db.query(`{query}`);\n"
                content += f"      expect(result.rows[0].count).toBe('{expected}');\n"

        elif assertion_type == "service_mock":
            service = assertion["service"]
            expected_calls = assertion["expected_calls"]
            content += f"      expect({service}.{assertion['method']}).toHaveBeenCalledTimes({expected_calls});\n"

        content += "    });\n"

        return content

    def _json_path_to_js(self, path: str) -> str:
        """Convert JSONPath to JavaScript property access."""
        # Simple implementation: convert $.foo.bar to .foo.bar
        return path.replace("$.", ".")

    def _generate_jest_contract_tests(self) -> str:
        """Generate Jest contract tests."""
        if not self.data.get("contract_tests"):
            return ""

        content = "describe('Contract Tests', () => {\n"

        for contract in self.data.get("contract_tests", []):
            content += f"""
  describe('{contract["name"]}', () => {{
    it('should validate request schema', () => {{
      const schema = {json.dumps(contract.get("request_schema", {}), indent=6)};
      // Add schema validation logic
    }});

    it('should validate success response schema', () => {{
      const schema = {json.dumps(contract.get("response_schema_success", {}), indent=6)};
      // Add schema validation logic
    }});

    it('should validate error response schema', () => {{
      const schema = {json.dumps(contract.get("response_schema_error", {}), indent=6)};
      // Add schema validation logic
    }});
  }});
"""

        content += "});\n\n"
        return content

    def _generate_jest_footer(self) -> str:
        """Generate Jest test file footer."""
        return """
// Export metadata for test reporting
export const testMetadata = {
  featureId: '""" + self.data["metadata"]["feature_id"] + """',
  scenarioCount: """ + str(len(self.data.get("scenarios", []))) + """,
  contractTestCount: """ + str(len(self.data.get("contract_tests", []))) + """,
  generatedAt: '""" + datetime.now().isoformat() + """'
};
"""

    def _generate_jest_utils(self, tests_dir: Path):
        """Generate Jest test utilities."""
        utils_file = tests_dir / "utils.ts"

        content = '''/**
 * Test utilities for executable specification tests
 */

import { Pool } from 'pg';

export const db = new Pool({
  host: process.env.TEST_DB_HOST || 'localhost',
  port: parseInt(process.env.TEST_DB_PORT || '5432'),
  database: process.env.TEST_DB_NAME || 'test_db',
  user: process.env.TEST_DB_USER || 'test_user',
  password: process.env.TEST_DB_PASSWORD || 'test_pass',
});

export async function truncateTable(table: string): Promise<void> {
  await db.query(`TRUNCATE TABLE ${table} CASCADE`);
}

export async function seedDatabase(table: string, data: any): Promise<void> {
  // Implementation for seeding database
}

export function mockService(serviceName: string): void {
  // Implementation for mocking services
}
'''

        with open(utils_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Jest utils: {utils_file}")

    def _generate_cucumber_tests(self):
        """Generate Cucumber (Gherkin) feature files."""
        feature_id = self.data["metadata"]["feature_id"]
        feature_name = self.data["metadata"]["feature_name"]

        # Create tests directory
        tests_dir = self.feature_dir / "tests" / "cucumber"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate feature file
        feature_file = tests_dir / f"{snakecase(feature_name)}.feature"

        content = f"""Feature: {feature_name}
  As a user
  I want to {feature_name.lower()}
  So that I can achieve my goals

"""

        # Generate scenarios
        for scenario in self.data.get("scenarios", []):
            content += f"  Scenario: {scenario['name']}\n"

            # Given steps
            for given_step in scenario.get("given", []):
                content += f"    Given {given_step['description']}\n"

            # When steps
            for when_step in scenario.get("when", []):
                content += f"    When {when_step['description']}\n"

            # Then steps
            for then_step in scenario.get("then", []):
                content += f"    Then {then_step['description']}\n"

            content += "\n"

        with open(feature_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Cucumber feature: {feature_file}")

        # Generate step definitions
        self._generate_cucumber_steps(tests_dir)

    def _generate_cucumber_steps(self, tests_dir: Path):
        """Generate Cucumber step definitions."""
        steps_file = tests_dir / "steps.ts"

        content = '''/**
 * Auto-generated step definitions from executable specification
 */

import {{ Given, When, Then }} from '@cucumber/cucumber';
import {{ expect }} from 'chai';

// Given steps
'''

        # Collect unique Given steps
        given_steps = {}
        for scenario in self.data.get("scenarios", []):
            for step in scenario.get("given", []):
                desc = step["description"]
                step_id = step["step_id"]
                given_steps[step_id] = desc

        for step_id, desc in given_steps.items():
            pattern = self._gherkin_pattern(desc)
            content += f"Given('{pattern}', async function () {{\n"
            content += f"    // Step {step_id}: {desc}\n"
            content += f"    // TODO: Implement step logic\n"
            content += f"}});\n\n"

        # Collect unique When steps
        content += "\n// When steps\n"
        when_steps = {}
        for scenario in self.data.get("scenarios", []):
            for step in scenario.get("when", []):
                desc = step["description"]
                step_id = step.get("step_id", "W001")
                when_steps[step_id] = desc

        for step_id, desc in when_steps.items():
            pattern = self._gherkin_pattern(desc)
            content += f"When('{pattern}', async function () {{\n"
            content += f"    // Step {step_id}: {desc}\n"
            content += f"    // TODO: Implement step logic\n"
            content += f"}});\n\n"

        # Collect unique Then steps
        content += "\n// Then steps\n"
        then_steps = {}
        for scenario in self.data.get("scenarios", []):
            for step in scenario.get("then", []):
                desc = step["description"]
                step_id = step["step_id"]
                then_steps[step_id] = desc

        for step_id, desc in then_steps.items():
            pattern = self._gherkin_pattern(desc)
            content += f"Then('{pattern}', async function () {{\n"
            content += f"    // Step {step_id}: {desc}\n"
            content += f"    // TODO: Implement step logic\n"
            content += f"}});\n\n"

        with open(steps_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Cucumber steps: {steps_file}")

    def _gherkin_pattern(self, description: str) -> str:
        """Convert description to Gherkin regex pattern."""
        # Escape special regex characters
        pattern = description.replace("(", "\\(").replace(")", "\\)")
        return pattern

    def _generate_pytest_tests(self):
        """Generate Pytest test files."""
        feature_id = self.data["metadata"]["feature_id"]
        feature_name = self.data["metadata"]["feature_name"]

        # Create tests directory
        tests_dir = self.feature_dir / "tests" / "pytest"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate test file
        test_file = tests_dir / f"test_{snakecase(feature_name)}.py"

        content = f'''"""
Auto-generated test file from executable specification
Feature: {feature_name}
Generated: {datetime.now().isoformat()}
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestExecutableScenarios:
    """Test cases from executable specification scenarios."""

'''

        # Generate test methods
        for scenario in self.data.get("scenarios", []):
            content += self._generate_pytest_scenario(scenario)

        with open(test_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Pytest tests: {test_file}")

    def _generate_pytest_scenario(self, scenario: Dict[str, Any]) -> str:
        """Generate a single Pytest scenario test."""
        method_name = snakecase(scenario["name"])

        content = f"""
    def test_{method_name}(self, test_client):
        \"\"\"Test: {scenario['name']}

        Story: {scenario['story_mapping']}
        Acceptance Criteria: {scenario['acceptance_criteria']}
        \"\"\"
'''

        # Generate Given steps
        for given_step in scenario.get("given", []):
            content += f"        # Given: {given_step['description']}\n"
            for setup_action in given_step.get("setup", []):
                action = setup_action["action"]
                target = setup_action["target"]
                if action == "truncate_table":
                    content += f"        test_client.truncate_table('{target}')\n"

        # Generate When step
        for when_step in scenario.get("when", []):
            content += f"\n        # When: {when_step['description']}\n"
            action = when_step["action"]
            method = action["method"].lower()
            endpoint = action["endpoint"]
            content += f"        response = test_client.{method}('{endpoint}'"

            body = action.get("body")
            if body:
                content += f", json={json.dumps(body)}"
            content += ")\n"

        # Generate Then steps
        for then_step in scenario.get("then", []):
            content += f"\n        # Then: {then_step['description']}\n"
            assertion = then_step["assertion"]

            if assertion["type"] == "status_code":
                content += f"        assert response.status_code == {assertion['expected']}\n"
            elif assertion["type"] == "json_path":
                path = assertion["path"]
                if assertion["comparison"] == "exists":
                    content += f"        assert '{path.replace('$.', '').lstrip('.')}' in response.json()\n"
                elif assertion["comparison"] == "equals":
                    content += f"        assert response.json(){''.join(f'['{p.lstrip('$.')}]' for p in path.split('.'))} == '{assertion['expected']}'\n"

        return content


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 test_generator.py <feature_dir> [--framework jest|cucumber|pytest] [--no-context] [--context-file PATH]")
        print("Example: python3 test_generator.py .sam/001_user_auth --framework jest")
        print("Example: python3 test_generator.py .sam/001_user_auth --framework jest --context-file custom/CONTEXT.yaml")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    framework = "jest"
    use_context = True
    context_file = None

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--framework" and i + 1 < len(sys.argv):
            framework = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--no-context":
            use_context = False
            i += 1
        elif sys.argv[i] == "--context-file" and i + 1 < len(sys.argv):
            context_file = Path(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Find scenarios file
    scenarios_file = feature_dir / "SCENARIOS.json"

    if not scenarios_file.exists():
        print(f"Error: SCENARIOS.json not found in {feature_dir}")
        print("Hint: Run scenario_parser.py first to generate SCENARIOS.json")
        sys.exit(1)

    # Generate tests
    print(f"Generating {framework.upper()} tests from: {scenarios_file}")
    generator = TestGenerator(scenarios_file, framework, use_context=use_context)

    # Override context file if specified
    if context_file and generator.context_resolver:
        generator.context_resolver.feature_context_path = context_file
    generator.generate_all()

    print(f"\n✓ Test generation complete!")
    print(f"  Framework: {framework.upper()}")
    print(f"  Output directory: {feature_dir / 'tests'}")


if __name__ == "__main__":
    main()
