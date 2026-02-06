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

### 1. Task Planning (MODULAR SPEC READING)

1. **Read codebase context:**
   ```
   .sam/CODEBASE_CONTEXT.md
   ```
   Extract existing patterns, reusable components, and architecture conventions.

2. **Read TASKS.json from `.sam/{feature_id}/`**:
   ```bash
   python3 skills/sam-develop/scripts/task_registry.py read .sam/{feature_id}
   ```

3. **Read project type from TASKS.json metadata** (NEW):
   ```python
   project_type = registry.get_project_type()  # e.g., "baas-fullstack", "frontend-only"
   phase_structure = registry.get_phase_structure(project_type)  # e.g., ["1", "2", "3", "4"]
   ```
   - Phase count varies by project_type (3-5 phases)
   - Use phase_structure to adapt task planning

4. **Identify current phase** from TASKS.json checkpoint

5. **Read only current phase's PHASE_*.md file**:
   - If current_phase = "1", read IMPLEMENTATION_TASKS/PHASE_1_FOUNDATION.md
   - If current_phase = "2" and project_type = "baas-fullstack", read PHASE_2_BAAS_INTEGRATION.md
   - If current_phase = "2" and project_type = "full-stack", read PHASE_2_BACKEND.md
   - etc. (Phase names vary by project type)

6. **Load relevant sections from main TECHNICAL_SPEC.md**:
   - Architecture Overview (once, at start)
   - Database Schema (if backend phase or BaaS integration)
   - API Specification (if backend phase, skip for frontend-only)
   - BaaS Integration (if project_type = "baas-fullstack")
   - Component Architecture (if frontend phase)

7. **Parse checkbox tasks from current phase only**

8. **Identify uncompleted tasks** (checkboxes with `[ ]`)

9. **Prioritize tasks based on dependencies**

10. **Pattern Validation:** Before spawning subagents, verify:
   - New code follows existing patterns from CODEBASE_CONTEXT.md
   - Reusable components are referenced, not recreated
   - Tech stack versions are compatible
   - Architecture aligns with existing conventions

**If TASKS.json or modular files are missing**:
- Fall back to reading entire TECHNICAL_SPEC.md (legacy mode)
- Log warning: "Modular spec structure not found, using legacy mode"
- Consider migrating: `python3 scripts/migrate_spec.py .sam/{feature_id}`

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

**AUTONOMOUS EXECUTION MANDATE**: This skill operates in FULLY AUTONOMOUS mode.
You MUST continue execution WITHOUT stopping or asking for confirmation unless
you encounter a CRITICAL BLOCKER (defined below). When in doubt: KEEP GOING.

**Loop Condition**:
```
while (uncompleted_checkboxes_exist in TECHNICAL_SPEC.md):
    execute_sections_3_1_through_3_8()
```

**CRITICAL BLOCKER DEFINITION** (ONLY stop for these):
- 🔴 CRITICAL BLOCKER: External service is DOWN (API returns 500/502/503, confirmed not transient)
- 🔴 CRITICAL BLOCKER: Required credentials/keys are MISSING and CANNOT be obtained from:
  - Environment variables, .env files, documentation, .sam/{feature_id}/ directory
- 🔴 CRITICAL BLOCKER: Git repository state is CORRUPTED

**MUST NOT STOP FOR** (Continue autonomous execution):
- ✅ Minor linting/type/build/test errors → Fix and continue
- ✅ Missing dependencies → Install and continue
- ✅ Ambiguous requirements → Make best interpretation, document, continue
- ✅ Architecture decisions → Make decision based on best practices, document, continue
- ✅ Verification gaps → Create fix tasks and continue loop

#### 3.1 Task Planning (Each Loop Iteration) - INCREMENTAL READING

**CRITICAL**: Use TASKS.json for 98% token reduction. DO NOT read entire spec.

1. **Read TASKS.json first**:
   ```bash
   python3 skills/sam-develop/scripts/task_registry.py read .sam/{feature_id}
   ```

2. **Get pending tasks from registry**:
   - Filter to ONLY uncompleted tasks (status: "pending")
   - Identify parallelizable tasks (no dependencies on incomplete tasks)

3. **Incrementally read spec sections**:
   - For each pending task, read ONLY its section from TECHNICAL_SPEC.md
   - Use line numbers from TASKS.json (section_start, section_end)
   - DO NOT read the entire file

4. **Respect parallel limits**:
   - Maximum 3 parallel subagents per iteration (configurable via SAM_MAX_PARALLEL_SUBAGENTS)
   - Only spawn tasks that are truly independent

**Example incremental reading**:
```python
# Instead of reading entire spec (5,000-10,000 tokens)
full_spec = read_file("TECHNICAL_SPEC.md")  # ❌ DON'T DO THIS

# Read only what you need (~100-500 tokens)
task = registry.get_task("1.1")
task_spec = read_lines("TECHNICAL_SPEC.md", task.section_start, task.section_end)  # ✅ DO THIS
```

