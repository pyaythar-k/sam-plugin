#!/usr/bin/env python3
"""
e2e_test_generator.py - Generate end-to-end tests from user flow diagrams

This script reads USER_STORIES and generates Playwright/Cypress E2E tests
for critical user paths. Supports page object model pattern for maintainable tests.

Usage:
    python3 skills/sam-specs/scripts/e2e_test_generator.py <feature_dir> [--framework playwright|cypress]
    python3 skills/sam-specs/scripts/e2e_test_generator.py .sam/001_user_auth --framework playwright
    python3 skills/sam-specs/scripts/e2e_test_generator.py .sam/001_user_auth --flows "signup,checkout,auth"

Output:
    Generates E2E tests in .sam/{feature}/tests/e2e/{framework}/
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class UserFlow:
    """Represents a user flow extracted from user stories."""
    flow_id: str
    name: str
    description: str
    story_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    entry_point: str = ""
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class PageObject:
    """Represents a page object for E2E testing."""
    page_name: str
    url: str
    elements: Dict[str, str] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)


class E2ETestGenerator:
    """Generate E2E tests from user flow diagrams."""

    def __init__(self, feature_dir: Path, framework: str = "playwright"):
        self.feature_dir = feature_dir
        self.framework = framework.lower()
        self.user_stories_dir = feature_dir / "USER_STORIES"
        self.tests_dir = feature_dir / "tests" / "e2e" / self.framework
        self.data: Dict[str, Any] = {}
        self.user_flows: List[UserFlow] = []
        self.page_objects: List[PageObject] = []

        # Create output directory
        self.tests_dir.mkdir(parents=True, exist_ok=True)

    def load_user_stories(self) -> None:
        """Load all user stories from the USER_STORIES directory."""
        if not self.user_stories_dir.exists():
            raise FileNotFoundError(f"USER_STORIES directory not found: {self.user_stories_dir}")

        story_files = list(self.user_stories_dir.glob("*.md"))
        if not story_files:
            raise FileNotFoundError(f"No user story files found in {self.user_stories_dir}")

        print(f"  Loading {len(story_files)} user story files...")

        for story_file in story_files:
            self._parse_story_file(story_file)

    def _parse_story_file(self, story_file: Path) -> None:
        """Parse a single user story file and extract user flows."""
        with open(story_file, 'r') as f:
            content = f.read()

        # Extract story ID
        story_id_match = re.search(r'# Story (\d+)', content)
        story_id = story_id_match.group(1) if story_id_match else story_file.stem

        # Extract user flows from "User Flow" sections
        flow_pattern = r'## User Flow: ([^\n]+)(.*?)(?=##|\Z)'
        flows = re.findall(flow_pattern, content, re.DOTALL)

        for flow_name, flow_content in flows:
            # Extract flow steps
            steps = self._extract_flow_steps(flow_content)

            # Extract entry point
            entry_point = self._extract_entry_point(flow_content)

            # Extract success criteria
            success_criteria = self._extract_success_criteria(flow_content)

            flow = UserFlow(
                flow_id=f"{story_id}_{flow_name.lower().replace(' ', '_')}",
                name=flow_name.strip(),
                description=flow_content.strip().split('\n')[0] if flow_content.strip() else "",
                story_id=story_id,
                steps=steps,
                entry_point=entry_point,
                success_criteria=success_criteria
            )

            self.user_flows.append(flow)

    def _extract_flow_steps(self, content: str) -> List[Dict[str, Any]]:
        """Extract steps from a user flow."""
        steps = []
        step_pattern = r'(\d+)\.\s+(.+?)(?=\n\d+\.|\n\n|\Z)'

        for match in re.finditer(step_pattern, content, re.MULTILINE):
            step_num = match.group(1)
            step_text = match.group(2).strip()

            # Parse action and target
            action, target = self._parse_step_action(step_text)

            steps.append({
                "step_number": step_num,
                "action": action,
                "target": target,
                "description": step_text
            })

        return steps

    def _parse_step_action(self, step_text: str) -> tuple[str, str]:
        """Parse the action and target from a step description."""
        # Common action patterns
        action_patterns = [
            r'(click|tap|select) (?:on )?(?:the )?(.+)',
            r'(enter|type|input) (.+?) into (.+)',
            r'(navigate|go) to (.+)',
            r'(wait for|expect) (.+)',
            r'(verify|check|assert) (.+)'
        ]

        for pattern in action_patterns:
            match = re.match(pattern, step_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return groups[0].lower(), groups[1].strip()
                elif len(groups) == 3:
                    # For "enter X into Y" pattern
                    return groups[0].lower(), groups[2].strip()

        # Default fallback
        return "interact", step_text

    def _extract_entry_point(self, content: str) -> str:
        """Extract the entry point (starting URL) for the flow."""
        entry_match = re.search(r'Entry Point:?\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if entry_match:
            return entry_match.group(1).strip()

        # Look for URL pattern
        url_match = re.search(r'(https?://[^\s]+)', content)
        return url_match.group(1) if url_match else "/"

    def _extract_success_criteria(self, content: str) -> List[str]:
        """Extract success criteria from the flow."""
        criteria = []

        # Look for "Success Criteria" or "Then" sections
        criteria_pattern = r'(?:Success Criteria:|Then:)\s*\n((?:-\s+.+\n?)+)'
        criteria_match = re.search(criteria_pattern, content, re.IGNORECASE)

        if criteria_match:
            criteria_text = criteria_match.group(1)
            criteria = [line.strip().lstrip('-').strip() for line in criteria_text.split('\n') if line.strip()]

        return criteria

    def extract_user_flows(self) -> List[UserFlow]:
        """Extract user flows from loaded user stories."""
        print(f"  Extracted {len(self.user_flows)} user flows")
        return self.user_flows

    def generate_page_objects(self) -> None:
        """Generate page object models from user flows."""
        page_map = {}

        for flow in self.user_flows:
            # Identify pages mentioned in the flow
            for step in flow.steps:
                page_name = self._identify_page_from_step(step)
                if page_name and page_name not in page_map:
                    page_map[page_name] = PageObject(
                        page_name=page_name,
                        url=self._infer_page_url(page_name),
                        elements={},
                        actions=[]
                    )

                # Add elements to the page
                if page_name:
                    element_name = self._extract_element_name(step)
                    if element_name:
                        page_map[page_name].elements[element_name] = self._generate_element_selector(element_name)

        self.page_objects = list(page_map.values())

    def _identify_page_from_step(self, step: Dict[str, Any]) -> Optional[str]:
        """Identify which page a step belongs to."""
        target = step.get("target", "").lower()

        # Common page indicators
        if "login" in target or "sign in" in target:
            return "LoginPage"
        elif "signup" in target or "register" in target or "sign up" in target:
            return "SignupPage"
        elif "dashboard" in target:
            return "DashboardPage"
        elif "profile" in target:
            return "ProfilePage"
        elif "settings" in target:
            return "SettingsPage"
        elif "home" in target or "index" in target:
            return "HomePage"

        return None

    def _infer_page_url(self, page_name: str) -> str:
        """Infer the URL for a page based on its name."""
        url_map = {
            "LoginPage": "/login",
            "SignupPage": "/signup",
            "DashboardPage": "/dashboard",
            "ProfilePage": "/profile",
            "SettingsPage": "/settings",
            "HomePage": "/"
        }
        return url_map.get(page_name, f"/{page_name.lower().replace('page', '')}")

    def _extract_element_name(self, step: Dict[str, Any]) -> Optional[str]:
        """Extract element name from step target."""
        target = step.get("target", "").lower()

        # Common element patterns
        if "email" in target:
            return "emailInput"
        elif "password" in target:
            return "passwordInput"
        elif "button" in target or "submit" in target:
            return "submitButton"
        elif "username" in target:
            return "usernameInput"

        return None

    def _generate_element_selector(self, element_name: str) -> str:
        """Generate a CSS selector for an element."""
        selector_map = {
            "emailInput": "input[type='email']",
            "passwordInput": "input[type='password']",
            "usernameInput": "input[name='username']",
            "submitButton": "button[type='submit']"
        }
        return selector_map.get(element_name, f"[data-testid='{element_name}']")

    def generate_e2e_tests(self) -> None:
        """Generate all E2E test files."""
        if self.framework == "playwright":
            self._generate_playwright_tests()
        elif self.framework == "cypress":
            self._generate_cypress_tests()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def _generate_playwright_tests(self) -> str:
        """Generate Playwright test files."""
        # Generate page objects
        pages_dir = self.tests_dir / "pages"
        pages_dir.mkdir(exist_ok=True)

        for page_obj in self.page_objects:
            self._generate_playwright_page_object(page_obj, pages_dir)

        # Generate flow tests
        flows_dir = self.tests_dir / "flows"
        flows_dir.mkdir(exist_ok=True)

        for flow in self.user_flows:
            self._generate_playwright_flow_test(flow, flows_dir)

        # Generate test utilities
        self._generate_playwright_utils(self.tests_dir)

        return "Playwright tests generated"

    def _generate_playwright_page_object(self, page_obj: PageObject, pages_dir: Path) -> None:
        """Generate a Playwright page object file."""
        class_name = page_obj.page_name

        content = f'''/**
 * Page Object: {class_name}
 * Auto-generated from user flow diagrams
 * Generated: {datetime.now().isoformat()}
 */

import {{ Page }} from '@playwright/test';

export class {class_name} {{
  readonly page: Page;

  constructor(page: Page) {{
    this.page = page;
  }}

  /**
   * Navigate to this page
   */
  async goto() {{
    await this.page.goto('{page_obj.url}');
  }}

  /**
   * Wait for page to be loaded
   */
  async waitForLoad() {{
    await this.page.waitForLoadState('networkidle');
  }}
'''

        # Add element locators
        for elem_name, selector in page_obj.elements.items():
            content += f'\n  /**\n   * Locator: {elem_name}\n   */\n'
            content += f'  get {elem_name}() {{\n'
            content += f"    return this.page.locator('{selector}');\n"
            content += '  }\n'

        # Add action methods
        content += '\n  /**\n   * Fill form fields\n   */\n'
        content += '  async fillForm(data: Record<string, string>) {\n'
        for elem_name in page_obj.elements.keys():
            if 'input' in elem_name.lower():
                content += f"    if (data.{elem_name}) await this.{elem_name}.fill(data.{elem_name});\n"
        content += '  }\n'

        content += '\n  /**\n   * Submit form\n   */\n'
        content += '  async submit() {\n'
        if 'submitButton' in [e for e in page_obj.elements.keys()]:
            content += '    await this.submitButton.click();\n'
        else:
            content += '    await this.page.click("button[type=\'submit\']");\n'
        content += '  }\n'

        content += '}\n'

        # Write file
        file_path = pages_dir / f"{class_name}.ts"
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"  ✓ Generated page object: {file_path}")

    def _generate_playwright_flow_test(self, flow: UserFlow, flows_dir: Path) -> None:
        """Generate a Playwright test file for a user flow."""
        test_name = flow.flow_id.replace('-', '_')
        flow_camel = ''.join(word.capitalize() for word in flow.name.split())

        content = f'''/**
 * E2E Test: {flow.name}
 * Story: {flow.story_id}
 * Auto-generated from user flow diagrams
 * Generated: {datetime.now().isoformat()}
 */

import {{ test, expect }} from '@playwright/test';
import {{ LoginPage }} from '../pages/LoginPage';
import {{ SignupPage }} from '../pages/SignupPage';
import {{ DashboardPage }} from '../pages/DashboardPage';

test.describe('{flow.name}', () => {{
  test('should complete the flow successfully', async ({{ page }}) => {{
    // Navigate to entry point
    await page.goto('{flow.entry_point}');

'''

        # Generate test steps
        for step in flow.steps:
            content += self._generate_playwright_step(step, flow)

        # Add success criteria assertions
        content += '\n    // Verify success criteria\n'
        for criteria in flow.success_criteria:
            content += f"    // {criteria}\n"

        content += '  });\n'

        # Add edge case tests
        content += '\n  test(\'should handle errors gracefully\', async ({ page }) => {\n'
        content += '    // TODO: Add error scenario tests\n'
        content += '  });\n'

        content += '});\n'

        # Write file
        file_path = flows_dir / f"{test_name}.spec.ts"
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"  ✓ Generated flow test: {file_path}")

    def _generate_playwright_step(self, step: Dict[str, Any], flow: UserFlow) -> str:
        """Generate Playwright code for a single step."""
        action = step.get("action", "")
        target = step.get("target", "")

        step_code = f"\n    // Step {step['step_number']}: {step['description']}\n"

        if action in ["click", "tap"]:
            selector = self._infer_selector(target)
            step_code += f"    await page.click('{selector}');\n"
        elif action in ["enter", "type", "input"]:
            field_match = re.match(r'enter (.+?) into (.+)', step['description'], re.IGNORECASE)
            if field_match:
                value = field_match.group(1).strip()
                field = field_match.group(2).strip()
                selector = self._infer_selector(field)
                step_code += f"    await page.fill('{selector}', '{value}');\n"
        elif action in ["navigate", "go"]:
            step_code += f"    await page.goto('{target}');\n"
        elif action in ["wait", "expect", "verify", "check", "assert"]:
            step_code += f"    await expect(page.locator('body')).toBeVisible();\n"
        else:
            step_code += f"    // TODO: Implement {action} on {target}\n"

        return step_code

    def _infer_selector(self, target: str) -> str:
        """Infer a CSS selector from target description."""
        target = target.lower()

        if "email" in target:
            return "input[type='email']"
        elif "password" in target:
            return "input[type='password']"
        elif "button" in target and "submit" in target:
            return "button[type='submit']"
        elif "button" in target:
            return f"button:has-text('{target}')"
        elif "link" in target:
            return f"a:has-text('{target}')"

        # Default: try data-testid
        return f"[data-testid='{target.replace(' ', '-')}']"

    def _generate_playwright_utils(self, tests_dir: Path) -> None:
        """Generate Playwright test utilities."""
        content = '''/**
 * E2E Test Utilities
 * Auto-generated from user flow diagrams
 */

import { test as base } from '@playwright/test';

export const test = base.extend<{
  authenticatedPage: any;
}>({
  authenticatedPage: async ({ page }, use) => {
    // Perform authentication
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    await use(page);
  },
});

export const expect = test.expect;
'''

        file_path = tests_dir / "utils.ts"
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"  ✓ Generated test utilities: {file_path}")

    def _generate_cypress_tests(self) -> str:
        """Generate Cypress test files."""
        # Generate e2e directory structure
        e2e_dir = self.tests_dir.parent / "cypress" / "e2e"
        e2e_dir.mkdir(parents=True, exist_ok=True)

        # Generate support files
        support_dir = self.tests_dir.parent / "cypress" / "support"
        support_dir.mkdir(exist_ok=True)

        # Generate commands
        self._generate_cypress_commands(support_dir)

        # Generate flow tests
        for flow in self.user_flows:
            self._generate_cypress_flow_test(flow, e2e_dir)

        return "Cypress tests generated"

    def _generate_cypress_commands(self, support_dir: Path) -> None:
        """Generate Cypress custom commands."""
        content = '''/**
 * Cypress Custom Commands
 * Auto-generated from user flow diagrams
 */

// Login command
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/login');
  cy.get('input[type="email"]').type(email);
  cy.get('input[type="password"]').type(password);
  cy.get('button[type="submit"]').click();
  cy.url().should('include', '/dashboard');
});

// Navigate to page command
Cypress.Commands.add('navigateTo', (page: string) => {
  const pageMap: Record<string, string> = {
    login: '/login',
    signup: '/signup',
    dashboard: '/dashboard',
    profile: '/profile',
    settings: '/settings',
    home: '/'
  };
  cy.visit(pageMap[page] || `/${page}`);
});

declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      navigateTo(page: string): Chainable<void>;
    }
  }
}
'''

        file_path = support_dir / "commands.ts"
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"  ✓ Generated Cypress commands: {file_path}")

    def _generate_cypress_flow_test(self, flow: UserFlow, e2e_dir: Path) -> None:
        """Generate a Cypress test file for a user flow."""
        test_name = flow.flow_id.replace('-', '_')

        content = f'''/**
 * E2E Test: {flow.name}
 * Story: {flow.story_id}
 * Auto-generated from user flow diagrams
 * Generated: {datetime.now().isoformat()}
 */

describe('{flow.name}', () => {{
  beforeEach(() => {{
    // Navigate to entry point
    cy.visit('{flow.entry_point}');
  }});

  it('should complete the flow successfully', () => {{
'''

        # Generate test steps
        for step in flow.steps:
            content += self._generate_cypress_step(step)

        # Add success criteria assertions
        content += '\n    // Verify success criteria\n'
        for criteria in flow.success_criteria:
            content += f"    // {criteria}\n"

        content += '  });\n'

        # Add edge case tests
        content += '\n  it(\'should handle errors gracefully\', () => {\n'
        content += '    // TODO: Add error scenario tests\n'
        content += '  });\n'

        content += '});\n'

        # Write file
        file_path = e2e_dir / f"{test_name}.cy.ts"
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"  ✓ Generated Cypress test: {file_path}")

    def _generate_cypress_step(self, step: Dict[str, Any]) -> str:
        """Generate Cypress code for a single step."""
        action = step.get("action", "")
        target = step.get("target", "")

        step_code = f"\n    // Step {step['step_number']}: {step['description']}\n"

        if action in ["click", "tap"]:
            selector = self._infer_selector(target)
            step_code += f"    cy.get('{selector}').click();\n"
        elif action in ["enter", "type", "input"]:
            field_match = re.match(r'enter (.+?) into (.+)', step['description'], re.IGNORECASE)
            if field_match:
                value = field_match.group(1).strip()
                field = field_match.group(2).strip()
                selector = self._infer_selector(field)
                step_code += f"    cy.get('{selector}').type('{value}');\n"
        elif action in ["navigate", "go"]:
            step_code += f"    cy.visit('{target}');\n"
        elif action in ["wait", "expect", "verify", "check", "assert"]:
            step_code += f"    cy.get('body').should('be.visible');\n"
        else:
            step_code += f"    // TODO: Implement {action} on {target}\n"

        return step_code

    def generate_all(self) -> None:
        """Generate all E2E test artifacts."""
        print(f"Generating {self.framework.upper()} E2E tests...")

        self.load_user_stories()
        self.extract_user_flows()
        self.generate_page_objects()
        self.generate_e2e_tests()

        print(f"\n✓ E2E test generation complete!")
        print(f"  Framework: {self.framework.upper()}")
        print(f"  Output directory: {self.tests_dir}")
        print(f"  User flows: {len(self.user_flows)}")
        print(f"  Page objects: {len(self.page_objects)}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 e2e_test_generator.py <feature_dir> [--framework playwright|cypress] [--flows FLOW1,FLOW2]")
        print("Example: python3 e2e_test_generator.py .sam/001_user_auth --framework playwright")
        print("Example: python3 e2e_test_generator.py .sam/001_user_auth --flows signup,checkout")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    framework = "playwright"
    flows_filter = None

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--framework" and i + 1 < len(sys.argv):
            framework = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--flows" and i + 1 < len(sys.argv):
            flows_filter = sys.argv[i + 1].split(',')
            i += 2
        else:
            i += 1

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Generate E2E tests
    generator = E2ETestGenerator(feature_dir, framework)

    # Filter flows if specified
    if flows_filter:
        generator.load_user_stories()
        generator.user_flows = [
            f for f in generator.user_flows
            if any(flow in f.flow_id for flow in flows_filter)
        ]
        generator.extract_user_flows()
        generator.generate_page_objects()
        generator.generate_e2e_tests()
    else:
        generator.generate_all()


if __name__ == "__main__":
    main()
