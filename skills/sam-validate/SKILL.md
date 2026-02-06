# SAM-Validate Skill

Phase 4: Validation & Verification - Comprehensive quality assurance and traceability for the SAM workflow.

## Overview

SAM-Validate provides four core capabilities for ensuring feature implementation quality:

1. **Code-to-Task Mapping** (`code_task_mapper.py`) - Bidirectional traceability between code and requirements
2. **Conflict Detection** (`conflict_detector.py`) - Detect resource and logic conflicts between parallel tasks
3. **Phase Gate Validation** (`phase_gate_validator.py`) - Enforce quality thresholds before phase transitions
4. **Verification Linking** (`verification_linker.py`) - Link tasks to tests and generate traceability matrices

## Installation

The skill is automatically available when SAM-Plugin is installed. All scripts are located in:
```
skills/sam-validate/scripts/
```

## Tools

### 1. Code-to-Task Mapper

Maps code artifacts (files, functions, classes, endpoints) to their implementing tasks through multiple discovery strategies.

**Discovery Methods:**
- **Static Analysis**: Parses `@task` annotations in source code
- **Git Blame**: Analyzes commit messages for task references
- **Directory Heuristics**: Infers tasks from directory structure (e.g., `features/001/` → task `1.1`)
- **Endpoint Registration**: Maps API routes to tasks

**Usage:**
```bash
# Scan entire codebase and generate mappings
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/{feature} --scan

# Find which task implements specific code
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/{feature} \
    --map-file src/api/users.ts --line 45

# Show all code implementing a task
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/{feature} \
    --task 2.1.3 --show-code

# Detect new code since baseline commit
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/{feature} \
    --detect-new --baseline main~1

# Export mappings as JSON
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/{feature} \
    --export-mappings > mappings.json
```

**Output:**
- Updates `TASKS.json` with `code_mappings` field
- Prints summary of mappings by task

**Supported Languages:**
- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.jsx`, `.ts`, `.tsx`)
- Rust (`.rs`)
- Go (`.go`)
- Java/Kotlin (`.java`, `.kt`)

**Annotation Format:**
```python
# @task 1.2.3
def user_login():
    pass
```

```typescript
// @task 2.1.3
export const handleAuth = () => {
  // ...
};
```

---

### 2. Conflict Detector

Detects conflicts between parallel task implementations before they cause production issues.

**Conflict Types:**

| Type | Description | Severity |
|------|-------------|----------|
| **File Conflicts** | Multiple tasks modifying the same file | Critical/Major/Minor |
| **Endpoint Conflicts** | Multiple tasks defining same API route | Critical |
| **Database Conflicts** | Multiple tasks modifying same table | Major |
| **Component Conflicts** | Multiple tasks implementing same component | Minor |
| **Duplicate Implementations** | Same functionality in multiple tasks | Minor |
| **Type Incompatibilities** | Interface mismatches between tasks | Major |

**Usage:**
```bash
# Run full conflict detection
python3 skills/sam-validate/scripts/conflict_detector.py .sam/{feature} --detect

# Check specific conflict types
python3 skills/sam-validate/scripts/conflict_detector.py .sam/{feature} --resource-conflicts
python3 skills/sam-validate/scripts/conflict_detector.py .sam/{feature} --logic-conflicts

# Check conflicts for specific task
python3 skills/sam-validate/scripts/conflict_detector.py .sam/{feature} \
    --task 2.1.3 --check-conflicts

# Generate detailed markdown report
python3 skills/sam-validate/scripts/conflict_detector.py .sam/{feature} \
    --report > conflicts.md

# Check for cycles involving conflicts
python3 skills/sam-validate/scripts/conflict_detector.py .sam/{feature} \
    --check-cycles
