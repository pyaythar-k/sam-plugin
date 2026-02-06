# User Story: {Title}

## Metadata
- **Story ID**: {XXX}
- **Feature**: {Feature Name}
- **Status**: Draft | Ready | In Progress | Completed
- **Priority**: {Must Have | Should Have | Could Have}
- **Estimate**: {Points}
- **Created**: {Date}

---

## Title

**As a** {Who},
**When** {condition trigger},
**I can** {action verb} {What}.

---

## Why

{User problem being solved and business value created}

---

## Acceptance Criteria

### Functional Requirements
- [ ] {Criterion 1 - user-observable behavior}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

### Business Rules
- [ ] {Business rule 1}
- [ ] {Business rule 2}

### Edge Cases Covered
- [ ] {Edge case 1 handling}
- [ ] {Edge case 2 handling}

### Definition of Done
- [ ] All acceptance criteria met
- [ ] Code reviewed
- [ ] Tests pass
- [ ] Documentation updated

---

## Behavioral Scenarios (Gherkin)

*(Optional)* Use this section to define behavior-driven test scenarios that non-technical stakeholders can understand and validate. These scenarios follow the Given-When-Then format and can be converted to automated tests.

### Scenario 1: {Scenario Name}

**Given** the system is in the initial state
  **And** {additional precondition}
**When** I {action}
**Then** {expected outcome}
  **And** {additional outcome}

### Scenario Outline: {Parameterized Scenario}

Use scenario outlines when you need to test the same behavior with multiple combinations of inputs.

**Given** a <user_type> with <status>
**When** I request <resource>
**Then** I should receive <response_code>

| Examples: |
| user_type | status | resource | response_code |
| admin | active | /api/users | 200 |
| guest | inactive | /api/users | 401 |
| member | suspended | /api/users | 403 |

---

## Technical Considerations

## Technical Considerations

### Implementation Approach
{Technical guidance for developers}

### Performance Notes
{Performance considerations}

### Security Notes
{Security requirements}

---

## Design

### Screens/Wireframes
{Attach or link to designs}

### UI Components
{List components to be used}

### User Interactions
{Describe user interaction patterns}

---

## Resources

### API Endpoints
{Required API documentation}

### Data Models
{Data structure requirements}

### Dependencies
{Other stories or features this depends on}

### References
{Links to relevant documentation}
