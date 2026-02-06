#!/usr/bin/env python3
"""
state_machine_generator.py - Generate state machine code from YAML definitions

This script reads parsed state machine definitions from SCENARIOS.json and
generates executable state machine code in various frameworks:
- XState (TypeScript/JavaScript)
- Python transitions library
- Mermaid diagrams for documentation

Usage:
    python3 skills/sam-specs/scripts/state_machine_generator.py <feature_dir> [--framework xstate|transitions|mermaid] [--all]
    python3 skills/sam-specs/scripts/state_machine_generator.py .sam/001_user_auth --framework xstate
    python3 skills/sam-specs/scripts/state_machine_generator.py .sam/001_user_auth --all

Output:
    Generates state machine code in .sam/{feature}/state-machines/
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from stringcase import camelcase, pascalcase, snakecase


@dataclass
class StateMachineConfig:
    """Configuration for state machine code generation."""
    framework: str  # "xstate", "transitions", "mermaid"
    output_dir: Path
    machine_name: str
    add_types: bool = True
    add_logging: bool = True
    add_guards: bool = True


@dataclass
class GeneratedState:
    """State information for code generation."""
    state_id: str
    name: str
    on_entry: List[str]
    transitions: List[Dict[str, Any]]
    is_final: bool = False


class StateMachineGenerator:
    """Generate state machine code from YAML definitions."""

    def __init__(self, scenarios_file: Path, framework: str = "xstate"):
        """
        Initialize the state machine generator.

        Args:
            scenarios_file: Path to SCENARIOS.json
            framework: Target framework ("xstate", "transitions", "mermaid")
        """
        self.scenarios_file = scenarios_file
        self.framework = framework.lower()
        self.feature_dir = scenarios_file.parent
        self.data: Dict[str, Any] = {}
        self.state_machines: List[Dict[str, Any]] = []

    def load_scenarios(self) -> None:
        """Load state machines from SCENARIOS.json."""
        with open(self.scenarios_file, 'r') as f:
            self.data = json.load(f)
        self.state_machines = self.data.get("state_machines", [])

    def generate_all(self) -> None:
        """Generate all state machine code files."""
        self.load_scenarios()

        if not self.state_machines:
            print("  ⚠ No state machines found in SCENARIOS.json")
            return

        if self.framework == "xstate":
            self._generate_xstate_all()
        elif self.framework == "transitions":
            self._generate_transitions_all()
        elif self.framework == "mermaid":
            self._generate_mermaid_all()
        elif self.framework == "all":
            self._generate_xstate_all()
            self._generate_transitions_all()
            self._generate_mermaid_all()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    # ==================== XState Generation ====================

    def _generate_xstate_all(self) -> None:
        """Generate all XState machine files."""
        output_dir = self.feature_dir / "state-machines" / "xstate"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate types file
        types_content = self._generate_xstate_types_file()
        types_file = output_dir / "types.ts"
        with open(types_file, 'w') as f:
            f.write(types_content)
        print(f"  ✓ Generated XState types: {types_file}")

        # Generate individual machine files
        for sm in self.state_machines:
            machine_content = self._generate_xstate_machine(sm)
            machine_name = pascalcase(sm["name"])
            machine_file = output_dir / f"{machine_name}Machine.ts"
            with open(machine_file, 'w') as f:
                f.write(machine_content)
            print(f"  ✓ Generated XState machine: {machine_file}")

        # Generate index file
        index_content = self._generate_xstate_index()
        index_file = output_dir / "index.ts"
        with open(index_file, 'w') as f:
            f.write(index_content)
        print(f"  ✓ Generated XState index: {index_file}")

    def _generate_xstate_machine(self, sm: Dict[str, Any]) -> str:
        """Generate XState machine configuration."""
        machine_name = pascalcase(sm["name"])
        machine_id = sm["machine_id"]
        description = sm["description"]
        initial_state = sm["initial_state"]
        states = sm["states"]

        # Generate context interface
        context_interface = self._generate_xstate_context_interface(sm)

        # Generate events type
        events_type = self._generate_xstate_events_type(sm)

        # Generate states configuration
        states_config = self._generate_xstate_states(states, sm)

        # Generate guards
        guards = self._generate_xstate_guards(sm)

        # Generate services
        services = self._generate_xstate_services(sm)

        # Generate actions
        actions = self._generate_xstate_actions(sm)

        return f'''/**
 * {machine_name} - {description}
 *
 * Auto-generated from EXECUTABLE_SPEC.yaml
 * Source: {self.data["metadata"]["feature_id"]}
 * Generated: {datetime.now().isoformat()}
 */

import {{ createMachine, assign }} from 'xstate';
import type {{ StateMachineConfig }} from 'xstate';

{context_interface}

{events_type}

export const {machine_name}Machine = createMachine<{machine_name}Context, {machine_name}Event>({{
  id: '{machine_id}',
  initial: '{initial_state}',
  context: {{
    userId: null,
    error: null,
    attempts: 0,
  }},
  states: {{
{states_config}
  }},
}}, {{
{guards}{services}{actions}
}});
'''

    def _generate_xstate_context_interface(self, sm: Dict[str, Any]) -> str:
        """Generate TypeScript interface for machine context."""
        machine_name = pascalcase(sm["name"])
        return f'''interface {machine_name}Context {{
  userId: string | null;
  error: string | null;
  attempts: number;
}}'''

    def _generate_xstate_events_type(self, sm: Dict[str, Any]) -> str:
        """Generate TypeScript type for machine events."""
        machine_name = pascalcase(sm["name"])

        # Collect unique events from all transitions
        events = set()
        for state in sm["states"]:
            for transition in state.get("transitions", []):
                events.add(transition.get("event", "UNKNOWN"))

        event_types = []
        for event in sorted(events):
            event_name = camelcase(event)
            event_types.append(f"  | {{ type: '{event}' }}")

        return f'''type {machine_name}Event =
{chr(10).join(event_types)};'''

    def _generate_xstate_states(self, states: List[Dict], sm: Dict[str, Any]) -> str:
        """Generate XState states configuration."""
        lines = []

        for state in states:
            state_id = state["state_id"]
            state_name = state["name"]
            on_entry = state.get("on_entry", [])
            transitions = state.get("transitions", [])
            is_final = state.get("final", False)

            lines.append(f"    {state_id}: {{")

            # Add entry actions
            if on_entry:
                entry_actions = ", ".join([f"'{action}'" for action in on_entry])
                lines.append(f"      onEntry: [{entry_actions}],")

            # Add final state marker
            if is_final:
                lines.append(f"      type: 'final',")

            # Add transitions
            if transitions and not is_final:
                lines.append(f"      on: {{")
                for transition in transitions:
                    event = transition.get("event", "UNKNOWN")
                    target = transition.get("target", "")
                    guard = transition.get("guard")
                    action = transition.get("action")

                    line = f"        {event}: '{target}'"
                    if guard:
                        line += f","
                        lines.append(f"        {event}: {{")
                        lines.append(f"          target: '{target}',")
                        lines.append(f"          cond: '{guard}',")
                        if action:
                            lines.append(f"          actions: ['{action}'],")
                        lines.append(f"        }},")
                    else:
                        lines.append(f"        {event}: '{target}',")
                lines.append(f"      }},")

            lines.append(f"    }},")

        return "\n".join(lines)

    def _generate_xstate_guards(self, sm: Dict[str, Any]) -> str:
        """Generate XState guards configuration."""
        # Collect unique guards from all transitions
        guards = set()
        for state in sm["states"]:
            for transition in state.get("transitions", []):
                guard = transition.get("guard")
                if guard:
                    guards.add(guard)

        if not guards:
            return ""

        lines = ["  guards: {"]
        for guard in sorted(guards):
            guard_name = camelcase(guard)
            lines.append(f"    {guard}: (context, event) => {{")
            lines.append(f"      // TODO: Implement guard logic for {guard}")
            lines.append(f"      return true;")
            lines.append(f"    }},")
        lines.append("  },")

        return "\n".join(lines) + "\n"

    def _generate_xstate_services(self, sm: Dict[str, Any]) -> str:
        """Generate XState services configuration."""
        # Services would typically be defined from state invocations
        # For now, return empty - can be extended based on YAML spec
        return ""

    def _generate_xstate_actions(self, sm: Dict[str, Any]) -> str:
        """Generate XState actions configuration."""
        # Collect unique actions from on_entry and transitions
        actions = set()

        for state in sm["states"]:
            for action in state.get("on_entry", []):
                actions.add(action)
            for transition in state.get("transitions", []):
                action = transition.get("action")
                if action:
                    actions.add(action)

        if not actions:
            return ""

        lines = ["  actions: {"]
        for action in sorted(actions):
            action_name = camelcase(action)
            lines.append(f"    {action}: (context, event) => {{")
            lines.append(f"      // TODO: Implement action logic for {action}")
            lines.append(f"    }},")
        lines.append("  },")

        return "\n".join(lines) + "\n"

    def _generate_xstate_types_file(self) -> str:
        """Generate shared types file for XState machines."""
        return '''/**
 * Shared types for XState state machines
 */

export interface BaseMachineContext {
  userId: string | null;
  error: string | null;
  attempts: number;
}

export type MachineEvent<T = string> = {
  type: T;
  data?: any;
};
'''

    def _generate_xstate_index(self) -> str:
        """Generate index file exporting all machines."""
        exports = []
        for sm in self.state_machines:
            machine_name = pascalcase(sm["name"])
            exports.append(f"export * from './{machine_name}Machine';")

        return f'''/**
 * XState state machines for {self.data["metadata"]["feature_name"]}
 *
 * Auto-generated from EXECUTABLE_SPEC.yaml
 * Generated: {datetime.now().isoformat()}
 */

{chr(10).join(exports)}
'''

    # ==================== Python Transitions Generation ====================

    def _generate_transitions_all(self) -> None:
        """Generate all Python transitions files."""
        output_dir = self.feature_dir / "state-machines" / "transitions"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate models file
        models_content = self._generate_transitions_models()
        models_file = output_dir / "models.py"
        with open(models_file, 'w') as f:
            f.write(models_content)
        print(f"  ✓ Generated Transitions models: {models_file}")

        # Generate individual machine files
        for sm in self.state_machines:
            machine_content = self._generate_transitions_machine(sm)
            machine_name = snakecase(sm["name"])
            machine_file = output_dir / f"{machine_name}.py"
            with open(machine_file, 'w') as f:
                f.write(machine_content)
            print(f"  ✓ Generated Transitions machine: {machine_file}")

    def _generate_transitions_models(self) -> str:
        """Generate base models for Python state machines."""
        return '''"""