```

**Output:**
```json
{
  "total_conflicts": 3,
  "by_severity": {
    "critical": 1,
    "major": 1,
    "minor": 1
  },
  "has_blocking_conflicts": true,
  "resource_conflicts": [...],
  "logic_conflicts": [...]
}
```

**Updates TASKS.json checkpoint:**
```json
{
  "checkpoint": {
    "conflict_detection": {
      "last_scan": "2025-02-06T...",
      "total_conflicts": 3,
      "by_severity": {...},
      "has_blocking": true
    }
  }
}
```

---

### 3. Phase Gate Validator

Validates that all phase completion criteria are met before allowing phase transitions.

**Phase-Specific Criteria:**

| Phase | Tasks Complete | Quality Gate | Coverage | Conflicts | Docs |
|-------|----------------|--------------|----------|-----------|------|
| **Foundation** | ✓ | ✓ | - | ✓ | ✓ |
| **Backend** | ✓ | ✓ | 80% | ✓ | ✓ |
| **Frontend** | ✓ | ✓ | 80% | ✓ | ✓ |
| **Integration** | ✓ | ✓ | 75% | ✓ | ✓ |
| **Deployment** | ✓ | ✓ | - | ✓ | ✓ |

**Usage:**
```bash
# Validate a specific phase gate
python3 skills/sam-validate/scripts/phase_gate_validator.py .sam/{feature} \
    --validate-phase 2

# Generate completion report
python3 skills/sam-validate/scripts/phase_gate_validator.py .sam/{feature} \
    --completion-report 2 > PHASE_2_REPORT.md

# Check if transition is allowed
python3 skills/sam-validate/scripts/phase_gate_validator.py .sam/{feature} \
    --can-transition 2 3

# Validate all phase gates
python3 skills/sam-validate/scripts/phase_gate_validator.py .sam/{feature} \
    --validate-all

# List criteria for each phase
python3 skills/sam-validate/scripts/phase_gate_validator.py .sam/{feature} \
    --list-criteria
```

**Exit Codes:**
- `0`: Gate passed
- `1`: Gate failed

**Updates TASKS.json checkpoint:**
```json
{
  "checkpoint": {
    "phase_gate_status": {
      "current_phase": "3",
      "last_validated_phase": "2",
      "last_validation_time": "2025-02-06T...",
      "can_transition": true,
      "phase_2": {
        "passed": true,
        "validated_at": "2025-02-06T...",
        "criteria": {...}
      }
    }
  }
}
```

---

### 4. Verification Linker

Links tasks to their verification methods (tests, manual checks) and generates traceability matrices.

**Verification Method Types:**
- `unit_test` - Unit tests
- `integration_test` - Integration tests
- `e2e_test` - End-to-end tests
- `contract_test` - API contract tests
- `manual_check` - Manual verification

**Usage:**
```bash
# Discover all verification methods
python3 skills/sam-validate/scripts/verification_linker.py .sam/{feature} --discover

# Check verification status for a task
python3 skills/sam-validate/scripts/verification_linker.py .sam/{feature} \
    --task 2.1.3 --status

# Generate traceability matrix
python3 skills/sam-validate/scripts/verification_linker.py .sam/{feature} \
    --matrix > traceability.md

# Find verification gaps
python3 skills/sam-validate/scripts/verification_linker.py .sam/{feature} \
    --find-gaps

# Run verification for a task
python3 skills/sam-validate/scripts/verification_linker.py .sam/{feature} \
    --verify 2.1.3
