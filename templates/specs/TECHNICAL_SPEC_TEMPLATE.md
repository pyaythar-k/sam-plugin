# Technical Specification: {{FEATURE_NAME}}

## Metadata

- **Feature**: {{FEATURE_NAME}}
- **Feature ID**: {{FEATURE_ID}}
- **Status**: Draft
- **Created**: {{CREATED_DATE}}
- **Last Updated**: {{UPDATED_DATE}}
- **Spec Version**: 2.0 (Modular)
- **Registry**: TASKS.json (required for incremental reading)
- **Project Type**: {{PROJECT_TYPE}} (baas-fullstack | frontend-only | full-stack | static-site)

---

# Architecture Overview

## System Architecture

{{ARCHITECTURE_DIAGRAM_OR_DESCRIPTION}}

## Technology Stack

| Layer    | Technology         | Version     | Rationale     |
| -------- | ------------------ | ----------- | ------------- |
| Frontend | {{FRAMEWORK}}      | {{VERSION}} | {{RATIONALE}} |
| Backend  | {{FRAMEWORK}}      | {{VERSION}} | {{RATIONALE}} |
| Database | {{DATABASE}}       | {{VERSION}} | {{RATIONALE}} |
| ORM      | {{ORM}}            | {{VERSION}} | {{RATIONALE}} |
| Auth     | {{AUTH_LIBRARY}}   | {{VERSION}} | {{RATIONALE}} |
| Testing  | {{TEST_FRAMEWORK}} | {{VERSION}} | {{RATIONALE}} |

## Design Patterns

{{PATTERNS_TO_BE_APPLIED}}

---

# Database Schema

**CONDITIONAL SECTION**: Include only if project_type != "frontend-only" and project_type != "static-site"

**For BaaS-fullstack projects**: Replace with "BaaS Database Configuration" covering:
- Table/collection structure
- Row Level Security (RLS) policies for Supabase
- Firestore security rules for Firebase
- Indexes and constraints

**For full-stack projects**: Include standard SQL DDL below.

**For frontend-only/static-site projects**: Skip this entire section.

---

# Database Schema - Standard SQL

**NOTE**: This section is for custom backend projects with SQL databases. For BaaS projects, see "BaaS Database Configuration" above. For frontend-only projects, skip this section.

## Entities

