---

# Decision Table Modeling

**WHEN TO INCLUDE**: Add this section when the feature involves complex business rules with multiple conditions determining different actions.

**CONDITIONAL**: Optional - include only if applicable to the feature.

---

## Decision Table: {{TABLE_NAME}}

### Description

{{DECISION_TABLE_DESCRIPTION}}

### Business Context

{{BUSINESS_CONTEXT}}

**Inputs**: {{INPUT_COUNT}}
**Rules**: {{RULE_COUNT}}
**Coverage Target**: 100%

---

### Inputs

| Field | Type | Possible Values | Required | Description |
|-------|------|-----------------|----------|-------------|
| {{INPUT_1}} | {{INPUT_1_TYPE}} | {{INPUT_1_VALUES}} | {{INPUT_1_REQUIRED}} | {{INPUT_1_DESCRIPTION}} |
| {{INPUT_2}} | {{INPUT_2_TYPE}} | {{INPUT_2_VALUES}} | {{INPUT_2_REQUIRED}} | {{INPUT_2_DESCRIPTION}} |
| {{INPUT_3}} | {{INPUT_3_TYPE}} | {{INPUT_3_VALUES}} | {{INPUT_3_REQUIRED}} | {{INPUT_3_DESCRIPTION}} |

---

### Rules

| Rule | {{CONDITION_HEADER_1}} | {{CONDITION_HEADER_2}} | {{CONDITION_HEADER_3}} | {{ACTION_HEADER_1}} | {{ACTION_HEADER_2}} | {{ACTION_HEADER_3}} | Priority |
|------|------------------------|------------------------|------------------------|---------------------|---------------------|---------------------|----------|
| 1 | {{CONDITION_1_R1}} | {{CONDITION_2_R1}} | {{CONDITION_3_R1}} | {{ACTION_1_R1}} | {{ACTION_2_R1}} | {{ACTION_3_R1}} | {{PRIORITY_R1}} |
| 2 | {{CONDITION_1_R2}} | {{CONDITION_2_R2}} | {{CONDITION_3_R2}} | {{ACTION_1_R2}} | {{ACTION_2_R2}} | {{ACTION_3_R2}} | {{PRIORITY_R2}} |
| 3 | {{CONDITION_1_R3}} | {{CONDITION_2_R3}} | {{CONDITION_3_R3}} | {{ACTION_1_R3}} | {{ACTION_2_R3}} | {{ACTION_3_R3}} | {{PRIORITY_R3}} |
| 4 | {{CONDITION_1_R4}} | {{CONDITION_2_R4}} | {{CONDITION_3_R4}} | {{ACTION_1_R4}} | {{ACTION_2_R4}} | {{ACTION_3_R4}} | {{PRIORITY_R4}} |

---

### Rule Descriptions

#### Rule 1: {{RULE_1_NAME}}
**Conditions**: {{RULE_1_CONDITIONS_DESCRIPTION}}
**Actions**: {{RULE_1_ACTIONS_DESCRIPTION}}
**Priority**: {{RULE_1_PRIORITY}}
**Business Justification**: {{RULE_1_JUSTIFICATION}}

#### Rule 2: {{RULE_2_NAME}}
**Conditions**: {{RULE_2_CONDITIONS_DESCRIPTION}}
**Actions**: {{RULE_2_ACTIONS_DESCRIPTION}}
**Priority**: {{RULE_2_PRIORITY}}
**Business Justification**: {{RULE_2_JUSTIFICATION}}

#### Rule 3: {{RULE_3_NAME}}
**Conditions**: {{RULE_3_CONDITIONS_DESCRIPTION}}
**Actions**: {{RULE_3_ACTIONS_DESCRIPTION}}
**Priority**: {{RULE_3_PRIORITY}}
**Business Justification**: {{RULE_3_JUSTIFICATION}}

---

### Edge Cases

