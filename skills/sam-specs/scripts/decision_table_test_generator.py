#!/usr/bin/env python3
"""
decision_table_test_generator.py - Generate test cases from decision tables

This script reads parsed decision table definitions from SCENARIOS.json and
generates exhaustive test cases covering all rules. Supports multiple testing
frameworks with data-driven test patterns.

Usage:
    python3 skills/sam-specs/scripts/decision_table_test_generator.py <feature_dir> [--framework jest|cucumber|pytest] [--edge-cases]
    python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/001_user_auth --framework jest
    python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/001_user_auth --framework jest --edge-cases

Output:
    Generates test files in .sam/{feature}/tests/decision-tables/
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from stringcase import camelcase, pascalcase, snakecase


@dataclass
class TestCase:
    """Generated test case from decision table rule."""
    test_id: str
    description: str
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    rule_index: int
    priority: str  # "critical", "high", "medium", "low"


@dataclass
class DecisionTableConfig:
    """Configuration for test generation."""
    framework: str  # "jest", "cucumber", "pytest"
    output_dir: Path
    generate_data_driven: bool = True
    include_edge_cases: bool = False
    coverage_target: int = 100


class DecisionTableTestGenerator:
    """Generate test cases from decision tables."""

    def __init__(self, scenarios_file: Path, framework: str = "jest", edge_cases: bool = False):
        """
        Initialize the decision table test generator.

        Args:
            scenarios_file: Path to SCENARIOS.json
            framework: Target framework ("jest", "cucumber", "pytest")
            edge_cases: Whether to generate edge case tests
        """
        self.scenarios_file = scenarios_file
        self.framework = framework.lower()
        self.include_edge_cases = edge_cases
        self.feature_dir = scenarios_file.parent
        self.data: Dict[str, Any] = {}
        self.decision_tables: List[Dict[str, Any]] = []

    def load_scenarios(self) -> None:
        """Load decision tables from SCENARIOS.json."""
        with open(self.scenarios_file, 'r') as f:
            self.data = json.load(f)
        self.decision_tables = self.data.get("decision_tables", [])

    def generate_all(self) -> None:
        """Generate all test files."""
        self.load_scenarios()

        if not self.decision_tables:
            print("  ⚠ No decision tables found in SCENARIOS.json")
            return

        if self.framework == "jest":
            self._generate_jest_all()
        elif self.framework == "cucumber":
            self._generate_cucumber_all()
        elif self.framework == "pytest":
            self._generate_pytest_all()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    # ==================== Test Case Generation ====================

    def _generate_test_cases(self, dt: Dict[str, Any]) -> List[TestCase]:
        """Generate test cases from decision table rules."""
        test_cases = []
        table_id = dt["table_id"]
        rules = dt.get("rules", [])

        for idx, rule in enumerate(rules):
            conditions = rule.get("conditions", {})
            actions = rule.get("actions", {})

            # Generate test ID
            test_id = f"{table_id}_R{idx + 1:03d}"

            # Generate description
            condition_desc = ", ".join([f"{k}={v}" for k, v in conditions.items()])
            action_desc = ", ".join([f"{k}={v}" for k, v in actions.items()])
            description = f"Rule {idx + 1}: {condition_desc} → {action_desc}"

            # Determine priority
            priority = self._determine_priority(rule, idx)

            test_case = TestCase(
                test_id=test_id,
                description=description,
                inputs=conditions,
                expected_outputs=actions,
                rule_index=idx,
                priority=priority
            )
            test_cases.append(test_case)

        return test_cases

    def _generate_edge_cases(self, dt: Dict[str, Any]) -> List[TestCase]:
        """Generate edge case test cases."""
        edge_cases = []
        table_id = dt["table_id"]
        inputs = dt.get("inputs", [])

        # Generate boundary value tests for each input
        for input_def in inputs:
            field = input_def["field"]
            values = input_def.get("values", [])

            if not values:
                continue

            # Test first value (lower boundary)
            edge_cases.append(TestCase(
                test_id=f"{table_id}_EDGE_{field}_LOWER",
                description=f"Edge case: {field} at lower boundary ({values[0]})",
                inputs={field: values[0]},
                expected_outputs={},  # Will be filled by matching rule
                rule_index=-1,
                priority="medium"
            ))

            # Test last value (upper boundary)
            if len(values) > 1:
                edge_cases.append(TestCase(
                    test_id=f"{table_id}_EDGE_{field}_UPPER",
                    description=f"Edge case: {field} at upper boundary ({values[-1]})",
                    inputs={field: values[-1]},
                    expected_outputs={},
                    rule_index=-1,
                    priority="medium"
                ))

        # Generate null/undefined tests
        for input_def in inputs:
            field = input_def["field"]
            edge_cases.append(TestCase(
                test_id=f"{table_id}_EDGE_{field}_NULL",
                description=f"Edge case: {field} is null",
                inputs={field: None},
                expected_outputs={},
                rule_index=-1,
                priority="high"
            ))

        return edge_cases

    def _determine_priority(self, rule: Dict[str, Any], index: int) -> str:
        """Determine test priority based on rule content."""
        conditions = rule.get("conditions", {})

        # Rules with many conditions are more complex (higher priority)
        condition_count = len(conditions)

        if condition_count >= 3:
            return "critical"
        elif condition_count == 2:
            return "high"
        elif condition_count == 1:
            return "medium"
        else:
            return "low"

    def _calculate_coverage(self, dt: Dict[str, Any], generated_tests: int) -> Dict[str, int]:
        """Calculate test coverage metrics."""
        rules = dt.get("rules", [])
        rule_count = len(rules)

        # Basic coverage: one test per rule
        coverage_percentage = min(100, int((generated_tests / rule_count) * 100))

        return {
            "total_rules": rule_count,
            "generated_tests": generated_tests,
            "coverage_percentage": coverage_percentage,
            "target_percentage": 100
        }

    # ==================== Jest Generation ====================

    def _generate_jest_all(self) -> None:
        """Generate all Jest test files."""
        output_dir = self.feature_dir / "tests" / "decision-tables" / "jest"
        output_dir.mkdir(parents=True, exist_ok=True)

        for dt in self.decision_tables:
            test_content = self._generate_jest_test(dt)
            table_name = pascalcase(dt["name"])
            test_file = output_dir / f"{table_name}.test.ts"
            with open(test_file, 'w') as f:
                f.write(test_content)
            print(f"  ✓ Generated Jest tests: {test_file}")

            # Generate edge cases if requested
            if self.include_edge_cases:
                edge_content = self._generate_jest_edge_cases(dt)
                edge_file = output_dir / f"{table_name}.edge.test.ts"
                with open(edge_file, 'w') as f:
                    f.write(edge_content)
                print(f"  ✓ Generated Jest edge cases: {edge_file}")

    def _generate_jest_test(self, dt: Dict[str, Any]) -> str:
        """Generate Jest test file for decision table."""
        table_id = dt["table_id"]
        table_name = pascalcase(dt["name"])
        table_desc = dt["description"]
        inputs = dt.get("inputs", [])
        rules = dt.get("rules", [])

        # Generate test cases
        test_cases = self._generate_test_cases(dt)
        coverage = self._calculate_coverage(dt, len(test_cases))

        # Generate input fields
        input_fields = [inp["field"] for inp in inputs]

        # Generate output fields from first rule
        output_fields = list(rules[0].get("actions", {}).keys()) if rules else []

        return f'''/**
 * Auto-generated tests from decision table: {table_name}
 *
 * {table_desc}
 * Source: {self.data["metadata"]["feature_id"]}
 * Generated: {datetime.now().isoformat()}
 *
 * Coverage: {coverage["coverage_percentage"]}% ({coverage["generated_tests"]}/{coverage["total_rules"]} rules)
 */

import {{ describe, it }} from '@jest/globals';
import {{ determine{table_name} }} from '@/services/{{snakecase(dt["name"])}}';

describe('{table_name} Decision Table', () => {{
  describe('Individual Rule Tests', () => {{
{self._generate_jest_individual_tests(dt, test_cases)}
  }});

  describe('Data-Driven Coverage (All Rules)', () => {{
    describe.each([
{self._generate_jest_data_driven_tests(dt, test_cases)}
    ])('Rule %d: %s', (ruleIndex, description, {', '.join(self._to_camel_case_list(input_fields))}, expected) => {{
      it(`should return ${{JSON.stringify(expected)}}`, () => {{
        const result = determine{table_name}({{
          {', '.join([f'{self._to_js_arg(f)}' for f in input_fields])}
        }});

        expect(result).toEqual(expected);
      }});
    }});
  }});
}});
'''

    def _generate_jest_individual_tests(self, dt: Dict[str, Any], test_cases: List[TestCase]) -> str:
        """Generate individual test cases for Jest."""
        table_name = pascalcase(dt["name"])
        lines = []

        for tc in test_cases:
            test_name = f"Rule {tc.rule_index + 1}"
            lines.append(f"    describe('{test_name}', () => {{")
            lines.append(f"      it('{tc.description}', () => {{")

            # Generate function call
            inputs_str = ", ".join([
                f"{self._to_js_arg(k)}: {self._to_js_value(v)}"
                for k, v in tc.inputs.items()
            ])

            lines.append(f"        const result = determine{table_name}({{ {inputs_str} }});")

            # Generate assertions
            for key, value in tc.expected_outputs.items():
                expected = self._to_js_value(value)
                lines.append(f"        expect(result.{key}).toBe({expected});")

            lines.append(f"      }});")
            lines.append(f"    }});")
            lines.append("")

        return "\n".join(lines)

    def _generate_jest_data_driven_tests(self, dt: Dict[str, Any], test_cases: List[TestCase]) -> str:
        """Generate data-driven test array for Jest."""
        table_name = pascalcase(dt["name"])
        lines = []

        for tc in test_cases:
            # Input values
            input_values = []
            for field in dt.get("inputs", []):
                field_name = field["field"]
                value = tc.inputs.get(field_name, "null")
                input_values.append(self._to_js_value(value))

            # Expected output
            expected_output = "{" + ", ".join([
                f"{k}: {self._to_js_value(v)}"
                for k, v in tc.expected_outputs.items()
            ]) + "}"

            line = f"      [{tc.rule_index + 1}, '{tc.description.replace(chr(39), "\\'")}", {', '.join(input_values)}, {expected_output}],"
            lines.append(line)

        return "\n".join(lines)

    def _generate_jest_edge_cases(self, dt: Dict[str, Any]) -> str:
        """Generate edge case tests for Jest."""
        table_name = pascalcase(dt["name"])
        edge_cases = self._generate_edge_cases(dt)

        lines = [
            f'''/**
 * Edge case tests for {table_name}
 */

import {{ describe, it }} from '@jest/globals';
import {{ determine{table_name} }} from '@/services/{snakecase(dt["name"])}';

describe('{table_name} - Edge Cases', () => {{"''
        ]

        for ec in edge_cases:
            lines.append(f"  it('{ec.description}', () => {{")
            lines.append(f"    const result = determine{table_name}({{")
            lines.append(f"      {', '.join([f'{self._to_js_arg(k)}: {self._to_js_value(v)}' for k, v in ec.inputs.items()])}")
            lines.append(f"    }});")
            lines.append(f"    // TODO: Define expected behavior for edge case")
            lines.append(f"    expect(result).toBeDefined();")
            lines.append(f"  }});")

        lines.append("});")

        return "\n".join(lines)

    # ==================== Cucumber Generation ====================

    def _generate_cucumber_all(self) -> None:
        """Generate all Cucumber feature files."""
        output_dir = self.feature_dir / "tests" / "decision-tables" / "cucumber"
        output_dir.mkdir(parents=True, exist_ok=True)

        for dt in self.decision_tables:
            feature_content = self._generate_cucumber_feature(dt)
            table_name = snakecase(dt["name"])
            feature_file = output_dir / f"{table_name}.feature"
            with open(feature_file, 'w') as f:
                f.write(feature_content)
            print(f"  ✓ Generated Cucumber feature: {feature_file}")

    def _generate_cucumber_feature(self, dt: Dict[str, Any]) -> str:
        """Generate Cucumber feature file for decision table."""
        table_id = dt["table_id"]
        table_name = dt["name"]
        table_desc = dt["description"]
        inputs = dt.get("inputs", [])
        rules = dt.get("rules", [])

        test_cases = self._generate_test_cases(dt)
        coverage = self._calculate_coverage(dt, len(test_cases))

        # Generate input field names (pipe-separated)
        input_headers = " | ".join([self._to_cucumber_arg(f["field"]) for f in inputs])

        # Generate output field names from first rule
        output_fields = list(rules[0].get("actions", {}).keys()) if rules else []
        output_headers = " | ".join(output_fields)

        return f'''Feature: {table_name}
  {table_desc}

  Scenario Outline: Decision table rule coverage
    Given a decision table "{table_name}"
    When the following inputs are provided
      | {input_headers} |
      | {self._generate_cucumber_examples(inputs, test_cases)} |
    Then the following outputs should be produced
      | {output_headers} |
      | {self._generate_cucumber_outputs(output_fields, test_cases)} |

    Examples:
      | Rule | Description | {input_headers} | {output_headers} |
{self._generate_cucumber_examples_table(dt, test_cases)}

  @edge
  Scenario Outline: Edge case testing
    Given a decision table "{table_name}"
    When edge case input is provided
      | Input Field | Value |
      | {self._generate_cucumber_edge_inputs(dt)} |
    Then the system should handle gracefully

    Examples:
      | Scenario | Input Field | Value |
{self._generate_cucumber_edge_examples(dt)}
'''

    def _generate_cucumber_examples(self, inputs: List[Dict], test_cases: List[TestCase]) -> str:
        """Generate Cucumber example values."""
        lines = []
        for tc in test_cases[:2]:  # Show first 2 as examples
            values = []
            for inp in inputs:
                field = inp["field"]
                value = tc.inputs.get(field, "")
                values.append(str(value) if value is not None else "")
            lines.append("      | " + " | ".join(values) + " |")
        return "\n".join(lines)

    def _generate_cucumber_outputs(self, output_fields: List[str], test_cases: List[TestCase]) -> str:
        """Generate Cucumber expected output values."""
        lines = []
        for tc in test_cases[:2]:  # Show first 2 as examples
            values = []
            for field in output_fields:
                value = tc.expected_outputs.get(field, "")
                values.append(str(value) if value is not None else "")
            lines.append("      | " + " | ".join(values) + " |")
        return "\n".join(lines)

    def _generate_cucumber_examples_table(self, dt: Dict[str, Any], test_cases: List[TestCase]) -> str:
        """Generate Cucumber examples table."""
        inputs = dt.get("inputs", [])
        rules = dt.get("rules", [])
        output_fields = list(rules[0].get("actions", {}).keys()) if rules else []

        lines = []
        for tc in test_cases:
            row_values = [str(tc.rule_index + 1), tc.description.replace("|", "\\|")]

            # Input values
            for inp in inputs:
                field = inp["field"]
                value = tc.inputs.get(field, "")
                row_values.append(str(value) if value is not None else "")

            # Output values
            for field in output_fields:
                value = tc.expected_outputs.get(field, "")
                row_values.append(str(value) if value is not None else "")

            lines.append("      | " + " | ".join(row_values) + " |")

        return "\n".join(lines)

    def _generate_cucumber_edge_inputs(self, dt: Dict[str, Any]) -> str:
        """Generate Cucumber edge case input table."""
        edge_cases = self._generate_edge_cases(dt)
        lines = []
        for ec in edge_cases[:3]:
            for field, value in ec.inputs.items():
                lines.append(f"      | {field} | {value} |")
        return "\n".join(lines) if lines else "      | - | - |"

    def _generate_cucumber_edge_examples(self, dt: Dict[str, Any]) -> str:
        """Generate Cucumber edge case examples."""
        edge_cases = self._generate_edge_cases(dt)
        lines = []
        for ec in edge_cases:
            for field, value in ec.inputs.items():
                lines.append(f"      | {ec.description} | {field} | {value} |")
        return "\n".join(lines) if lines else "      | - | - | - |"

    # ==================== Pytest Generation ====================

    def _generate_pytest_all(self) -> None:
        """Generate all Pytest test files."""
        output_dir = self.feature_dir / "tests" / "decision-tables" / "pytest"
        output_dir.mkdir(parents=True, exist_ok=True)

        for dt in self.decision_tables:
            test_content = self._generate_pytest_test(dt)
            table_name = snakecase(dt["name"])
            test_file = output_dir / f"test_{table_name}.py"
            with open(test_file, 'w') as f:
                f.write(test_content)
            print(f"  ✓ Generated Pytest tests: {test_file}")

            # Generate edge cases if requested
            if self.include_edge_cases:
                edge_content = self._generate_pytest_edge_cases(dt)
                edge_file = output_dir / f"test_{table_name}_edge.py"
                with open(edge_file, 'w') as f:
                    f.write(edge_content)
                print(f"  ✓ Generated Pytest edge cases: {edge_file}")

    def _generate_pytest_test(self, dt: Dict[str, Any]) -> str:
        """Generate Pytest test file for decision table."""
        table_id = dt["table_id"]
        table_name = pascalcase(dt["name"])
        table_snake = snakecase(dt["name"])
        table_desc = dt["description"]
        inputs = dt.get("inputs", [])
        rules = dt.get("rules", [])

        test_cases = self._generate_test_cases(dt)
        coverage = self._calculate_coverage(dt, len(test_cases))

        # Generate parameter names
        param_names = [f["field"] for f in inputs]
        output_fields = list(rules[0].get("actions", {}).keys()) if rules else []

        return f'''"""
