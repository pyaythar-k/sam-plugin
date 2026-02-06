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

### 1.5. Codebase Context Analysis (NEW)

Before generating specifications, understand the current project state:

**Run codebase analyzer:**
```bash
python3 skills/sam-specs/scripts/codebase_analyzer.py {project_root}
```

**Read generated context:**
```
.sam/CODEBASE_CONTEXT.md
```

**Extract for spec generation:**
- Existing tech stack → Match versions/patterns
- Reusable components → Reference instead of recreate
- Architecture patterns → Follow established conventions
- Existing services → Integrate with current APIs
- Existing features → Avoid duplication

**Output includes in spec:**
- Section: "Integration with Existing Codebase"
- References to reusable components
- Pattern alignment notes
- Tech stack version compatibility

### 1.6. Project Type Classification (NEW)

**Classify project before generating specs:**

```bash
# Run classification
python3 skills/sam-specs/scripts/classify_project.py .sam/{feature}

# Read result
cat .sam/{feature}/TASKS.json | jq .metadata.project_type
```

**Override from discovery**:
- If FEATURE_DOCUMENTATION.md contains `project_type` field, use it
- User-specified type takes precedence over auto-detection

**Project Types:**

| Type | Description | Phases | API Spec | Database |
|------|-------------|--------|----------|----------|
| `baas-fullstack` | Supabase/Firebase + frontend | 5 | BaaS Integration | RLS policies |
| `frontend-only` | No backend + external API | 4 | Skip | Skip |
| `full-stack` | Custom backend detected | 5 | Standard API | SQL DDL |
| `static-site` | Next.js static, no backend | 4 | Skip | Skip |

**Phase Structure by Type:**

```python
# baas-fullstack
phases = ["FOUNDATION", "BAAS_INTEGRATION", "FRONTEND", "INTEGRATION", "QA"]

# frontend-only
phases = ["FOUNDATION", "FRONTEND", "INTEGRATION", "QA"]

# full-stack
phases = ["FOUNDATION", "BACKEND", "FRONTEND", "INTEGRATION", "QA"]

# static-site
phases = ["FOUNDATION", "CONTENT", "DEPLOYMENT", "QA"]
```

### 2. Context7 Research (WITH FALLBACK)

**Fallback Chain:** Context7 → Web Search → Brave Search → Built-in Search

**Pattern:** Use the research fallback approach for tech research:
1. Primary: Context7 (for latest framework documentation)
2. Fallback 1: mcp__web-search-prime__webSearchPrime (if Context7 unavailable)
3. Fallback 2: WebSearch (built-in, if web-search-prime quota exceeded)

For each technical area identified, use `mcp__plugin_context7_context7__query-docs`:

**If Context7 fails or is unavailable, automatically fallback to:**
```
mcp__web-search-prime__webSearchPrime(search_query="{query}")
```

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

### 3. Specification Generation (CONDITIONAL)

**Read project type first:**
```python
# Get project type from TASKS.json or run classification
project_type = get_project_type()  # from TASKS.json metadata
baas_provider = get_baas_provider()  # from CODEBASE_CONTEXT.json
```

**Conditional section generation:**

| Section | baas-fullstack | frontend-only | full-stack | static-site |
|---------|----------------|---------------|------------|-------------|
| API Specification | BaaS Integration | ❌ Skip | Standard | ❌ Skip |
| Database Schema | RLS Policies | ❌ Skip | SQL DDL | ❌ Skip |
| Component Architecture | BaaS-focused | Standard | Standard | Minimal |

**Generate specification sections based on project type:**

```python
if project_type == "baas-fullstack":
    # API Specification becomes "BaaS Integration"
    # Database Schema shows RLS policies/Firestore rules
    generate_baas_integration_section(baas_provider)
    generate_rls_policies_section()

elif project_type == "frontend-only":
    # Skip API Specification entirely
    # Skip Database Schema entirely
    # Focus on component architecture and API client

elif project_type == "full-stack":
    # Standard structure with API endpoints and SQL DDL
    generate_api_specification()
    generate_database_schema()

elif project_type == "static-site":
    # Minimal component architecture
    # No API or database sections
```

**Architecture Overview** (always generated):
- System architecture diagram/description
- Technology stack table with versions and rationale
- Design patterns to apply

**Component Architecture** (adapted based on type):
- Frontend component hierarchy
- State management approach
- Routing structure
- For BaaS: Add BaaS client integration notes

