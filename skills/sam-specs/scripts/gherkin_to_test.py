#!/usr/bin/env python3
"""
gherkin_to_test.py - Enhanced Gherkin test generator

This script parses Gherkin scenarios from user story markdown files and generates
executable tests with support for:
- Parameterized steps
- Scenario outlines
- Multiple test frameworks (Cucumber, Jest-cucumber)

Usage:
    python3 skills/sam-specs/scripts/gherkin_to_test.py <story_file>
    python3 skills/sam-specs/scripts/gherkin_to_test.py .sam/{feature}/USER_STORIES/
    python3 skills/sam-specs/scripts/gherkin_to_test.py .sam/{feature}/USER_STORIES/ --framework jest
    python3 skills/sam-specs/scripts/gherkin_to_test.py .sam/{feature}/USER_STORIES/ --framework cucumber

Output:
    Generates .feature files and TypeScript step definitions in the feature's tests/ directory
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class GherkinStep:
    """Represents a single Gherkin step."""
    keyword: str  # Given, When, Then, And
    text: str
    parameters: Dict[str, str] = field(default_factory=dict)  # Extracted parameters


@dataclass
class GherkinScenario:
    """Represents a Gherkin scenario or scenario outline."""
    scenario_id: str
    name: str
    type: str  # "scenario" or "scenario_outline"
    description: Optional[str] = None
    steps: List[GherkinStep] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)  # For scenario outlines
    story_id: Optional[str] = None


@dataclass
class GherkinFeature:
    """Represents a Gherkin feature from a user story."""
    feature_id: str
    feature_name: str
    story_id: str
    scenarios: List[GherkinScenario] = field(default_factory=list)


class GherkinParser:
    """Parser for Gherkin scenarios in user story markdown files."""

    def __init__(self, story_file: Path):
        self.story_file = story_file
        self.content = ""
        self.lines: List[str] = []
        self.story_id = ""
        self.story_name = ""

    def parse(self) -> GherkinFeature:
        """Parse Gherkin scenarios from the user story file."""
        with open(self.story_file, 'r') as f:
            self.content = f.read()
            self.lines = self.content.split('\n')

        # Extract story metadata
        self._extract_metadata()

        feature = GherkinFeature(
            feature_id=self.story_file.parent.parent.name,
            feature_name=self.story_name,
            story_id=self.story_id
        )

        # Find Gherkin section
        gherkin_section = self._find_gherkin_section()
        if gherkin_section:
            feature.scenarios = self._parse_scenarios(gherkin_section)

        return feature

    def _extract_metadata(self):
        """Extract story ID and name from metadata section."""
        for line in self.lines:
            if line.strip().startswith('- **Story ID**'):
                match = re.search(r'Story ID\*\*:\s*(\w+)', line)
                if match:
                    self.story_id = match.group(1)
            elif line.strip().startswith('#') and not self.story_name:
                # Extract title from first heading
                title_match = re.search(r'#\s+(.+)', line)
                if title_match:
                    self.story_name = title_match.group(1).strip()

        if not self.story_name:
            self.story_name = self.story_file.stem

    def _find_gherkin_section(self) -> Optional[List[str]]:
        """Find the Behavioral Scenarios (Gherkin) section."""
        in_gherkin = False
        gherkin_lines = []

        for line in self.lines:
            if 'Behavioral Scenarios' in line and 'Gherkin' in line:
                in_gherkin = True
                continue

            if in_gherkin:
                # Check if we've hit the next major section
                if line.strip().startswith('## ') and 'Behavioral Scenarios' not in line:
                    break
                gherkin_lines.append(line)

        return gherkin_lines if gherkin_lines else None

    def _parse_scenarios(self, lines: List[str]) -> List[GherkinScenario]:
        """Parse scenarios from Gherkin section lines."""
        scenarios = []
        current_scenario: Optional[GherkinScenario] = None
        scenario_counter = 1

        for line in lines:
            line = line.strip()

            # Scenario header
            if line.startswith('### ') or (line.startswith('**') and 'Scenario' in line):
                # Save previous scenario
                if current_scenario:
                    scenarios.append(current_scenario)

                # Determine scenario type
                scenario_type = "scenario_outline" if "Scenario Outline" in line else "scenario"

                # Extract scenario name
                name_match = re.search(r'(?:Scenario|Scenario Outline)\s*(?:\d+:)?\s*(.+?)(?:\*\*)?$', line)
                scenario_name = name_match.group(1).strip() if name_match else f"Scenario {scenario_counter}"

                current_scenario = GherkinScenario(
                    scenario_id=f"S{scenario_counter:03d}",
                    name=scenario_name,
                    type=scenario_type,
                    story_id=self.story_id
                )
                scenario_counter += 1

            # Gherkin steps
            elif current_scenario and line.startswith('**'):
                keyword_match = re.match(r'\*\*(Given|When|Then|And)\*\*', line)
                if keyword_match:
                    keyword = keyword_match.group(1)
                    # Extract step text after keyword
                    step_text = line[keyword_match.end():].strip()

                    # Extract parameters (e.g., <user_type>)
                    parameters = {}
                    param_matches = re.findall(r'<(\w+)>', step_text)
                    for param in param_matches:
                        parameters[param] = f"{{{param}}}"

                    step = GherkinStep(
                        keyword=keyword,
                        text=step_text,
                        parameters=parameters
                    )
                    current_scenario.steps.append(step)

            # Examples table for scenario outlines
            elif current_scenario and current_scenario.type == "scenario_outline":
                if '| Examples:' in line or '| Examples' in line:
                    continue
                elif line.startswith('|') and current_scenario:
                    # Parse table row
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]

                    # First row is headers
                    if not current_scenario.examples:
                        # Headers row - create empty example dict
                        current_scenario.examples = {header: "" for header in cells}
                    elif len(cells) == len(current_scenario.examples):
                        # Data row - add to examples list
                        examples_list = current_scenario.examples if isinstance(current_scenario.examples, list) else []
                        row_dict = dict(zip(current_scenario.examples.keys() if isinstance(current_scenario.examples, dict) else [], cells))
                        examples_list.append(row_dict)
                        current_scenario.examples = examples_list

        # Save last scenario
        if current_scenario:
            scenarios.append(current_scenario)

        return scenarios


class GherkinToTestGenerator:
    """Generate executable tests from Gherkin scenarios."""

    def __init__(self, feature: GherkinFeature, output_dir: Path, framework: str = "cucumber"):
        self.feature = feature
        self.output_dir = output_dir
        self.framework = framework.lower()

    def generate_all(self):
        """Generate all test files."""
        if self.framework == "cucumber":
            self._generate_cucumber_tests()
        elif self.framework == "jest":
            self._generate_jest_cucumber_tests()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def _generate_cucumber_tests(self):
        """Generate Cucumber .feature files and TypeScript step definitions."""
        tests_dir = self.output_dir / "tests" / "cucumber"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate .feature file
        feature_file = tests_dir / f"{self._to_snake_case(self.feature.feature_name)}.feature"
        feature_content = self._generate_feature_file()
        with open(feature_file, 'w') as f:
            f.write(feature_content)

        print(f"✓ Generated Cucumber feature: {feature_file}")

        # Generate step definitions
        steps_file = tests_dir / "steps.ts"
        steps_content = self._generate_step_definitions()
        with open(steps_file, 'w') as f:
            f.write(steps_content)

        print(f"✓ Generated step definitions: {steps_file}")

    def _generate_feature_file(self) -> str:
        """Generate .feature file content."""
        content = f"""Feature: {self.feature.feature_name}
  As a stakeholder
  I want to verify the behavior
  So that I can ensure the system meets requirements

  Story: {self.feature.story_id}
  Generated: {datetime.now().isoformat()}