**If NO uncompleted tasks remain**:
- Verify via TASKS.json: `coverage_percent == 100`
- Proceed to Section 4 (Verification Phase)
- DO NOT create additional tasks

**If TASKS.json is missing**:
- Fall back to reading entire TECHNICAL_SPEC.md (legacy mode)
- Generate TASKS.json: `python3 skills/sam-specs/scripts/spec_parser.py .sam/{feature_id}`
- Use registry for next iteration

#### 3.2 Spawn Parallel Subagents (WITH LIMITS)

For the CURRENT iteration's parallel task group:

**PARALLEL LIMITS (CRITICAL)**:
- **Maximum 3 parallel subagents per iteration** (default)
- Configurable via `SAM_MAX_PARALLEL_SUBAGENTS` environment variable
- Respect dependencies from TASKS.json
- Only spawn truly independent tasks

**Get parallel limit**:
```python
import os
max_parallel = int(os.environ.get('SAM_MAX_PARALLEL_SUBAGENTS', '3'))
```

**Example with 3 parallel limit**:
```python
# Get 3 independent tasks
pending = registry.get_pending_tasks()
independent = [t for t in pending if not t.dependencies]

# Spawn only 3 at a time
for batch in chunks(independent, max_parallel):
    spawn_parallel_subagents(batch)
    wait_for_all_complete()
    update_checkpoints()
```

**SUBAGENT AUTONOMOUS EXECUTION RULES**:
- Each subagent MUST complete its task WITHOUT asking for confirmation
- If issues encountered → Attempt autonomous resolution (up to 3 retries)
- Document issues, create fix tasks if unable to resolve
- DO NOT ask "Should I do X?" → Just do X
- DO NOT ask "Which approach?" → Choose best practice

1. **Spawn Subagents**: Launch up to max_parallel subagents simultaneously using Task tool
2. **Implementation**: Each subagent:
   - Reads assigned task requirements from current phase's PHASE_*.md
   - Implements the code
   - Runs `./skills/sam-develop/scripts/lint_build_test.sh`
   - Updates checkboxes: `[ ]` → `[x]` using Edit tool
   - Updates TASKS.json: `python3 task_registry.py update .sam/{feature} {task_id} --status completed`
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

#### 3.4 Update Checkboxes and Task Registry (NEW)

**After each task completes successfully, you MUST update BOTH files:**

1. **Update TECHNICAL_SPEC.md**:
   - Read the file
   - Locate the specific checkbox
   - Update: `[ ]` → `[x]`
   - Add completion note with timestamp
   ```markdown
   - [x] Implement POST /api/users
     - Maps to: Story 001 (AC: User can sign up)
     - Completed: 2025-02-06
   ```

2. **Update TASKS.json** (CRITICAL for checkpoint/resume):
   ```bash
   python3 skills/sam-develop/scripts/task_registry.py update .sam/{feature_id} {task_id} --status completed
   ```

**This dual update ensures:**
- Visual progress in spec file
- Fast state tracking in registry
- Resume capability if interrupted
- Accurate coverage reporting

#### 3.5 MANDATORY QUALITY GATE CHECKPOINT

**CRITICAL**: Before EVERY loop iteration, you MUST:

1. **Run ALL Quality Checks**:
   ```bash
   ./skills/sam-develop/scripts/lint_build_test.sh
   ```

2. **Verify Check Results**:
   - If ALL pass → Proceed to step 3
   - If ANY fails → Fix, re-run, DO NOT proceed until ALL pass

3. **Update TASKS.json checkpoint with quality gate results**:
   ```bash
   python3 skills/sam-develop/scripts/task_registry.py update .sam/{feature_id} {task_id} --status completed
   ```

   Then manually update checkpoint with quality gate results:
   ```json
   {
     "checkpoint": {
       "quality_gate_last_passed": "2025-02-06T14:30:00Z",
       "last_quality_gate_result": {
         "linting": "passed",
         "type_check": "passed",
         "build": "passed",
         "tests": "passed"
       }
     }
   }
   ```

4. **Update TECHNICAL_SPEC.md Progress**:
   - Mark completed tasks as `[x]`
   - Add completion notes with timestamp
   - Save the file

**QUALITY GATE RESULTS MUST BE**:
- ✅ Linting: PASSED (0 errors, 0 warnings)
- ✅ Type Checking: PASSED (0 type errors)
- ✅ Build: PASSED (successful compilation)
- ✅ Unit Tests: PASSED (all tests passing)
- ✅ E2E Tests: PASSED (or N/A if not configured)

**Quality gate tracking in TASKS.json enables**:
- Resume from last known good state
- Audit trail of quality checks
- Debug failed iterations by examining checkpoint history

#### 3.6 Check Loop Condition (UPDATED)

**After each iteration, explicitly check via TASKS.json**:
```bash
python3 skills/sam-develop/scripts/task_registry.py read .sam/{feature_id}
```

**Or use checkpoint command**:
```bash
python3 skills/sam-develop/scripts/task_registry.py checkpoint .sam/{feature_id} --task {last_completed_task_id}
```