```sql
-- {{ENTITY_NAME_1}}
CREATE TABLE {{TABLE_NAME_1}} (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  {{FIELD_1}} {{TYPE}} {{CONSTRAINTS}},
  {{FIELD_2}} {{TYPE}} {{CONSTRAINTS}},
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- {{ENTITY_NAME_2}}
CREATE TABLE {{TABLE_NAME_2}} (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  {{FIELD_1}} {{TYPE}} {{CONSTRAINTS}},
  {{FIELD_2}} {{TYPE}} {{CONSTRAINTS}},
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Relationships

{{ENTITY_RELATIONSHIP_DIAGRAM}}

## Indexes

```sql
-- Performance indexes
CREATE INDEX idx_{{TABLE}}_{{FIELD}} ON {{TABLE}} ({{FIELD}});
CREATE INDEX idx_{{TABLE}}_{{FIELD}}_{{FIELD2}} ON {{TABLE}} ({{FIELD}}, {{FIELD2}});
```

---

# API Specification

**CONDITIONAL SECTION**: Include only if project_type != "frontend-only" and project_type != "static-site"

**For BaaS-fullstack projects**: Replace this section with "BaaS Integration" covering:
- BaaS client initialization and configuration
- Authentication integration (e.g., Supabase Auth, Firebase Auth)
- Database client setup (e.g., Supabase PostgREST, Firebase Firestore)
- Storage configuration (if applicable)
- Real-time subscriptions setup (if applicable)

**For full-stack projects**: Include standard REST API specification below.

**For frontend-only/static-site projects**: Skip this entire section.

---

# API Specification (if applicable) - Standard REST API

**NOTE**: This section is for custom backend projects. For BaaS projects, see "BaaS Integration" above. For frontend-only projects, skip this section.

## Endpoints

### {{RESOURCE_NAME}}

#### POST /api/{{RESOURCE}}

**Purpose**: {{WHAT_IT_DOES}}

**Authentication**: {{REQUIRED_OR_OPTIONAL}}

**Request Headers**:

```http
Content-Type: application/json
Authorization: Bearer {{JWT_TOKEN}}
```

**Request Body**:

```json
{
  "{{FIELD_1}}": "{{TYPE}}",
  "{{FIELD_2}}": "{{TYPE}}",
  "{{FIELD_3}}": "{{TYPE}}"
}
```

**Response**: 200 OK

```json
{
  "{{RESPONSE_FIELD_1}}": "{{TYPE}}",
  "{{RESPONSE_FIELD_2}}": "{{TYPE}}"
}
```

**Error Responses**:

- 400 Bad Request - Invalid input
- 401 Unauthorized - Missing or invalid token
- 404 Not Found - Resource not found
- 500 Internal Server Error - Server error

---

#### GET /api/{{RESOURCE}}

**Purpose**: {{WHAT_IT_DOES}}

**Authentication**: {{REQUIRED_OR_OPTIONAL}}

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| {{PARAM_1}} | {{TYPE}} | {{YES_NO}} | {{DESCRIPTION}} |
| {{PARAM_2}} | {{TYPE}} | {{YES_NO}} | {{DESCRIPTION}} |

**Response**: 200 OK

```json
{
  "{{RESOURCE}}": [
    {
      "{{FIELD_1}}": "{{VALUE}}",
      "{{FIELD_2}}": "{{VALUE}}"
    }
  ],
  "pagination": {
    "page": {{NUMBER}},
    "limit": {{NUMBER}},
    "total": {{NUMBER}}
  }
}
```

---

#### GET /api/{{RESOURCE}}/:id

**Purpose**: {{WHAT_IT_DOES}}

**Authentication**: {{REQUIRED_OR_OPTIONAL}}

**Response**: 200 OK

```json
{
  "{{FIELD_1}}": "{{VALUE}}",
  "{{FIELD_2}}": "{{VALUE}}"
}
```

**Error Responses**:

- 404 Not Found - Resource not found

---

#### PUT /api/{{RESOURCE}}/:id

**Purpose**: {{WHAT_IT_DOES}}

**Authentication**: {{REQUIRED_OR_OPTIONAL}}

**Request Body**:

```json
{
  "{{FIELD_1}}": "{{TYPE}}",
  "{{FIELD_2}}": "{{TYPE}}"
}
```

**Response**: 200 OK

```json
{
  "{{FIELD_1}}": "{{VALUE}}",
  "{{FIELD_2}}": "{{VALUE}}"
}
```

---

#### DELETE /api/{{RESOURCE}}/:id

**Purpose**: {{WHAT_IT_DOES}}

**Authentication**: {{REQUIRED_OR_OPTIONAL}}

**Response**: 204 No Content

---

# Component Architecture

## Frontend Components

```
src/
├── components/
│   ├── {{FeatureName}}/
│   │   ├── {{Component1}}.tsx
│   │   ├── {{Component2}}.tsx
│   │   ├── {{Component3}}.tsx
│   │   └── index.ts
├── hooks/
│   └── {{FeatureName}}/
│       ├── use{{Hook1}}.ts
│       └── use{{Hook2}}.ts
├── services/
│   └── {{FeatureName}}/
│       └── {{ServiceName}}.ts
└── types/
    └── {{FeatureName}}.ts