**Create comprehensive technical specification covering:**

**Architecture Overview**
- System architecture diagram/description
- Technology stack table with versions and rationale
- Design patterns to apply

**Database Schema** (if applicable)
- Entity definitions with DDL statements OR RLS policies
- Relationships and constraints
- Indexes for performance

**API Specification** (if applicable)
- For BaaS: BaaS client integration patterns
- For custom backend: All endpoints with HTTP methods
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

### 5. Output Generation (MODULAR STRUCTURE)

Generate modular specification files:

**5.1 Main TECHNICAL_SPEC.md** (architecture and stable content):
- Architecture Overview
- Technology Stack
- Design Patterns
- Database Schema
- API Specification
- Component Architecture
- Development Guidelines
- Context7 References
- Deployment Checklist

**5.2 IMPLEMENTATION_TASKS.md** (phase summaries):
- List all phases with links to detailed files
- Provide quick overview of phase structure

**5.3 PHASE_*.md files** (detailed implementation tasks):

**Phase structure based on project_type:**

```python
# Phase structure based on project_type
if project_type == "baas-fullstack":
    phases = ["FOUNDATION", "BAAS_INTEGRATION", "FRONTEND", "INTEGRATION", "QA"]
    phase_files = [
        "PHASE_1_FOUNDATION.md",
        "PHASE_2_BAAS_INTEGRATION.md",
        "PHASE_3_FRONTEND.md",
        "PHASE_4_INTEGRATION.md",
        "PHASE_5_QUALITY_ASSURANCE.md"
    ]
elif project_type == "frontend-only":
    phases = ["FOUNDATION", "FRONTEND", "INTEGRATION", "QA"]
    phase_files = [
        "PHASE_1_FOUNDATION.md",
        "PHASE_2_FRONTEND.md",
        "PHASE_3_INTEGRATION.md",
        "PHASE_4_QUALITY_ASSURANCE.md"
    ]
elif project_type == "full-stack":
    phases = ["FOUNDATION", "BACKEND", "FRONTEND", "INTEGRATION", "QA"]
    phase_files = [
        "PHASE_1_FOUNDATION.md",
        "PHASE_2_BACKEND.md",
        "PHASE_3_FRONTEND.md",
        "PHASE_4_INTEGRATION.md",
        "PHASE_5_QUALITY_ASSURANCE.md"
    ]
elif project_type == "static-site":
    phases = ["FOUNDATION", "CONTENT", "DEPLOYMENT", "QA"]
    phase_files = [
        "PHASE_1_FOUNDATION.md",
        "PHASE_2_CONTENT.md",
        "PHASE_3_DEPLOYMENT.md",
        "PHASE_4_QUALITY_ASSURANCE.md"
    ]
```

**Standard full-stack example**:
- PHASE_1_FOUNDATION.md
- PHASE_2_BACKEND.md
- PHASE_3_FRONTEND.md
- PHASE_4_INTEGRATION.md
- PHASE_5_QUALITY_ASSURANCE.md

**Directory Structure**:
```
.sam/{feature}/
├── TECHNICAL_SPEC.md          # Main spec (architecture, database, API)
├── TASKS.json                  # Task registry (auto-generated in step 6)
└── IMPLEMENTATION_TASKS.md     # Phase summaries
    ├── PHASE_1_FOUNDATION.md
    ├── PHASE_2_BACKEND.md
    ├── PHASE_3_FRONTEND.md
    ├── PHASE_4_INTEGRATION.md
    └── PHASE_5_QUALITY_ASSURANCE.md
```

**Benefits**:
- Main spec contains only stable content (rarely changes)
- Implementation tasks are phase-isolated (read only current phase)
- 98% token reduction for sam-develop (reads only current phase)

### 6. Executable Specification Generation (NEW - BMAD/SpecKit Enhancement)

**After generating TECHNICAL_SPEC.md, generate EXECUTABLE_SPEC.yaml:**

```bash
# Copy template
cp skills/sam-specs/templates/EXECUTABLE_SPEC_TEMPLATE.yaml .sam/{feature}/EXECUTABLE_SPEC.yaml

# Fill in scenarios based on user story acceptance criteria
# Parse and validate
python3 skills/sam-specs/scripts/scenario_parser.py .sam/{feature}
```

**What is an Executable Specification?**

