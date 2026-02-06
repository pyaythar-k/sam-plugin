#!/usr/bin/env python3
"""
scenario_parser.py - Parse executable specifications and extract scenario metadata

This script parses EXECUTABLE_SPEC.yaml files and extracts:
- Scenarios with Given/When/Then structure
- Contract tests with schema definitions
- State machine definitions
- Decision tables for business rules

Usage:
    python3 skills/sam-specs/scripts/scenario_parser.py <feature_dir>
    python3 skills/sam-specs/scripts/scenario_parser.py .sam/001_user_auth

Output:
    Generates SCENARIOS.json with parsed scenario metadata
"""

import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class ScenarioStep:
    """Represents a single step in a scenario (Given/When/Then)."""
    step_id: str
    description: str
    action: Optional[Dict[str, Any]] = None
    assertion: Optional[Dict[str, Any]] = None
    setup: Optional[List[Dict[str, Any]]] = None


@dataclass
class Scenario:
    """Represents an executable scenario."""
    scenario_id: str
    name: str
    description: str
    story_mapping: str
    acceptance_criteria: str
    given: List[ScenarioStep] = field(default_factory=list)
    when: List[Dict[str, Any]] = field(default_factory=list)
    then: List[ScenarioStep] = field(default_factory=list)
    test_generation: Optional[Dict[str, Any]] = None


@dataclass
class ContractTest:
    """Represents a contract test for API validation."""
    contract_id: str
    name: str
    description: str
    request_schema: Dict[str, Any] = field(default_factory=dict)
    response_schema_success: Dict[str, Any] = field(default_factory=dict)
    response_schema_error: Dict[str, Any] = field(default_factory=dict)


@dataclass
class State:
    """Represents a state in a state machine."""
    state_id: str
    name: str
    on_entry: List[str] = field(default_factory=list)
    transitions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StateMachine:
    """Represents a state machine definition."""
    machine_id: str
    name: str
    description: str
    initial_state: str
    states: List[State] = field(default_factory=list)


@dataclass
class DecisionRule:
    """Represents a single rule in a decision table."""
    conditions: Dict[str, Any]
    actions: Dict[str, Any]


@dataclass
class DecisionTable:
    """Represents a decision table for business rules."""
    table_id: str
    name: str
    description: str
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    rules: List[DecisionRule] = field(default_factory=list)


@dataclass
class ExecutableSpecRegistry:
    """Complete registry for an executable specification."""
    metadata: Dict[str, str] = field(default_factory=dict)
    scenarios: List[Scenario] = field(default_factory=list)
    contract_tests: List[ContractTest] = field(default_factory=list)
    state_machines: List[StateMachine] = field(default_factory=list)
    decision_tables: List[DecisionTable] = field(default_factory=list)
    test_generation_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": self.metadata,
            "scenarios": [self._scenario_to_dict(s) for s in self.scenarios],
            "contract_tests": [asdict(ct) for ct in self.contract_tests],
            "state_machines": [self._state_machine_to_dict(sm) for sm in self.state_machines],
            "decision_tables": [self._decision_table_to_dict(dt) for dt in self.decision_tables],
            "test_generation_config": self.test_generation_config
        }

    def _scenario_to_dict(self, scenario: Scenario) -> dict:
        """Convert scenario to dictionary."""
        return {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "description": scenario.description,
            "story_mapping": scenario.story_mapping,
            "acceptance_criteria": scenario.acceptance_criteria,
            "given": [asdict(step) for step in scenario.given],
            "when": scenario.when,
            "then": [asdict(step) for step in scenario.then],
            "test_generation": scenario.test_generation
        }

    def _state_machine_to_dict(self, sm: StateMachine) -> dict:
        """Convert state machine to dictionary."""
        return {
            "machine_id": sm.machine_id,
            "name": sm.name,
            "description": sm.description,
            "initial_state": sm.initial_state,
            "states": [asdict(state) for state in sm.states]
        }

    def _decision_table_to_dict(self, dt: DecisionTable) -> dict:
        """Convert decision table to dictionary."""
        return {
            "table_id": dt.table_id,
            "name": dt.name,
            "description": dt.description,
            "inputs": dt.inputs,
            "rules": [asdict(rule) for rule in dt.rules]
        }