```

## Component Hierarchy

```
{{PARENT_COMPONENT}}
├── {{CHILD_COMPONENT_1}}
│   └── {{GRANDCHILD_COMPONENT}}
└── {{CHILD_COMPONENT_2}}
```

## State Management

{{STATE_MANAGEMENT_APPROACH}}

```typescript
// Example: Zustand store
interface {{FeatureName}}State {
  {{STATE_1}}: {{TYPE}};
  {{STATE_2}}: {{TYPE}};
  actions: {
    {{ACTION_1}}: ({{PARAMS}}) => void;
    {{ACTION_2}}: ({{PARAMS}}) => void;
  };
}
```

## Routing

```typescript
// Route definitions
const {{FeatureName}}Routes = [
  {
    path: '{{ROUTE_PATH}}',
    component: {{ComponentName}},
    protected: {{TRUE_FALSE}},
  },
];
```

---

# Implementation Tasks

**PHASE STRUCTURE VARIES BY PROJECT TYPE**:

| Project Type | Phase 2 Name | Total Phases |
|--------------|--------------|--------------|
| baas-fullstack | BaaS Integration | 5 |
| frontend-only | Frontend | 4 |
| full-stack | Backend | 5 |
| static-site | Content | 4 |

**Adjust phase names and counts below based on project_type.**

---

## Phase 1: Foundation

- [ ] **1.1 Project Setup**
  - [ ] Create feature branch: `feature/{{FEATURE_ID}}-{{DESCRIPTION}}`
  - [ ] Initialize package dependencies
  - [ ] Configure build tools (Vite/Next.js/webpack)
  - [ ] Set up linting (ESLint, Prettier)
  - [ ] Set up type checking (TypeScript)

- [ ] **1.2 Database**
  - [ ] Create migration files
  - [ ] Run database migrations
  - [ ] Create seed data for development
  - [ ] Verify schema with test queries
  - [ ] Set up database indexes

- [ ] **1.3 Development Environment**
  - [ ] Configure environment variables
  - [ ] Set up local development services
  - [ ] Create development database
  - [ ] Verify local setup

## Phase 2: Backend

- [ ] **2.1 API Development**
  - [ ] Implement POST /api/{{RESOURCE}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Implement GET /api/{{RESOURCE}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Implement GET /api/{{RESOURCE}}/:id
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Implement PUT /api/{{RESOURCE}}/:id
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Implement DELETE /api/{{RESOURCE}}/:id
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Add request validation middleware
  - [ ] Add error handling middleware
  - [ ] Add authentication/authorization checks

- [ ] **2.2 Business Logic**
  - [ ] Implement {{SERVICE_1}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Implement {{SERVICE_2}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Implement {{SERVICE_3}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Add business rule validation
  - [ ] Add edge case handling

- [ ] **2.3 Backend Testing**
  - [ ] Write unit tests for services
  - [ ] Write integration tests for API endpoints
  - [ ] Test error scenarios
  - [ ] Test edge cases
  - [ ] Achieve 80%+ code coverage

## Phase 3: Frontend

- [ ] **3.1 Components**
  - [ ] Create {{Component1}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Create {{Component2}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Create {{Component3}}
    - Maps to: Story {{XXX}} (AC: {{ACCEPTANCE_CRITERION}})
  - [ ] Add TypeScript types for components
  - [ ] Add component documentation

- [ ] **3.2 State Management**
  - [ ] Create Zustand/Redux store
  - [ ] Define state shape
  - [ ] Implement state actions
  - [ ] Add state selectors

- [ ] **3.3 API Integration**
  - [ ] Create API client/service
  - [ ] Implement data fetching hooks
  - [ ] Add loading states
  - [ ] Add error states
  - [ ] Add retry logic

- [ ] **3.4 UI Implementation**
  - [ ] Build forms with validation
  - [ ] Implement navigation
  - [ ] Add responsive design
  - [ ] Add accessibility features (ARIA labels, keyboard nav)
  - [ ] Add loading indicators
  - [ ] Add error messages

- [ ] **3.5 Frontend Testing**
  - [ ] Write component tests
  - [ ] Write hook tests
  - [ ] Test user interactions
  - [ ] Test error states
  - [ ] Achieve 80%+ code coverage

## Phase 4: Integration

- [ ] **4.1 End-to-End Integration**
  - [ ] Connect frontend to backend
  - [ ] Test complete user flows
    - Maps to: Story {{XXX}} (User Flow: {{FLOW_NAME}})
  - [ ] Test error handling
  - [ ] Test loading states
  - [ ] Test edge cases

- [ ] **4.2 E2E Testing**
  - [ ] Write Playwright/Cypress tests
  - [ ] Test critical user paths
  - [ ] Test cross-browser compatibility
  - [ ] Test mobile responsiveness

- [ ] **4.3 Polish**
  - [ ] Add animations/transitions
  - [ ] Optimize performance
  - [ ] Fix accessibility issues
  - [ ] Verify design system compliance

## Phase 5: Quality Assurance

- [ ] **5.1 Code Quality**
  - [ ] Run linting: `npm run lint` ✓
  - [ ] Run type checking: `npm run type-check` ✓
  - [ ] Run build: `npm run build` ✓
  - [ ] Fix all linting errors
  - [ ] Fix all type errors

- [ ] **5.2 Testing**
  - [ ] All unit tests pass: `npm test` ✓
  - [ ] All integration tests pass ✓
  - [ ] All E2E tests pass: `npm run test:e2e` ✓
  - [ ] Coverage report: 80%+ ✓

- [ ] **5.3 Security Review**
  - [ ] Review for SQL injection vulnerabilities
  - [ ] Review for XSS vulnerabilities
  - [ ] Review for CSRF vulnerabilities
  - [ ] Verify authentication/authorization
  - [ ] Audit data handling

- [ ] **5.4 Performance Review**
  - [ ] Measure API response times
  - [ ] Optimize slow queries
  - [ ] Optimize bundle size
  - [ ] Optimize images and assets
  - [ ] Verify caching strategy

---

# Development Guidelines

## Code Quality Standards

### Linting

```bash
npm run lint
```

- All linting errors must be fixed
- No exceptions

### Type Checking

```bash
npm run type-check
```

- All TypeScript errors must be resolved
- No `any` types without justification

### Build

```bash
npm run build
```

- Production build must succeed
- No build errors or warnings

## Testing Standards

### Unit Tests

- Framework: {{TEST_FRAMEWORK}}
- Coverage Target: 80%+
- Run: `npm test`

### Integration Tests

- Framework: {{TEST_FRAMEWORK}}
- Coverage: All API endpoints
- Run: `npm run test:integration`

### E2E Tests

- Framework: {{E2E_FRAMEWORK}}
- Coverage: Critical user paths
- Run: `npm run test:e2e`

---

# State Machine Modeling

**WHEN TO INCLUDE**: Add this section when the feature involves complex workflows, multi-step processes, or stateful entities that transition between different states.

**CONDITIONAL**: Optional - include only if applicable to the feature.

---

## State Machine: {{MACHINE_NAME}}

### Description

{{STATE_MACHINE_DESCRIPTION}}

### Business Context

{{BUSINESS_CONTEXT}}

**States**: {{STATE_COUNT}}
**Transitions**: {{TRANSITION_COUNT}}
**Final States**: {{FINAL_STATES}}

---

### States

| State ID | State Name | Description | Entry Actions | Exit Actions |
|----------|------------|-------------|---------------|--------------|
| {{STATE_1_ID}} | {{STATE_1_NAME}} | {{STATE_1_DESCRIPTION}} | {{STATE_1_ON_ENTRY}} | {{STATE_1_ON_EXIT}} |
| {{STATE_2_ID}} | {{STATE_2_NAME}} | {{STATE_2_DESCRIPTION}} | {{STATE_2_ON_ENTRY}} | {{STATE_2_ON_EXIT}} |
| {{STATE_3_ID}} | {{STATE_3_NAME}} | {{STATE_3_DESCRIPTION}} | {{STATE_3_ON_ENTRY}} | {{STATE_3_ON_EXIT}} |

---

### Transitions

| From State | Event | To State | Guard Condition | Action | Timeout |
|------------|-------|----------|-----------------|--------|---------|
| {{FROM_STATE_1}} | {{EVENT_1}} | {{TO_STATE_1}} | {{GUARD_1}} | {{ACTION_1}} | {{TIMEOUT_1}} |
| {{FROM_STATE_2}} | {{EVENT_2}} | {{TO_STATE_2}} | {{GUARD_2}} | {{ACTION_2}} | {{TIMEOUT_2}} |
| {{FROM_STATE_3}} | {{EVENT_3}} | {{TO_STATE_3}} | {{GUARD_3}} | {{ACTION_3}} | {{TIMEOUT_3}} |

---

### State Context

The state machine maintains the following context:

```typescript
interface {{MACHINE_NAME}}Context {
  {{CONTEXT_FIELD_1}}: {{CONTEXT_TYPE_1}};
  {{CONTEXT_FIELD_2}}: {{CONTEXT_TYPE_2}};
  {{CONTEXT_FIELD_3}}: {{CONTEXT_TYPE_3}};
}
```

---

### Events

```typescript
type {{MACHINE_NAME}}Event =
  | { type: '{{EVENT_1_TYPE}}'; {{EVENT_1_PAYLOAD}} }
  | { type: '{{EVENT_2_TYPE}}'; {{EVENT_2_PAYLOAD}} }
  | { type: '{{EVENT_3_TYPE}}'; {{EVENT_3_PAYLOAD}} };
