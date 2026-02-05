---
name: sam-develop
description: Development & verification skill for SAM workflow. Orchestrates parallel development execution, tracks progress via checkbox updates, and verifies complete coverage against specifications. Spawns multiple subagents for independent tasks to maximize parallelism. Use when user says "start development", "implement feature", "execute tasks", or "continue development".
---

# sam-develop: Development & Verification Skill

## Overview

Phase 4 of the SAM (Specs → Stories → Development) workflow. This skill orchestrates parallel development execution, tracks progress via checkbox updates, and verifies complete coverage against specifications.

## Trigger Phrases

- "start development"
- "implement feature"
- "execute tasks"
- "continue development"

## Usage

```bash
/sam-develop [feature_id]
```

## Workflow

### 1. Task Planning

1. Read `TECHNICAL_SPEC.md` from `.sam/{feature_id}/`
2. Parse all checkbox tasks from the specification
3. Identify uncompleted tasks (checkboxes with `[ ]`)
4. Prioritize tasks based on dependencies

### 2. Parallel Development Strategy

**Key Principle**: Spawn multiple subagents for independent tasks to maximize parallelism.

**Task Independence Check:**
- No dependencies on other incomplete tasks
- Self-contained (doesn't require shared state coordination)
- Can be verified independently

**Example Parallelizable Tasks:**
```
Parallel Group 1 (Foundation):
- Setup project
- Configure linting
- Set up type checking

Parallel Group 2 (Backend):
- Implement POST /api/users
- Implement GET /api/users
- Implement PUT /api/users/:id

Parallel Group 3 (Frontend):
- Create LoginForm component
- Create SignupForm component
- Create PasswordResetForm component
```

### 3. MAIN DEVELOPMENT LOOP (Repeat Until All Tasks Complete)

**CRITICAL INSTRUCTION**: This entire section MUST repeat until ALL checkboxes are `[x]`.
DO NOT proceed to Section 4 until 100% of tasks are complete.

**Loop Condition**:
```
while (uncompleted_checkboxes_exist in TECHNICAL_SPEC.md):
    execute_sections_3_1_through_3_7()
```

**Stopping Rules**:
- ✅ CONTINUE if: Any `[ ]` checkboxes remain in TECHNICAL_SPEC.md
- ⚠️ PAUSE and ask user if: Blocked by external dependency (API down, credentials needed, architecture decision required)
- ❌ DO NOT STOP if: Verification shows gaps → Create fix tasks as new checkboxes and continue loop

#### 3.1 Task Planning (Each Loop Iteration)

1. Read `TECHNICAL_SPEC.md` from `.sam/{feature_id}/`
2. Parse ALL checkbox tasks using regex pattern `- \[([ x])\]`
3. Filter to ONLY uncompleted tasks (`[ ]` checkboxes)
4. Identify parallelizable tasks (no dependencies on incomplete tasks)

**If NO uncompleted tasks remain**:
- Verify ALL checkboxes are `[x]`
- Proceed to Section 4 (Verification Phase)
- DO NOT create additional tasks

#### 3.2 Spawn Parallel Subagents

For the CURRENT iteration's parallel task group:

1. **Spawn Subagents**: Launch multiple subagents simultaneously using Task tool
2. **Implementation**: Each subagent:
   - Reads assigned task requirements from TECHNICAL_SPEC.md
   - Implements the code
   - Runs `./skills/sam-develop/scripts/lint_build_test.sh`
   - Updates checkboxes: `[ ]` → `[x]` using Edit tool
3. **Report Results**: Each subagent reports:
   - Completed tasks
   - Failed checks
   - Issues encountered

#### 3.3 Quality Gates (After Each Subagent)

Run mandatory checks after each task completion:
```bash
./skills/sam-develop/scripts/lint_build_test.sh
```

**If ANY check fails**:
- Fix the failure
- Re-run the failed check
- DO NOT mark task as `[x]` until all checks pass
- DO NOT proceed to next task until current task passes

#### 3.4 Update Checkboxes

After each task completes successfully:
1. Read the TECHNICAL_SPEC.md file
2. Locate the specific checkbox
3. Update: `[ ]` → `[x]`
4. Optionally add completion note:
   ```markdown
   - [x] Implement POST /api/users
     - Maps to: Story 001 (AC: User can sign up)
     - Completed: 2025-02-05
   ```

#### 3.5 Check Loop Condition

**After each iteration, explicitly check**:
```bash
grep -c '\[ \]' .sam/{feature_id}/TECHNICAL_SPEC.md
```

**Decision**:
- If count = 0: All tasks complete → EXIT loop and proceed to Section 4
- If count > 0: Uncompleted tasks remain → RETURN to Section 3.1

#### 3.6 Handle Failures

**For failed quality gates**:
- Create specific fix task
- Add as new checkbox in TECHNICAL_SPEC.md
- Continue loop with fix task

**For blocking issues**:
- Document the blocker
- PAUSE and ask user for guidance
- Do NOT exit the loop

#### 3.7 Loop Back Instruction

**CRITICAL**: After completing sections 3.1 through 3.6:
1. Re-read TECHNICAL_SPEC.md
2. Count uncompleted checkboxes
3. **If any `[ ]` remain: RETURN to Section 3.1**
4. **If all `[x]`: Proceed to Section 4**

### 4. Verification Phase (ONLY After 100% Completion)

**IMPORTANT**: Only run this AFTER Section 3 loop is complete (all checkboxes are `[x]`).

Spawn a code verifier subagent that checks:

#### 4.1 Coverage Checks

1. **User Story Coverage**
   - Parse all user story acceptance criteria from `.sam/{feature_id}/USER_STORIES/*.md`
   - Verify each criterion is implemented in code
   - Report any gaps

2. **Technical Spec Coverage**
   - Verify all checkbox tasks are `[x]`
   - Verify all API endpoints are implemented
   - Verify all components are created
   - Report any gaps

3. **Code Quality Standards**
   - Linting passes: `npm run lint` ✓
   - Type checking passes: `npm run type-check` ✓
   - Build succeeds: `npm run build` ✓
   - Tests pass: `npm test` ✓

4. **Browser Automation Tests**
   - Run E2E tests: `npm run test:e2e`
   - Verify user flows work end-to-end

#### 4.2 Gap Closure Loop

If verification finds gaps:

```
while (gaps_exist):
    create_fix_tasks()
    add_fix_tasks_as_checkboxes_in_TECHNICAL_SPEC()
    RETURN_to_Section_3_1()
```

**DO NOT proceed to Section 5 until**:
- All gaps are closed
- All fix tasks are complete
- Coverage is 100%

### 5. Verification Report

Generate `.sam/{feature_id}/VERIFICATION_REPORT.md`:

```markdown
# Verification Report: {{FEATURE_NAME}}

## Summary
- Feature ID: {{FEATURE_ID}}
- Verified: {{DATE}}
- Coverage: {{PERCENTAGE}}%
- Status: {{PASSED/FAILED}}

## User Story Coverage
- Total Stories: {{NUM}}
- Covered: {{NUM}}
- Gaps: {{NUM}}

## Technical Spec Coverage
- Total Tasks: {{NUM}}
- Completed: {{NUM}}
- Gaps: {{NUM}}

## Code Quality
- Linting: ✓ PASSED
- Type Checking: ✓ PASSED
- Build: ✓ PASSED
- Unit Tests: ✓ PASSED ({{COVERAGE}}% coverage)
- E2E Tests: ✓ PASSED

## Gaps Found
{{GAPS_LIST_OR_NONE}}

## Recommendation
{{READY_FOR_DEPLOYMENT_OR_NEEDS_WORK}}
```

### 6. FINAL COMPLETION CHECK

Before reporting completion:

1. **Re-read TECHNICAL_SPEC.md**
2. **Count uncompleted checkboxes**:
   ```bash
   grep -c '\[ \]' .sam/{feature_id}/TECHNICAL_SPEC.md
   ```
3. **If count > 0**:
   - ❌ DO NOT generate completion summary
   - ❌ DO NOT report as complete
   - ✅ **RETURN to Section 3.1 and complete remaining tasks**
4. **If count == 0**:
   - ✅ All quality checks pass
   - ✅ Verification report shows 100% coverage
   - ✅ Proceed to completion summary

### 7. Completion Summary

```
✅ Development complete: {{FEATURE_ID}}

Statistics:
• Tasks Completed: {{NUM}}/{{NUM}}
• User Stories Covered: {{NUM}}/{{NUM}}
• Code Coverage: {{PERCENTAGE}}%
• Quality Checks: All Passed ✓

Verification Report: .sam/{{FEATURE_ID}}/VERIFICATION_REPORT.md

Next Steps:
• Create pull request
• Deploy to staging
• Monitor metrics
```

## Development Scripts

### lint_build_test.sh

Comprehensive quality check script executed after each task:

```bash
#!/bin/bash
set -e

echo "▶️ Linting..."
npm run lint

echo "▶️ Type Checking..."
npm run type-check

echo "▶️ Building..."
npm run build

echo "▶️ Running Tests..."
npm test

echo "▶️ Browser Automation..."
npm run test:e2e

echo "✅ All checks passed!"
```

### verify_coverage.py

Python script to verify coverage against specifications:

```python
#!/usr/bin/env python3
"""Verify code coverage against specifications."""

import sys
import re
from pathlib import Path

def parse_checkboxes(spec_file):
    """Parse all checkbox tasks from spec."""
    content = spec_file.read_text()
    tasks = re.findall(r'- \[([ x])\] (.+)', content)
    completed = sum(1 for status, _ in tasks if status == 'x')
    total = len(tasks)
    return completed, total

def parse_acceptance_criteria(stories_dir):
    """Parse all acceptance criteria from stories."""
    criteria = []
    for story_file in Path(stories_dir).glob("*.md"):
        content = story_file.read_text()
        # Extract acceptance criteria
        ac = re.findall(r'- \[([ x])\] (.+)', content)
        criteria.extend(ac)
    return criteria

def verify_coverage(feature_dir):
    """Verify complete coverage."""
    spec_file = feature_dir / "TECHNICAL_SPEC.md"
    stories_dir = feature_dir / "USER_STORIES"

    completed, total = parse_checkboxes(spec_file)
    spec_coverage = (completed / total * 100) if total > 0 else 0

    gaps = []
    if spec_coverage < 100:
        gaps.append(f"Spec tasks: {completed}/{total} complete ({spec_coverage:.0f}%)")

    if gaps:
        print("❌ Coverage gaps found:")
        for gap in gaps:
            print(f"  - {gap}")
        return False
    else:
        print("✅ 100% coverage verified!")
        return True

if __name__ == "__main__":
    feature_dir = Path(".cdd") / sys.argv[1]
    success = verify_coverage(feature_dir)
    sys.exit(0 if success else 1)
```

## Checkbox Update Protocol

After completing a task:

1. **Read the spec**: Locate the specific checkbox
2. **Update the checkbox**: Change `[ ]` to `[x]`
3. **Add completion note**: Optionally add when completed

```markdown
- [x] Implement POST /api/users
  - Maps to: Story 001 (AC: User can sign up with email and password)
  - Completed: 2025-01-15
```

## Parallel Development Patterns

### Pattern 1: Component Development

**Independent Components** (can be parallelized):
```
Subagent 1: Create LoginForm
Subagent 2: Create SignupForm
Subagent 3: Create PasswordResetForm
```

**Shared Components** (sequential):
```
Task 1: Create Button component
Task 2: Create Form wrapper (depends on Button)
```

### Pattern 2: API Endpoints

**CRUD Operations** (can be parallelized):
```
Subagent 1: Implement POST /api/users
Subagent 2: Implement GET /api/users
Subagent 3: Implement PUT /api/users/:id
Subagent 4: Implement DELETE /api/users/:id
```

**Dependent Endpoints** (sequential):
```
Task 1: Implement POST /api/auth/login
Task 2: Implement POST /api/auth/refresh (depends on login tokens)
```

### Pattern 3: Testing

**Test Writing** (can be parallelized):
```
Subagent 1: Write unit tests for services
Subagent 2: Write integration tests for API
Subagent 3: Write E2E tests for user flows
```

## Success Criteria

Development phase is complete when:

- [ ] All checkbox tasks are marked `[x]`
- [ ] All user story acceptance criteria are implemented
- [ ] Linting passes: `npm run lint` ✓
- [ ] Type checking passes: `npm run type-check` ✓
- [ ] Build succeeds: `npm run build` ✓
- [ ] All tests pass: `npm test` ✓
- [ ] E2E tests pass: `npm run test:e2e` ✓
- [ ] Verification report shows 100% coverage
- [ ] No critical gaps identified

## Error Handling

**If linting fails:**
- Identify specific linting errors
- Fix issues in code
- Re-run linting
- Continue after passing

**If type checking fails:**
- Identify type errors
- Add type annotations
- Fix type mismatches
- Re-run type checking

**If build fails:**
- Identify build errors
- Fix compilation issues
- Re-run build

**If tests fail:**
- Identify failing tests
- Determine if test or implementation is wrong
- Fix accordingly
- Re-run tests

**If E2E tests fail:**
- Identify failing scenarios
- Debug with browser DevTools
- Fix implementation or update test
- Re-run E2E tests

## Dependencies

- Read tool (for reading spec)
- Edit tool (for updating checkboxes)
- Task tool (for spawning subagents)
- Bash tool (for running lint/build/test)
- Write tool (for verification report)

## Reference Materials

- Development Guidelines: `references/development-guidelines.md`
- Scripts: `scripts/lint_build_test.sh`, `scripts/verify_coverage.py`

## Examples

### Example 1: Simple Feature

**Feature**: Password Reset

**Parallel Development**:
```
Cycle 1:
- Subagent 1: Create database schema
- Subagent 2: Implement POST /api/password-reset/request

Cycle 2:
- Subagent 1: Implement POST /api/password-reset/confirm
- Subagent 2: Create request form component
- Subagent 3: Create new password form component

Cycle 3:
- Subagent 1: Write tests
- Subagent 2: E2E tests
```

### Example 2: Complex Feature

**Feature**: User Authentication

**Parallel Development**:
```
Cycle 1 (Foundation):
- Subagent 1: Setup project
- Subagent 2: Create database schema
- Subagent 3: Configure auth library

Cycle 2 (Backend - Parallel):
- Subagent 1: POST /api/auth/signup
- Subagent 2: POST /api/auth/login
- Subagent 3: POST /api/auth/logout

Cycle 3 (Frontend - Parallel):
- Subagent 1: SignupForm component
- Subagent 2: LoginForm component
- Subagent 3: Auth state management

Cycle 4 (Integration):
- Subagent 1: E2E tests
- Subagent 2: Error handling
- Subagent 3: Loading states
```

## Handoff to Deployment

When development is complete:

```
✅ Development complete: {feature_id}

All tasks completed and verified.

Verification Report: .sam/{feature_id}/VERIFICATION_REPORT.md

Ready for:
• Code review
• Pull request
• Deployment
```

---

## CRITICAL: Phase Boundaries

DO NOT include these during development:
- ❌ New feature discovery or requirements gathering → Use `/sam-discover` instead
- ❌ Writing user stories → Use `/sam-stories` instead
- ❌ Creating technical specifications → Use `/sam-specs` instead
- ❌ Modifying templates or changing the SAM workflow

Development is about IMPLEMENTING the approved specs.
Uncertainties should be documented, not resolved by scope creep.

If uncertainties arise during implementation:
1. Document the uncertainty in comments or task notes
2. Implement based on the best interpretation of the spec
3. Note any clarifications needed for future iterations
4. DO NOT rewrite the spec or user stories during development