class ScenarioParser:
    """Parser for executable specification files."""

    def __init__(self, spec_file: Path, feature_id: str, feature_name: str):
        self.spec_file = spec_file
        self.feature_id = feature_id
        self.feature_name = feature_name
        self.content: Dict[str, Any] = {}

    def parse(self) -> ExecutableSpecRegistry:
        """Parse the executable specification file."""
        with open(self.spec_file, 'r') as f:
            self.content = yaml.safe_load(f)

        registry = ExecutableSpecRegistry()
        registry.metadata = {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "version": self.content.get("version", "1.0"),
            "parsed_at": datetime.now().isoformat()
        }

        # Parse scenarios
        if "scenarios" in self.content:
            for scenario_data in self.content["scenarios"]:
                scenario = self._parse_scenario(scenario_data)
                registry.scenarios.append(scenario)

        # Parse contract tests
        if "contract_tests" in self.content:
            for contract_data in self.content["contract_tests"]:
                contract = ContractTest(
                    contract_id=contract_data["contract_id"],
                    name=contract_data["name"],
                    description=contract_data["description"],
                    request_schema=contract_data.get("request_schema", {}),
                    response_schema_success=contract_data.get("response_schema_success", {}),
                    response_schema_error=contract_data.get("response_schema_error", {})
                )
                registry.contract_tests.append(contract)

        # Parse state machines
        if "state_machines" in self.content:
            for sm_data in self.content["state_machines"]:
                sm = self._parse_state_machine(sm_data)
                registry.state_machines.append(sm)

        # Parse decision tables
        if "decision_tables" in self.content:
            for dt_data in self.content["decision_tables"]:
                dt = self._parse_decision_table(dt_data)
                registry.decision_tables.append(dt)

        # Parse test generation config
        registry.test_generation_config = self.content.get("test_generation_config", {})

        return registry

    def _parse_scenario(self, data: Dict[str, Any]) -> Scenario:
        """Parse a single scenario."""
        given = []
        for step_data in data.get("given", []):
            step = ScenarioStep(
                step_id=step_data["step_id"],
                description=step_data["description"],
                setup=step_data.get("setup")
            )
            given.append(step)

        then = []
        for step_data in data.get("then", []):
            step = ScenarioStep(
                step_id=step_data["step_id"],
                description=step_data["description"],
                assertion=step_data.get("assertion")
            )
            then.append(step)

        return Scenario(
            scenario_id=data["scenario_id"],
            name=data["name"],
            description=data["description"],
            story_mapping=data["story_mapping"],
            acceptance_criteria=data["acceptance_criteria"],
            given=given,
            when=data.get("when", []),
            then=then,
            test_generation=data.get("test_generation")
        )

    def _parse_state_machine(self, data: Dict[str, Any]) -> StateMachine:
        """Parse a state machine definition."""
        states = []
        for state_data in data.get("states", []):
            state = State(
                state_id=state_data["state_id"],
                name=state_data["name"],
                on_entry=state_data.get("on_entry", []),
                transitions=state_data.get("transitions", [])
            )
            states.append(state)

        return StateMachine(
            machine_id=data["machine_id"],
            name=data["name"],
            description=data["description"],
            initial_state=data["initial_state"],
            states=states
        )

    def _parse_decision_table(self, data: Dict[str, Any]) -> DecisionTable:
        """Parse a decision table."""
        rules = []
        for rule_data in data.get("rules", []):
            rule = DecisionRule(
                conditions=rule_data["conditions"],
                actions=rule_data["actions"]
            )
            rules.append(rule)

        return DecisionTable(
            table_id=data["table_id"],
            name=data["name"],
            description=data["description"],
            inputs=data.get("inputs", []),
            rules=rules
        )


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 scenario_parser.py <feature_dir>")
        print("Example: python3 scenario_parser.py .sam/001_user_auth")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Find executable spec
    spec_file = feature_dir / "EXECUTABLE_SPEC.yaml"

    if not spec_file.exists():
        print(f"Error: EXECUTABLE_SPEC.yaml not found in {feature_dir}")
        sys.exit(1)

    # Extract feature info
    feature_id = feature_dir.name

    # Parse specification
    print(f"Parsing executable specification: {spec_file}")
    parser = ScenarioParser(spec_file, feature_id, feature_id.replace('_', ' ').title())
    registry = parser.parse()

    # Write SCENARIOS.json
    output_file = feature_dir / "SCENARIOS.json"
    with open(output_file, 'w') as f:
        json.dump(registry.to_dict(), f, indent=2)

    print(f"✓ Generated SCENARIOS.json")
    print(f"  Feature: {registry.metadata['feature_name']}")
    print(f"  Scenarios: {len(registry.scenarios)}")
    print(f"  Contract Tests: {len(registry.contract_tests)}")
    print(f"  State Machines: {len(registry.state_machines)}")
    print(f"  Decision Tables: {len(registry.decision_tables)}")

    # Print scenario summary
    if registry.scenarios:
        print("\n  Scenarios:")
        for scenario in registry.scenarios:
            print(f"    - {scenario.scenario_id}: {scenario.name}")
            print(f"      Story: {scenario.story_mapping}")
            print(f"      Given: {len(scenario.given)} steps")
            print(f"      Then: {len(scenario.then)} assertions")


if __name__ == "__main__":
    main()