```

---

### Guards

| Guard Name | Description | Implementation |
|------------|-------------|----------------|
| {{GUARD_1_NAME}} | {{GUARD_1_DESCRIPTION}} | `{{GUARD_1_FUNCTION}}()` |
| {{GUARD_2_NAME}} | {{GUARD_2_DESCRIPTION}} | `{{GUARD_2_FUNCTION}}()` |
| {{GUARD_3_NAME}} | {{GUARD_3_DESCRIPTION}} | `{{GUARD_3_FUNCTION}}()` |

---

### Services

| Service Name | Description | Implementation |
|--------------|-------------|----------------|
| {{SERVICE_1_NAME}} | {{SERVICE_1_DESCRIPTION}} | `{{SERVICE_1_FUNCTION}}()` |
| {{SERVICE_2_NAME}} | {{SERVICE_2_DESCRIPTION}} | `{{SERVICE_2_FUNCTION}}()` |

---

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> {{INITIAL_STATE}}

    {{STATE_1}}: {{STATE_1_NAME}}
    {{STATE_1}} --> {{STATE_2}}: {{EVENT_1}} ({{GUARD_1}})
    {{STATE_1}} --> {{STATE_3}}: {{EVENT_2}} ({{TIMEOUT_1}})

    {{STATE_2}}: {{STATE_2_NAME}}
    {{STATE_2}} --> {{STATE_3}}: {{EVENT_3}}
    {{STATE_2}} --> {{STATE_4}}: {{EVENT_4}} ({{GUARD_2}})

    {{STATE_3}}: {{STATE_3_NAME}}
    {{STATE_3}} --> {{STATE_1}}: {{EVENT_5}}

    {{STATE_4}}: {{STATE_4_NAME}}
    {{STATE_4}} --> [*]

    note right of {{STATE_1}}
        on_entry: {{STATE_1_ON_ENTRY}}
        on_exit: {{STATE_1_ON_EXIT}}
    end note
```