An executable specification is a YAML file that defines:
- **Scenarios**: Given/When/Then test cases from user story acceptance criteria
- **Contract Tests**: API request/response schema validation
- **State Machines**: Complex workflow modeling (optional)
- **Decision Tables**: Business rules in tabular form (optional)

**Example Scenario from User Story:**

User Story AC: "User can sign up with email and password"

→ Becomes executable scenario:

```yaml
scenarios:
  - scenario_id: "S001"
    name: "User signup with valid credentials"
    story_mapping: "Story 001"
    acceptance_criteria: "User can sign up with email and password"

    given:
      - description: "the database is empty"
        setup:
          - action: "truncate_table"
            target: "users"

    when:
      - description: "POST /api/users with valid credentials"
        action:
          method: "POST"
          endpoint: "/api/users"
          body:
            email: "test@example.com"
            password: "SecurePass123!"

    then:
      - description: "response status is 201"
        assertion:
          type: "status_code"
          expected: 201

      - description: "database contains 1 user"
        assertion:
          type: "database_query"
          query: "SELECT COUNT(*) FROM users"
          expected: "1"
```

**Generate Tests from Scenarios:**

```bash
# Generate Jest tests
python3 skills/sam-specs/scripts/test_generator.py .sam/{feature} --framework jest

# Generate Cucumber tests
python3 skills/sam-specs/scripts/test_generator.py .sam/{feature} --framework cucumber

# Generate Pytest tests
python3 skills/sam-specs/scripts/test_generator.py .sam/{feature} --framework pytest
```

**Benefits:**
- Specifications ARE tests (not just documentation)
- Acceptance criteria become executable test cases
- Run `npm test` to verify specifications pass
- Living documentation that never drifts from implementation

### 7. Task Registry Generation (NEW - CRITICAL)

**After generating TECHNICAL_SPEC.md and EXECUTABLE_SPEC.yaml, you MUST generate TASKS.json:**

```bash
python3 skills/sam-specs/scripts/spec_parser.py .sam/{feature}
```

**This step is MANDATORY because:**
- TASKS.json enables incremental reading (98% token reduction)
- Provides fast status checks without parsing entire spec
- Enables checkpoint/resume capability for sam-develop
- Tracks line numbers for precise spec section reading
- Links tasks to acceptance criteria for shift-left verification

**TASKS.json Schema:**
```json
{
  "metadata": {
    "feature_id": "001_user_auth",
    "feature_name": "User Authentication",
    "spec_version": "2.0",
    "total_tasks": 47,
    "completed_tasks": 0,
    "current_phase": "1"
  },
  "phases": [
    {
      "phase_id": "1",
      "phase_name": "Foundation",
      "status": "pending",
      "tasks": [
        {
          "task_id": "1.1",
          "title": "Project Setup",
          "status": "pending",
          "spec_file": "TECHNICAL_SPEC.md",
          "section_start": 267,
          "section_end": 285,
          "dependencies": [],
          "story_mapping": null
        }
      ]
    }
  ],
  "checkpoint": {
    "last_completed_task": null,
    "last_checkpoint_time": null,
    "iteration_count": 0,
    "current_phase": "1",
    "active_tasks": [],
    "quality_gate_last_passed": null,
    "last_quality_gate_result": {}
  }
}
```

Report completion:
```
✅ Technical specification created: .sam/001_user_auth/TECHNICAL_SPEC.md
✅ Executable specification created: .sam/001_user_auth/EXECUTABLE_SPEC.yaml
✅ Scenario registry generated: .sam/001_user_auth/SCENARIOS.json
✅ Task registry generated: .sam/001_user_auth/TASKS.json
📚 Context7 research: 3 documentation sources queried
📋 Tasks: 24 implementation tasks with checkbox tracking
🧪 Scenarios: 8 executable test scenarios from acceptance criteria
📋 Next: Run /sam-develop to start implementation
```

### 8. Placeholder Validation (NEW - Production Safety)

**Before finalizing the specification, validate all {{VARIABLE}} placeholders:**

```bash
# Validate all placeholders in the spec
python3 skills/sam-specs/scripts/context_resolver.py .sam/{feature} --validate TECHNICAL_SPEC.md

# For strict validation (fail on missing required variables)
python3 skills/sam-specs/scripts/context_resolver.py .sam/{feature} --validate TECHNICAL_SPEC.md --strict
```

