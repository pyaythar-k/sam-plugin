# Playwright E2E Test Template

This template provides the structure for generating Playwright end-to-end tests from user flow diagrams.

## Directory Structure

```
tests/e2e/playwright/
├── pages/                    # Page Object Models
│   ├── BasePage.ts           # Base page class
│   ├── LoginPage.ts          # Login page object
│   ├── SignupPage.ts         # Signup page object
│   └── DashboardPage.ts      # Dashboard page object
├── flows/                    # User flow tests
│   ├── authentication.spec.ts # Auth flow tests
│   ├── signup.spec.ts        # Signup flow tests
│   └── checkout.spec.ts      # Checkout flow tests
├── fixtures/                 # Test data fixtures
│   ├── users.ts              # User test data
│   └── scenarios.ts          # Scenario data
└── utils.ts                  # Test utilities
```

## Page Object Model Pattern

### Base Page Class

```typescript
/**
 * Base page class with common functionality
 */
export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to a URL
   */
  async goto(url: string): Promise<void> {
    await this.page.goto(url);
  }

  /**
   * Wait for page to be stable
   */
  async waitForLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for element to be visible
   */
  async waitForVisible(selector: string): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'visible' });
  }

  /**
   * Click element
   */
  async click(selector: string): Promise<void> {
    await this.page.click(selector);
  }

  /**
   * Fill input field
   */
  async fill(selector: string, value: string): Promise<void> {
    await this.page.fill(selector, value);
  }

  /**
   * Get text content
   */
  async getText(selector: string): Promise<string> {
    return await this.page.textContent(selector) || '';
  }
}
```

### Example Page Object

```typescript
/**
 * Login Page Object
 */
export class LoginPage extends BasePage {
  readonly url = '/login';
  readonly emailInput = 'input[type="email"]';
  readonly passwordInput = 'input[type="password"]';
  readonly submitButton = 'button[type="submit"]';
  readonly errorMessage = '[data-testid="login-error"]';

  /**
   * Navigate to login page
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
  }

  /**
   * Fill login form
   */
  async fillForm(email: string, password: string): Promise<void> {
    await this.page.fill(this.emailInput, email);
    await this.page.fill(this.passwordInput, password);
  }

  /**
   * Submit login form
   */
  async submit(): Promise<void> {
    await this.page.click(this.submitButton);
  }

  /**
   * Complete login flow
   */
  async login(email: string, password: string): Promise<void> {
    await this.goto();
    await this.waitForLoad();
    await this.fillForm(email, password);
    await this.submit();
  }

  /**
   * Get error message
   */
  async getErrorMessage(): Promise<string> {
    await this.page.waitForSelector(this.errorMessage);
    return await this.getText(this.errorMessage);
  }
}
```

## Flow Test Template

```typescript
/**
 * {{FLOW_NAME}} Flow Test
 * Story: {{STORY_ID}}
 * Auto-generated from user flow diagrams
 * Generated: {{TIMESTAMP}}
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

test.describe('{{FLOW_NAME}}', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to entry point
    await page.goto('{{ENTRY_POINT_URL}}');
  });

  test('should complete the flow successfully', async ({ page }) => {
    // Step 1: {{STEP_DESCRIPTION}}
    {{STEP_CODE}}

    // Step 2: {{STEP_DESCRIPTION}}
    {{STEP_CODE}}

    // Verify success criteria
    await expect(page).toHaveURL(/{{SUCCESS_URL_PATTERN}}/);
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Test error scenarios
    {{ERROR_TEST_CODE}}
  });

  test('should validate required fields', async ({ page }) => {
    // Test form validation
    {{VALIDATION_TEST_CODE}}
  });
});
```

## Test Data Fixtures

```typescript
/**
 * User test data fixtures
 */
export const testUsers = {
  valid: {
    email: 'test@example.com',
    password: 'SecurePass123!',
    name: 'Test User'
  },
  invalid: {
    email: 'invalid-email',
    password: '123',
    name: ''
  },
  edgeCases: {
    longEmail: 'a'.repeat(1000) + '@example.com',
    specialChars: "test@example.com",
    unicode: 'test@例え.jp'
  }
};

/**
 * Scenario test data
 */
export const scenarios = {
  happyPath: {
    description: 'Standard user flow with valid data',
    data: testUsers.valid
  },
  invalidInput: {
    description: 'User flow with invalid data',
    data: testUsers.invalid
  },
  edgeCase: {
    description: 'User flow with edge case data',
    data: testUsers.edgeCases
  }
};
```

## Test Utilities

```typescript
/**
 * E2E Test Utilities
 */
import { test as base } from '@playwright/test';

export const test = base.extend<{
  authenticatedPage: Page;
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

/**
 * Wait for API response
 */
export async function waitForApiResponse(
  page: Page,
  urlPattern: string,
  timeout = 5000
): Promise<any> {
  return await page.waitForResponse(
    (response) => response.url().includes(urlPattern),
    { timeout }
  );
}

/**
 * Mock API response
 */
export async function mockApiResponse(
  page: Page,
  urlPattern: string,
  response: any
): Promise<void> {
  await page.route(urlPattern, (route) => {
    route.fulfill({
      status: 200,
      body: JSON.stringify(response),
      headers: { 'Content-Type': 'application/json' }
    });
  });
}
```

## Best Practices

1. **Use Page Objects**: Encapsulate page-specific logic in page object classes
2. **Wait for Stability**: Use `waitForLoadState('networkidle')` before assertions
3. **Data-Driven Tests**: Use fixtures for test data instead of hardcoding
4. **Explicit Selectors**: Use data-testid attributes for reliable selectors
5. **Avoid Timeouts**: Use explicit waits instead of arbitrary timeouts
6. **Mock External APIs**: Mock external dependencies for reliable tests
7. **Clean Up**: Use test hooks to clean up test data
8. **Parallel Execution**: Design tests to run in parallel
