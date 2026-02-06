#!/usr/bin/env python3
"""
context_resolver.py - Resolve {{VARIABLE}} placeholders with actual values

This script provides context variable resolution for template generation.
It loads global context from templates/CONTEXT.yaml and feature-specific
context from .sam/{feature}/CONTEXT.yaml, then interpolates placeholders.

Usage:
    python3 skills/sam-specs/scripts/context_resolver.py <feature_dir> [--export OUTPUT_FILE]
    python3 skills/sam-specs/scripts/context_resolver.py .sam/001_user_auth --export CONTEXT_RESOLVED.yaml
    python3 skills/sam-specs/scripts/context_resolver.py .sam/001_user_auth --resolve-file input.md output.md

Output:
    Resolves {{VARIABLE}} placeholders in templates
"""

import sys
import re
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union


class ContextResolver:
    """Resolve {{VARIABLE}} placeholders with actual values."""

    def __init__(
        self,
        feature_dir: Path,
        global_context_path: Optional[Path] = None,
        feature_context_path: Optional[Path] = None
    ):
        """
        Initialize the context resolver.

        Args:
            feature_dir: Path to the feature directory
            global_context_path: Path to global CONTEXT.yaml (default: templates/CONTEXT.yaml)
            feature_context_path: Path to feature CONTEXT.yaml (default: {feature_dir}/CONTEXT.yaml)
        """
        self.feature_dir = feature_dir
        self.global_context_path = global_context_path or self._find_global_context()
        self.feature_context_path = feature_context_path or (feature_dir / "CONTEXT.yaml")
        self.context: Dict[str, Any] = {}

    def _find_global_context(self) -> Path:
        """Find the global context file relative to the feature directory."""
        # Try relative path from feature dir
        feature_dir = self.feature_dir
        for parent in [feature_dir] + list(feature_dir.parents):
            candidates = [
                parent / "templates" / "CONTEXT.yaml",
                parent / "CONTEXT.yaml",
            ]
            for candidate in candidates:
                if candidate.exists():
                    return candidate

        # Default to templates/CONTEXT.yaml in sam-plugin root
        return Path(__file__).parent.parent.parent.parent / "templates" / "CONTEXT.yaml"

    def load_context(self) -> None:
        """Load global and feature-specific context."""
        # Load global context
        if self.global_context_path and self.global_context_path.exists():
            with open(self.global_context_path, 'r') as f:
                global_data = yaml.safe_load(f)
                if global_data:
                    self._deep_merge(global_data)

        # Load feature context (overrides global)
        if self.feature_context_path.exists():
            with open(self.feature_context_path, 'r') as f:
                feature_data = yaml.safe_load(f)
                if feature_data:
                    self._deep_merge(feature_data)

    def resolve_string(self, template: str) -> str:
        """
        Resolve {{VARIABLE}} placeholders in a string.

        Supports dot notation: {{application.name}}, {{database.host}}
        Also supports nested access: {{services.email.provider}}

        Args:
            template: String containing {{VARIABLE}} placeholders

        Returns:
            String with placeholders replaced by actual values
        """
        result = template

        # Replace placeholders with flattened context
        for key, value in self._flatten_context().items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # Replace any remaining placeholders with empty string (with warning)
        remaining = re.findall(r'\{\{([^}]+)\}\}', result)
        if remaining:
            import warnings
            for var in remaining:
                warnings.warn(f"Context variable not found: {{{{var}}}}")
                result = result.replace(f"{{{{{var}}}}}", "")

        return result

    def resolve_file(self, input_file: Path, output_file: Path) -> None:
        """
        Resolve placeholders in a file.

        Args:
            input_file: Input file path
            output_file: Output file path
        """
        with open(input_file, 'r') as f:
            content = f.read()

        resolved = self.resolve_string(content)

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(resolved)

    def export_context(self, output_file: Path, format: str = "yaml") -> None:
        """
        Export resolved context to a file.

        Args:
            output_file: Output file path
            format: Export format ("yaml" or "json")
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_file, 'w') as f:
                json.dump(self.context, f, indent=2)
        else:  # yaml
            with open(output_file, 'w') as f:
                yaml.dump(self.context, f, default_flow_style=False)

    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get a context value by dot-notation path.

        Args:
            path: Dot-notation path (e.g., "application.name")
            default: Default value if path not found

        Returns:
            Value at path or default
        """
        keys = path.split('.')
        value = self.context

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set_value(self, path: str, value: Any) -> None:
        """
        Set a context value by dot-notation path.

        Args:
            path: Dot-notation path (e.g., "application.name")
            value: Value to set
        """
        keys = path.split('.')
        context = self.context

        for key in keys[:-1]:
            if key not in context:
                context[key] = {}
            context = context[key]

        context[keys[-1]] = value

    def _flatten_context(self, prefix: str = "") -> Dict[str, Any]:
        """
        Flatten nested context to dot-notation keys.

        Args:
            prefix: Current prefix for recursive calls

        Returns:
            Flattened dictionary with dot-notation keys
        """
        flat = {}

        def _flatten(obj: Any, prefix: str) -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}.{key}" if prefix else key
                    _flatten(value, new_key)
            else:
                flat[prefix] = obj

        _flatten(self.context, prefix)
        return flat

    def _deep_merge(self, new_data: Dict[str, Any]) -> None:
        """
        Deep merge new data into context.

        Args:
            new_data: New data to merge
        """
        def _merge(base: Dict, update: Dict) -> Dict:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = _merge(base[key], value)
                else:
                    base[key] = value
            return base

        self.context = _merge(self.context, new_data)

    def validate_context(self) -> List[str]:
        """
        Validate context completeness.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for required top-level keys
        required_keys = ['application']
        for key in required_keys:
            if key not in self.context:
                errors.append(f"Missing required context key: {key}")

        # Check for placeholder values (strings starting with {{)
        for key, value in self._flatten_context().items():
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                errors.append(f"Unresolved placeholder: {key} = {value}")

        return errors

    def validate_placeholders(self, content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate all {{VARIABLE}} placeholders in content.

        This is a comprehensive validation that checks:
        - All placeholders are present in context
        - Reports missing required variables
        - Warns about optional variables
        - Suggests default values for common variables

        Args:
            content: String containing placeholders
            context: Optional context dict (defaults to self.context)

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "missing_required": List[str],
                "missing_optional": List[str],
                "warnings": List[str],
                "suggestions": Dict[str, str]
            }
        """
        if context is None:
            context = self.context

        # Extract all placeholders from content
        placeholders = self.get_template_variables(content)

        # Flatten context for lookup
        flat_context = self._flatten_context()

        # Common optional variables with default values
        COMMON_DEFAULTS = {
            "application.version": "1.0.0",
            "application.environment": "development",
            "database.port": "5432",
            "database.ssl_mode": "require",
            "api.timeout": "30000",
            "api.rate_limit": "1000",
            "cache.ttl": "3600",
            "logging.level": "info",
        }

        # Required variables (must be provided)
        required_patterns = ["application.name", "application.description"]

        # Validation results
        missing_required = []
        missing_optional = []
        warnings = []
        suggestions = {}

        for placeholder in placeholders:
            if placeholder in flat_context:
                # Placeholder exists in context
                continue

            # Check if it's a required variable
            is_required = any(
                placeholder.startswith(pattern) or placeholder == pattern
                for pattern in required_patterns
            )

            if is_required:
                missing_required.append(placeholder)
            else:
                missing_optional.append(placeholder)

                # Suggest default values for common variables
                if placeholder in COMMON_DEFAULTS:
                    suggestions[placeholder] = COMMON_DEFAULTS[placeholder]
                else:
                    # Try to suggest a value based on the variable name
                    if "port" in placeholder:
                        suggestions[placeholder] = "3000"
                    elif "host" in placeholder or "url" in placeholder:
                        if "database" in placeholder:
                            suggestions[placeholder] = "localhost"
                        elif "api" in placeholder:
                            suggestions[placeholder] = "http://localhost:3000"
                    elif "email" in placeholder:
                        suggestions[placeholder] = "noreply@example.com"

        # Generate warnings
        if missing_required:
            warnings.append(f"Missing {len(missing_required)} required placeholder(s): generation will fail")
        if missing_optional:
            warnings.append(f"Missing {len(missing_optional)} optional placeholder(s): will be replaced with empty strings")

        # Determine overall validity
        is_valid = len(missing_required) == 0

        return {
            "is_valid": is_valid,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "warnings": warnings,
            "suggestions": suggestions,
            "total_placeholders": len(placeholders),
            "resolved_count": len(placeholders) - len(missing_required) - len(missing_optional)
        }

    def apply_defaults(self, content: str, defaults: Dict[str, str]) -> str:
        """
        Apply default values to placeholders before resolution.

        Args:
            content: String containing placeholders
            defaults: Dictionary of placeholder -> default value

        Returns:
            String with defaults applied
        """
        result = content

        for placeholder, default_value in defaults.items():
            placeholder_str = f"{{{{{placeholder}}}}}"
            if placeholder_str in result:
                result = result.replace(placeholder_str, default_value)

        return result

    def resolve_with_validation(self, content: str, strict: bool = False) -> Dict[str, Any]:
        """
        Resolve placeholders with full validation and reporting.

        Args:
            content: String containing placeholders
            strict: If True, fail on missing required placeholders

        Returns:
            Dictionary with:
            {
                "content": str (resolved content),
                "validation": dict (validation results),
                "success": bool
            }
        """
        # First, validate placeholders
        validation = self.validate_placeholders(content)

        # If strict mode and missing required, return error
        if strict and not validation["is_valid"]:
            return {
                "content": content,
                "validation": validation,
                "success": False
            }

        # Apply suggestions for missing placeholders (in non-strict mode)
        if not strict and validation["suggestions"]:
            content = self.apply_defaults(content, validation["suggestions"])

        # Resolve placeholders
        resolved_content = self.resolve_string(content)

        return {
            "content": resolved_content,
            "validation": validation,
            "success": True
        }

    def get_template_variables(self, content: str) -> List[str]:
        """
        Extract all {{VARIABLE}} placeholders from content.

        Args:
            content: String containing placeholders

        Returns:
            List of unique variable names
        """
        matches = re.findall(r'\{\{([^}]+)\}\}', content)
        return list(set(matches))