**What this checks:**
- ✅ All {{VARIABLE}} placeholders have corresponding values in CONTEXT.yaml
- ⚠️  Reports missing required variables (generation will fail)
- ⚠️  Reports missing optional variables (will become empty strings)
- 💡 Suggests default values for common variables

**Example output:**
```
📋 Validating placeholders in: TECHNICAL_SPEC.md
============================================================

Total placeholders found: 47
Resolved placeholders: 42
Missing required: 2
Missing optional: 3

❌ Missing Required Placeholders:
   - {{application.name}}
   - {{application.description}}

⚠️  Missing Optional Placeholders:
   - {{application.version}}
     Suggested value: 1.0.0
   - {{database.port}}
     Suggested value: 5432
   - {{api.timeout}}
     Suggested value: 30000

⚠️  Warnings:
   - Missing 2 required placeholder(s): generation will fail
   - Missing 3 optional placeholder(s): will be replaced with empty strings

❌ Validation failed! Missing required placeholders.
```

**If validation fails:**
1. Update `templates/CONTEXT.yaml` or `.sam/{feature}/CONTEXT.yaml` with missing values
2. Re-run validation until it passes
3. Only proceed to development when all required placeholders are resolved

**Benefits:**
- 🛡️ Prevents empty values in production specs
- 🔍 Catches configuration gaps before development starts
- 📝 Provides clear guidance on what needs to be filled in

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

---

## Section 8: Gherkin Test Generation

### Overview

Generate executable tests from Gherkin scenarios in user story files. This enables behavior-driven development (BDD) where non-technical stakeholders can read and validate test scenarios.

### When to Use

Use Gherkin test generation when:
- User stories contain behavioral scenarios in Given/When/Then format
- You need non-technical stakeholders to understand test coverage
- You want executable tests directly from acceptance criteria

### CLI Usage

```bash
# Generate tests from a single user story
python3 skills/sam-specs/scripts/gherkin_to_test.py .sam/{feature}/USER_STORIES/001_*.md

# Generate tests for all stories in a feature
python3 skills/sam-specs/scripts/gherkin_to_test.py .sam/{feature}/USER_STORIES/

# Specify output framework
python3 skills/sam-specs/scripts/gherkin_to_test.py .sam/{feature}/USER_STORIES/ --framework jest
python3 skills/sam-specs/scripts/gherkin_to_test.py .sam/{feature}/USER_STORIES/ --framework cucumber
```

### Supported Frameworks

- **Cucumber**: Generates `.feature` files and TypeScript step definitions
- **Jest-cucumber**: Generates Jest tests compatible with jest-cucumber library

### Gherkin Steps Library

Reusable Gherkin steps are available in:
```
skills/sam-specs/templates/GHERKIN_STEPS.md
```

This library provides standardized step patterns for:
- Authentication steps
- Data management steps
- API interaction steps
- UI interaction steps
- State management steps
- Error handling steps

### Example Gherkin Scenario

```gherkin
Scenario: User logs in with valid credentials
  Given I am on the login page
  When I type "user@example.com" into the email field
  And I type "password123" into the password field
  And I click on the login button
  Then I should be authenticated
  And I should be on the dashboard page
  And I should see a welcome message
```

### Output Structure

```
.sam/{feature}/
├── tests/
│   ├── cucumber/
│   │   ├── {feature_name}.feature      # Gherkin feature file
│   │   └── steps.ts                    # Step definitions
│   └── jest-cucumber/
│       └── {feature_name}.test.ts      # Jest tests
```

### Integration with Workflow

- **After** user stories are created with Gherkin scenarios
- **Before** development starts (shift-left verification)
- Tests verify acceptance criteria are implemented correctly

---

## Section 9: OpenAPI and Contract Testing

### Overview

Generate OpenAPI 3.0 specifications from API specifications and create contract tests to verify runtime compliance. This catches breaking changes before deployment.

### When to Use

Use OpenAPI generation when:
- Technical spec contains API endpoints
- You need API documentation
- You want contract testing for APIs
- You're building backend services

### CLI Usage

```bash
# Generate OpenAPI specification
python3 skills/sam-specs/scripts/openapi_generator.py .sam/{feature}

# Generate contract tests (Zod)
python3 skills/sam-specs/scripts/contract_test_generator.py .sam/{feature} --framework zod

# Generate contract tests (Pact)
python3 skills/sam-specs/scripts/contract_test_generator.py .sam/{feature} --framework pact

# Verify contracts against implementation
python3 skills/sam-specs/scripts/contract_test_generator.py .sam/{feature} --verify
```