Auto-generated tests from decision table: {table_name}

{table_desc}
Source: {self.data["metadata"]["feature_id"]}
Generated: {datetime.now().isoformat()}

Coverage: {coverage["coverage_percentage"]}% ({coverage["generated_tests"]}/{coverage["total_rules"]} rules)
"""

import pytest
from app.services.{table_snake} import determine_{table_snake}


class Test{table_name}DecisionTable:
    """Test cases for {table_name} decision table."""

    @pytest.mark.parametrize({", ".join([f'"{snakecase(f)}"' for f in param_names + ["expected"]])}, [
{self._generate_pytest_parametrize_tests(dt, test_cases, param_names, output_fields)}
    ])
    def test_decision_table_rules(self, {', '.join([snakecase(f) for f in param_names])}, expected):
        """Test all rules from decision table."""
        result = determine_{table_snake}({{
            {', '.join([f'"{snakecase(f)}": {snakecase(f)}' for f in param_names])}
        }})

        assert result == expected
'''

    def _generate_pytest_parametrize_tests(
        self,
        dt: Dict[str, Any],
        test_cases: List[TestCase],
        param_names: List[str],
        output_fields: List[str]
    ) -> str:
        """Generate Pytest parametrize test data."""
        lines = []

        for tc in test_cases:
            # Input values
            values = []
            for field in param_names:
                value = tc.inputs.get(field)
                values.append(self._to_py_value(value))

            # Expected output
            expected_dict = {k: v for k, v in tc.expected_outputs.items()}
            values.append(self._to_py_value(expected_dict))

            line = f"        ({', '.join(values)}),"
            lines.append(line)

        return "\n".join(lines)

    def _generate_pytest_edge_cases(self, dt: Dict[str, Any]) -> str:
        """Generate edge case tests for Pytest."""
        table_name = pascalcase(dt["name"])
        table_snake = snakecase(dt["name"])
        edge_cases = self._generate_edge_cases(dt)

        lines = [
            f'''"""
