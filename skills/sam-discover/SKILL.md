---
name: sam-discover
description: Feature discovery and documentation agent. Spawns web research subagents for domain knowledge, conducts iterative user interviews using AskUserQuestion for 100% clarity, generates comprehensive feature documentation following company template. Use when user says "discover feature", "document feature request", "clarify requirements", or "create feature documentation". For large requests (e.g., "build Tinder clone"), proposes feature breakdown with numbered IDs.
---

# Feature Discovery Agent

## Overview

This skill conducts comprehensive feature discovery through parallel web research and iterative user interviews, resulting in complete, unambiguous feature documentation.

## Workflow

### 1. Initial Assessment

Accept the user's raw feature description and assess scope:
- **Single feature**: "Add user authentication"
- **Multi-feature epic**: "Build a Tinder clone" → Propose breakdown

### 1.5. Check for Existing Features (NEW)

Before creating new feature documentation:

**Check .sam/ directory for related features:**
```bash
find .sam/ -name "FEATURE_DOCUMENTATION.md" -exec grep -l "{feature_keywords}" {} \;
```

**If related features found:**
- Inform user about potential overlap
- Ask if this is an extension or replacement
- Reference existing feature IDs in new documentation

**Example output:**
```
ℹ️ Found related feature: .sam/001_user_auth/FEATURE_DOCUMENTATION.md
This may overlap with your request. Would you like to:
  1. Extend the existing feature
  2. Create a new separate feature
  3. Replace the existing feature
```

### 2. Parallel Domain Research (WITH FALLBACK)

**Fallback Chain:** Web Search → Context7 → Brave Search → Built-in

**Pattern:** Use the research fallback approach for feature research:
1. Primary: mcp__web-search-prime__webSearchPrime (broad feature research)
2. Fallback 1: mcp__plugin_context7_context7__query-docs (if web search unavailable)
3. Fallback 2: WebSearch (built-in, if web-search-prime quota exceeded)

Spawn 4 subagents simultaneously. **If primary method fails, automatically try fallbacks:**

**Subagent 1 - Industry Best Practices**
```
Search for: "best practices {feature domain} implementation 2025"
Focus: Standards, patterns, industry conventions
```

**Subagent 2 - Technical Implementation Patterns**
```
Search for: "{feature} technical implementation patterns architecture"
Focus: Code patterns, frameworks, libraries
```

**Subagent 3 - Competitive Analysis**
```
Search for: "{feature} examples production implementations"
Focus: Real-world examples, UX patterns
```

**Subagent 4 - Security/Compliance**
```
Search for: "{feature} security requirements compliance standards"
Focus: Security considerations, regulatory requirements
```

### 3. Interactive Interview Loop

Use `AskUserQuestion` tool systematically. Continue until 100% clarity.

#### Product Questions
- Who are the target users? (personas, demographics)
- What is the primary business value? (metrics, ROI)
- What defines success for this feature? (KPIs, outcomes)

#### Technical Questions
- What is the current tech stack? (frameworks, languages, database)
- Are there constraints? (performance, memory, compatibility)
- What integrations are required? (APIs, third-party services)

#### Project Architecture Question (NEW)
"Is this project:" (Use AskUserQuestion with these options)
- Frontend-only (consuming external APIs)
- Full-stack (custom backend)
- BaaS-based (Supabase, Firebase, etc.)
- Static site (no backend)

Store answer in FEATURE_DOCUMENTATION.md metadata:

#### UX/UI Questions
- Is there a design system to follow? (Figma, Storybook)
- What accessibility level is required? (WCAG 2.1 AA/AAA)
- Which devices must be supported? (mobile, tablet, desktop)

#### Data Questions
- What data needs to be stored? (PII, user-generated content)
- Are there privacy requirements? (GDPR, CCPA, retention policies)
- What is the expected data volume? (users, transactions per day)

#### Edge Cases
- What happens when the service is unavailable? (offline mode)
- What are the boundary conditions? (limits, quotas, thresholds)
- How should errors be handled? (user-facing messages, logging)

### 4. Scope Decision

**If scope is too large** (e.g., "build entire CRM system"):
1. Propose logical feature breakdown
2. Create numbered feature list:
   - `001_user_authentication`
   - `002_contact_management`
   - `003_sales_pipeline`
   - `004_reporting_dashboard`
3. Recommend starting with highest-value feature
4. Ask user to confirm breakdown

**If scope is appropriate**: Proceed to documentation.

### 5. Generate Feature Documentation

Create `.sam/{XXX_feature_name}/FEATURE_DOCUMENTATION.md` following the EXACT template structure provided in "## Output Format Requirement" above.