| Scenario | Input Values | Expected Output | Notes |
|----------|--------------|-----------------|-------|
| {{EDGE_CASE_1}} | {{EDGE_CASE_1_INPUTS}} | {{EDGE_CASE_1_OUTPUT}} | {{EDGE_CASE_1_NOTES}} |
| {{EDGE_CASE_2}} | {{EDGE_CASE_2_INPUTS}} | {{EDGE_CASE_2_OUTPUT}} | {{EDGE_CASE_2_NOTES}} |
| {{EDGE_CASE_3}} | {{EDGE_CASE_3_INPUTS}} | {{EDGE_CASE_3_OUTPUT}} | {{EDGE_CASE_3_NOTES}} |

---

### Test Coverage

**Generated Tests Location**: `tests/decision-tables/{{TABLE_NAME}}/`

**To Generate Jest Tests**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework jest
```

**To Generate Cucumber Tests**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework cucumber
```

**To Generate Pytest Tests**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework pytest
```

**To Generate with Edge Cases**:
```bash
python3 skills/sam-specs/scripts/decision_table_test_generator.py .sam/{feature} --framework jest --edge-cases
```

**Expected Coverage**: 100% (all rules tested)

---

### Implementation Example

#### TypeScript/JavaScript
```typescript
function {{TABLE_NAME}}(inputs: {{TABLE_NAME}}Inputs): {{TABLE_NAME}}Outputs {
  // Rule 1
  if ({{CONDITION_1_LOGIC}}) {
    return {
      {{OUTPUT_1}}: {{VALUE_1}},
      {{OUTPUT_2}}: {{VALUE_2}},
    };
  }

  // Rule 2
  if ({{CONDITION_2_LOGIC}}) {
    return {
      {{OUTPUT_1}}: {{VALUE_3}},
      {{OUTPUT_2}}: {{VALUE_4}},
    };
  }

  // Default fallback
  return {
    {{OUTPUT_1}}: {{DEFAULT_VALUE_1}},
    {{OUTPUT_2}}: {{DEFAULT_VALUE_2}},
  };
}
```

#### Python
```python
def {{table_name}}(inputs: {{TableName}}Inputs) -> {{TableName}}Outputs:
    \"\"\"Execute {{TABLE_NAME}} decision table.\"\"\"

    # Rule 1
    if {{CONDITION_1_LOGIC}}:
        return {{TableName}}Outputs(
            {{OUTPUT_1}}={{VALUE_1}},
            {{OUTPUT_2}}={{VALUE_2}},
        )

    # Rule 2
    if {{CONDITION_2_LOGIC}}:
        return {{TableName}}Outputs(
            {{OUTPUT_1}}={{VALUE_3}},
            {{OUTPUT_2}}={{VALUE_4}},
        )

    # Default fallback
    return {{TableName}}Outputs(
        {{OUTPUT_1}}={{DEFAULT_VALUE_1}},
        {{OUTPUT_2}}={{DEFAULT_VALUE_2}},
    )
```

---

### Testing Strategy

1. **Rule Coverage**: Every rule must have at least one test
2. **Data-Driven Tests**: Use parameterized tests for all rules
3. **Edge Cases**: Test boundary values and null/undefined inputs
4. **Priority Testing**: Ensure high-priority rules are tested first
5. **Regression Tests**: Add tests for any bugs found in production

---

### Maintenance

**When to Update**:
- New business rules are added
- Existing rules are modified
- New input combinations are identified
- Edge cases are discovered in production

**Update Process**:
1. Update the decision table in EXECUTABLE_SPEC.yaml
2. Re-run scenario_parser.py
3. Regenerate tests using decision_table_test_generator.py
4. Verify all new tests pass
5. Update this documentation section

---

### Notes

- {{BUSINESS_RULE_NOTE_1}}
- {{IMPLEMENTATION_NOTE_1}}
- {{TESTING_NOTE_1}}
- {{PERFORMANCE_NOTE_1}}: Consider caching if this function is called frequently
