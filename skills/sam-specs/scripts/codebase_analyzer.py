#!/usr/bin/env python3
"""
Hybrid codebase analyzer for SAM workflow.
Combines .sam/ documentation analysis with actual codebase scanning.

Generates CODEBASE_CONTEXT.md with:
- Tech stack summary
- Existing patterns to follow
- Reusable components/services
- Architecture notes
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class CodebaseContext:
    """Container for analyzed codebase context."""
    tech_stack: Dict[str, str] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    components: Dict[str, List[str]] = field(default_factory=dict)
    services: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    architecture_notes: List[str] = field(default_factory=list)
    existing_features: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Codebase Context Analysis\n",
            "## Technology Stack\n",
            "| Layer | Technology | Notes |",
            "|-------|-----------|-------|"
        ]
        for layer, tech in self.tech_stack.items():
            lines.append(f"| {layer} | {tech} | |")

        if self.existing_features:
            lines.extend([
                "\n## Existing Features",
                "The following features have been documented in .sam/:\n"
            ])
            for feature in self.existing_features:
                lines.append(f"- `{feature}`")

        lines.extend([
            "\n## Existing Patterns",
            *self.patterns,
            "\n## Reusable Components",
        ])
        for category, items in self.components.items():
            lines.append(f"\n### {category}")
            lines.extend(f"- `{item}`" for item in items)

        if self.services:
            lines.extend([
                "\n## Services",
                *[f"- `{service}`" for service in self.services]
            ])

        lines.extend([
            "\n## Architecture Notes",
            *self.architecture_notes
        ])

        return "\n".join(lines)


class HybridCodebaseAnalyzer:
    """
    Analyzes codebase using hybrid approach:
    1. Scan .sam/ documentation for intended architecture
    2. Scan actual codebase to validate and fill gaps
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.sam_dir = self.project_root / ".sam"
        self.context = CodebaseContext()

    def analyze(self) -> CodebaseContext:
        """Run full hybrid analysis."""
        logger.info("Starting hybrid codebase analysis...")

        # Step 1: Analyze existing SAM documentation
        self._analyze_sam_docs()

        # Step 2: Scan actual codebase
        self._analyze_codebase()

        # Step 3: Validate and merge findings
        self._validate_and_merge()

        logger.info("Codebase analysis complete")
        return self.context

    def _analyze_sam_docs(self):
        """Step 1: Analyze existing SAM documentation."""
        if not self.sam_dir.exists():
            logger.info("No .sam/ directory found - no existing features documented")
            return

        logger.info("Analyzing .sam/ documentation...")

        # Scan all feature directories
        for feature_dir in sorted(self.sam_dir.glob("*/")):
            if not feature_dir.is_dir():
                continue

            feature_id = feature_dir.name
            self.context.existing_features.append(feature_id)

            # Read feature documentation
            feat_doc = feature_dir / "FEATURE_DOCUMENTATION.md"
            if feat_doc.exists():
                self._extract_from_feature_doc(feat_doc)

            # Read technical specs
            tech_spec = feature_dir / "TECHNICAL_SPEC.md"
            if tech_spec.exists():
                self._extract_from_tech_spec(tech_spec)

    def _analyze_codebase(self):
        """Step 2: Scan actual codebase."""
        logger.info("Analyzing codebase...")

        # Detect package managers and tech stack
        self._detect_tech_stack()

        # Scan source code structure
        self._scan_source_structure()

        # Find patterns in code
        self._detect_patterns()

    def _validate_and_merge(self):
        """Step 3: Validate docs match code, merge findings."""
        # Check for discrepancies
        # Add undocumented patterns found
        pass

    def _detect_tech_stack(self):
        """Detect technology stack from package files."""
        # Check package.json (JavaScript/TypeScript)
        pkg_json = self.project_root / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text())
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})

                all_deps = {**deps, **dev_deps}

                # Detect framework
                if "next" in all_deps:
                    version = all_deps.get("next", "")
                    self.context.tech_stack["framework"] = f"Next.js {version}"
                elif "react" in all_deps:
                    version = all_deps.get("react", "")
                    self.context.tech_stack["framework"] = f"React {version}"
                elif "vue" in all_deps:
                    version = all_deps.get("vue", "")
                    self.context.tech_stack["framework"] = f"Vue {version}"
                elif "svelte" in all_deps:
                    version = all_deps.get("svelte", "")
                    self.context.tech_stack["framework"] = f"Svelte {version}"

                # Detect database/ORM
                if "prisma" in all_deps:
                    self.context.tech_stack["orm"] = "Prisma"
                if "drizzle-orm" in all_deps:
                    self.context.tech_stack["orm"] = "Drizzle ORM"
                if "@supabase/supabase-js" in all_deps:
                    self.context.tech_stack["database"] = "Supabase"
                if "mongoose" in all_deps:
                    self.context.tech_stack["database"] = "MongoDB (Mongoose)"

                # Detect auth
                if "next-auth" in all_deps or "@auth/core" in all_deps:
                    self.context.tech_stack["auth"] = "NextAuth.js"

                # Detect state management
                if "zustand" in all_deps:
                    self.context.tech_stack["state"] = "Zustand"
                if "@reduxjs/toolkit" in all_deps:
                    self.context.tech_stack["state"] = "Redux Toolkit"

                # Detect UI library
                if "@radix-ui/react-*" in str(all_deps) or "radix-ui" in str(all_deps):
                    self.context.tech_stack["ui"] = "Radix UI"
                if "@mui/material" in all_deps:
                    self.context.tech_stack["ui"] = "Material-UI"
                if "@chakra-ui/react" in all_deps:
                    self.context.tech_stack["ui"] = "Chakra UI"

            except json.JSONDecodeError:
                logger.warning("Failed to parse package.json")

        # Check for Python
        if (self.project_root / "requirements.txt").exists():
            self.context.tech_stack["language"] = "Python"
            # Try to detect framework
            reqs = (self.project_root / "requirements.txt").read_text()
            if "django" in reqs.lower():
                self.context.tech_stack["framework"] = "Django"
            elif "fastapi" in reqs.lower():
                self.context.tech_stack["framework"] = "FastAPI"
            elif "flask" in reqs.lower():
                self.context.tech_stack["framework"] = "Flask"

        # Check for Go
        if (self.project_root / "go.mod").exists():
            self.context.tech_stack["language"] = "Go"

        # Check for Ruby
        if (self.project_root / "Gemfile").exists():
            self.context.tech_stack["language"] = "Ruby"

    def _scan_source_structure(self):
        """Scan source code directory structure."""
        common_src_dirs = ["src", "app", "lib", "components", "frontend", "backend"]

        for src_dir in common_src_dirs:
            path = self.project_root / src_dir
            if path.exists():
                self._scan_directory(path, src_dir)

    def _scan_directory(self, path: Path, category: str):
        """Recursively scan directory for components/services."""
        try:
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Skip node_modules and similar
                    if item.name in ['node_modules', '.git', 'dist', 'build', 'target']:
                        continue
                    self._scan_directory(item, f"{category}/{item.name}")
                elif item.is_file():
                    # Track files by category
                    ext = item.suffix
                    if ext in ['.tsx', '.jsx', '.ts', '.js', '.py', '.go']:
                        rel_path = item.relative_to(self.project_root)
                        if category not in self.context.components:
                            self.context.components[category] = []
                        self.context.components[category].append(str(rel_path))
        except PermissionError:
            pass

    def _detect_patterns(self):
        """Detect coding patterns from source code."""
        # Look for common patterns
        # This is a simplified implementation

        src_dirs = [d for d in [self.project_root / "src", self.project_root / "app"] if d.exists()]

        for src_dir in src_dirs:
            # Look for hooks pattern (React)
            hooks_dir = src_dir / "hooks"
            if hooks_dir.exists():
                self.context.patterns.append("Uses custom hooks directory: `src/hooks/`")
                for hook in hooks_dir.glob("use*.ts"):
                    self.context.components.setdefault("hooks", []).append(f"use{hook.stem}")

            # Look for services/api pattern
            services_dir = src_dir / "services"
            if services_dir.exists():
                self.context.patterns.append("Uses services layer: `src/services/`")
                for service in services_dir.glob("*.ts"):
                    self.context.services.append(service.stem)

            # Look for components pattern
            components_dir = src_dir / "components"
            if components_dir.exists():
                self.context.patterns.append("Uses component directory: `src/components/`")

            # Look for lib/util pattern
            lib_dirs = [src_dir / "lib", src_dir / "utils"]
            for lib_dir in lib_dirs:
                if lib_dir.exists():
                    self.context.patterns.append(f"Uses utilities directory: `{lib_dir.relative_to(self.project_root)}/`")

    def _extract_from_feature_doc(self, doc_path: Path):
        """Extract context from feature documentation."""
        try:
            content = doc_path.read_text()

            # Extract tech stack preferences
            tech_section = re.search(r'### Stack Preferences.*?(?=###|\n\n|$)', content, re.DOTALL)
            if tech_section:
                # Parse tech preferences
                pass

            # Extract integrations
            integrations_section = re.search(r'### Integrations Required.*?(?=###|\n\n|$)', content, re.DOTALL)
            if integrations_section:
                pass

        except Exception as e:
            logger.warning(f"Failed to extract from feature doc {doc_path}: {e}")

    def _extract_from_tech_spec(self, spec_path: Path):
        """Extract context from technical specifications."""
        try:
            content = spec_path.read_text()

            # Extract technology stack table
            stack_match = re.search(
                r'## Technology Stack.*?(?=##|\Z)',
                content,
                re.DOTALL
            )
            if stack_match:
                # Parse tech stack from spec
                pass

        except Exception as e:
            logger.warning(f"Failed to extract from tech spec {spec_path}: {e}")


def main():
    """CLI entry point."""
    import sys

    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    analyzer = HybridCodebaseAnalyzer(project_root)
    context = analyzer.analyze()

    # Output markdown
    markdown = context.to_markdown()
    print(markdown)

    # Save to file
    output_path = project_root / ".sam" / "CODEBASE_CONTEXT.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(markdown)
    print(f"\n✓ Codebase context saved to: {output_path}")


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    main()