### OpenAPI Specification

Generates `openapi.yaml` in the feature directory with:
- API endpoints from technical spec
- Request/response schemas
- Authentication requirements
- Error responses
- Server definitions

### Contract Testing Frameworks

**Zod** (Recommended for TypeScript):
- Runtime schema validation
- Type-safe contract tests
- Integrates with existing TypeScript codebase

**Pact**:
- Consumer-driven contract testing
- Provider contract verification
- Useful for microservices

**Joi**:
- Alternative schema validation
- Node.js ecosystem friendly

### Output Structure

```
.sam/{feature}/
├── openapi.yaml                        # OpenAPI specification
└── tests/
    └── contract/
        ├── zod/
        │   ├── schemas.ts              # Zod schemas
        │   ├── validators.ts           # Request/response validators
        │   └── contract.test.ts        # Contract tests
        └── pact/
            └── pact.test.ts            # Pact tests
```

### Quality Gate Integration

Contract tests should run:
- In CI/CD pipeline before deployment
- As part of sam-develop quality gates
- Before API changes are merged

### Integration with Workflow

- **After** technical spec is generated with API endpoints
- **Before** API implementation starts (defines contracts)
- Tests verify implementation matches specification

---

## Section 10: Impact Analysis

### Overview

Analyze the impact of changes using task dependencies. Generates Mermaid diagrams and impact reports showing what's affected when requirements change.

### When to Use

Use impact analysis when:
- Modifying user stories or requirements
- Planning refactoring work
- Understanding change impact before implementation
- Reviewing proposed changes

### CLI Usage

```bash
# Analyze impact of changing a specific task
python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --task 2.1.3

# Analyze impact of changing a user story
python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --story 001

# Generate visual dependency graph
python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --visualize

# Generate full impact report
python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --task 1.1 --report

# Export Mermaid graph to file
python3 skills/sam-specs/scripts/impact_analyzer.py .sam/{feature} --visualize --output deps.mmd
```

### Impact Report Contents

- **Direct Impact**: Tasks/stories immediately affected
- **Transitive Impact**: Cascading effects through dependencies
- **Affected Stories**: User stories that may need updates
- **Affected Files**: Specification files to modify
- **Risk Level**: Low/Medium/High assessment
- **Recommendations**: How to handle the change

### Risk Assessment

**Low Risk**:
- No dependent tasks
- Isolated change
- No completed tasks affected

**Medium Risk**:
- Some dependencies
- Affects pending tasks
- May require coordination

**High Risk**:
- Many dependencies
- Affects completed tasks
- Requires re-verification

### Mermaid Visualization

Generates Mermaid graphs showing:
- Task dependencies
- Phase boundaries
- Status indicators (completed/pending)
- Impact paths

View at: https://mermaid.live/

### Output Structure

```
.sam/{feature}/
├── openapi.yaml                        # OpenAPI specification
├── IMPACT_REPORT_{task_id}.md          # Impact analysis reports
└── diagrams/
    └── dependency_graph.mmd            # Mermaid diagrams
```

### Integration with Workflow

- **Before** modifying user stories or specs
- **During** planning phase
- Helps communicate change impact
- Prevents unintended breaking changes

---

## Section 11: State Machine Code Generation

### Overview

Generate executable state machine code from YAML specifications. Supports XState (TypeScript/JavaScript), Python transitions library, and Mermaid diagrams for documentation.

### When to Use

Use state machine generation when:
- Features have complex multi-step workflows
- Entities transition between different states
- Business logic requires state-dependent behavior
- You need visual documentation of workflows
- Implementing user flows, order processing, or approval workflows

### CLI Usage

```bash
# Parse the executable spec first (generates SCENARIOS.json)
python3 skills/sam-specs/scripts/scenario_parser.py .sam/{feature}

# Generate XState machines (TypeScript/JavaScript)
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework xstate

# Generate Python transitions
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework transitions

# Generate Mermaid diagrams
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework mermaid

# Generate all frameworks
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --all
```

### Supported Frameworks

**XState (TypeScript/JavaScript)**:
- Type-safe state machine definitions
- Context, events, guards, services, actions
- Nested states and parallel states
- Compatible with React, Vue, Angular

**Python Transitions**:
- Imperative state machine implementation
- Model class with state tracking
- Guard conditions and callbacks
- Django/Flask integration ready