---

### Error Handling

| Error Scenario | Handling Strategy | Target State |
|----------------|-------------------|--------------|
| {{ERROR_SCENARIO_1}} | {{ERROR_HANDLING_1}} | {{ERROR_TARGET_STATE_1}} |
| {{ERROR_SCENARIO_2}} | {{ERROR_HANDLING_2}} | {{ERROR_TARGET_STATE_2}} |
| {{ERROR_SCENARIO_3}} | {{ERROR_HANDLING_3}} | {{ERROR_TARGET_STATE_3}} |

---

### Implementation

**Generated Code Location**: `state-machines/{{MACHINE_NAME}}/`

**To Generate XState (TypeScript/JavaScript)**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework xstate
```

**To Generate Python Transitions**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework transitions
```

**To Generate Mermaid Diagram**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework mermaid
```

**To Generate All Frameworks**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --all
```

---

### Testing Strategy

1. **Unit Tests**: Test individual guards and services
2. **Integration Tests**: Test state transitions with valid and invalid inputs
3. **Visual Tests**: Verify Mermaid diagram accurately represents the state machine
4. **Edge Cases**: Test timeout scenarios, guard failures, and error handling

---

### Notes

- {{IMPLEMENTATION_NOTE_1}}
- {{IMPLEMENTATION_NOTE_2}}
- {{BUSINESS_RULE_NOTE_1}}

---

# Decision Table Modeling

**WHEN TO INCLUDE**: Add this section when the feature involves complex business rules with multiple conditions determining different actions.

**CONDITIONAL**: Optional - include only if applicable to the feature.

---

## Decision Table: {{TABLE_NAME}}

### Description

{{DECISION_TABLE_DESCRIPTION}}

### Business Context

{{BUSINESS_CONTEXT}}

**Inputs**: {{INPUT_COUNT}}
**Rules**: {{RULE_COUNT}}
**Coverage Target**: 100%

---

### Inputs

| Field | Type | Possible Values | Required | Description |
|-------|------|-----------------|----------|-------------|
| {{INPUT_1}} | {{INPUT_1_TYPE}} | {{INPUT_1_VALUES}} | {{INPUT_1_REQUIRED}} | {{INPUT_1_DESCRIPTION}} |
| {{INPUT_2}} | {{INPUT_2_TYPE}} | {{INPUT_2_VALUES}} | {{INPUT_2_REQUIRED}} | {{INPUT_2_DESCRIPTION}} |
| {{INPUT_3}} | {{INPUT_3_TYPE}} | {{INPUT_3_VALUES}} | {{INPUT_3_REQUIRED}} | {{INPUT_3_DESCRIPTION}} |

---

### Rules