- Include ALL required sections from the template
- DO NOT add sections from other phases (user stories, database schema, API endpoints)
- DO NOT invent new section titles
- Populate Domain Research Summary with findings from the 4 parallel subagents
- Keep functional requirements at HIGH LEVEL (what, not how)

### 6. Output

Report completion and provide next steps:
```
✅ Feature documentation created: .sam/001_user_auth/FEATURE_DOCUMENTATION.md
📋 Next steps:
   1. Run /sam-stories to generate detailed user stories
   2. Run /sam-specs to generate technical specifications
   3. Run /sam-develop to begin implementation
```

---

## Output Format Requirement

You MUST generate FEATURE_DOCUMENTATION.md following THIS EXACT STRUCTURE:

# Feature: {Feature Name}

## Metadata
- **Feature ID**: {XXX}_{feature_name}
- **Status**: Discovery | In Progress | Completed
- **Created**: {Date}
- **Last Updated**: {Date}
- **Project Type**: baas-fullstack | frontend-only | full-stack | static-site (optional, overrides auto-detection)

---

# Problem Statement

## What are we trying to solve?
{Clear articulation of the user problem}

## Objectives
{Business objectives and success metrics}

## Target Users
{Primary and secondary user personas}

---

# Solution

## Functional Requirements

### Core Capabilities
- {Bullet points of user-facing functionality}

### User Flows
{Describe key user journeys}

## UX/UI

### Design System Alignment
{References to existing design system}

### Design Approach
{Describe the design methodology and style direction}

**Consider**:
- Visual hierarchy and layout patterns
- Component library or design system to follow
- Brand guidelines to adhere to
- Accessibility requirements (WCAG level)
- Responsive breakpoints to support

### Screens
{List all screens/pages with descriptions}

## Business Logic

### Rules & Workflows
{Business rules that govern feature behavior}

### CRUD Definition
| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| ...    | ...    | ...  | ...    | ...    |

### Edge Cases
- {Edge case 1}
- {Edge case 2}

### State Transitions
{Diagram or description of state changes}

### Roles & Permissions
| Role | Permissions |
|------|-------------|
| ...  | ...         |

---

# Technical Context

### Stack Preferences
{Framework, language, database preferences}

### Integrations Required
{External APIs, services, or systems}

### Performance Requirements
{Response times, throughput, etc.}

### Security Considerations
{Authentication, authorization, data handling}

---

# Domain Research Summary

## Industry Best Practices
{Findings from web search subagent 1}

## Technical Patterns
{Findings from web search subagent 2}

## Competitive Landscape
{Findings from web search subagent 3}

## Compliance Notes
{Findings from web search subagent 4}

---

# Resources

## API Documentation (if applicable)
> Only include this section if building custom APIs. For BaaS solutions (Supabase, Firebase, etc.), this section is not needed.

{Links to external API documentation, if applicable}

## Design Guidelines
{Textual design direction and principles}

**Examples**:
- "Follow modern minimalist design with card-based layouts"
- "Use Material Design 3 components with custom theming"
- "Implement dark mode with system preference detection"
- "Focus on accessibility with WCAG 2.1 AA compliance"
- "Mobile-first responsive design approach"

## Reference Materials
{Any additional resources}

---

## CRITICAL: Phase Boundaries

DO NOT include these sections in FEATURE_DOCUMENTATION.md:
- ❌ User Stories with "As a... When... I can..." format → Use `/sam-stories` instead
- ❌ Database Schema with CREATE TABLE statements → Use `/sam-specs` instead
- ❌ API Endpoints with POST/GET/PUT/DELETE details → Use `/sam-specs` instead
- ❌ Implementation Tasks with checkboxes → Use `/sam-specs` instead
- ❌ Executive Summary with "Problem Statement, Proposed Solution, Business Value" → Not in template
- ❌ Dependencies section → Use Technical Context > Integrations Required
- ❌ Success Criteria table → Use Problem Statement > Objectives
- ❌ Calculations section → Use Business Logic > Rules & Workflows

The discovery phase is about UNDERSTANDING the problem and solution space.
Details are for subsequent phases.

## Key Principles

- **No assumptions**: Every detail must be confirmed with the user
- **Parallel research**: All 4 subagents run simultaneously
- **100% clarity**: Interview continues until no ambiguity remains
- **Numbered IDs**: Features use 001_, 002_, etc. for traceability

## Template Reference

The template at `/templates/feature/FEATURE_TEMPLATE.md` defines the canonical structure.
This skill embeds the EXACT structure above in "## Output Format Requirement" to ensure strict adherence.