"""

        for scenario in self.feature.scenarios:
            if scenario.type == "scenario_outline":
                content += self._generate_scenario_outline(scenario)
            else:
                content += self._generate_scenario(scenario)

        return content

    def _generate_scenario(self, scenario: GherkinScenario) -> str:
        """Generate a single scenario."""
        content = f"  Scenario: {scenario.name}\n"

        for step in scenario.steps:
            content += f"    {step.keyword} {step.text}\n"

        content += "\n"
        return content

    def _generate_scenario_outline(self, scenario: GherkinScenario) -> str:
        """Generate a scenario outline with examples table."""
        content = f"  Scenario Outline: {scenario.name}\n"

        for step in scenario.steps:
            content += f"    {step.keyword} {step.text}\n"

        # Add examples table
        if scenario.examples and isinstance(scenario.examples, list) and len(scenario.examples) > 0:
            content += "\n    Examples:\n"
            # Header row
            headers = list(scenario.examples[0].keys())
            content += f"      | {' | '.join(headers)} |\n"

            # Data rows
            for example in scenario.examples:
                values = [str(example[h]) for h in headers]
                content += f"      | {' | '.join(values)} |\n"

        content += "\n"
        return content

    def _generate_step_definitions(self) -> str:
        """Generate TypeScript step definitions."""
        content = f'''/**
 * Auto-generated step definitions from user story Gherkin scenarios
 * Feature: {self.feature.feature_name}
 * Story: {self.feature.story_id}
 * Generated: {datetime.now().isoformat()}
 */

import {{ Given, When, Then }} from '@cucumber/cucumber';
import {{ expect }} from 'chai';
import {{ TestContext }} from '@/types/test';

// Shared test context
let context: TestContext = {{}};

'''

        # Collect unique steps by keyword and pattern
        given_steps = {}
        when_steps = {}
        then_steps = {}

        for scenario in self.feature.scenarios:
            for step in scenario.steps:
                step_key = self._get_step_pattern(step.text)

                if step.keyword in ["Given", "And"]:
                    # Determine if this is a Given or And based on context
                    given_steps[step_key] = step
                elif step.keyword == "When":
                    when_steps[step_key] = step
                elif step.keyword == "Then":
                    then_steps[step_key] = step

        # Generate Given steps
        content += "// Given steps\n"
        for pattern, step in given_steps.items():
            content += self._generate_step_definition(step)

        # Generate When steps
        content += "\n// When steps\n"
        for pattern, step in when_steps.items():
            content += self._generate_step_definition(step)

        # Generate Then steps
        content += "\n// Then steps\n"
        for pattern, step in then_steps.items():
            content += self._generate_step_definition(step)

        return content

    def _generate_step_definition(self, step: GherkinStep) -> str:
        """Generate a single step definition."""
        # Convert parameters to regex capture groups
        pattern = step.text
        for param_name in step.parameters.keys():
            pattern = pattern.replace(f"<{param_name}>", r'([^"]+)')

        # Escape special regex characters in the rest of the pattern
        pattern = re.sub(r'([.^$*+?(){}\[\]|])', r'\\\1', pattern)
        # Restore our capture groups
        pattern = pattern.replace(r'\(([^"]+)\)', r'([^"]+)')

        # Build parameters string
        params = ""
        if step.parameters:
            param_names = list(step.parameters.keys())
            if len(param_names) == 1:
                params = f", {param_names[0]}: string"
            else:
                params = ", " + ", ".join(f"{p}: string" for p in param_names)

        content = f"""{step.keyword}(/^{{{pattern}}}$/, async function ({params}) {{
  // TODO: Implement step: {step.text}
  // Parameters: {step.parameters if step.parameters else 'none'}}
}});
"""

        return content

    def _generate_jest_cucumber_tests(self):
        """Generate Jest-cucumber compatible tests."""
        tests_dir = self.output_dir / "tests" / "jest-cucumber"
        tests_dir.mkdir(parents=True, exist_ok=True)

        test_file = tests_dir / f"{self._to_snake_case(self.feature.feature_name)}.test.ts"

        content = f'''/**
 * Auto-generated Jest-cucumber tests from user story Gherkin scenarios
 * Feature: {self.feature.feature_name}
 * Story: {self.feature.story_id}
 * Generated: {datetime.now().isoformat()}
 */

import {{ defineFeature, loadFeature }} from 'jest-cucumber';
import {{ request }} from '@/tests/setup';

const feature = loadFeature('./cucumber/{self._to_snake_case(self.feature.feature_name)}.feature');

defineFeature(feature, (test) => {{
'''

        for scenario in self.feature.scenarios:
            content += self._generate_jest_scenario(scenario)

        content += "});\n"

        with open(test_file, 'w') as f:
            f.write(content)

        print(f"✓ Generated Jest-cucumber tests: {test_file}")

    def _generate_jest_scenario(self, scenario: GherkinScenario) -> str:
        """Generate Jest-cucumber scenario."""
        content = f"""  test('{scenario.name}', ({{ given, when, then }}) => {{
"""

        for step in scenario.steps:
            step_impl = self._generate_jest_step_impl(step)
            if step.keyword in ["Given", "And"]:
                content += f"    given('{step.text}', {step_impl});\n"
            elif step.keyword == "When":
                content += f"    when('{step.text}', {step_impl});\n"
            elif step.keyword == "Then":
                content += f"    then('{step.text}', {step_impl});\n"

        content += "  });\n\n"
        return content

    def _generate_jest_step_impl(self, step: GherkinStep) -> str:
        """Generate Jest-cucumber step implementation placeholder."""
        params = ""
        if step.parameters:
            param_names = list(step.parameters.keys())
            if len(param_names) == 1:
                params = f"{{{param_names[0]}}}"
            else:
                params = "{" + ", ".join(param_names) + "}"

        return f"async ({params}) => {{\n      // TODO: Implement: {step.text}\n    }}"

    def _get_step_pattern(self, text: str) -> str:
        """Generate a unique key for a step pattern."""
        # Normalize for use as dict key
        return text.lower().replace(" ", "_")

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        return re.sub(r'[^a-zA-Z0-9]+', '_', text).lower('_').strip('_')


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 gherkin_to_test.py <story_file_or_dir> [--framework cucumber|jest]")
        print("Example: python3 gherkin_to_test.py .sam/001_user_auth/USER_STORIES/001_*.md")
        print("Example: python3 gherkin_to_test.py .sam/001_user_auth/USER_STORIES/ --framework jest")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    framework = "cucumber"

    # Parse optional framework argument
    if len(sys.argv) >= 4 and sys.argv[2] == "--framework":
        framework = sys.argv[3]

    if not input_path.exists():
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)

    # Determine if input is a file or directory
    if input_path.is_file():
        story_files = [input_path]
        output_dir = input_path.parent.parent
    else:
        story_files = list(input_path.glob("*.md"))
        output_dir = input_path.parent

    if not story_files:
        print(f"Error: No markdown files found in {input_path}")
        sys.exit(1)

    # Process each story file
    print(f"Generating {framework.upper()} tests from {len(story_files)} story file(s)...")

    for story_file in story_files:
        try:
            parser = GherkinParser(story_file)
            feature = parser.parse()

            if not feature.scenarios:
                print(f"  Skipping {story_file.name}: No Gherkin scenarios found")
                continue

            generator = GherkinToTestGenerator(feature, output_dir, framework)
            generator.generate_all()

            print(f"  ✓ Processed {story_file.name}")
            print(f"    Scenarios: {len(feature.scenarios)}")

        except Exception as e:
            print(f"  ✗ Error processing {story_file.name}: {e}")

    print(f"\n✓ Test generation complete!")
    print(f"  Framework: {framework.upper()}")
    print(f"  Output directory: {output_dir / 'tests'}")


if __name__ == "__main__":
    main()