| Rule | {{CONDITION_HEADER_1}} | {{CONDITION_HEADER_2}} | {{CONDITION_HEADER_3}} | {{ACTION_HEADER_1}} | {{ACTION_HEADER_2}} | {{ACTION_HEADER_3}} | Priority |
|------|------------------------|------------------------|------------------------|---------------------|---------------------|---------------------|----------|
| 1 | {{CONDITION_1_R1}} | {{CONDITION_2_R1}} | {{CONDITION_3_R1}} | {{ACTION_1_R1}} | {{ACTION_2_R1}} | {{ACTION_3_R1}} | {{PRIORITY_R1}} |
| 2 | {{CONDITION_1_R2}} | {{CONDITION_2_R2}} | {{CONDITION_3_R2}} | {{ACTION_1_R2}} | {{ACTION_2_R2}} | {{ACTION_3_R2}} | {{PRIORITY_R2}} |
| 3 | {{CONDITION_1_R3}} | {{CONDITION_2_R3}} | {{CONDITION_3_R3}} | {{ACTION_1_R3}} | {{ACTION_2_R3}} | {{ACTION_3_R3}} | {{PRIORITY_R3}} |
| 4 | {{CONDITION_1_R4}} | {{CONDITION_2_R4}} | {{CONDITION_3_R4}} | {{ACTION_1_R4}} | {{ACTION_2_R4}} | {{ACTION_3_R4}} | {{PRIORITY_R4}} |

---

### Rule Descriptions

#### Rule 1: {{RULE_1_NAME}}
**Conditions**: {{RULE_1_CONDITIONS_DESCRIPTION}}
**Actions**: {{RULE_1_ACTIONS_DESCRIPTION}}
**Priority**: {{RULE_1_PRIORITY}}
**Business Justification**: {{RULE_1_JUSTIFICATION}}

#### Rule 2: {{RULE_2_NAME}}
**Conditions**: {{RULE_2_CONDITIONS_DESCRIPTION}}
**Actions**: {{RULE_2_ACTIONS_DESCRIPTION}}
**Priority**: {{RULE_2_PRIORITY}}
**Business Justification**: {{RULE_2_JUSTIFICATION}}

#### Rule 3: {{RULE_3_NAME}}
**Conditions**: {{RULE_3_CONDITIONS_DESCRIPTION}}
**Actions**: {{RULE_3_ACTIONS_DESCRIPTION}}
**Priority**: {{RULE_3_PRIORITY}}
**Business Justification**: {{RULE_3_JUSTIFICATION}}

---

### Edge Cases

| Scenario | Input Values | Expected Output | Notes |
|----------|--------------|-----------------|-------|
| {{EDGE_CASE_1}} | {{EDGE_CASE_1_INPUTS}} | {{EDGE_CASE_1_OUTPUT}} | {{EDGE_CASE_1_NOTES}} |
| {{EDGE_CASE_2}} | {{EDGE_CASE_2_INPUTS}} | {{EDGE_CASE_2_OUTPUT}} | {{EDGE_CASE_2_NOTES}} |
| {{EDGE_CASE_3}} | {{EDGE_CASE_3_INPUTS}} | {{EDGE_CASE_3_OUTPUT}} | {{EDGE_CASE_3_NOTES}} |

---

### Test Coverage

**Generated Tests Location**: `tests/decision-tables/{{TABLE_NAME}}/`

**To Generate Jest Tests**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework jest
```

**To Generate Cucumber Tests**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework cucumber
```

**To Generate Pytest Tests**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework pytest
```

**To Generate with Edge Cases**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework jest --edge-cases
```

**Expected Coverage**: 100% (all rules tested)

---

### Implementation Example

#### TypeScript/JavaScript
```typescript
function {{TABLE_NAME}}(inputs: {{TABLE_NAME}}Inputs): {{TABLE_NAME}}Outputs {
  // Rule 1
  if ({{CONDITION_1_LOGIC}}) {
    return {
      {{OUTPUT_1}}: {{VALUE_1}},
      {{OUTPUT_2}}: {{VALUE_2}},
    };
  }

  // Rule 2
  if ({{CONDITION_2_LOGIC}}) {
    return {
      {{OUTPUT_1}}: {{VALUE_3}},
      {{OUTPUT_2}}: {{VALUE_4}},
    };
  }

  // Default fallback
  return {
    {{OUTPUT_1}}: {{DEFAULT_VALUE_1}},
    {{OUTPUT_2}}: {{DEFAULT_VALUE_2}},
  };
}
```