def resolve_directory(
    feature_dir: Path,
    input_dir: Path,
    output_dir: Path,
    resolver: ContextResolver,
    pattern: str = "*.md"
) -> None:
    """
    Resolve placeholders in all files in a directory.

    Args:
        feature_dir: Feature directory path
        input_dir: Input directory path
        output_dir: Output directory path
        resolver: ContextResolver instance
        pattern: File pattern to match (default: "*.md")
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_file in input_dir.glob(pattern):
        output_file = output_dir / input_file.name
        resolver.resolve_file(input_file, output_file)
        print(f"  ✓ Resolved: {input_file.name} -> {output_file}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 context_resolver.py <feature_dir> [--export OUTPUT_FILE] [--resolve-file INPUT OUTPUT] [--validate INPUT] [--strict]")
        print("Example: python3 context_resolver.py .sam/001_user_auth --export CONTEXT_RESOLVED.yaml")
        print("Example: python3 context_resolver.py .sam/001_user_auth --resolve-file input.md output.md")
        print("Example: python3 context_resolver.py .sam/001_user_auth --validate TECHNICAL_SPEC.md")
        print("Example: python3 context_resolver.py .sam/001_user_auth --validate TECHNICAL_SPEC.md --strict")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    # Create resolver
    resolver = ContextResolver(feature_dir)

    # Load context
    resolver.load_context()

    print(f"✓ Loaded context for: {feature_dir.name}")
    print(f"  Global context: {resolver.global_context_path}")
    print(f"  Feature context: {resolver.feature_context_path}")

    # Parse arguments
    if len(sys.argv) >= 4:
        if sys.argv[2] == "--export":
            # Export resolved context
            output_file = Path(sys.argv[3])
            format = "yaml" if output_file.suffix == ".yaml" or output_file.suffix == ".yml" else "json"
            resolver.export_context(output_file, format)
            print(f"✓ Exported context to: {output_file}")

            # Show context summary
            print(f"\nContext Summary:")
            for key, value in sorted(resolver._flatten_context().items()):
                print(f"  {key}: {value}")

        elif sys.argv[2] == "--resolve-file":
            # Resolve a single file
            if len(sys.argv) < 5:
                print("Error: --resolve-file requires INPUT and OUTPUT arguments")
                sys.exit(1)

            input_file = Path(sys.argv[3])
            output_file = Path(sys.argv[4])

            if not input_file.exists():
                print(f"Error: Input file not found: {input_file}")
                sys.exit(1)

            resolver.resolve_file(input_file, output_file)
            print(f"✓ Resolved: {input_file} -> {output_file}")

        elif sys.argv[2] == "--validate":
            # Validate placeholders in a file
            if len(sys.argv) < 4:
                print("Error: --validate requires INPUT argument")
                sys.exit(1)

            input_file = Path(sys.argv[3])

            if not input_file.exists():
                print(f"Error: Input file not found: {input_file}")
                sys.exit(1)

            # Check for strict mode
            strict = "--strict" in sys.argv

            with open(input_file, 'r') as f:
                content = f.read()

            print(f"\n📋 Validating placeholders in: {input_file.name}")
            print("=" * 60)

            validation = resolver.validate_placeholders(content)

            print(f"\nTotal placeholders found: {validation['total_placeholders']}")
            print(f"Resolved placeholders: {validation['resolved_count']}")
            print(f"Missing required: {len(validation['missing_required'])}")
            print(f"Missing optional: {len(validation['missing_optional'])}")

            if validation['missing_required']:
                print(f"\n❌ Missing Required Placeholders:")
                for var in validation['missing_required']:
                    print(f"   - {{{{var}}}}")

            if validation['missing_optional']:
                print(f"\n⚠️  Missing Optional Placeholders:")
                for var in validation['missing_optional']:
                    print(f"   - {{{{var}}}}")
                    if var in validation['suggestions']:
                        print(f"     Suggested value: {validation['suggestions'][var]}")

            if validation['warnings']:
                print(f"\n⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")

            if validation['is_valid']:
                print(f"\n✅ Validation passed! All placeholders can be resolved.")
                sys.exit(0)
            else:
                print(f"\n❌ Validation failed! Missing required placeholders.")
                if strict:
                    print("   (Strict mode: Would fail generation)")
                sys.exit(1)

    else:
        # Validate context
        errors = resolver.validate_context()
        if errors:
            print(f"\n⚠ Validation warnings:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"\n✓ Context is valid")

        # Show context summary
        print(f"\nContext Summary:")
        for key, value in sorted(resolver._flatten_context().items()):
            print(f"  {key}: {value}")

    print(f"\n✓ Context resolution complete!")


if __name__ == "__main__":
    main()
