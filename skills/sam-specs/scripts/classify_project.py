#!/usr/bin/env python3
"""
classify_project.py - Classify project type and update TASKS.json

This script classifies a feature's project type based on the codebase context
and updates the TASKS.json metadata with the classification.

Usage:
    python3 skills/sam-specs/scripts/classify_project.py <feature_dir>
    python3 skills/sam-specs/scripts/classify_project.py .sam/001_user_auth

Output:
    Updates TASKS.json with metadata.project_type field
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from codebase_analyzer import HybridCodebaseAnalyzer
except ImportError:
    # Fallback if running directly
    logging.warning("Could not import codebase_analyzer, using standalone classification")
    from codebase_analyzer import HybridCodebaseAnalyzer


# Project type phase configurations
PHASE_STRUCTURES = {
    "baas-fullstack": {
        "phases": [
            {"id": "1", "name": "Foundation"},
            {"id": "2", "name": "BaaS Integration"},
            {"id": "3", "name": "Frontend"},
            {"id": "4", "name": "Integration"},
            {"id": "5", "name": "Quality Assurance"}
        ],
        "api_section": "BaaS Integration",
        "database_section": "RLS Policies / Firestore Rules"
    },
    "frontend-only": {
        "phases": [
            {"id": "1", "name": "Foundation"},
            {"id": "2", "name": "Frontend"},
            {"id": "3", "name": "Integration"},
            {"id": "4", "name": "Quality Assurance"}
        ],
        "api_section": None,  # Skip API specification
        "database_section": None  # Skip database section
    },
    "full-stack": {
        "phases": [
            {"id": "1", "name": "Foundation"},
            {"id": "2", "name": "Backend"},
            {"id": "3", "name": "Frontend"},
            {"id": "4", "name": "Integration"},
            {"id": "5", "name": "Quality Assurance"}
        ],
        "api_section": "Standard REST API",
        "database_section": "SQL DDL"
    },
    "static-site": {
        "phases": [
            {"id": "1", "name": "Foundation"},
            {"id": "2", "name": "Content"},
            {"id": "3", "name": "Deployment"},
            {"id": "4", "name": "Quality Assurance"}
        ],
        "api_section": None,
        "database_section": None
    }
}


def get_project_type_from_context(project_root: Path) -> str:
    """Get project type from CODEBASE_CONTEXT.json if available."""
    context_json = project_root / ".sam" / "CODEBASE_CONTEXT.json"
    if context_json.exists():
        try:
            data = json.loads(context_json.read_text())
            return data.get("project_type", "unknown")
        except (json.JSONDecodeError, KeyError):
            pass
    return "unknown"


def classify_manually(feature_dir: Path) -> str:
    """
    Classify project based on feature documentation.

    Checks FEATURE_DOCUMENTATION.md for user-specified project type.
    """
    feat_doc = feature_dir / "FEATURE_DOCUMENTATION.md"
    if feat_doc.exists():
        content = feat_doc.read_text()
        # Look for project_type in metadata section
        for line in content.split('\n'):
            if 'project_type:' in line.lower():
                # Extract the value after the colon
                value = line.split(':', 1)[1].strip().lower()
                # Validate against known types
                if value in PHASE_STRUCTURES:
                    return value
    return None


def update_tasks_json(feature_dir: Path, project_type: str) -> bool:
    """Update TASKS.json with project type metadata."""
    tasks_file = feature_dir / "TASKS.json"

    # Create TASKS.json if it doesn't exist
    if not tasks_file.exists():
        data = {
            "metadata": {
                "feature_id": feature_dir.name,
                "feature_name": feature_dir.name.replace('_', ' ').title(),
                "spec_version": "2.0",
                "total_tasks": "0",
                "completed_tasks": "0",
                "current_phase": "1"
            },
            "phases": [],
            "checkpoint": {}
        }
    else:
        try:
            with open(tasks_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Failed to parse {tasks_file}")
            return False

    # Update metadata with project type
    data.setdefault("metadata", {})["project_type"] = project_type

    # Add phase structure configuration
    if project_type in PHASE_STRUCTURES:
        data["metadata"]["phase_structure"] = PHASE_STRUCTURES[project_type]

    # Write back
    with open(tasks_file, 'w') as f:
        json.dump(data, f, indent=2)

    return True


def print_classification_summary(project_type: str):
    """Print summary of the classification."""
    if project_type not in PHASE_STRUCTURES:
        print(f"⚠️  Unknown project type: {project_type}")
        return

    config = PHASE_STRUCTURES[project_type]
    print(f"\n📋 Project Type: {project_type}")
    print(f"   Phases: {len(config['phases'])}")

    for phase in config['phases']:
        print(f"     - Phase {phase['id']}: {phase['name']}")

    print(f"\n   API Specification: {config['api_section'] or 'Skip'}")
    print(f"   Database Section: {config['database_section'] or 'Skip'}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 classify_project.py <feature_dir>")
        print("Example: python3 classify_project.py .sam/001_user_auth")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Get project root (parent of .sam directory)
    if feature_dir.parent.name == ".sam":
        project_root = feature_dir.parent.parent
    else:
        project_root = feature_dir

    print(f"🔍 Analyzing project type for: {feature_dir.name}")

    # Step 1: Check for manual classification in feature documentation
    manual_type = classify_manually(feature_dir)
    if manual_type:
        print(f"✓ Using manual classification from FEATURE_DOCUMENTATION.md")
        project_type = manual_type
    else:
        # Step 2: Run codebase analysis
        print("✓ Running codebase analysis...")
        analyzer = HybridCodebaseAnalyzer(project_root)
        context = analyzer.analyze()
        project_type = context.project_type

    # Step 3: Update TASKS.json
    print(f"✓ Updating TASKS.json with project type: {project_type}")
    if update_tasks_json(feature_dir, project_type):
        print(f"✓ TASKS.json updated successfully")

        # Print summary
        print_classification_summary(project_type)
    else:
        print(f"✗ Failed to update TASKS.json")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    main()
