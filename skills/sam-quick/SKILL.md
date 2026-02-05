---
name: sam-quick
description: Quick task handler for small features, bug fixes, and chores. Validates if request is actually small - if not, refers to /sam-discover. Skips full three-tier workflow for fast turnaround on trivial tasks.
---

# sam-quick: Small Feature & Bug Fix Handler

## Overview

Lightweight workflow for small tasks that don't require the full three-tier discovery process.

## Trigger Phrases

- "quick fix"
- "small change"
- "minor bug"
- "simple task"
- /sam-quick

## Workflow

### 1. Size Validation

**CRITICAL**: First, validate whether the request is actually small.

Ask yourself these questions:
1. Can this be described in 1-2 sentences?
2. Will this take less than 2 hours to implement?
3. Does this affect 1-3 files maximum?
4. Are there NO database schema changes?
5. Are there NO new API endpoints?
6. Is there NO complex business logic?
7. Is there NO need for user research?
8. Are there NO significant design changes?

**If ALL answers are YES**: Proceed with quick workflow.

**If ANY answer is NO**:
- Tell user: "This request is too complex for /sam-quick. Please use /sam-discover for the full workflow."
- Explain why it doesn't qualify
- DO NOT proceed

### 2. Quick Documentation

Create `.sam/{task_name}/QUICK_TASK.md` with:

```markdown
# Quick Task: {Task Name}

## Description
{1-2 sentence description}

## Type
- [ ] Bug Fix
- [ ] Small Feature
- [ ] Chore/Refactor
- [ ] Text/Content Change

## Files to Modify
- List each file that needs changes

## Implementation Steps
- [ ] Step 1
- [ ] Step 2
- [ ] ...

## Acceptance Criteria
- [ ] {Specific testable outcome}
- [ ] {Another specific outcome}

## Notes
{Any edge cases or considerations}
```

### 3. Output

```
✅ Quick task documented: .sam/{task_name}/QUICK_TASK.md
📋 Next step: Run /sam-develop to implement
```

## Size Validation Examples

**QUALIFIES for /sam-quick**:
- ✅ "Fix submit button disabled on login form" (1 file, clear bug)
- ✅ "Change error message text" (1 file, simple text change)
- ✅ "Add loading state to profile page" (1-2 files, minor enhancement)
- ✅ "Fix typo in navigation" (1 file, trivial fix)

**DOES NOT QUALIFY - use /sam-discover**:
- ❌ "Add user authentication" (complex feature, security implications)
- ❌ "Build dashboard with charts" (new feature, multiple components)
- ❌ "Implement file upload" (complex logic, storage integration)
- ❌ "Add notifications system" (new infrastructure, real-time)

## Integration with Other Skills

The `/sam-quick` command integrates with `/sam-develop`:
- `/sam-quick` creates `QUICK_TASK.md` with checkbox steps
- `/sam-develop` reads the checkbox steps and implements them
- No need for `/sam-stories` or `/sam-specs` for quick tasks
