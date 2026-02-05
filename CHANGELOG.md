# Changelog

All notable changes to the SAM Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-15

### Added

#### Phase 1: Feature Discovery (sam-discover)
- Parallel web search with 4 subagents
  - Industry best practices researcher
  - Technical patterns researcher
  - Competitive analyzer
  - Security/compliance analyst
- Interactive interview loop with AskUserQuestion
- Scope assessment with automatic feature breakdown
- Feature documentation template
- Discovery methodology reference

#### Phase 2: User Story Generation (sam-stories)
- INVEST-compliant story decomposition
- Automatic story numbering and file generation
- Coverage verification with verifier subagent
- Gap closure until 100% coverage
- User story template
- Story guidelines reference

#### Phase 3: Technical Specification (sam-specs)
- Context7 integration for latest documentation
- Comprehensive technical specification template
- Checkbox-based task tracking
- Task mapping to acceptance criteria
- Architecture overview generation
- Database schema specification
- API endpoint documentation
- Component hierarchy definition

#### Phase 4: Development & Verification (sam-develop)
- Parallel subagent development
- Checkbox progress tracking ([ ] → [x])
- Coverage verification script (verify_coverage.py)
- Quality check script (lint_build_test.sh)
- Verification report generation
- Gap closure loop

#### Utility: Status Tracking (sam-status)
- Feature phase detection
- Progress calculation
- Terminal-friendly status display
- STATUS.md generation
- Progress bars

#### Scripts
- `lint_build_test.sh` - Comprehensive quality checks
- `verify_coverage.py` - Coverage verification
- `status_report.py` - Status report generation

#### Templates
- `FEATURE_TEMPLATE.md` - Feature documentation template
- `USER_STORY_TEMPLATE.md` - User story template
- `TECHNICAL_SPEC_TEMPLATE.md` - Technical specification template

#### Reference Documentation
- `discovery-methodology.md` - Phase 1 guidelines
- `story-guidelines.md` - Phase 2 guidelines
- `development-guidelines.md` - Phase 4 guidelines

#### Agent Configurations
- `feature-discoverer.json` - Phase 1 agent
- `story-generator.json` - Phase 2 agent
- `spec-writer.json` - Phase 3 agent
- `code-verifier.json` - Verification agent

#### Configuration Files
- `.claude-plugin/plugin.json` - Plugin manifest
- `.mcp.json` - Context7 MCP server configuration

### Features

- **Parallel Research**: 4 concurrent subagents for domain research
- **Checkbox Tracking**: Visual progress tracking in specs
- **Coverage Verification**: Automated 100% coverage verification
- **Parallel Development**: Multiple subagents for independent tasks
- **Context7 Integration**: Latest documentation at your fingertips
- **Feature Breakdown**: Automatic recommendation for large features
- **Status Dashboard**: At-a-glance progress tracking

### Documentation

- Comprehensive README with quick start guide
- Individual skill documentation (SKILL.md files)
- Reference materials for each phase
- Workflow diagram
- Troubleshooting guide

### Output Structure

```
.cdd/
├── 001_feature_name/
│   ├── FEATURE_DOCUMENTATION.md
│   ├── USER_STORIES/
│   │   ├── 001_story_name.md
│   │   └── ...
│   ├── TECHNICAL_SPEC.md
│   └── VERIFICATION_REPORT.md
└── STATUS.md
```

## [Unreleased]

### Planned Features

- [ ] Web UI for status tracking
- [ ] Integration with GitHub Issues
- [ ] Export to JIRA format
- [ ] burndown chart generation
- [ ] Sprint planning assistance
- [ ] Automated PR description generation

---

## Version Format

- **Major.Minor.Patch** (e.g., 1.0.0)
- Major: Breaking changes
- Minor: New features (backwards compatible)
- Patch: Bug fixes

## Release Notes

Each release includes:
- Summary of changes
- New features
- Bug fixes
- Migration guide (if needed)
