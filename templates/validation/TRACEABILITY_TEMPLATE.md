# Requirements-to-Tests Traceability Matrix

**Feature**: {{FEATURE_NAME}}
**Feature ID**: {{FEATURE_ID}}
**Generated**: {{TIMESTAMP}}
**Version**: {{VERSION}}

---

## Overview

This document provides complete traceability from requirements through implementation to verification (tests).

**Coverage Summary**:
- Total Tasks: {{TOTAL_TASKS}}
- Verified Tasks: {{VERIFIED_TASKS}}
- Overall Coverage: {{COVERAGE_PERCENTAGE}}%

---

## Traceability Matrix

| Task ID | Task Title | Requirement | Acceptance Criteria | Verification Methods | Coverage | Gaps |
|---------|-----------|-------------|---------------------|---------------------|----------|------|
{{TRACEABILITY_ROWS}}

---

## Verification Gaps

### Unverified Tasks

{{UNVERIFIED_TASKS}}

### Partial Coverage

{{PARTIAL_COVERAGE_TASKS}}

---

## Detailed Task Breakdown

{{DETAILED_TASK_SECTIONS}}

---

## Verification Methods Summary

### By Type

| Method Type | Count | Status |
|-------------|-------|--------|
| Unit Tests | {{UNIT_TEST_COUNT}} | {{UNIT_TEST_STATUS}} |
| Integration Tests | {{INTEGRATION_TEST_COUNT}} | {{INTEGRATION_TEST_STATUS}} |
| E2E Tests | {{E2E_TEST_COUNT}} | {{E2E_TEST_STATUS}} |
| Contract Tests | {{CONTRACT_TEST_COUNT}} | {{CONTRACT_TEST_STATUS}} |
| Manual Checks | {{MANUAL_CHECK_COUNT}} | {{MANUAL_CHECK_STATUS}} |

### Test Files

{{TEST_FILES_LIST}}

---

## Acceptance Criteria Coverage

### Fully Covered

{{FULLY_COVERED_CRITERIA}}

### Not Covered

{{UNCOVERED_CRITERIA}}

---

## Recommendations

{{RECOMMENDATIONS}}

---

## Appendix

### Code Mappings

**Last Scan**: {{CODE_MAPPING_SCAN_DATE}}
**Total Mappings**: {{TOTAL_CODE_MAPPINGS}}

{{CODE_MAPPINGS_DETAIL}}

### Conflict Status

**Last Scan**: {{CONFLICT_SCAN_DATE}}
**Total Conflicts**: {{TOTAL_CONFLICTS}}

{{CONFLICTS_DETAIL}}

### Phase Gate Status

{{PHASE_GATE_STATUS}}

---

**Document History**:
- {{TIMESTAMP}}: Initial generation