**Decision**:
- If `coverage_percent == 100`: All tasks complete → EXIT loop and proceed to Section 4
- If `coverage_percent < 100`: Uncompleted tasks remain → RETURN to Section 3.1

**Checkpoint saves**:
- Last completed task ID
- Current timestamp
- Iteration count (incremented automatically)
- Current phase
- Active tasks (if any)

#### 3.7 Checkpoint and Resume Capability (NEW)

**Enhanced TASKS.json checkpoint schema**:
```json
{
  "checkpoint": {
    "last_completed_task": "2.1.3",
    "last_checkpoint_time": "2025-02-06T14:30:00Z",
    "iteration_count": 15,
    "current_phase": "2",
    "active_tasks": ["2.1.4", "2.1.5", "2.2.1"],
    "quality_gate_last_passed": "2025-02-06T14:25:00Z",
    "last_quality_gate_result": {
      "linting": "passed",
      "type_check": "passed",
      "build": "passed",
      "tests": "passed"
    }
  }
}
```

**Resume Logic**:
- On start: Check for TASKS.json checkpoint
- If exists: Load checkpoint, resume from `last_completed_task`
- If missing: Start from beginning, create initial checkpoint

**Resume command**:
```bash
python3 skills/sam-develop/scripts/task_registry.py resume .sam/{feature_id}
```

Output:
```
Resume Information:
  Last Completed: 2.1.3
  Current Phase: 2
  Progress: 12/47 (26%)
  Active Tasks: 2.1.4, 2.1.5, 2.2.1

Next Tasks (Phase 2):
  - 2.1.4: Add authentication middleware
  - 2.1.5: Add error handling middleware
  - 2.2.1: Implement user service
```

#### 3.8 Handle Failures

**For failed quality gates**:
- Create specific fix task
- Add as new checkbox in TECHNICAL_SPEC.md
- Add to TASKS.json using update command
- Continue loop with fix task
- DO NOT pause or ask for confirmation

**For CRITICAL BLOCKERS only** (see definition in Section 3):
- Document the blocker
- Save checkpoint with error state
- PAUSE and ask user for guidance
- Do NOT exit the loop

#### 3.9 Loop Back Instruction

**Decision**:
- If `coverage_percent == 100`: All tasks complete → EXIT loop and proceed to Section 4
- If `coverage_percent < 100`: Uncompleted tasks remain → **RETURN to Section 3.1 WITHOUT ASKING**

**IMPORTANT**: The transition from 3.9 back to 3.1 is AUTOMATIC.
- ❌ DO NOT ask for confirmation
- ❌ DO NOT report status
- ❌ DO NOT pause for any reason
- ✅ IMMEDIATELY continue to 3.1

### 4. Verification Phase (ONLY After 100% Completion)

**IMPORTANT**: Only run this AFTER Section 3 loop is complete (all checkboxes are `[x]`).

#### 4.1 MANDATORY PRE-VERIFICATION QUALITY GATES

**CRITICAL**: Before running ANY verification checks, you MUST:

1. **Run Complete Quality Gate Suite**:
   ```bash
   ./skills/sam-develop/scripts/lint_build_test.sh
   ```

2. **IF ANY CHECK FAILS**:
   - DO NOT proceed to verification
   - Create fix task checkboxes
   - Return to Section 3.1
   - Complete fix tasks
   - Only return to Section 4 when ALL pass

3. **Only when ALL quality gates pass** → Proceed to Section 4.2

Spawn a code verifier subagent that checks:

#### 4.2 Coverage Checks

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

#### 4.3 Gap Closure Loop

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

### AUTONOMOUS ERROR RESOLUTION MANDATE

**CRITICAL**: ALL errors MUST be resolved autonomously. DO NOT ask user for help
unless you've exhausted ALL autonomous resolution options (3+ retry attempts).

**If linting fails**:
1. Identify specific errors
2. Fix autonomously (add imports, fix syntax, resolve types)
3. Re-run linting
4. If still failing after 3 attempts → Create fix task checkbox, continue

**If type checking fails**:
1. Identify type errors
2. Fix autonomously (add type annotations, fix mismatches)
3. Re-run type checking
4. If still failing after 3 attempts → Create fix task checkbox, continue

**If build fails**:
1. Identify build errors
2. Fix autonomously (resolve compilation issues)
3. Re-run build
4. If still failing after 3 attempts → Create fix task checkbox, continue

**If tests fail**:
1. Identify failing tests
2. Determine if test or implementation is wrong
3. Fix autonomously based on best practices
4. Re-run tests
5. If still failing after 3 attempts → Create fix task checkbox, continue

**If E2E tests fail**:
1. Identify failing scenarios
2. Debug autonomously
3. Fix implementation or update test
4. Re-run E2E tests
5. If still failing after 3 attempts → Create fix task checkbox, continue

**If credentials/keys are missing**:
1. Search for credentials in: env vars, .env files, docs, .sam/{feature_id}/
2. If found → Use and continue
3. If NOT found after exhaustive search → **CRITICAL BLOCKER** → PAUSE and ask user

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
