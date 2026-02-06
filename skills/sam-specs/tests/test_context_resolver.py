#!/usr/bin/env python3
"""
Unit tests for context_resolver.py

Tests context variable loading, merging, and interpolation.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from context_resolver import ContextResolver


def test_context_loading():
    """Test loading global and feature context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create global context
        global_ctx = tmpdir / "CONTEXT.yaml"
        global_ctx.write_text("""
application:
  name: "TestApp"
  environment: "development"
database:
  host: "localhost"
  port: 5432
""")

        # Create feature context
        feature_dir = tmpdir / "feature"
        feature_dir.mkdir()
        feature_ctx = feature_dir / "CONTEXT.yaml"
        feature_ctx.write_text("""
feature:
  id: "F001"
  name: "Test Feature"
database:
  port: 3306  # Override global value
""")

        # Create resolver
        resolver = ContextResolver(
            feature_dir,
            global_context_path=global_ctx,
            feature_context_path=feature_ctx
        )
        resolver.load_context()

        # Verify global values loaded
        assert resolver.get_value("application.name") == "TestApp"
        assert resolver.get_value("database.host") == "localhost"

        # Verify feature override
        assert resolver.get_value("database.port") == 3306

        # Verify feature values
        assert resolver.get_value("feature.id") == "F001"

        print("✓ test_context_loading passed")


def test_flatten_context():
    """Test flattening nested context to dot notation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        feature_dir = tmpdir / "feature"
        feature_dir.mkdir()

        ctx_file = feature_dir / "CONTEXT.yaml"
        ctx_file.write_text("""
application:
  name: "Test"
  api:
    url: "https://api.test.com"
    version: "v1"
database:
  primary:
    host: "db1.test.com"
    port: 5432
""")

        resolver = ContextResolver(feature_dir)
        resolver.load_context()

        flat = resolver._flatten_context()

        # Verify flattened keys
        assert "application.name" in flat
        assert "application.api.url" in flat
        assert "application.api.version" in flat
        assert "database.primary.host" in flat
        assert "database.primary.port" in flat

        # Verify values
        assert flat["application.api.url"] == "https://api.test.com"
        assert flat["database.primary.port"] == 5432

        print("✓ test_flatten_context passed")


def test_resolve_string():
    """Test resolving placeholders in strings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        feature_dir = tmpdir / "feature"
        feature_dir.mkdir()

        ctx_file = feature_dir / "CONTEXT.yaml"
        ctx_file.write_text("""
application:
  name: "MyApp"
  version: "1.0.0"
api:
  base_url: "https://api.example.com"
""")

        resolver = ContextResolver(feature_dir)
        resolver.load_context()

        # Test single placeholder
        result = resolver.resolve_string("{{application.name}}")
        assert result == "MyApp"

        # Test multiple placeholders
        result = resolver.resolve_string("{{application.name}} v{{application.version}}")
        assert result == "MyApp v1.0.0"

        # Test nested placeholder
        result = resolver.resolve_string("API: {{api.base_url}}")
        assert result == "API: https://api.example.com"

        print("✓ test_resolve_string passed")


def test_deep_merge():
    """Test deep merge of global and feature context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        global_ctx = tmpdir / "CONTEXT.yaml"
        global_ctx.write_text("""
application:
  name: "GlobalApp"
  settings:
    feature_a: true
    feature_b: false
    feature_c: true
""")

        feature_dir = tmpdir / "feature"
        feature_dir.mkdir()
        feature_ctx = feature_dir / "CONTEXT.yaml"
        feature_ctx.write_text("""
application:
  name: "FeatureApp"
  settings:
    feature_b: true  # Override
    feature_d: false  # New value
""")

        resolver = ContextResolver(
            feature_dir,
            global_context_path=global_ctx,
            feature_context_path=feature_ctx
        )
        resolver.load_context()

        # Verify override
        assert resolver.get_value("application.name") == "FeatureApp"
        assert resolver.get_value("application.settings.feature_b") is True

        # Verify preserved values
        assert resolver.get_value("application.settings.feature_a") is True
        assert resolver.get_value("application.settings.feature_c") is True

        # Verify new value
        assert resolver.get_value("application.settings.feature_d") is False

        print("✓ test_deep_merge passed")


def test_validation():
    """Test context validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        feature_dir = tmpdir / "feature"
        feature_dir.mkdir()

        # Valid context
        ctx_file = feature_dir / "CONTEXT.yaml"
        ctx_file.write_text("""
application:
  name: "TestApp"
""")

        resolver = ContextResolver(feature_dir)
        resolver.load_context()

        errors = resolver.validate_context()
        assert len(errors) == 0  # Should have no errors

        print("✓ test_validation passed")


def test_set_get_value():
    """Test setting and getting context values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        feature_dir = tmpdir / "feature"
        feature_dir.mkdir()

        resolver = ContextResolver(feature_dir)
        resolver.load_context()

        # Set simple value
        resolver.set_value("test.key", "test_value")
        assert resolver.get_value("test.key") == "test_value"

        # Set nested value
        resolver.set_value("level1.level2.key", "nested_value")
        assert resolver.get_value("level1.level2.key") == "nested_value"

        # Get with default
        assert resolver.get_value("nonexistent", "default") == "default"

        print("✓ test_set_get_value passed")


def main():
    """Run all tests."""
    print("Running context_resolver tests...")
    print()

    test_context_loading()
    test_flatten_context()
    test_resolve_string()
    test_deep_merge()
    test_validation()
    test_set_get_value()

    print()
    print("✓ All tests passed!")


if __name__ == "__main__":
    main()