Base models for Python transitions state machines
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class BaseStateMachineModel:
    """Base model for state machine context."""

    user_id: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "user_id": self.user_id,
            "error": self.error,
            "attempts": self.attempts,
        }
'''

    def _generate_transitions_machine(self, sm: Dict[str, Any]) -> str:
        """Generate Python transitions machine."""
        machine_name = pascalcase(sm["name"])
        machine_snake = snakecase(sm["name"])
        machine_id = sm["machine_id"]
        description = sm["description"]
        initial_state = sm["initial_state"]
        states = sm["states"]

        # Generate model class
        model_class = self._generate_transitions_model_class(sm)

        # Generate state configurations
        state_configs = self._generate_transitions_states(states, sm)

        return f'''"""
{machine_name} - {description}

Auto-generated from EXECUTABLE_SPEC.yaml
Source: {self.data["metadata"]["feature_id"]}
Generated: {datetime.now().isoformat()}
"""

from transitions import Machine
from transitions.extensions.nesting import NestedMachine
from typing import Optional, Dict, Any, List


{model_class}


class {machine_name}Machine:
    """
    State machine for {machine_snake}.

    {description}
    """

    def __init__(self, model: {machine_name}Model):
        """
        Initialize the state machine.

        Args:
            model: State model instance
        """
        self.model = model
        self.machine = self._create_machine()

    def _create_machine(self) -> Machine:
        """Create and configure the transitions Machine."""
        states = [
{state_configs}
        ]

        machine = Machine(
            model=self.model,
            states=states,
            initial='{initial_state}',
            send_event=True,
            auto_transitions=False,
            model_attribute='state',
        )

        return machine

    # Guard conditions
    def _get_guards(self) -> Dict[str, callable]:
        """Get all guard condition methods."""
        return {{
            # Guards would be defined here based on YAML spec
        }}

    # Callbacks
    def on_transition(self, event_data):
        """Called on every state transition."""
        print(f"Transition: {{event_data.transition}}")
        print(f"State: {{event_data.state.name}}")