**Mermaid Diagrams**:
- Visual state diagrams (stateDiagram-v2)
- Renderable in GitHub, GitLab, Notion
- Living documentation from source

### YAML Definition Format

Define state machines in EXECUTABLE_SPEC.yaml:

```yaml
state_machines:
  - machine_id: "SM001"
    name: "User Account State Machine"
    description: "States and transitions for user account lifecycle"
    initial_state: "pending"
    states:
      - state_id: "pending"
        name: "Pending Verification"
        on_entry:
          - send_verification_email
        transitions:
          - event: "verify_email"
            target: "verified"
            guard: "token_is_valid"
          - event: "timeout"
            target: "expired"
            after: "24h"
```

### Output Structure

```
.sam/{feature}/
└── state-machines/
    ├── xstate/
    │   ├── UserAccountStateMachine.ts    # Machine definition
    │   ├── types.ts                       # Shared types
    │   └── index.ts                       # Exports
    ├── transitions/
    │   ├── user_account_state_machine.py  # Machine implementation
    │   └── models.py                      # Model classes
    └── diagrams/
        └── user_account_state_machine.mmd # Mermaid diagram
```

### Generated XState Example

```typescript
export const UserAccountStateMachine = createMachine<
  UserAccountContext,
  UserAccountEvent
>({
  id: 'SM001',
  initial: 'pending',
  context: {
    userId: null,
    error: null,
    attempts: 0,
  },
  states: {
    pending: {
      onEntry: ['send_verification_email'],
      on: {
        verify_email: {
          target: 'verified',
          cond: 'token_is_valid',
        },
        timeout: 'expired',
      },
    },
    // ... additional states
  },
}, {
  guards: {
    token_is_valid: (context, event) => {
      // Guard implementation
    },
  },
  actions: {
    send_verification_email: (context, event) => {
      // Action implementation
    },
  },
});
```

### Testing Strategy

1. **Unit Tests**: Test guard conditions and service functions
2. **Integration Tests**: Test state transitions with various inputs
3. **Visual Tests**: Verify Mermaid diagram matches specification
4. **Edge Cases**: Test timeout scenarios, guard failures

### Validation

The generator includes automatic validation:
- Checks initial state exists
- Verifies all transitions reference valid states
- Reports missing guards or actions
- Warns about unreachable states

### Integration with Workflow

- **After** defining state machines in EXECUTABLE_SPEC.yaml
- **After** running scenario_parser.py
- **Before** implementing workflow logic
- Use generated code as implementation foundation

---

## Section 12: Decision Table Test Generation

### Overview

Generate exhaustive test cases from decision table business rules. Supports Jest (data-driven), Cucumber (scenario outlines), and Pytest (parametrize) with 100% rule coverage.

### When to Use

Use decision table generation when:
- Features have complex business rules
- Multiple conditions determine different actions
- You need comprehensive test coverage
- Implementing pricing, eligibility, or routing logic
- Business requirements can be expressed as rules

### CLI Usage

```bash
# Parse the executable spec first (generates SCENARIOS.json)
python3 skills/sam-specs/scripts/scenario_parser.py .sam/{feature}

# Generate Jest tests from decision tables
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework jest

# Generate Cucumber tests
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework cucumber

# Generate Pytest tests
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework pytest

# Generate with edge cases
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework jest --edge-cases
```

### Supported Frameworks

**Jest**:
- Data-driven tests with `describe.each()`
- Individual test cases per rule
- Type-safe test parameters
- Compatible with TypeScript projects

**Cucumber**:
- Scenario outlines with examples tables
- Human-readable test specifications
- Gherkin syntax for BDD teams
- Step definition templates

**Pytest**:
- Parameterized tests with `@pytest.mark.parametrize`
- Clean test case organization
- Python type hints
- Django/Flask compatible

### YAML Definition Format

Define decision tables in EXECUTABLE_SPEC.yaml:

```yaml
decision_tables:
  - table_id: "DT001"
    name: "Storage Allocation Decision Table"
    description: "Determine storage allocation based on user tier and age"
    inputs:
      - field: "user_tier"
        values: ["free", "premium", "enterprise"]
      - field: "age"
        values: ["<18", ">=18"]
    rules:
      - conditions:
          user_tier: "free"
          age: "<18"
        actions:
          storage_gb: 5
          require_consent: true
```

### Output Structure

