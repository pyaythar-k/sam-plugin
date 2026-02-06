# SAM Plugin for Claude Code

> A comprehensive, autonomous software development workflow system that guides projects from discovery through deployment with built-in quality gates, observability, and CI/CD integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![SAM Quality](https://img.shields.io/badge/SAM-Quality_Gates-brightgreen)]()

## What is SAM?

**SAM (Software Architecture Methodology)** is a structured approach to building software that combines autonomous agent execution with human oversight. It provides a complete workflow from feature discovery to production deployment, with quality enforcement at every stage.

### Key Principles

- **Autonomy First**: Agents work in parallel to complete complex tasks independently
- **Quality Gates**: Automated enforcement of linting, type-checking, building, and 80%+ test coverage
- **Traceability**: Every line of code maps back to requirements through TASKS.json
- **Observability**: Built-in logging, metrics, tracing, and error tracking
- **Shift-Left Verification**: Validate immediately after implementation, not at the end

### Why Use SAM?

- **98% Token Reduction**: TASKS.json enables incremental reading of specifications
- **Parallel Execution**: Up to 3 subagents work simultaneously on independent tasks
- **Checkpoint/Resume**: Long-running tasks can be paused and resumed
- **Rollback Capability**: Failed parallel batches can be automatically rolled back
- **Deadlock Detection**: Prevents circular dependencies before parallel execution

## Quick Start

### Installing SAM (One-Time)

1. Clone SAM to your Claude Code plugins directory:
   ```bash
   # macOS/Linux
   git clone https://github.com/your-org/sam-plugin.git ~/.claude/plugins/sam-plugin

   # Windows
   git clone https://github.com/your-org/sam-plugin.git %APPDATA%\claude\plugins\sam-plugin
   ```

2. Restart Claude Code to load the plugin

### Setting Up Your Project

In your project directory, run:

```bash
# Option 1: Using absolute path to SAM scripts
~/.claude/plugins/sam-plugin/scripts/observe-setup.sh
~/.claude/plugins/sam-plugin/scripts/setup-pre-commit.sh

# Option 2: Copy SAM scripts to your project (recommended)
mkdir -p .sam/scripts
cp ~/.claude/plugins/sam-plugin/scripts/*.sh .sam/scripts/
./.sam/scripts/observe-setup.sh
./.sam/scripts/setup-pre-commit.sh

# Option 3: Create a symlink (Linux/macOS)
ln -s ~/.claude/plugins/sam-plugin/scripts .sam/scripts
./.sam/scripts/observe-setup.sh
./.sam/scripts/setup-pre-commit.sh
```

### Start Building

```bash
# For small tasks (bug fixes, minor changes):
/sam-quick fix the login button color

# For new features:
/sam-discover user authentication feature
/sam-stories generate from feature documentation
/sam-specs create technical specification
/sam-develop start implementation

# Check progress
/sam-status show all features
```

## SAM Workflow Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DISCOVERY  │───▶│   STORIES   │───▶│    SPECS    │───▶│ DEVELOPMENT │───▶│ VALIDATION  │
│  sam-       │    │  sam-       │    │  sam-       │    │  sam-       │    │  sam-       │
│  discover   │    │  stories    │    │  specs      │    │  develop    │    │  validate   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │                  │
      ▼                  ▼                  ▼                  ▼                  ▼
 Feature          User Stories      Technical         Code + Tests      Quality
 Documentation    (INVEST)          Specification     (Parallel)        Assurance
                                        │                                    │
                                        ▼                                    ▼
                                  TASKS.json                      Verification
                                  (98% token                         Report
                                   reduction)                        (Traceability)

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         QUALITY GATES (Enforced at each stage)                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │  Lint   │ │ Type    │ │  Build  │ │  Unit   │ │ E2E     │ │ 80%     │       │
│  │ Checks  │ │ Checks  │ │ Verify  │ │  Tests  │ │  Tests  │ │Coverage │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            OBSERVABILITY (Cross-cutting)                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                                   │
│  │  Logs   │ │ Metrics │ │ Tracing │ │ Errors  │                                   │
│  │ (JSON)  │ │ (Perf)  │ │ (Spans) │ │ (Track) │                                   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Workflow Phases

| Phase | Purpose | Output | Skill |
|-------|---------|--------|-------|
| **Discovery** | Document complete, unambiguous requirements | `FEATURE_DOCUMENTATION.md` | `sam-discover` |
| **Stories** | Create INVEST-compliant user stories | `001_*.md`, `002_*.md` | `sam-stories` |
| **Specs** | Generate actionable technical specifications | `PHASE_*.md`, `TASKS.json` | `sam-specs` |
| **Development** | Parallel implementation with verification | Code + Tests | `sam-develop` |
| **Validation** | Quality assurance and traceability | `VERIFICATION_REPORT.md` | `sam-validate` |

## Core Skills

SAM provides **8 specialized skills** covering the entire software development lifecycle:

### 1. sam-quick - Small Feature & Bug Fix Handler

For small tasks that don't require the full discovery process.

**Trigger Phrases:**
- "quick fix"
- "small change"
- "minor bug"
- "simple task"
- `/sam-quick`

**Features:**
- Size validation (8-question checklist)
- Creates `QUICK_TASK.md` with checkbox steps
- Integrates with `/sam-develop` for implementation
- Bypasses `/sam-stories` and `/sam-specs`

### 2. sam-discover - Feature Discovery Agent

Comprehensive feature discovery through parallel web research.

**Trigger Phrases:**
- "discover feature"
- "document feature request"
- "clarify requirements"
- "create feature documentation"

**Features:**
- Spawns 4 parallel research subagents
  - Industry best practices
  - Technical patterns
  - Competitive analysis
  - Security/compliance
- Interactive interview loop
- Generates `FEATURE_DOCUMENTATION.md`
- Proposes feature breakdown for large requests

### 3. sam-stories - User Story Generation

Transforms features into INVEST-compliant user stories.

**Trigger Phrases:**
- "generate user stories"
- "create stories from feature"
- "break down into stories"

**Features:**
- INVEST compliance checking (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- Automatic gap verification
- Who/When/What title structure
- Optional Gherkin scenarios (Given-When-Then)
- Generates numbered story files (`001_*.md`, `002_*.md`)

### 4. sam-specs - Technical Specification Writer

Creates actionable technical specifications with executable tests.

**Trigger Phrases:**
- "generate technical specs"
- "create technical specification"
- "write implementation plan"

**Features:**
- Context7-powered documentation research
- Project type classification (baas-fullstack, frontend-only, full-stack, static-site)
- Generates `TASKS.json` for 98% token reduction
- Modular spec structure (`PHASE_*.md` files)
- 16 advanced capabilities:
  - Gherkin test generation
  - OpenAPI and contract testing
  - Impact analysis
  - State machine generation
  - Decision table tests
  - E2E test generation
  - Security tests (OWASP Top 10)
  - Test data generation

### 5. sam-develop - Development & Verification

Orchestrates parallel development execution with quality gates.

**Trigger Phrases:**
- "start development"
- "implement feature"
- "execute tasks"
- "continue development"

**Features:**
- **Autonomous execution mode** - continues without stopping
- **Parallel execution** - up to 3 subagents simultaneously
- **Checkpoint/Resume** - pause and resume long tasks
- **Shift-left verification** - verify each task immediately
- **Rollback capability** - auto-rollback failed batches
- **Deadlock detection** - prevent circular dependencies
- Project type-aware phase structure

### 6. sam-validate - Validation & Verification

Comprehensive quality assurance and traceability.

**Features:**
- Code-to-task mapping (bidirectional traceability)
- Conflict detection (files, endpoints, databases, components)
- Phase gate validation
- Verification linking (tasks to tests)

**Tools:**
- `code_task_mapper.py` - Maps code to requirements
- `conflict_detector.py` - Detects conflicts
- `phase_gate_validator.py` - Validates phase completion
- `verification_linker.py` - Links tasks to tests

### 7. sam-observe - Observability & Monitoring

Comprehensive observability for the SAM workflow.

**Features:**
- Structured JSON logging
- Performance metrics collection
- Distributed tracing with span tracking
- Error tracking with grouping

**CLI Commands:**
```bash
python3 -m skills.sam_observe.cli init
python3 -m skills.sam_observe.cli logs --component sam-specs --level ERROR
python3 -m skills.sam_observe.cli metrics
python3 -m skills.sam_observe.cli dashboard
python3 -m skills.sam_observe.cli console
python3 -m skills.sam_observe.cli export --output diag.zip
```

### 8. sam-status - Status Tracking

At-a-glance view of all features in progress.

**Trigger Phrases:**
- "show status"
- "track progress"
- "status report"
- "what's the status"

**Features:**
- Scans `.sam/` directory for feature status
- Generates `STATUS.md` report
- Performance metrics integration
- Watch mode for real-time monitoring

## Installation & Setup

### Prerequisites

- **Claude Code**: Latest version with plugin support
- **Python**: 3.9 or higher
- **Node.js**: 18.x or 20.x
- **Git**: For version control

### Part 1: Install SAM Plugin (One-Time)

SAM is installed as a Claude Code plugin. You only need to do this once.

#### Option A: Clone to Plugins Directory
```bash
# macOS/Linux
git clone https://github.com/your-org/sam-plugin.git ~/.claude/plugins/sam-plugin
cd ~/.claude/plugins/sam-plugin
npm install
pip install -r requirements.txt

# Windows
git clone https://github.com/your-org/sam-plugin.git %APPDATA%\claude\plugins\sam-plugin
cd %APPDATA%\claude\plugins\sam-plugin
npm install
pip install -r requirements.txt
```

#### Option B: Install from Marketplace (when available)
```bash
# Via Claude Code CLI
claude plugin install sam-plugin
```

**Restart Claude Code** after installation to load the plugin.

### Part 2: Set Up Your Project

Each project using SAM needs initialization. Run these commands in **your project directory** (not the plugin directory).

#### 1. Copy CI/CD Templates (Optional but Recommended)

SAM provides CI/CD templates that you should copy to your project:

```bash
# In your project directory

# GitHub Actions
mkdir -p .github/workflows
cp ~/.claude/plugins/sam-plugin/.github/workflows/sam-quality-gate.yml .github/workflows/

# GitLab CI
cp ~/.claude/plugins/sam-plugin/.gitlab-ci.yml .

# Pre-commit hooks
cp ~/.claude/plugins/sam-plugin/.pre-commit-config.yaml .
```

#### 2. Initialize Observability

```bash
# Using absolute path to plugin scripts
~/.claude/plugins/sam-plugin/scripts/observe-setup.sh

# Or copy scripts to your project first (recommended)
mkdir -p .sam/scripts
cp ~/.claude/plugins/sam-plugin/scripts/*.sh .sam/scripts/
./.sam/scripts/observe-setup.sh
```

This creates the `.sam/` directory structure:
```
.sam/
├── logs/           # Structured JSON logs
├── metrics/        # Performance metrics
├── traces/         # Distributed traces
└── errors/         # Error reports
```

#### 3. Install Pre-commit Hooks

```bash
~/.claude/plugins/sam-plugin/scripts/setup-pre-commit.sh
# or
./.sam/scripts/setup-pre-commit.sh
```

This installs hooks for:
- Prettier formatting
- ESLint linting
- Black formatting (Python)
- Flake8 linting (Python)
- Bandit security checks
- SAM-specific checks (coverage, contract tests, type-check, build)

### Configuration

Edit `.sam/config.yaml` in your project to customize:
- Log levels
- Metrics retention
- Trace sampling rate
- Quality gate thresholds

### Verification

```bash
# Check SAM is loaded
claude plugin list

# Verify observability
ls -la .sam/

# Check pre-commit hooks
pre-commit run --all-files
```

## Usage Examples

### Example 1: Quick Bug Fix

```bash
# For small, well-defined tasks
User: /sam-quick Fix the login button color to blue

# SAM generates QUICK_TASK.md with steps:
☐ Verify current button color
☐ Update CSS/color tokens
☐ Run tests
☐ Create pull request

# Then automatically calls /sam-develop to implement
```

### Example 2: New Feature (Full Workflow)

```bash
# Step 1: Discovery
User: /sam-discover I need user authentication with OAuth2

# SAM spawns 4 parallel researchers and conducts interviews
# Output: .sam/001_user_auth/FEATURE_DOCUMENTATION.md

# Step 2: User Stories
User: /sam-stories Generate stories from feature documentation

# SAM creates INVEST-compliant stories
# Output: .sam/001_user_auth/stories/001_oauth_integration.md
#        .sam/001_user_auth/stories/002_user_profile.md

# Step 3: Technical Specification
User: /sam-specs Create technical specification for story 001

# SAM generates spec with Context7 research
# Output: .sam/001_user_auth/specs/PHASE_1_AUTH_FLOW.md
#        .sam/001_user_auth/specs/TASKS.json

# Step 4: Development
User: /sam-develop Start implementation

# SAM executes tasks in parallel with quality gates
# Output: Implementation code + tests

# Step 5: Validation
User: /sam-validate Generate verification report

# SAM creates traceability matrix
# Output: .sam/001_user_auth/VERIFICATION_REPORT.md
```

### Example 3: Status Monitoring

```bash
# Check all features
User: /sam-status show all features

# SAM generates STATUS.md:
# Feature           | Phase      | Tasks | Status
# -----------------|------------|-------|--------
# 001_user_auth    | Specs      | 47    | Draft
# 002_dashboard    | Develop    | 23/32 | In Progress
# 003_api_cleanup  | Complete   | 15/15 | ✅ Passed
```

## Project Type Classification

SAM automatically classifies your project to tailor the workflow:

| Type | Description | Phases | API Spec | Database |
|------|-------------|--------|----------|----------|
| **baas-fullstack** | Supabase/Firebase + frontend | 5 | BaaS Integration | RLS policies |
| **frontend-only** | No backend + external API | 4 | Skip | Skip |
| **full-stack** | Custom backend detected | 5 | Standard API | SQL DDL |
| **static-site** | Next.js static, no backend | 4 | Skip | Skip |

### Classification Logic

SAM detects project type by analyzing:
- Package.json dependencies (`supabase`, `firebase`, `next`, `express`, etc.)
- Directory structure (`pages/`, `api/`, `server/`, etc.)
- Configuration files (`supabase/config.toml`, `firebase.json`, etc.)

## Quality Gates

SAM enforces quality at multiple stages:

### Development Quality Gates
```bash
# Enforced by sam-develop/scripts/lint_build_test.sh
┌─────────────────────────────────────────────────┐
│  ☐ ESLint - No errors or warnings              │
│  ☐ Prettier - All files formatted              │
│  ☐ TypeScript - No type errors                 │
│  ☐ Build - Production build succeeds           │
│  ☐ Unit Tests - All tests pass                 │
│  ☐ Coverage - 80%+ threshold met               │
└─────────────────────────────────────────────────┘
```

### CI/CD Quality Gates

**GitHub Actions** (`.github/workflows/sam-quality-gate.yml`):
1. **quality-check** - Fast feedback (linting, type-check, build)
2. **unit-tests** - Matrix testing across Node.js versions [18.x, 20.x]
3. **coverage-check** - Coverage enforcement (80% threshold)
4. **contract-tests** - API contract verification
5. **security-tests** - npm audit and SAM security tests
6. **e2e-tests** - Optional browser automation tests
7. **quality-gate** - Comprehensive final quality gate

**GitLab CI** (`.gitlab-ci.yml`):
- quality → test → coverage → security → contract → e2e → report
- Caching for npm dependencies
- Parallel matrix execution
- Coverage badge generation

## CI/CD Integration

SAM provides CI/CD templates that you copy to your project during setup. These templates enforce quality gates at every stage.

### Setup

```bash
# Copy templates to your project (from Part 2: Set Up Your Project)
mkdir -p .github/workflows
cp ~/.claude/plugins/sam-plugin/.github/workflows/sam-quality-gate.yml .github/workflows/
cp ~/.claude/plugins/sam-plugin/.gitlab-ci.yml .
```

### GitHub Actions

The `.github/workflows/sam-quality-gate.yml` template includes:

```yaml
# .github/workflows/sam-quality-gate.yml (copied to your project)
on:
  push:
    branches: [main, develop, staging, production]
  pull_request:
  workflow_dispatch:

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run quality checks
        run: npx prettier --check . && npm run lint && npm run type-check && npm run build
```

### GitLab CI

The `.gitlab-ci.yml` template provides a comprehensive pipeline:

```yaml
# .gitlab-ci.yml (copied to your project)
stages:
  - quality
  - test
  - coverage
  - security
  - contract
  - e2e
  - report

quality:lint:
  stage: quality
  script:
    - npm run lint
    - npm run format:check
```

### Pre-commit Hooks

Installed via `./scripts/setup-pre-commit.sh`:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: prettier
        name: Prettier
        entry: npx prettier --check
      - id: eslint
        name: ESLint
        entry: npm run lint
      - id: sam-coverage
        name: SAM Coverage Check
        entry: npm run test:coverage
        pass_filenames: false
```

## Observability

SAM provides comprehensive observability out of the box:

### Logging

```python
from skills.shared.observability import get_logger

logger = get_logger("sam-specs")
logger.info("Generating specification", feature_id="001_user_auth")
logger.error("Failed to parse spec", error=str(e))
```

### Metrics

```python
from skills.shared.observability import get_metrics

metrics = get_metrics()
metrics.timing("spec_generation_duration_ms", duration_ms)
metrics.counter("tasks_generated", value=47)
metrics.gauge("active_features", value=3)
```

### Tracing

```python
from skills.shared.observability import get_tracer

tracer = get_tracer()
with tracer.span("generate_specification"):
    # Your code here
    tracer.add_event("context7_query")
    tracer.set_attribute("feature_id", "001_user_auth")
```

### Error Tracking

```python
from skills.shared.observability import get_error_tracker

error_tracker = get_error_tracker()
error_tracker.track_exception(e, context={
    "feature_id": "001_user_auth",
    "phase": "specs"
})
```

### Decorators

```python
from skills.shared.observability import observe, timed, catch_and_track

@observe()
def generate_spec():
    pass

@timed()
def parse_tasks():
    pass

@catch_and_track()
def risky_operation():
    pass
```

## Directory Structure

### Plugin Directory (Installed Once)

The SAM plugin is installed in Claude Code's plugins directory:

```
~/.claude/plugins/sam-plugin/ (or %APPDATA%\claude\plugins\sam-plugin on Windows)
├── skills/
│   ├── sam-quick/SKILL.md              # Quick task handler
│   ├── sam-discover/SKILL.md           # Feature discovery
│   ├── sam-stories/SKILL.md            # User story generation
│   ├── sam-specs/
│   │   ├── SKILL.md                    # Technical specification
│   │   └── scripts/
│   │       ├── spec_parser.py          # Parse specs
│   │       ├── codebase_analyzer.py    # Analyze codebase
│   │       ├── classify_project.py     # Classify project type
│   │       ├── test_generator.py       # Generate tests
│   │       ├── openapi_generator.py    # Generate OpenAPI
│   │       ├── security_test_generator.py  # OWASP tests
│   │       └── ... (16 generators)
│   ├── sam-develop/
│   │   ├── SKILL.md                    # Development orchestration
│   │   └── scripts/
│   │       ├── task_registry.py        # TASKS.json management
│   │       ├── lint_build_test.sh      # Quality gate script
│   │       ├── coverage_enforcer.py    # Coverage enforcement
│   │       ├── rollback_manager.py     # Rollback capability
│   │       └── ci_helpers.py           # CI helpers
│   ├── sam-validate/
│   │   ├── SKILL.md                    # Validation & verification
│   │   └── scripts/
│   │       ├── code_task_mapper.py     # Code-to-task mapping
│   │       ├── conflict_detector.py    # Conflict detection
│   │       ├── phase_gate_validator.py # Phase gate validation
│   │       └── verification_linker.py  # Verification linking
│   ├── sam-observe/
│   │   ├── SKILL.md                    # Observability system
│   │   ├── sam_logger.py               # Structured logging
│   │   ├── metrics_collector.py        # Metrics collection
│   │   ├── tracing_context.py          # Distributed tracing
│   │   ├── error_tracker.py            # Error tracking
│   │   └── cli.py                      # Observability CLI
│   ├── sam-status/
│   │   ├── SKILL.md                    # Status tracking
│   │   └── scripts/
│   │       └── status_report.py        # Status reporting
│   └── shared/
│       └── observability/__init__.py   # Shared observability API
├── templates/
│   ├── feature/FEATURE_TEMPLATE.md     # Feature documentation
│   ├── stories/USER_STORY_TEMPLATE.md  # User story structure
│   ├── specs/
│   │   ├── TECHNICAL_SPEC_TEMPLATE.md  # Technical specification
│   │   └── OPENAPI_TEMPLATE.yaml       # OpenAPI 3.0 template
│   ├── CONTEXT.yaml                    # Global context variables
│   ├── observability/
│   │   └── OBSERVABILITY_CONFIG.yaml   # Observability configuration
│   ├── validation/
│   │   └── TRACEABILITY_TEMPLATE.md    # Traceability matrix
│   └── ci/DEPLOYMENT_GATE.md           # Pre-deployment checklist
├── .github/workflows/
│   └── sam-quality-gate.yml           # GitHub Actions CI template
├── .gitlab-ci.yml                      # GitLab CI template
├── .pre-commit-config.yaml             # Pre-commit hooks template
├── scripts/
│   ├── observe-setup.sh                # Observability setup script
│   └── setup-pre-commit.sh             # Pre-commit setup script
└── config/
    └── observability.yaml              # Observability config
```

### Your Project Directory (.sam/)

SAM creates a `.sam/` directory in **your project root** (not the plugin directory):

```
your-project/
├── .sam/
│   ├── 001_user_auth/
│   │   ├── FEATURE_DOCUMENTATION.md        # From sam-discover
│   │   ├── stories/
│   │   │   ├── 001_oauth_integration.md   # From sam-stories
│   │   │   └── 002_user_profile.md
│   │   ├── specs/
│   │   │   ├── PHASE_1_AUTH_FLOW.md       # From sam-specs
│   │   │   ├── PHASE_2_API_DESIGN.md
│   │   │   ├── TASKS.json                  # Task registry
│   │   │   └── EXECUTABLE_SPEC.yaml        # Executable spec
│   │   ├── VERIFICATION_REPORT.md          # From sam-validate
│   │   └── QUICK_TASK.md                   # From sam-quick (if small)
│   ├── logs/                               # Structured JSON logs
│   ├── metrics/                            # Performance metrics
│   ├── traces/                             # Distributed traces
│   ├── errors/                             # Error reports
│   ├── scripts/                            # Copied setup scripts (optional)
│   └── STATUS.md                           # Overall status
├── .github/workflows/
│   └── sam-quality-gate.yml           # Copied from plugin templates
├── .gitlab-ci.yml                      # Copied from plugin templates
└── .pre-commit-config.yaml             # Copied from plugin templates
```

## Advanced Features

### TASKS.json - 98% Token Reduction

The heart of SAM's incremental reading capability:

```json
{
  "metadata": {
    "feature_id": "001_user_auth",
    "feature_name": "User Authentication",
    "spec_version": "2.0",
    "total_tasks": 47,
    "completed_tasks": 23,
    "current_phase": "2"
  },
  "phases": [
    {
      "phase_id": "1",
      "phase_name": "Authentication Flow",
      "tasks": [
        {
          "task_id": "1.1",
          "title": "Setup OAuth2 provider",
          "status": "completed",
          "assignee": "agent-1"
        }
      ]
    }
  ],
  "checkpoint": {
    "last_completed_task": "1.15",
    "last_checkpoint_time": "2025-01-15T10:30:00Z",
    "iteration_count": 0
  }
}
```

### Parallel Execution

SAM spawns up to 3 subagents in parallel for independent tasks:

```python
# sam-develop automatically detects parallelizable tasks
parallel_tasks = detect_parallelizable_tasks(tasks)
if len(parallel_tasks) > 1:
    # Detect deadlocks before spawning
    if has_deadlock(parallel_tasks):
        resolve_deadlock(parallel_tasks)
    # Spawn in batches of 3
    for batch in chunks(parallel_tasks, 3):
        results = execute_parallel(batch)
        if any_failed(results):
            rollback_batch(batch)
```

### Checkpoint/Resume

Long-running tasks can be paused and resumed:

```bash
# Start development
/sam-develop start implementation

# ... later, resume from checkpoint
/sam-develop resume from checkpoint

# SAM reads TASKS.json and continues from last checkpoint
```

### Rollback Capability

Failed parallel batches are automatically rolled back:

```bash
# If any task in a parallel batch fails:
1. Stop all in-flight tasks
2. Revert all completed tasks in batch
3. Report failure to user
4. Offer retry with sequential execution
```

### Deadlock Detection

SAM detects circular dependencies before parallel execution:

```python
# Builds dependency graph and detects cycles
if has_cycle(dependency_graph):
    resolve_cycles(dependency_graph)
    # Offer resolution options to user
```

### Shift-Left Verification

Verify each task immediately after implementation:

```bash
# Traditional (verify at end)
Implement all tasks → Run all tests → Fix failures

# SAM Shift-Left (verify continuously)
Implement task 1 → Verify task 1 → Fix immediately
Implement task 2 → Verify task 2 → Fix immediately
...
```

## Troubleshooting

### Plugin-Specific Issues

**Issue: "SAM skills not recognized"**
- **Cause**: Plugin not loaded after installation
- **Solution**: Restart Claude Code after installing the plugin

**Issue: "Scripts not found" error**
- **Cause**: Script path incorrect or scripts not copied to project
- **Solution**: Use absolute path to plugin scripts (`~/.claude/plugins/sam-plugin/scripts/`) or copy scripts to your project's `.sam/scripts/` directory

**Issue: "Claude Code plugins directory not found"**
- **Cause**: Claude Code plugins directory doesn't exist yet
- **Solution**: Create the directory first: `mkdir -p ~/.claude/plugins/` (or `%APPDATA%\claude\plugins\` on Windows)

**Issue: "CI/CD workflows not running"**
- **Cause**: CI/CD template files not copied to your project
- **Solution**: Copy template files from plugin to your project:
  ```bash
  cp ~/.claude/plugins/sam-plugin/.github/workflows/sam-quality-gate.yml .github/workflows/
  cp ~/.claude/plugins/sam-plugin/.gitlab-ci.yml .
  cp ~/.claude/plugins/sam-plugin/.pre-commit-config.yaml .
  ```

### Workflow-Specific Issues

**Issue: "Feature not found" error**
- **Cause**: Feature documentation doesn't exist in `.sam/`
- **Solution**: Run `/sam-discover` first to create feature documentation

**Issue: "TASKS.json not found" error**
- **Cause**: Technical specification hasn't been generated
- **Solution**: Run `/sam-specs` to generate TASKS.json

**Issue: "Quality gate failed" error**
- **Cause**: Linting, type-check, build, or tests failed
- **Solution**: Run `npm run lint`, `npm run type-check`, `npm run build`, `npm test` locally

**Issue: "Parallel execution deadlock" error**
- **Cause**: Circular dependencies detected between tasks
- **Solution**: SAM will offer resolution options (break cycle, sequential execution)

**Issue: "Coverage below 80%" error**
- **Cause**: Test coverage is below threshold
- **Solution**: Add tests for uncovered code paths

**Issue: "Observability not initialized" error**
- **Cause**: `.sam/` directory doesn't exist in your project
- **Solution**: Run the setup script in your project directory:
  ```bash
  ~/.claude/plugins/sam-plugin/scripts/observe-setup.sh
  # or if you copied scripts:
  ./.sam/scripts/observe-setup.sh
  ```

### Debug Mode

Enable debug logging:

```bash
export SAM_LOG_LEVEL=DEBUG
/sam-develop start implementation
```

### Diagnostic Export

Export observability data for debugging:

```bash
python3 -m skills.sam_observe.cli export --output diag.zip
```

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run quality gates (`./skills/sam-develop/scripts/lint_build_test.sh`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- **JavaScript/TypeScript**: Prettier + ESLint
- **Python**: Black + Flake8
- **Markdown**: 80-character line width where possible

### Testing

- Unit tests: 80%+ coverage required
- Integration tests: For cross-skill functionality
- Contract tests: For API boundaries

### Skill Guidelines

When creating new skills:

1. Follow the existing SKILL.md structure
2. Use the shared observability API
3. Generate TASKS.json for long-running tasks
4. Include quality gate enforcement
5. Document trigger phrases and usage

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built for [Claude Code](https://claude.com/claude-code)
- Inspired by [INVEST criteria](https://www.agilealliance.org/invest/) for user stories
- Quality gates based on [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- Observability design inspired by [OpenTelemetry](https://opentelemetry.io/)

---

**Made with ❤️ by the SAM Plugin Team**
