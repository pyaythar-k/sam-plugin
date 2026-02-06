#!/usr/bin/env python3
"""
Verification script for Phase 3: Advanced Modeling

This script verifies that all Phase 3 components have been created
and are properly structured.
"""

import sys
from pathlib import Path


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and print status."""
    if path.exists():
        print(f"  ✓ {description}: {path}")
        return True
    else:
        print(f"  ✗ {description}: {path} (NOT FOUND)")
        return False


def check_file_contains(path: Path, text: str, description: str) -> bool:
    """Check if a file contains specific text."""
    if not path.exists():
        return False

    content = path.read_text()
    if text in content:
        print(f"  ✓ {description}")
        return True
    else:
        print(f"  ✗ {description} (NOT FOUND)")
        return False


def verify_phase3():
    """Verify all Phase 3 components."""
    print("=" * 60)
    print("Phase 3: Advanced Modeling - Verification")
    print("=" * 60)
    print()

    # Find the sam-plugin root by going up from the scripts directory
    base_path = Path(__file__).parent.parent.parent.parent
    all_passed = True

    # ===== Component 1: Context Propagation System =====
    print("1. Context Propagation System")
    print("-" * 40)

    # Check context_resolver.py
    all_passed &= check_file_exists(
        base_path / "skills/sam-specs/scripts/context_resolver.py",
        "context_resolver.py script"
    )

    if (base_path / "skills/sam-specs/scripts/context_resolver.py").exists():
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/context_resolver.py",
            "class ContextResolver",
            "ContextResolver class defined"
        )

    # Check global CONTEXT.yaml
    all_passed &= check_file_exists(
        base_path / "templates/CONTEXT.yaml",
        "Global CONTEXT.yaml template"
    )

    all_passed &= check_file_contains(
        base_path / "templates/CONTEXT.yaml",
        "application:",
        "Global context has application section"
    )

    # Check FEATURE_CONTEXT.yaml
    all_passed &= check_file_exists(
        base_path / "skills/sam-specs/templates/FEATURE_CONTEXT.yaml",
        "Feature CONTEXT.yaml template"
    )

    print()

    # ===== Component 2: State Machine Generator =====
    print("2. State Machine Generator")
    print("-" * 40)

    all_passed &= check_file_exists(
        base_path / "skills/sam-specs/scripts/state_machine_generator.py",
        "state_machine_generator.py script"
    )

    if (base_path / "skills/sam-specs/scripts/state_machine_generator.py").exists():
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/state_machine_generator.py",
            "class StateMachineGenerator",
            "StateMachineGenerator class defined"
        )
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/state_machine_generator.py",
            "_generate_xstate_machine",
            "XState generation method"
        )
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/state_machine_generator.py",
            "_generate_transitions_machine",
            "Python transitions generation method"
        )
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/state_machine_generator.py",
            "_generate_mermaid_diagram",
            "Mermaid diagram generation method"
        )

    # Check STATE_MACHINE_SECTION.md template
    all_passed &= check_file_exists(
        base_path / "skills/sam-specs/templates/STATE_MACHINE_SECTION.md",
        "State Machine Section template"
    )

    print()

    # ===== Component 3: Decision Table Test Generator =====
    print("3. Decision Table Test Generator")
    print("-" * 40)

    all_passed &= check_file_exists(
        base_path / "skills/sam-specs/scripts/decision_table_test_generator.py",
        "decision_table_test_generator.py script"
    )

    if (base_path / "skills/sam-specs/scripts/decision_table_test_generator.py").exists():
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/decision_table_test_generator.py",
            "class DecisionTableTestGenerator",
            "DecisionTableTestGenerator class defined"
        )
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/decision_table_test_generator.py",
            "_generate_jest_test",
            "Jest test generation method"
        )
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/decision_table_test_generator.py",
            "_generate_cucumber_feature",
            "Cucumber feature generation method"
        )
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/decision_table_test_generator.py",
            "_generate_pytest_test",
            "Pytest test generation method"
        )

    # Check DECISION_TABLE_SECTION.md template
    all_passed &= check_file_exists(
        base_path / "skills/sam-specs/templates/DECISION_TABLE_SECTION.md",
        "Decision Table Section template"
    )

    print()

    # ===== Component 4: Template Updates =====
    print("4. Template Updates")
    print("-" * 40)

    all_passed &= check_file_contains(
        base_path / "templates/specs/TECHNICAL_SPEC_TEMPLATE.md",
        "# State Machine Modeling",
        "State Machine section in TECHNICAL_SPEC_TEMPLATE.md"
    )

    all_passed &= check_file_contains(
        base_path / "templates/specs/TECHNICAL_SPEC_TEMPLATE.md",
        "# Decision Table Modeling",
        "Decision Table section in TECHNICAL_SPEC_TEMPLATE.md"
    )

    print()

    # ===== Component 5: SKILL.md Documentation =====
    print("5. SKILL.md Documentation")
    print("-" * 40)

    all_passed &= check_file_contains(
        base_path / "skills/sam-specs/SKILL.md",
        "## Section 11: State Machine Code Generation",
        "Section 11: State Machine Code Generation"
    )

    all_passed &= check_file_contains(
        base_path / "skills/sam-specs/SKILL.md",
        "## Section 12: Decision Table Test Generation",
        "Section 12: Decision Table Test Generation"
    )

    all_passed &= check_file_contains(
        base_path / "skills/sam-specs/SKILL.md",
        "## Section 13: Context Propagation",
        "Section 13: Context Propagation"
    )

    print()

    # ===== Component 6: Integration with Existing Generators =====
    print("6. Integration with Existing Generators")
    print("-" * 40)

    # Check test_generator.py
    if (base_path / "skills/sam-specs/scripts/test_generator.py").exists():
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/test_generator.py",
            "from context_resolver import ContextResolver",
            "test_generator.py imports ContextResolver"
        )
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/test_generator.py",
            "resolve_context",
            "test_generator.py has resolve_context method"
        )

    # Check contract_test_generator.py
    if (base_path / "skills/sam-specs/scripts/contract_test_generator.py").exists():
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/contract_test_generator.py",
            "from context_resolver import ContextResolver",
            "contract_test_generator.py imports ContextResolver"
        )

    # Check openapi_generator.py
    if (base_path / "skills/sam-specs/scripts/openapi_generator.py").exists():
        all_passed &= check_file_contains(
            base_path / "skills/sam-specs/scripts/openapi_generator.py",
            "from context_resolver import ContextResolver",
            "openapi_generator.py imports ContextResolver"
        )

    print()

    # ===== Summary =====
    print("=" * 60)
    if all_passed:
        print("✓ All Phase 3 components verified successfully!")
        return 0
    else:
        print("✗ Some Phase 3 components are missing or incomplete")
        return 1


if __name__ == "__main__":
    sys.exit(verify_phase3())
