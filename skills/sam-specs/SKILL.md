---
name: sam-specs
description: Technical specification writer with Context7 integration. Reads user stories, uses Context7 MCP for latest technical documentation, generates comprehensive specs with checkbox task tracking ([ ]/[x]). Covers architecture, database schema, API endpoints, component hierarchy, and implementation tasks. Use when user says "generate technical specs", "create technical specification", or "write implementation plan".
---

# Technical Specification Agent

## Overview

This skill transforms user stories into actionable technical specifications with Context7-powered latest documentation research.

## Workflow

### 1. Input Processing

Read all user stories from `.sam/{feature}/USER_STORIES/`.

Identify:
- All functional requirements across stories
- Technical considerations from each story
- Dependencies and constraints
- Data models and API needs

### 2. Context7 Research

For each technical area identified, use `mcp__plugin_context7_context7__query-docs`:

**Framework/Stack Research:**
```
Library ID: {e.g., /vercel/next.js}
Query: "Latest best practices for {feature} implementation, including authentication patterns, state management, and API routes"
```

**Database Research:**
```
Library ID: {e.g., /mongodb/docs or /supabase/supabase}
Query: "Schema design patterns for {data models}, indexing strategies, and migration best practices"
```

**Security Research:**
```
Library ID: {e.g., /authjs/next-auth}
Query: "Security best practices for {authentication/authorization}, session management, and token handling"
```

### 3. Specification Generation

Create comprehensive technical specification covering:

**Architecture Overview**
- System architecture diagram/description
- Technology stack table with versions and rationale
- Design patterns to apply

**Database Schema**
- Entity definitions with DDL statements
- Relationships and constraints
- Indexes for performance

**API Specification**
- All endpoints with HTTP methods
- Request/response schemas
- Authentication requirements
- Error response codes

**Component Architecture**
- Frontend component hierarchy
- State management approach
- Routing structure

### 4. Task Breakdown with Checkboxes

Convert all user story acceptance criteria into actionable technical tasks.

**Checkbox Format:**
```markdown
## Phase 1: Foundation
- [ ] **1.1 Project Setup**
  - [ ] Initialize repository
  - [ ] Configure build tools
  - [ ] Set up linting (ESLint, Prettier)
```

### 5. Output Generation

Generate `.sam/{feature}/TECHNICAL_SPEC.md`.

Report completion:
```
✅ Technical specification created: .sam/001_user_auth/TECHNICAL_SPEC.md
📚 Context7 research: 3 documentation sources queried
📋 Tasks: 24 implementation tasks with checkbox tracking
📋 Next: Run /sam-develop to start implementation
```

## Checkbox Task Format

All tasks use `[ ]` / `[x]` format:
- `[ ]` = Not started
- `[x]` = Completed

Nested tasks:
```markdown
- [ ] **Parent Task**
  - [ ] Subtask 1
  - [x] Subtask 2 (completed)
  - [ ] Subtask 3
```

## Context7 Query Strategy

1. **Always resolve library ID first** using `resolve-library-id`
2. **Use specific queries** - "authentication patterns" not "auth"
3. **Limit to 3 calls per technical area** to avoid token waste
4. **Cite sources** in spec for future reference

## Key Principles

- **Every user story acceptance criteria → Technical task**: No orphan requirements
- **Checkbox tracking**: Visual progress indication
- **Context7 integration**: Specs use current best practices, not outdated knowledge
- **Actionable tasks**: Developers can execute without clarification

## Output Format Requirement

You MUST generate TECHNICAL_SPEC.md following THIS EXACT STRUCTURE:

# Technical Specification: {{FEATURE_NAME}}

## Metadata
- **Feature**: {{FEATURE_NAME}}
- **Feature ID**: {{FEATURE_ID}}
- **Status**: Draft
- **Created**: {{CREATED_DATE}}
- **Last Updated**: {{UPDATED_DATE}}

---

# Architecture Overview

## System Architecture

{{ARCHITECTURE_DIAGRAM_OR_DESCRIPTION}}

## Technology Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Frontend | {{FRAMEWORK}} | {{VERSION}} | {{RATIONALE}} |
| Backend | {{FRAMEWORK}} | {{VERSION}} | {{RATIONALE}} |
| Database | {{DATABASE}} | {{VERSION}} | {{RATIONALE}} |
| ORM | {{ORM}} | {{VERSION}} | {{RATIONALE}} |
| Auth | {{AUTH_LIBRARY}} | {{VERSION}} | {{RATIONALE}} |
| Testing | {{TEST_FRAMEWORK}} | {{VERSION}} | {{RATIONALE}} |

## Design Patterns

{{PATTERNS_TO_BE_APPLIED}}

---

# Database Schema

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

## CRITICAL: Phase Boundaries

DO NOT include these sections in TECHNICAL_SPEC.md:
- ❌ User Stories with "As a... When... I can..." format → Use `/sam-stories` instead
- ❌ Feature-level objectives and target users → Use `/sam-discover` output instead
- ❌ Domain research summaries (industry best practices, competitive landscape) → Use `/sam-discover` instead
- ❌ Actual code implementation → Use `/sam-develop` instead

Technical specs are about HOW to build the feature.
User stories and discovery are for earlier phases.

## Template Reference

The template at `/templates/specs/TECHNICAL_SPEC_TEMPLATE.md` defines the canonical structure.
This skill embeds the EXACT structure above in "## Output Format Requirement" to ensure strict adherence.