```
.sam/{feature}/
└── tests/
    └── decision-tables/
        ├── jest/
        │   ├── StorageAllocation.test.ts    # Main test file
        │   └── StorageAllocation.edge.test.ts # Edge cases
        ├── cucumber/
        │   └── storage_allocation.feature   # Cucumber scenarios
        └── pytest/
            ├── test_storage_allocation.py   # Parametrized tests
            └── test_storage_allocation_edge.py # Edge cases
```

### Generated Jest Example

```typescript
describe('StorageAllocation Decision Table', () => {
  describe.each([
    ['free', '<18', true, 5, true, false],
    ['free', '<18', false, 0, true, true],
    ['premium', '>=18', null, 100, false, false],
  ])('Decision table coverage: userTier=%s, age=%s',
    (userTier, age, parentalConsent, expectedStorage,
     expectedConsent, expectedBlock) => {
    it(`should return storage=${expectedStorage}`, () => {
      const result = determineStorageAllocation({
        userTier,
        age,
        parentalConsent,
      });
      expect(result.storage_gb).toBe(expectedStorage);
    });
  });
});
```

### Edge Case Generation

With `--edge-cases` flag, automatically generates tests for:
- Boundary values (first/last items in enums)
- Null/undefined inputs
- Empty string values
- Invalid type combinations

### Coverage Reporting

The generator provides coverage metrics:
- Total rules in decision table
- Number of tests generated
- Coverage percentage
- Target: 100% (all rules tested)

### Priority-Based Testing

Tests are prioritized based on rule complexity:
- **Critical**: 3+ conditions
- **High**: 2 conditions
- **Medium**: 1 condition
- **Low**: Default/fallback rules

### Integration with Workflow

- **After** defining decision tables in EXECUTABLE_SPEC.yaml
- **After** running scenario_parser.py
- **Before** implementing business logic
- Tests verify implementation matches rules

---

## Section 13: Context Propagation

### Overview

Resolve `{{VARIABLE}}` placeholders across all templates using global and feature-specific context variables. Enables dynamic configuration and reduces hardcoding in generated code.

### When to Use

Use context propagation when:
- Templates contain configurable values
- Multiple features share common configuration
- Environment-specific values needed
- Reducing code duplication across templates

### CLI Usage

```bash
# Resolve and export context to file
python3 skills/sam-specs/scripts/context_resolver.py .sam/{feature} --export CONTEXT_RESOLVED.yaml

# Resolve placeholders in a specific file
python3 skills/sam-specs/scripts/context_resolver.py .sam/{feature} --resolve-file input.md output.md

# Validate context (show unresolved variables)
python3 skills/sam-specs/scripts/context_resolver.py .sam/{feature}
```

### Context Files

**Global Context** (`templates/CONTEXT.yaml`):
- Application-wide settings
- Technology stack versions
- Database configuration
- Authentication settings
- External service endpoints

**Feature Context** (`.sam/{feature}/CONTEXT.yaml`):
- Feature-specific overrides
- Test data defaults
- Mock service configurations
- Feature flags

### Context Resolution

Context variables use dot notation:
- `{{application.name}}` → Application name
- `{{database.host}}` → Database host
- `{{api.rate_limit.requests_per_minute}}` → Rate limit

Feature context overrides global context values.

### Example Global Context

```yaml
# templates/CONTEXT.yaml
application:
  name: "{{APP_NAME}}"
  environment: "{{ENVIRONMENT}}"
  api_url: "{{API_URL}}"

database:
  type: "{{DATABASE_TYPE}}"
  host: "{{DB_HOST}}"
  port: "{{DB_PORT}}"

auth:
  provider: "{{AUTH_PROVIDER}}"
  token_expiry: "{{TOKEN_EXPIRY}}"
```

### Example Feature Context

```yaml
# .sam/{feature}/CONTEXT.yaml
feature:
  id: "{{FEATURE_ID}}"
  name: "{{FEATURE_NAME}}"

# Override global values
database:
  tables:
    - "users"
    - "profiles"

testing:
  default_framework: "jest"
  coverage_target: 80
```

### Integration with Generators

Context resolver integrates with:
- `test_generator.py` - Resolve test configuration
- `contract_test_generator.py` - Resolve API endpoints
- `state_machine_generator.py` - Resolve timeouts and hooks
- `decision_table_test_generator.py` - Resolve test data

### Validation

Context resolver validates:
- Required top-level keys exist
- No unresolved placeholders remain
- Feature context overrides are valid
- Nested paths are accessible