#### Python
```python
def {{table_name}}(inputs: {{TableName}}Inputs) -> {{TableName}}Outputs:
    """Execute {{TABLE_NAME}} decision table."""

    # Rule 1
    if {{CONDITION_1_LOGIC}}:
        return {{TableName}}Outputs(
            {{OUTPUT_1}}={{VALUE_1}},
            {{OUTPUT_2}}={{VALUE_2}},
        )

    # Rule 2
    if {{CONDITION_2_LOGIC}}:
        return {{TableName}}Outputs(
            {{OUTPUT_1}}={{VALUE_3}},
            {{OUTPUT_2}}={{VALUE_4}},
        )

    # Default fallback
    return {{TableName}}Outputs(
        {{OUTPUT_1}}={{DEFAULT_VALUE_1}},
        {{OUTPUT_2}}={{DEFAULT_VALUE_2}},
    )
```

---

### Testing Strategy

1. **Rule Coverage**: Every rule must have at least one test
2. **Data-Driven Tests**: Use parameterized tests for all rules
3. **Edge Cases**: Test boundary values and null/undefined inputs
4. **Priority Testing**: Ensure high-priority rules are tested first
5. **Regression Tests**: Add tests for any bugs found in production

---

### Maintenance

**When to Update**:
- New business rules are added
- Existing rules are modified
- New input combinations are identified
- Edge cases are discovered in production

**Update Process**:
1. Update the decision table in EXECUTABLE_SPEC.yaml
2. Re-run scenario_parser.py
3. Regenerate tests using decision_table_test_generator.py
4. Verify all new tests pass
5. Update this documentation section

---

### Notes

- {{BUSINESS_RULE_NOTE_1}}
- {{IMPLEMENTATION_NOTE_1}}
- {{TESTING_NOTE_1}}
- {{PERFORMANCE_NOTE_1}}: Consider caching if this function is called frequently

---

## Git Workflow

### Branch Naming

```
feature/{{FEATURE_ID}}-{{short-description}}
```

### Commit Messages

Follow Conventional Commits:

```
feat: add user registration form
fix: resolve login token expiration issue
test: add integration tests for password reset
refactor: simplify auth state management
docs: update API documentation
```

### Pull Request Template

```markdown
## What

{{BRIEF_DESCRIPTION}}

## Why

{{BUSINESS_VALUE}}

## How

{{IMPLEMENTATION_APPROACH}}

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Checklist

- [ ] All acceptance criteria met
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] No console errors
- [ ] Accessibility audit passed
```

---

# Context7 References

## Latest Documentation

### Framework

- [{{FRAMEWORK}} Official Docs]({{URL}}) - {{KEY_INFO}}
- [{{LIBRARY}} Guide]({{URL}}) - {{KEY_INFO}}

### Database

- [{{DATABASE}} Documentation]({{URL}}) - {{KEY_INFO}}
- [{{ORM}} Reference]({{URL}}) - {{KEY_INFO}}

### Security

- [OWASP Guidelines]({{URL}}) - {{KEY_INFO}}
- [{{AUTH_LIBRARY}} Guide]({{URL}}) - {{KEY_INFO}}

### Best Practices

- [{{PATTERN}} Pattern]({{URL}}) - {{KEY_INFO}}
- [{{TOPIC}} Guide]({{URL}}) - {{KEY_INFO}}

---

# Deployment Checklist

## Pre-deployment

- [ ] All tests pass
- [ ] Build succeeds
- [ ] No console errors
- [ ] Accessibility audit passed
- [ ] Security review completed
- [ ] Performance benchmarks met

## Deployment

- [ ] Database migrations applied
- [ ] Database backups created
- [ ] Environment variables configured
- [ ] Feature flags set
- [ ] CDN cache cleared
- [ ] Monitoring configured

## Post-deployment

- [ ] Smoke tests passed
- [ ] Monitoring dashboards active
- [ ] Error tracking enabled
- [ ] Rollback plan documented
- [ ] User notification sent (if applicable)

---

# Notes

{{ADDITIONAL_TECHNOTES_CONTEXT}}

---

# Modular Spec Structure (v2.0)

**NEW**: This specification uses a modular structure for efficient incremental processing.

## Directory Structure