'''

    def _generate_transitions_model_class(self, sm: Dict[str, Any]) -> str:
        """Generate model class for state machine."""
        machine_name = pascalcase(sm["name"])

        # Generate guard methods
        guard_methods = self._generate_transitions_guard_methods(sm)

        # Generate action methods
        action_methods = self._generate_transitions_action_methods(sm)

        return f'''class {machine_name}Model:
    """State model for {machine_name}."""

    def __init__(self):
        self.user_id: Optional[str] = None
        self.error: Optional[str] = None
        self.attempts: int = 0

{guard_methods}
{action_methods}'''

    def _generate_transitions_guard_methods(self, sm: Dict[str, Any]) -> str:
        """Generate guard condition methods."""
        guards = set()
        for state in sm["states"]:
            for transition in state.get("transitions", []):
                guard = transition.get("guard")
                if guard:
                    guards.add(guard)

        if not guards:
            return ""

        lines = ["    # Guard conditions"]
        for guard in sorted(guards):
            guard_name = snakecase(guard)
            lines.append(f"    def {guard_name}(self) -> bool:")
            lines.append(f'        """Check if {guard}."""')
            lines.append(f"        # TODO: Implement guard logic")
            lines.append(f"        return True")
            lines.append("")

        return "\n    ".join(lines)

    def _generate_transitions_action_methods(self, sm: Dict[str, Any]) -> str:
        """Generate action methods."""
        actions = set()

        for state in sm["states"]:
            for action in state.get("on_entry", []):
                actions.add(action)
            for transition in state.get("transitions", []):
                action = transition.get("action")
                if action:
                    actions.add(action)

        if not actions:
            return ""

        lines = ["    # Action methods"]
        for action in sorted(actions):
            action_name = snakecase(action)
            lines.append(f"    def {action_name}(self) -> None:")
            lines.append(f'        """Execute {action}."""')
            lines.append(f"        # TODO: Implement action logic")
            lines.append(f"        pass")
            lines.append("")

        return "\n    ".join(lines)

    def _generate_transitions_states(self, states: List[Dict], sm: Dict[str, Any]) -> str:
        """Generate state configurations for transitions."""
        lines = []

        for state in states:
            state_id = state["state_id"]
            state_name = state["name"]
            on_entry = state.get("on_entry", [])
            transitions = state.get("transitions", [])
            is_final = state.get("final", False)

            lines.append(f"            {{")
            lines.append(f"                'name': '{state_id}',")

            if on_entry:
                entry_callbacks = ", ".join([f"'{snakecase(action)}'" for action in on_entry])
                lines.append(f"                'on_enter': [{entry_callbacks}],")

            if is_final:
                lines.append(f"                'tags': ['final'],")

            if transitions:
                lines.append(f"                'transitions': [")
                for transition in transitions:
                    event = transition.get("event", "UNKNOWN")
                    target = transition.get("target", "")
                    guard = transition.get("guard")

                    line = f"                    {{'trigger': '{snakecase(event)}', 'dest': '{target}'"
                    if guard:
                        line += f", 'conditions': '{snakecase(guard)}'"
                    line += "},"
                    lines.append(line)

                lines.append(f"                ],")

            lines.append(f"            }},")

        return "\n".join(lines)

    # ==================== Mermaid Diagram Generation ====================

    def _generate_mermaid_all(self) -> None:
        """Generate all Mermaid diagram files."""
        output_dir = self.feature_dir / "state-machines" / "diagrams"
        output_dir.mkdir(parents=True, exist_ok=True)

        for sm in self.state_machines:
            diagram_content = self._generate_mermaid_diagram(sm)
            machine_name = snakecase(sm["name"])
            diagram_file = output_dir / f"{machine_name}.mmd"
            with open(diagram_file, 'w') as f:
                f.write(diagram_content)
            print(f"  ✓ Generated Mermaid diagram: {diagram_file}")

    def _generate_mermaid_diagram(self, sm: Dict[str, Any]) -> str:
        """Generate Mermaid stateDiagram-v2."""
        machine_id = sm["machine_id"]
        machine_name = sm["name"]
        description = sm["description"]
        initial_state = sm["initial_state"]
        states = sm["states"]

        lines = [
            f"'''",
            f"State Machine: {machine_name}",
            f"ID: {machine_id}",
            f"{description}",
            f"'''",
            "",
            "stateDiagram-v2",
            f"    [*] --> {initial_state}",
            ""
        ]

        for state in states:
            state_id = state["state_id"]
            state_name = state["name"]
            on_entry = state.get("on_entry", [])
            transitions = state.get("transitions", [])
            is_final = state.get("final", False)

            # Add state definition with name
            lines.append(f"    {state_id}: {state_name}")

            # Add transitions
            for transition in transitions:
                event = transition.get("event", "UNKNOWN")
                target = transition.get("target", "")
                guard = transition.get("guard")
                after = transition.get("after")

                transition_line = f"    {state_id} --> {target}: {event}"

                # Add guard or timeout as note
                if guard:
                    transition_line += f" ({guard})"
                elif after:
                    transition_line += f" (after {after})"

                lines.append(transition_line)

            # Add final state marker
            if is_final:
                lines.append(f"    {state_id} --> [*]")

            # Add note for entry actions
            if on_entry:
                lines.append(f"    note right of {state_id}")
                for action in on_entry:
                    lines.append(f"        on_entry: {action}")
                lines.append(f"    end note")

            lines.append("")

        return "\n".join(lines)

    # ==================== Validation ====================

    def _validate_transitions(self, sm: Dict[str, Any]) -> List[str]:
        """
        Validate state machine transitions.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        state_ids = {state["state_id"] for state in sm["states"]}

        # Check initial state exists
        if sm["initial_state"] not in state_ids:
            errors.append(f"Initial state '{sm['initial_state']}' not found in states")

        # Check all transitions reference valid states
        for state in sm["states"]:
            state_id = state["state_id"]
            for transition in state.get("transitions", []):
                target = transition.get("target")
                if target and target not in state_ids:
                    errors.append(
                        f"Transition from '{state_id}' to invalid state '{target}'"
                    )

        return errors


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 state_machine_generator.py <feature_dir> [--framework xstate|transitions|mermaid] [--all]")
        print("Example: python3 state_machine_generator.py .sam/001_user_auth --framework xstate")
        print("Example: python3 state_machine_generator.py .sam/001_user_auth --all")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    framework = "xstate"

    # Parse optional framework argument
    if len(sys.argv) >= 4 and sys.argv[2] == "--framework":
        framework = sys.argv[3]
    elif len(sys.argv) >= 3 and sys.argv[2] == "--all":
        framework = "all"

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Find scenarios file
    scenarios_file = feature_dir / "SCENARIOS.json"

    if not scenarios_file.exists():
        print(f"Error: SCENARIOS.json not found in {feature_dir}")
        print("Hint: Run scenario_parser.py first to generate SCENARIOS.json")
        sys.exit(1)

    # Generate state machines
    print(f"Generating {framework.upper()} state machines from: {scenarios_file}")
    generator = StateMachineGenerator(scenarios_file, framework)
    generator.generate_all()

    # Validate if not generating all
    if framework != "all":
        for sm in generator.state_machines:
            errors = generator._validate_transitions(sm)
            if errors:
                print(f"\n  ⚠ Validation errors for {sm['name']}:")
                for error in errors:
                    print(f"    - {error}")
            else:
                print(f"  ✓ State machine '{sm['name']}' is valid")

    print(f"\n✓ State machine generation complete!")
    print(f"  Framework: {framework.upper()}")
    print(f"  State machines: {len(generator.state_machines)}")
    print(f"  Output directory: {feature_dir / 'state-machines'}")


if __name__ == "__main__":
    main()
