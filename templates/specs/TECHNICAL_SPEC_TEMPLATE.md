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
