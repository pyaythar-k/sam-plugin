# SAM Plugin - Context-Driven Development Plugin

A comprehensive Claude Code Plugin that orchestrates a production-grade development workflow from feature ideation to verified implementation.

## Overview

The SAM Plugin transforms raw feature ideas into fully implemented, verified code through a structured four-phase workflow:

1. **Discovery** - Research and document feature requirements
2. **Stories** - Break down into INVEST-compliant user stories
3. **Specs** - Generate technical specifications with actionable tasks
4. **Develop** - Execute implementation with parallel development and verification

## Installation

1. Copy this plugin to your Claude plugins directory:
```bash
cp -r sam-plugin ~/.claude/plugins/sam-plugin
```

2. Ensure the MCP server for Context7 is configured (included in `.mcp.json`)

3. Restart Claude Code to load the plugin

## Usage

### Quick Start

```bash
# Start with feature discovery
/sam-discover "Add user authentication with social login"

# Generate user stories
/sam-stories 001_user_auth

# Create technical specification
/sam-specs 001_user_auth

# Start development
/sam-develop 001_user_auth

# Check status
/sam-status
```

## Skills Reference

### cdd-discover

**Purpose:** Phase 1 - Feature Discovery

Conducts domain research through 4 parallel subagents and generates comprehensive feature documentation.

**Usage:**
```bash
/sam-discover "<feature description>"
```

**Output:** `.sam/{XXX_feature_name}/FEATURE_DOCUMENTATION.md`

### cdd-stories

**Purpose:** Phase 2 - User Story Generation

Breaks features into INVEST-compliant user stories with 100% coverage verification.

**Usage:**
```bash
/sam-stories [feature_id]
```

**Output:** `.sam/{feature_id}/USER_STORIES/{XXX_story_name}.md`

### cdd-specs

**Purpose:** Phase 3 - Technical Specification

Generates comprehensive technical specs with checkbox-based task tracking.

**Usage:**
```bash
/sam-specs [feature_id]
```

**Output:** `.sam/{feature_id}/TECHNICAL_SPEC.md`

### cdd-develop

**Purpose:** Phase 4 - Development & Verification

Orchestrates parallel development execution and verifies complete coverage.

**Usage:**
```bash
/sam-develop [feature_id]
```

**Output:** Updated spec files and `VERIFICATION_REPORT.md`

### cdd-status

**Purpose:** Track progress across all features

**Usage:**
```bash
/sam-status [feature_id]
```

**Output:** Terminal summary and `.sam/STATUS.md`

## Output Structure

```
project-root/
└── .sam/
    ├── 001_feature_name/
    │   ├── FEATURE_DOCUMENTATION.md
    │   ├── USER_STORIES/
    │   │   ├── 001_story_name.md
    │   │   ├── 002_story_name.md
    │   │   └── ...
    │   ├── TECHNICAL_SPEC.md
    │   └── VERIFICATION_REPORT.md
    ├── 002_feature_name/
    │   └── ...
    └── STATUS.md
```

## Key Features

### Parallel Research

Phase 1 spawns 4 parallel subagents for simultaneous domain research:
- Industry best practices
- Technical patterns
- Competitive analysis
- Security/compliance

### Checkbox Progress Tracking

Technical specs use markdown checkboxes for visual progress tracking:
```markdown
- [ ] Implement POST /api/users
- [x] Implement GET /api/users
- [ ] Implement PUT /api/users/:id
```

### Coverage Verification

Automated verification ensures 100% coverage of:
- User story acceptance criteria
- Technical specification tasks
- Code quality standards

### Parallel Development

Phase 4 spawns multiple subagents for independent tasks to maximize efficiency.

## Scripts

### lint_build_test.sh

Comprehensive quality check script:
```bash
./skills/sam-develop/scripts/lint_build_test.sh
```

Checks:
- Linting (ESLint)
- Type checking (TypeScript)
- Build
- Unit tests
- E2E tests

### verify_coverage.py

Verify coverage against specifications:
```bash
python3 skills/sam-develop/scripts/verify_coverage.py <feature_id>
python3 skills/sam-develop/scripts/verify_coverage.py --all
```

### status_report.py

Generate status report:
```bash
python3 skills/sam-status/scripts/status_report.py
```

## Configuration

### .mcp.json

Configured for Context7 MCP server to fetch latest documentation:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    }
  }
}
```

## Workflow Diagram

```
Raw Feature Idea
       ↓
┌─────────────────────────────────────────────────────┐
│ Phase 1: Discovery (cdd-discover)                    │
│ • Parallel web research (4 subagents)                │
│ • Interactive interviews                             │
│ • FEATURE_DOCUMENTATION.md                           │
└─────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────┐
│ Phase 2: Stories (cdd-stories)                       │
│ • INVEST-compliant story decomposition               │
│ • Coverage verification                              │
│ • USER_STORIES/*.md                                  │
└─────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────┐
│ Phase 3: Specs (cdd-specs)                           │
│ • Context7 research for latest docs                  │
│ • Checkbox task breakdown                            │
│ • TECHNICAL_SPEC.md                                  │
└─────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────┐
│ Phase 4: Develop (cdd-develop)                       │
│ • Parallel subagent development                      │
│ • Checkbox progress tracking                         │
│ • Coverage verification                              │
│ • VERIFICATION_REPORT.md                             │
└─────────────────────────────────────────────────────┘
       ↓
   Complete Feature
```

## Best Practices

1. **Start Small:** Begin with well-defined features before tackling large epics
2. **Complete Phases Sequentially:** Each phase builds on the previous
3. **Update Checkboxes:** Mark tasks complete as you work
4. **Run Verification:** Use verify_coverage.py regularly
5. **Check Status:** Use cdd-status to track overall progress

## Examples

### Example 1: Simple Feature

```bash
# Password reset functionality
/sam-discover "Add password reset via email"
/sam-stories 001_password_reset
/sam-specs 001_password_reset
/sam-develop 001_password_reset
```

### Example 2: Large Feature (Auto-breakdown)

```bash
# Large feature gets broken down automatically
/sam-discover "Build a complete project management system"

# Output: Recommended breakdown
# 001_user_authentication
# 002_project_management
# 003_task_tracking
# 004_team_collaboration
# 005_notifications

# Start with first feature
/sam-stories 001_user_authentication
```

## Troubleshooting

### Issue: "No .sam/ directory found"

**Solution:** The `.sam/` directory is created when you first run `/sam-discover`. Start with discovery.

### Issue: "Feature not found"

**Solution:** Use `/sam-status` to see available features. Check the feature ID format (001_feature_name).

### Issue: "Context7 not responding"

**Solution:** Ensure `.mcp.json` is configured correctly and the MCP server is running.

## Contributing

To extend the plugin:

1. Add new skills to `skills/`
2. Update `agents/*.json` configurations
3. Modify templates in `templates/`
4. Update this README

## License

MIT

## Version

1.0.0

## Support

For issues or questions, please refer to the individual skill documentation in `skills/*/SKILL.md`.
