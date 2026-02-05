---
name: sam-status
description: Status tracking utility for SAM workflow. Provides at-a-glance view of all features in discovery, stories, specs, development, or completed phases. Scans .sam/ directory to determine feature status and generates STATUS.md report. Use when user says "show status", "track progress", "status report", or "what's the status".
---

# sam-status: Status Tracking Skill

## Overview

Utility skill for tracking progress across all SAM features. Provides an at-a-glance view of what's in discovery, stories, specs, development, or completed.

## Trigger Phrases

- "show status"
- "track progress"
- "status report"
- "what's the status"

## Usage

```bash
/sam-status [feature_id]
```

- Without arguments: Shows status of all features
- With feature_id: Shows detailed status of specific feature

## Workflow

### 1. Scan .sam/ Directory

1. Check if `.sam/` directory exists
2. List all feature directories (001_*, 002_*, etc.)
3. Sort by feature number

### 2. Determine Feature Status

For each feature, check:

| Status | Criteria |
|--------|----------|
| Discovery | Only FEATURE_DOCUMENTATION.md exists |
| Stories | USER_STORIES/ exists but no TECHNICAL_SPEC.md |
| Specs | TECHNICAL_SPEC.md exists but checkboxes incomplete |
| Development | TECHNICAL_SPEC.md has some `[x]` but not all |
| Verification | VERIFICATION_REPORT.md exists |
| Completed | All checkboxes `[x]`, verification passed |

### 3. Generate Status Report

Create or update `.sam/STATUS.md`:

```markdown
# SAM Feature Status Report

Generated: {{DATE_TIME}}

---

## Summary

| Metric | Count |
|--------|-------|
| Total Features | {{TOTAL}} |
| In Discovery | {{DISCOVERY}} |
| In Stories | {{STORIES}} |
| In Specs | {{SPECS}} |
| In Development | {{DEVELOPMENT}} |
| In Verification | {{VERIFICATION}} |
| Completed | {{COMPLETED}} |

---

## Feature Details

### 001_feature_name

**Status**: {{STATUS_ICON}} {{STATUS_TEXT}}
**Progress**: {{PERCENTAGE}}%

**Phase**: {{CURRENT_PHASE}}

**Last Updated**: {{DATE}}

**Details**:
- Stories: {{NUM_STORIES}}
- Spec Tasks: {{COMPLETED}}/{{TOTAL}}
- Coverage: {{PERCENTAGE}}%

---

### 002_feature_name

...
```

### 4. Output Summary

```
═══════════════════════════════════════════════════
  SAM Feature Status Report
═══════════════════════════════════════════════════

Discovery:  📋 1
Stories:    📝 2
Specs:      📋 1
Development: 🚧 3
Completed:   ✅ 5

─────────────────────────────────────────────────

001_user_auth
  Status: ✅ Completed
  Progress: 100%

002_user_profiles
  Status: 🚧 Development
  Progress: 65%
  Tasks: 13/20 complete

...

Full report: .sam/STATUS.md
```

## Status Icons

| Icon | Meaning |
|------|---------|
| 📋 | Discovery - Feature documentation in progress |
| 📝 | Stories - User stories being generated |
| 📐 | Specs - Technical specification being written |
| 🚧 | Development - Implementation in progress |
| ✅ | Completed - Feature fully implemented |

## Progress Calculation

```
Discovery: 0%
Stories: Number of stories / Expected stories
Specs: Number of spec sections / Total sections
Development: Completed checkboxes / Total checkboxes
Completed: 100%
```

## Dependencies

- Read tool (for reading feature files)
- Write tool (for generating STATUS.md)
- Bash tool (for directory scanning)

## Status Report Template

See: Templates are generated dynamically based on discovered features.

## Example Output

```
═══════════════════════════════════════════════════
  SAM Feature Status Report
═══════════════════════════════════════════════════

📊 Overview
  Total Features:    8
  In Discovery:      1
  In Stories:        1
  In Specs:          1
  In Development:    2
  Completed:         3

─────────────────────────────────────────────────

📋 001_user_authentication
  Status: ✅ Completed
  Progress: 100%
  Stories: 8
  Tasks: 45/45 ✓

🚧 002_user_profiles
  Status: Development (65%)
  Tasks: 13/20 complete
  Remaining: Database setup, API endpoints

📐 003_messaging_system
  Status: Specs
  Progress: Technical specification in progress

📝 004_notifications
  Status: Stories
  Progress: User stories being generated

📋 005_admin_panel
  Status: Discovery
  Progress: Requirements gathering

─────────────────────────────────────────────────

Full report saved to: .sam/STATUS.md
```

---

## Note

This skill is a reporting utility that reads existing SAM artifacts and generates status summaries. It does not create new feature documentation, user stories, or specifications, so phase boundary issues are not applicable here.