### Output Structure

```
.sam/{feature}/
├── CONTEXT.yaml              # Feature-specific context
├── CONTEXT_RESOLVED.yaml     # Exported resolved context
└── resolved/                 # Resolved template files
    ├── spec.md
    ├── tests.ts
    └── config.json
```

### Best Practices

1. **Use dot notation** for nested values
2. **Define defaults** in global context
3. **Override selectively** in feature context
4. **Validate** before deployment
5. **Document** custom variables

### Integration with Workflow

- **Before** generating code from templates
- **When** environment-specific values needed
- **After** defining context variables
- Use to maintain consistency across features

---

## Section 14: E2E Test Generation (NEW)

### Overview

Generate end-to-end tests for critical user paths from user flow diagrams in USER_STORIES. Supports Playwright and Cypress frameworks with Page Object Model pattern for maintainable tests.

### When to Use

Use E2E test generation when:
- User stories contain user flow diagrams
- You need to test critical user paths
- You want to verify complete workflows end-to-end
- You need browser automation tests

### CLI Usage

```bash
# Generate Playwright E2E tests
python3 skills/sam-specs/scripts/e2e_test_generator.py .sam/{feature} --framework playwright

# Generate Cypress E2E tests
python3 skills/sam-specs/scripts/e2e_test_generator.py .sam/{feature} --framework cypress

# Generate tests for specific flows only
python3 skills/sam-specs/scripts/e2e_test_generator.py .sam/{feature} --flows "signup,checkout,auth"
```

### Output Structure

```
.sam/{feature}/tests/e2e/
├── playwright/
│   ├── pages/                   # Page Object Models
│   ├── flows/                   # User flow tests
│   ├── fixtures/                # Test data
│   └── utils.ts                 # Test utilities
└── cypress/
    ├── e2e/                     # E2E test specs
    └── support/                 # Commands and fixtures
```

### Integration with Workflow

- **After** user stories are created with user flow diagrams
- **During** test planning phase
- **Before** manual E2E test creation

---

## Section 15: Security Test Generation (NEW)

### Overview

Generate OWASP Top 10 security tests for Jest (frontend) and Pytest (backend). Covers SQL injection, XSS, CSRF, authentication bypass, and other security vulnerabilities.

### When to Use

Use security test generation when:
- Technical spec contains API endpoints
- You need to verify security controls
- You want automated security regression tests
- Preparing for security audits

### CLI Usage

```bash
# Generate Jest security tests
python3 skills/sam-specs/scripts/security_test_generator.py .sam/{feature} --framework jest

# Generate Pytest security tests
python3 skills/sam-specs/scripts/security_test_generator.py .sam/{feature} --framework pytest
```

### OWASP Top 10 Coverage

| Category | Description | Tests Generated |
|----------|-------------|-----------------|
| A01 | Broken Access Control | CSRF, privilege escalation |
| A02 | Cryptographic Failures | Data exposure, HTTPS enforcement |
| A03 | Injection | SQL injection, XSS, command injection |
| A07 | Auth Failures | Brute force, bypass attempts |
| A10 | SSRF | Server-side request forgery |

### Integration with Workflow

- **After** technical spec is generated with API endpoints
- **Before** API implementation (defines security requirements)
- **During** security review process

---

## Section 16: Test Data Generation (NEW)

### Overview

Generate realistic test data from database schema using Faker library. Supports locale-aware data generation and edge case scenarios for comprehensive testing.

### When to Use

Use test data generation when:
- Technical spec contains database schema
- Tests need realistic data instead of hardcoded values
- You need edge case test data
- Setting up test fixtures

### CLI Usage

```bash
# Generate factory for a specific entity
python3 skills/sam-specs/scripts/test_data_factory.py .sam/{feature} --generate User

# Generate seed data
python3 skills/sam-specs/scripts/test_data_factory.py .sam/{feature} --seed > seed_data.json

# Generate edge cases
python3 skills/sam-specs/scripts/test_data_factory.py .sam/{feature} --edge-cases User
```

### Output Structure

```
.sam/{feature}/tests/fixtures/
├── user.factory.ts             # TypeScript factory
├── seed_data.json              # Seed data
└── edge_cases.json             # Edge case data
```

### Integration with Workflow

- **After** database schema is defined in technical spec
- **Before** writing tests (generates test data)
- **During** test fixture setup
