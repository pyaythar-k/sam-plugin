---

# State Machine Modeling

**WHEN TO INCLUDE**: Add this section when the feature involves complex workflows, multi-step processes, or stateful entities that transition between different states.

**CONDITIONAL**: Optional - include only if applicable to the feature.

---

## State Machine: {{MACHINE_NAME}}

### Description

{{STATE_MACHINE_DESCRIPTION}}

### Business Context

{{BUSINESS_CONTEXT}}

**States**: {{STATE_COUNT}}
**Transitions**: {{TRANSITION_COUNT}}
**Final States**: {{FINAL_STATES}}

---

### States

| State ID | State Name | Description | Entry Actions | Exit Actions |
|----------|------------|-------------|---------------|--------------|
| {{STATE_1_ID}} | {{STATE_1_NAME}} | {{STATE_1_DESCRIPTION}} | {{STATE_1_ON_ENTRY}} | {{STATE_1_ON_EXIT}} |
| {{STATE_2_ID}} | {{STATE_2_NAME}} | {{STATE_2_DESCRIPTION}} | {{STATE_2_ON_ENTRY}} | {{STATE_2_ON_EXIT}} |
| {{STATE_3_ID}} | {{STATE_3_NAME}} | {{STATE_3_DESCRIPTION}} | {{STATE_3_ON_ENTRY}} | {{STATE_3_ON_EXIT}} |

---

### Transitions

| From State | Event | To State | Guard Condition | Action | Timeout |
|------------|-------|----------|-----------------|--------|---------|
| {{FROM_STATE_1}} | {{EVENT_1}} | {{TO_STATE_1}} | {{GUARD_1}} | {{ACTION_1}} | {{TIMEOUT_1}} |
| {{FROM_STATE_2}} | {{EVENT_2}} | {{TO_STATE_2}} | {{GUARD_2}} | {{ACTION_2}} | {{TIMEOUT_2}} |
| {{FROM_STATE_3}} | {{EVENT_3}} | {{TO_STATE_3}} | {{GUARD_3}} | {{ACTION_3}} | {{TIMEOUT_3}} |

---

### State Context

The state machine maintains the following context:

```typescript
interface {{MACHINE_NAME}}Context {
  {{CONTEXT_FIELD_1}}: {{CONTEXT_TYPE_1}};
  {{CONTEXT_FIELD_2}}: {{CONTEXT_TYPE_2}};
  {{CONTEXT_FIELD_3}}: {{CONTEXT_TYPE_3}};
}
```

---

### Events

```typescript
type {{MACHINE_NAME}}Event =
  | { type: '{{EVENT_1_TYPE}}'; {{EVENT_1_PAYLOAD}} }
  | { type: '{{EVENT_2_TYPE}}'; {{EVENT_2_PAYLOAD}} }
  | { type: '{{EVENT_3_TYPE}}'; {{EVENT_3_PAYLOAD}} };
```

---

### Guards

| Guard Name | Description | Implementation |
|------------|-------------|----------------|
| {{GUARD_1_NAME}} | {{GUARD_1_DESCRIPTION}} | `{{GUARD_1_FUNCTION}}()` |
| {{GUARD_2_NAME}} | {{GUARD_2_DESCRIPTION}} | `{{GUARD_2_FUNCTION}}()` |
| {{GUARD_3_NAME}} | {{GUARD_3_DESCRIPTION}} | `{{GUARD_3_FUNCTION}}()` |

---

### Services

| Service Name | Description | Implementation |
|--------------|-------------|----------------|
| {{SERVICE_1_NAME}} | {{SERVICE_1_DESCRIPTION}} | `{{SERVICE_1_FUNCTION}}()` |
| {{SERVICE_2_NAME}} | {{SERVICE_2_DESCRIPTION}} | `{{SERVICE_2_FUNCTION}}()` |

---

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> {{INITIAL_STATE}}

    {{STATE_1}}: {{STATE_1_NAME}}
    {{STATE_1}} --> {{STATE_2}}: {{EVENT_1}} ({{GUARD_1}})
    {{STATE_1}} --> {{STATE_3}}: {{EVENT_2}} ({{TIMEOUT_1}})

    {{STATE_2}}: {{STATE_2_NAME}}
    {{STATE_2}} --> {{STATE_3}}: {{EVENT_3}}
    {{STATE_2}} --> {{STATE_4}}: {{EVENT_4}} ({{GUARD_2}})

    {{STATE_3}}: {{STATE_3_NAME}}
    {{STATE_3}} --> {{STATE_1}}: {{EVENT_5}}

    {{STATE_4}}: {{STATE_4_NAME}}
    {{STATE_4}} --> [*]

    note right of {{STATE_1}}
        on_entry: {{STATE_1_ON_ENTRY}}
        on_exit: {{STATE_1_ON_EXIT}}
    end note
```

---

### Error Handling

| Error Scenario | Handling Strategy | Target State |
|----------------|-------------------|--------------|
| {{ERROR_SCENARIO_1}} | {{ERROR_HANDLING_1}} | {{ERROR_TARGET_STATE_1}} |
| {{ERROR_SCENARIO_2}} | {{ERROR_HANDLING_2}} | {{ERROR_TARGET_STATE_2}} |
| {{ERROR_SCENARIO_3}} | {{ERROR_HANDLING_3}} | {{ERROR_TARGET_STATE_3}} |

---

### Implementation

**Generated Code Location**: `state-machines/{{MACHINE_NAME}}/`

**To Generate XState (TypeScript/JavaScript)**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework xstate
```

**To Generate Python Transitions**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework transitions
```

**To Generate Mermaid Diagram**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --framework mermaid
```

**To Generate All Frameworks**:
```bash
python3 skills/sam-specs/scripts/state_machine_generator.py .sam/{feature} --all
```

---

### Testing Strategy

1. **Unit Tests**: Test individual guards and services
2. **Integration Tests**: Test state transitions with valid and invalid inputs
3. **Visual Tests**: Verify Mermaid diagram accurately represents the state machine
4. **Edge Cases**: Test timeout scenarios, guard failures, and error handling

---

### Notes

- {{IMPLEMENTATION_NOTE_1}}
- {{IMPLEMENTATION_NOTE_2}}
- {{BUSINESS_RULE_NOTE_1}}