Edge case tests for {table_name}
"""

import pytest
from app.services.{table_snake} import determine_{table_snake}


class Test{table_name}EdgeCases:
    """Edge case tests for {table_name} decision table."""
'''
        ]

        for ec in edge_cases:
            lines.append(f"    def test_{snakecase(ec.test_id)}(self):")
            lines.append(f'        """{ec.description}"""')
            lines.append(f"        result = determine_{table_snake}({{{', '.join([f'\'{k}\': {self._to_py_value(v)}' for k, v in ec.inputs.items()])}}}})")
            lines.append(f"        # TODO: Define expected behavior for edge case")
            lines.append(f"        assert result is not None")
            lines.append("")

        return "\n".join(lines)

    # ==================== Utility Methods ====================

    def _to_js_arg(self, name: str) -> str:
        """Convert field name to JavaScript camelCase."""
        return camelcase(name)

    def _to_js_value(self, value: Any) -> str:
        """Convert Python value to JavaScript literal."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return f"[{', '.join([self._to_js_value(v) for v in value])}]"
        elif isinstance(value, dict):
            items = [f"{k}: {self._to_js_value(v)}" for k, v in value.items()]
            return f"{{{', '.join(items)}}}"
        else:
            return "null"

    def _to_py_value(self, value: Any) -> str:
        """Convert Python value to Python literal."""
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return f"[{', '.join([self._to_py_value(v) for v in value])}]"
        elif isinstance(value, dict):
            items = [f"'{k}': {self._to_py_value(v)}" for k, v in value.items()]
            return f"{{{', '.join(items)}}}"
        else:
            return "None"

    def _to_cucumber_arg(self, name: str) -> str:
        """Convert field name to Cucumber-friendly format."""
        return name.replace("_", " ").title()

    def _to_camel_case_list(self, items: List[str]) -> List[str]:
        """Convert list of strings to camelCase."""
        return [self._to_js_arg(item) for item in items]


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 decision_table_test_generator.py <feature_dir> [--framework jest|cucumber|pytest] [--edge-cases]")
        print("Example: python3 decision_table_test_generator.py .sam/001_user_auth --framework jest")
        print("Example: python3 decision_table_test_generator.py .sam/001_user_auth --framework jest --edge-cases")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    framework = "jest"
    edge_cases = False

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--framework" and i + 1 < len(sys.argv):
            framework = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--edge-cases":
            edge_cases = True
            i += 1
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
    print(f"Generating {framework.upper()} decision table tests from: {scenarios_file}")
    generator = DecisionTableTestGenerator(scenarios_file, framework, edge_cases)
    generator.generate_all()

    # Calculate total coverage
    total_rules = sum(len(dt.get("rules", [])) for dt in generator.decision_tables)
    total_tests = sum(len(dt.get("rules", [])) for dt in generator.decision_tables)
    if edge_cases:
        total_tests += sum(len(generator._generate_edge_cases(dt)) for dt in generator.decision_tables)

    coverage = min(100, int((total_tests / total_rules) * 100)) if total_rules > 0 else 0

    print(f"\n✓ Decision table test generation complete!")
    print(f"  Framework: {framework.upper()}")
    print(f"  Decision tables: {len(generator.decision_tables)}")
    print(f"  Total rules: {total_rules}")
    print(f"  Tests generated: {total_tests}")
    print(f"  Coverage: {coverage}%")
    print(f"  Edge cases: {'Yes' if edge_cases else 'No'}")
    print(f"  Output directory: {feature_dir / 'tests' / 'decision-tables'}")


if __name__ == "__main__":
    main()
