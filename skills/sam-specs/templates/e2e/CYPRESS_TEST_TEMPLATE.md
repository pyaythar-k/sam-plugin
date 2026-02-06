# Cypress E2E Test Template

This template provides the structure for generating Cypress end-to-end tests from user flow diagrams.

## Directory Structure

```
tests/e2e/cypress/
├── e2e/                      # E2E test specs
│   ├── authentication.cy.ts  # Auth flow tests
│   ├── signup.cy.ts          # Signup flow tests
│   └── checkout.cy.ts        # Checkout flow tests
├── support/                  # Support files
│   ├── commands.ts           # Custom commands
│   ├── e2e.ts                # E2E test configuration
│   └── index.ts              # Global configuration
└── fixtures/                 # Test data fixtures
    ├── users.ts              # User test data
    └── scenarios.ts          # Scenario data
```

## Custom Commands

### Navigation Commands

```typescript
/**
 * Cypress Custom Commands
 */

// Navigate to specific pages
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

// Login command
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.navigateTo('login');
  cy.get('input[type="email"]').type(email);
  cy.get('input[type="password"]').type(password);
  cy.get('button[type="submit"]').click();
  cy.url().should('include', '/dashboard');
});

// Logout command
Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/login');
});

// Fill form by data-testid
Cypress.Commands.add('fillByTestId', (testId: string, value: string) => {
  cy.get(`[data-testid="${testId}"]`).clear().type(value);
});

declare global {
  namespace Cypress {
    interface Chainable {
      navigateTo(page: string): Chainable<void>;
      login(email: string, password: string): Chainable<void>;
      logout(): Chainable<void>;
      fillByTestId(testId: string, value: string): Chainable<void>;
    }
  }
}
```

## Test Spec Template

```typescript
/**
 * {{FLOW_NAME}} Flow Test
 * Story: {{STORY_ID}}
 * Auto-generated from user flow diagrams
 * Generated: {{TIMESTAMP}}
 */

describe('{{FLOW_NAME}}', () => {
  const testUser = {
    email: 'test@example.com',
    password: 'SecurePass123!',
    name: 'Test User'
  };

  beforeEach(() => {
    // Navigate to entry point
    cy.visit('{{ENTRY_POINT_URL}}');

    // Clear cookies and localStorage
    cy.clearCookies();
    cy.clearLocalStorage();
  });

  it('should complete the flow successfully', () => {
    // Step 1: {{STEP_DESCRIPTION}}
    {{STEP_CODE}}

    // Step 2: {{STEP_DESCRIPTION}}
    {{STEP_CODE}}

    // Verify success criteria
    cy.url().should('match', /{{SUCCESS_URL_PATTERN}}/);
  });

  it('should handle errors gracefully', () => {
    // Test error scenarios
    {{ERROR_TEST_CODE}}
  });

  it('should validate required fields', () => {
    // Test form validation
    {{VALIDATION_TEST_CODE}}
  });

  context('with authenticated user', () => {
    beforeEach(() => {
      cy.login(testUser.email, testUser.password);
    });

    it('should show personalized content', () => {
      // Test authenticated behavior
      {{AUTH_TEST_CODE}}
    });
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
    specialChars: 'test+tag@example.com',
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

## Page Object Pattern (Optional)

```typescript
/**
 * Login Page Object
 */
export class LoginPage {
  visit() {
    cy.visit('/login');
  }

  fillEmail(email: string) {
    cy.get('input[type="email"]').type(email);
  }

  fillPassword(password: string) {
    cy.get('input[type="password"]').type(password);
  }

  submit() {
    cy.get('button[type="submit"]').click();
  }

  login(email: string, password: string) {
    this.fillEmail(email);
    this.fillPassword(password);
    this.submit();
  }

  getErrorMessage() {
    return cy.get('[data-testid="login-error"]');
  }
}

// Usage in tests
const loginPage = new LoginPage();

it('should login with valid credentials', () => {
  loginPage.visit();
  loginPage.login('test@example.com', 'password123');
  cy.url().should('include', '/dashboard');
});
```

## API Interception

```typescript
/**
 * Mock API responses
 */
cy.intercept('GET', '/api/user', {
  fixture: 'user.json'
}).as('getUser');

cy.intercept('POST', '/api/login', (req) => {
  req.reply({
    statusCode: 200,
    body: { token: 'fake-token', user: { id: 1, name: 'Test' } }
  });
}).as('login');

// Wait for API response
cy.wait('@getUser').then((interception) => {
  expect(interception.response.statusCode).to.eq(200);
});
```

## Configuration

### cypress.config.ts

```typescript
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'tests/e2e/cypress/support/index.ts',
    specPattern: 'tests/e2e/cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    screenshotOnRunFailure: true,
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});
```

## Best Practices

1. **Use Data Attributes**: Select elements using `data-testid` for stability
2. **Avoid Hardcoded Waits**: Use assertions and built-in waits
3. **Custom Commands**: Reusable logic in custom commands
4. **Test Isolation**: Each test should be independent
5. **Clean Up**: Clear state between tests
6. **API Mocking**: Mock external dependencies
7. **Page Objects**: Optional but useful for complex flows
8. **Descriptive Tests**: Clear test names and context