```

**Test Discovery Patterns:**
- Filename: `test_task_1_2_3.ts`, `task.1.2.3.test.py`
- Test name: `test_task_1_2_3_user_login`, `it("task 1.2.3", ...)`
- Annotations: `@verifies task 1.2.3`

**Updates TASKS.json:**
```json
{
  "phases": [
    {
      "tasks": [
        {
          "task_id": "2.1.3",
          "verification_methods": [
            {
              "method_id": "...",
              "method_type": "unit_test",
              "name": "test_task_2_1_3_user_login",
              "file_path": "tests/auth.test.ts",
              "status": "passed"
            }
          ],
          "verification_status": "verified",
          "verified_at": "2025-02-06T...",
          "verification_coverage": 100.0
        }
      ]
    }
  ]
}
```

---

## Integration with SAM Workflow

### Automatic Execution

The validation tools are automatically called during SAM workflow execution:

1. **During Development** (`sam-develop`):
   - Conflict detection runs before parallel task execution
   - Code mapping updates on task completion

2. **Quality Gates** (`lint_build_test.sh`):
   - Phase gate validation runs before phase transitions
   - Verification status checked for completed tasks

3. **CI/CD Integration**:
   - All validation tools run in CI pipeline
   - Blocking failures prevent deployment

### TASKS.json Schema

Phase 4 extends TASKS.json with validation metadata:

```json
{
  "metadata": { ... },
  "phases": [
    {
      "phase_id": "2",
      "phase_name": "Backend",
      "status": "in_progress",
      "gate_result": {
        "passed": false,
        "validated_at": "2025-02-06T...",
        "criteria": {
          "all_tasks_complete": false,
          "quality_gate_passed": true,
          ...
        }
      },
      "tasks": [
        {
          "task_id": "2.1.3",
          "code_mappings": [
            {
              "file_path": "src/api/users.ts",
              "mapping_type": "endpoint",
              "name": "/api/users",
              "line_start": 45,
              "line_end": 78,
              "discovery_method": "annotation"
            }
          ],
          "verification_methods": [...],
          "verification_status": "verified",
          "verification_coverage": 100.0
        }
      ]
    }
  ],
  "checkpoint": {
    "phase_gate_status": { ... },
    "conflict_detection": { ... },
    "verification_status": { ... },
    "code_mappings": { ... }
  }
}
```

---

## Usage Examples

### Example 1: Before Phase Transition

```bash
# Validate phase 2 gate
python3 skills/sam-validate/scripts/phase_gate_validator.py .sam/001_feature \
    --validate-phase 2

# If passed, transition to phase 3
if [ $? -eq 0 ]; then
    python3 skills/sam-validate/scripts/phase_gate_validator.py .sam/001_feature \
        --can-transition 2 3
fi
```

### Example 2: Finding Conflicts

```bash
# Detect all conflicts
python3 skills/sam-validate/scripts/conflict_detector.py .sam/001_feature --detect

# Check specific task
python3 skills/sam-validate/scripts/conflict_detector.py .sam/001_feature \
    --task 2.1.3 --check-conflicts

# Generate report for review
python3 skills/sam-validate/scripts/conflict_detector.py .sam/001_feature \
    --report > conflicts.md
```

### Example 3: Traceability Report

```bash
# Discover verification methods
python3 skills/sam-validate/scripts/verification_linker.py .sam/001_feature --discover

# Generate traceability matrix
python3 skills/sam-validate/scripts/verification_linker.py .sam/001_feature \
    --matrix > traceability.md

# Find gaps
python3 skills/sam-validate/scripts/verification_linker.py .sam/001_feature \
    --find-gaps
```

### Example 4: Code Mapping

```bash
# Scan codebase
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/001_feature --scan

# Find which task owns code
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/001_feature \
    --map-file src/api/auth.ts --line 123

# Show task code map
python3 skills/sam-validate/scripts/code_task_mapper.py .sam/001_feature \
    --task 2.1.3 --show-code
```

---

## Requirements

**Python Packages:**
- `dataclasses` (built-in)
- `pathlib` (built-in)
- `json` (built-in)
- `re` (built-in)
- `datetime` (built-in)
- `subprocess` (built-in)
- `typing` (built-in)
- `ast` (built-in)

**No external dependencies required** - all tools use Python standard library.

**Optional:**
- `gitpython` - For enhanced git history analysis
- Test frameworks (Jest, Pytest, etc.) - For running tests

---

## Template Files

### Traceability Template

Location: `templates/validation/TRACEABILITY_TEMPLATE.md`

Provides a structured format for documenting requirements-to-tests traceability.

---

## Contributing

When adding new validation capabilities:

1. Follow the existing CLI interface pattern
2. Update TASKS.json checkpoint with results
3. Provide clear exit codes (0 = success, 1 = failure)
4. Generate human-readable output
5. Support JSON output for automation
6. Update this documentation

---

## License

Part of SAM-Plugin. See main LICENSE file.
