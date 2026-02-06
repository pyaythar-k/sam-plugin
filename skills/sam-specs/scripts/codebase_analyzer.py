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
import logging
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
    project_type: str = "unknown"  # NEW: Store project type classification

    def _get_project_type(self) -> str:
        """Get project type based on tech stack."""
        return self.project_type or "unknown"

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

        # Add project type classification (NEW)
        lines.extend([
            "\n## Project Classification\n",
            f"**Project Type**: `{self._get_project_type()}`\n",
            "*See `classify_project.py` for detailed classification logic.*\n"
        ])

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

        # Step 4: Classify project type (NEW)
        self.context.project_type = self.classify_project_type()

        logger.info(f"Codebase analysis complete (project type: {self.context.project_type})")
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

                # Detect BaaS providers (NEW)
                if "@supabase/supabase-js" in all_deps or "@supabase/postgrest-js" in all_deps:
                    self.context.tech_stack["baas"] = "Supabase"
                if "firebase" in all_deps or "@firebase/app" in all_deps:
                    self.context.tech_stack["baas"] = "Firebase"
                if "@aws-amplify/core" in all_deps or "aws-amplify" in all_deps:
                    self.context.tech_stack["baas"] = "AWS Amplify"

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

                # Detect backend frameworks
                if "express" in all_deps:
                    self.context.tech_stack["backend"] = "Express"
                if "fastify" in all_deps:
                    self.context.tech_stack["backend"] = "Fastify"
                if "nestjs" in all_deps or "@nestjs/common" in all_deps:
                    self.context.tech_stack["backend"] = "NestJS"
                if "@remix-run/node" in all_deps or "@remix-run/server-runtime" in all_deps:
                    self.context.tech_stack["backend"] = "Remix"

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

    def classify_project_type(self) -> str:
        """
        Classify project based on detected tech stack.

        Returns:
            One of: 'baas-fullstack', 'frontend-only', 'full-stack', 'static-site', 'unknown'
        """
        tech = self.context.tech_stack

        # Check for backend indicators
        backend_frameworks = ["express", "fastify", "nestjs", "remix", "django", "fastapi", "flask"]
        has_custom_backend = any(
            fw in str(tech).lower() for fw in backend_frameworks
        )

        # Check for BaaS provider
        has_baas = "baas" in tech

        # Check for frontend framework
        has_frontend = "framework" in tech

        # Check if configured for static export
        is_static_site = False
        if "next.js" in str(tech).lower():
            # Check next.config for static output
            next_config = self.project_root / "next.config.js"
            if next_config.exists():
                config_content = next_config.read_text()
                if "output: 'export'" in config_content or 'output: "export"' in config_content:
                    is_static_site = True

        # Classification logic
        if has_baas and has_frontend:
            return "baas-fullstack"
        elif has_frontend and not has_backend and not has_baas:
            return "frontend-only" if not is_static_site else "static-site"
        elif has_frontend and has_backend:
            return "full-stack"
        elif is_static_site:
            return "static-site"
        return "unknown"

    def get_baas_provider(self) -> Optional[str]:
        """Get the detected BaaS provider name."""
        return self.context.tech_stack.get("baas")

    def has_custom_backend(self) -> bool:
        """Check if project has a custom backend implementation."""
        backend_frameworks = ["express", "fastify", "nestjs", "remix", "django", "fastapi", "flask"]
        return any(
            fw in str(self.context.tech_stack).lower()
            for fw in backend_frameworks
        )

    def to_json(self) -> str:
        """
        Export context as JSON for programmatic use by sam-specs.

        Returns:
            JSON string with classification data
        """
        import json
        return json.dumps({
            "project_type": self.classify_project_type(),
            "tech_stack": self.context.tech_stack,
            "baas_provider": self.get_baas_provider(),
            "has_custom_backend": self.has_custom_backend(),
            "has_frontend": "framework" in self.context.tech_stack,
            "patterns": self.context.patterns,
            "components": self.context.components,
            "services": self.context.services
        }, indent=2)


def main():
    """CLI entry point."""
    import sys

    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    analyzer = HybridCodebaseAnalyzer(project_root)
    context = analyzer.analyze()

    # Output markdown
    markdown = context.to_markdown()
    print(markdown)

    # Save markdown to file
    output_path = project_root / ".sam" / "CODEBASE_CONTEXT.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(markdown)
    print(f"\n✓ Codebase context saved to: {output_path}")

    # Save JSON for programmatic use (NEW)
    json_output = analyzer.to_json()
    json_path = project_root / ".sam" / "CODEBASE_CONTEXT.json"
    json_path.write_text(json_output)
    print(f"✓ Codebase context JSON saved to: {json_path}")


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    main()
