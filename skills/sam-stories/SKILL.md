---
name: sam-stories
description: User story generation and verification agent. Reads feature documentation, generates INVEST-compliant user stories covering 100% of requirements, spawns verifier subagent for gap analysis, and amends until complete coverage. Use when user says "generate user stories", "create stories from feature", or "break down into stories". Follows company template format with Who/When/What title structure.
---

# User Story Generation Agent

## Overview

This skill transforms feature documentation into INVEST-compliant user stories with automatic gap verification.

## Workflow

### 1. Input Selection

If multiple features exist in `.sam/`:
```
Available features:
  001_user_auth
  002_contact_management
Which feature would you like to generate stories for?
```

Read the selected feature's `FEATURE_DOCUMENTATION.md`.

### 2. Story Decomposition

Analyze the feature documentation and identify user-centric capabilities.

**Decomposition Principles:**
- Each story should deliver standalone value
- Stories should be completable in one sprint
- Avoid technical tasks (those go in technical spec)
- Focus on user-facing behavior

### 3. Story Generation

For each identified capability, create a user story using the template.

**INVEST Compliance Check:**
- **I**ndependent: Does this story deliver value alone?
- **N**egotiable: Can details be discussed without breaking the story?
- **V**aluable: Is there clear business/user value?
- **E**stimable: Can developers estimate this?
- **S**mall: Can this be completed in one sprint?
- **T**estable: Are there clear acceptance criteria?

### 4. Verification Loop

Spawn a verifier subagent with this prompt:

```
You are a story verification agent. Compare the generated user stories
against the feature documentation and identify any gaps.

Feature documentation: {path to FEATURE_DOCUMENTATION.md}
Generated stories: {list of story files}

Report:
1. Requirements in feature doc not covered by any story
2. Stories that don't map to feature requirements
3. Missing acceptance criteria
4. Incomplete edge case coverage

Be thorough - we require 100% coverage.
```

### 5. Gap Closure

If the verifier finds gaps:
1. Create additional stories to cover missing requirements
2. Amend existing stories with missing acceptance criteria
3. Add edge cases to appropriate stories
4. Re-run verification until 100% coverage confirmed

### 6. Output Generation

Create `.sam/{XXX_feature_name}/USER_STORIES/` directory.

Generate numbered story files:
- `001_basic_login.md`
- `002_social_login.md`
- `003_password_reset.md`
- etc.

Report completion:
```
✅ Generated 5 user stories for feature: 001_user_auth
📁 Location: .sam/001_user_auth/USER_STORIES/
✅ Verification: 100% coverage confirmed
📋 Next: Run /sam-specs to generate technical specifications
```

## Title Format

Use the Who/When/What structure:

```
**As a** {Who},
**When** {condition trigger},
**I can** {action verb} {What}.
```

Examples:
- "As a registered user, when I forget my password, I can reset it via email"
- "As a new visitor, when I arrive on the landing page, I can sign up with Google"

## Key Principles

- **100% coverage**: Every requirement in feature doc must map to a story
- **User-centric**: Stories focus on user behavior, not technical implementation
- **Independent**: Stories should be shufflable without breaking dependencies
- **Testable**: Every story has clear, observable acceptance criteria
- **Verification**: Always spawn verifier subagent before declaring complete

## Output Format Requirement

You MUST generate each USER STORY file following THIS EXACT STRUCTURE:

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

---

## CRITICAL: Phase Boundaries

DO NOT include these sections in USER STORY files:
- ❌ Feature-level problem statements → Use `/sam-discover` output instead
- ❌ Database Schema with CREATE TABLE statements → Use `/sam-specs` instead
- ❌ API Endpoint specifications with full request/response → Use `/sam-specs` instead
- ❌ Implementation task checklists → Use `/sam-specs` instead
- ❌ Industry best practices research → Use `/sam-discover` output instead

User stories are about BEHAVIOR and ACCEPTANCE CRITERIA.
Technical specifications are for subsequent phases.

## Template Reference

The template at `/templates/stories/USER_STORY_TEMPLATE.md` defines the canonical structure.
This skill embeds the EXACT structure above in "## Output Format Requirement" to ensure strict adherence.