```
.sam/{feature}/
├── FEATURE_DOCUMENTATION.md
├── USER_STORIES/
│   ├── 001_*.md
│   └── 002_*.md
├── TECHNICAL_SPEC.md          # This file (architecture, database, API, components)
├── TASKS.json                  # Task registry with line numbers (auto-generated)
└── IMPLEMENTATION_TASKS.md     # Detailed tasks split by phase
    ├── PHASE_1_FOUNDATION.md
    ├── PHASE_2_BACKEND.md
    ├── PHASE_3_FRONTEND.md
    ├── PHASE_4_INTEGRATION.md
    └── PHASE_5_QUALITY_ASSURANCE.md
```

## TASKS.json Registry

The TASKS.json file is auto-generated by:
```bash
python3 skills/sam-specs/scripts/spec_parser.py .sam/{feature}
```

It contains:
- Task metadata with line numbers
- Phase information
- Checkpoint data for resumption
- Quality gate results

## Benefits

- **98% token reduction**: Read only current phase, not entire spec
- **Fast status checks**: Query TASKS.json instead of parsing
- **Checkpoint/resume**: Resume from last completed task
- **Parallel limits**: Enforce max 3 concurrent subagents

---

# Living Documentation (BMAD/SpecKit Enhancement)

## Spec Markers for Automatic Verification

This specification supports "living documentation" through spec markers that enable automatic verification against implementation.

### Database Schema Verification

```sql
<!-- spec:start:users_table -->
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
<!-- spec:end:users_table -->

<!-- verify:start:users_table -->
<!-- ✅ Verified: 2025-02-06 14:30:00 -->
<!-- SQL: SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' -->
<!-- Result: 4/4 columns match specification -->
<!-- verify:end:users_table -->
```

### API Endpoint Verification

```markdown
<!-- spec:start:api_post_users -->
#### POST /api/users

**Request Body**:
```json
{
  "email": "string",
  "password": "string"
}
```

**Response**: 201
```json
{
  "id": "uuid",
  "email": "string"
}
```
<!-- spec:end:api_post_users -->

<!-- verify:start:api_post_users -->
<!-- ✅ Verified: 2025-02-06 15:00:00 -->
<!-- curl -X POST http://localhost:3000/api/users ... -->
<!-- Result: Response matches specification -->
<!-- verify:end:api_post_users -->
```

### Component Verification

```markdown
<!-- spec:start:component_LoginForm -->
## LoginForm Component

**Props**:
- `onLogin: (credentials: Credentials) => void`
- `isLoading: boolean`
- `error: string | null`

**Usage**:
```tsx
<LoginForm onLogin={handleLogin} isLoading={false} error={null} />
```
<!-- spec:end:component_LoginForm -->

<!-- verify:start:component_LoginForm -->
<!-- ✅ Verified: 2025-02-06 15:30:00 -->
<!-- File: src/components/LoginForm.tsx exists -->
<!-- Props match specification -->
<!-- verify:end:component_LoginForm -->
```

## Running Verification

To verify all documentation against implementation:

```bash
python3 skills/sam-specs/scripts/verify_docs.py .sam/{feature_id}
```

This generates `DOCUMENTATION_VERIFICATION.md` with verification results.

## CI/CD Integration

Add to your CI pipeline for continuous documentation verification:

```yaml
- name: Verify Documentation
  run: python3 skills/sam-specs/scripts/verify_docs.py .sam/${{ feature_id }}
```

---

# Executable Specification (BMAD/SpecKit Enhancement)

## Overview

This feature includes an `EXECUTABLE_SPEC.yaml` file that defines testable scenarios from user story acceptance criteria.

## Structure

- **Scenarios**: Given/When/Then test cases
- **Contract Tests**: API schema validation
- **State Machines**: Workflow modeling (optional)
- **Decision Tables**: Business rules (optional)

## Generating Tests

From executable specifications, generate actual test files:

```bash
# Generate Jest tests
python3 skills/sam-specs/scripts/test_generator.py .sam/{feature_id} --framework jest

# Generate Cucumber tests
python3 skills/sam-specs/scripts/test_generator.py .sam/{feature_id} --framework cucumber

# Generate Pytest tests
python3 skills/sam-specs/scripts/test_generator.py .sam/{feature_id} --framework pytest
```

## Benefits

- **Specifications ARE tests**: No drift between docs and implementation
- **Given/When/Then clarity**: Unambiguous behavior specification
- **Automated verification**: Run `npm test` to verify specs
- **Living documentation**: Always in sync with code
