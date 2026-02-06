#!/usr/bin/env python3
"""
SAM Observability Configuration Loader.

Handles loading configuration from YAML files with environment variable
override support and sensible defaults.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    enabled: bool = True
    console_enabled: bool = True
    console_format: str = "text"
    file_enabled: bool = True
    file_path: str = ".sam/logs/sam.log"
    max_size_mb: int = 100
    max_files: int = 10
    component_levels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricsConfig:
    """Metrics configuration."""

    enabled: bool = True
    storage: str = "file"
    storage_path: str = ".sam/metrics/"
    retention_days: int = 30
    collect_timing: bool = True
    collect_counters: bool = True
    collect_gauges: bool = True
    collect_resource: bool = False


@dataclass
class TracingConfig:
    """Tracing configuration."""

    enabled: bool = True
    sample_rate: float = 1.0
    storage_type: str = "file"
    storage_path: str = ".sam/traces/"
    max_spans_per_trace: int = 1000


@dataclass
class ErrorsConfig:
    """Error tracking configuration."""

    enabled: bool = True
    storage_path: str = ".sam/errors/"
    retention_days: int = 90
    max_stack_frames: int = 50


@dataclass
class ObservabilityConfig:
    """Complete observability configuration."""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    errors: ErrorsConfig = field(default_factory=ErrorsConfig)
    backward_compatible: bool = True
    prometheus_integration: bool = False
    sentry_integration: bool = False


class ConfigLoader:
    """
    Load and manage observability configuration.

    Supports:
    - YAML configuration files
    - Environment variable overrides
    - Sensible defaults
    - Validation
    """

    DEFAULT_CONFIG_PATHS = [
        "config/observability.yaml",
        ".sam/observability.yaml",
        "~/.sam/observability.yaml",
    ]

    ENV_PREFIX = "SAM_OBS_"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self._config: Optional[ObservabilityConfig] = None

    def load(self) -> ObservabilityConfig:
        """
        Load configuration from file, environment, and defaults.

        Returns:
            ObservabilityConfig
        """
        if self._config is not None:
            return self._config

        # Start with defaults
        config_dict = {}

        # Load from file if available
        if self.config_path and self.config_path.exists():
            config_dict = self._load_yaml_file(self.config_path)
        else:
            # Try default paths
            for default_path in self.DEFAULT_CONFIG_PATHS:
                path = Path(default_path).expanduser()
                if path.exists():
                    config_dict = self._load_yaml_file(path)
                    self.config_path = path
                    break

        # Override with environment variables
        config_dict = self._apply_env_overrides(config_dict)

        # Parse into config objects
        self._config = self._parse_config(config_dict)

        return self._config

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Load YAML file if pyyaml is available."""
        if not HAS_YAML:
            return {}

        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}", file=sys.stderr)
            return {}

    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        # Environment variable format: SAM_OBS_{SECTION}_{KEY}
        # Example: SAM_OBS_LOGGING_LEVEL=DEBUG
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                # Remove prefix and convert to lowercase
                rest = key[len(self.ENV_PREFIX):].lower()

                # Split into sections
                parts = rest.split("__")  # Use __ as section separator
                parts = [p.replace("_", "") for p in parts]

                # Navigate config dict
                current = config_dict
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Set value (convert to appropriate type)
                current[parts[-1]] = self._parse_env_value(value)

        return config_dict

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False

        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # String
        return value

    def _parse_config(self, config_dict: Dict[str, Any]) -> ObservabilityConfig:
        """Parse configuration dictionary into dataclass instances."""
        # Logging config
        logging_dict = config_dict.get("logging", {})
        logging_config = LoggingConfig(
            level=logging_dict.get("level", "INFO"),
            format=logging_dict.get("format", "json"),
            enabled=logging_dict.get("enabled", True),
            console_enabled=logging_dict.get("outputs", [{}])[0].get("enabled", True)
                if logging_dict.get("outputs") else True,
            console_format=logging_dict.get("outputs", [{}])[0].get("format", "text")
                if logging_dict.get("outputs") else "text",
            file_enabled=logging_dict.get("outputs", [{}])[1].get("enabled", True)
                if len(logging_dict.get("outputs", [])) > 1 else True,
            file_path=logging_dict.get("outputs", [{}])[1].get("path", ".sam/logs/sam.log")
                if len(logging_dict.get("outputs", [])) > 1 else ".sam/logs/sam.log",
            max_size_mb=logging_dict.get("outputs", [{}])[1].get("rotation", {}).get("max_size_mb", 100)
                if len(logging_dict.get("outputs", [])) > 1 else 100,
            max_files=logging_dict.get("outputs", [{}])[1].get("rotation", {}).get("max_files", 10)
                if len(logging_dict.get("outputs", [])) > 1 else 10,
            component_levels=logging_dict.get("components", {}),
        )

        # Metrics config
        metrics_dict = config_dict.get("metrics", {})
        metrics_config = MetricsConfig(
            enabled=metrics_dict.get("enabled", True),
            storage=metrics_dict.get("storage", "file"),
            storage_path=metrics_dict.get("storage_options", {}).get("path", ".sam/metrics/"),
            retention_days=metrics_dict.get("storage_options", {}).get("retention_days", 30),
            collect_timing="timing" in metrics_dict.get("collect", ["timing"]),
            collect_counters="counters" in metrics_dict.get("collect", ["counters"]),
            collect_gauges=True,
            collect_resource="resource" in metrics_dict.get("collect", []),
        )

        # Tracing config
        tracing_dict = config_dict.get("tracing", {})
        tracing_config = TracingConfig(
            enabled=tracing_dict.get("enabled", True),
            sample_rate=tracing_dict.get("sample_rate", 1.0),
            storage_type=tracing_dict.get("storage", {}).get("type", "file"),
            storage_path=tracing_dict.get("storage", {}).get("path", ".sam/traces/"),
            max_spans_per_trace=1000,
        )

        # Errors config
        errors_dict = config_dict.get("errors", {})
        errors_config = ErrorsConfig(
            enabled=errors_dict.get("enabled", True),
            storage_path=errors_dict.get("storage", {}).get("path", ".sam/errors/"),
            retention_days=errors_dict.get("storage", {}).get("retention_days", 90),
            max_stack_frames=50,
        )

        # Main config
        features_dict = config_dict.get("features", {})
        config = ObservabilityConfig(
            logging=logging_config,
            metrics=metrics_config,
            tracing=tracing_config,
            errors=errors_config,
            backward_compatible=features_dict.get("backward_compatible", True),
            prometheus_integration=features_dict.get("prometheus_integration", False),
            sentry_integration=features_dict.get("sentry_integration", False),
        )

        return config

    def save_default_config(self, path: Path) -> None:
        """
        Save default configuration to a file.

        Args:
            path: Path to save configuration
        """
        default_config = {
            "version": "1.0",
            "logging": {
                "level": "INFO",
                "format": "json",
                "outputs": [
                    {
                        "type": "console",
                        "enabled": True,
                        "format": "text",
                    },
                    {
                        "type": "file",
                        "enabled": True,
                        "path": ".sam/logs/sam.log",
                        "rotation": {
                            "max_size_mb": 100,
                            "max_files": 10,
                        },
                    },
                ],
                "components": {
                    "sam-specs": "INFO",
                    "sam-develop": "DEBUG",
                    "sam-status": "INFO",
                },
            },
            "metrics": {
                "enabled": True,
                "storage": "file",
                "storage_options": {
                    "path": ".sam/metrics/",
                    "retention_days": 30,
                },
                "collect": ["timing", "counters"],
            },
            "tracing": {
                "enabled": True,
                "sample_rate": 1.0,
                "storage": {
                    "type": "file",
                    "path": ".sam/traces/",
                },
            },
            "errors": {
                "enabled": True,
                "storage": {
                    "path": ".sam/errors/",
                    "retention_days": 90,
                },
            },
            "features": {
                "backward_compatible": True,
                "prometheus_integration": False,
                "sentry_integration": False,
            },
        }

        path.parent.mkdir(parents=True, exist_ok=True)

        if HAS_YAML:
            with open(path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        else:
            # Fallback: write as JSON-commented file
            with open(path, "w") as f:
                f.write("# SAM Observability Configuration\n")
                f.write("# (pyyaml not installed, using JSON format)\n\n")
                import json
                json.dump(default_config, f, indent=2)


# Global config loader
_config_loader: Optional[ConfigLoader] = None
_config_lock = ...


def get_config(config_path: Optional[Path] = None) -> ObservabilityConfig:
    """
    Get or create the global configuration.

    Args:
        config_path: Optional path to configuration file

    Returns:
        ObservabilityConfig
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)

    return _config_loader.load()


def initialize_config(config_path: Optional[Path] = None) -> ObservabilityConfig:
    """
    Initialize configuration from a specific path.

    Args:
        config_path: Path to configuration file

    Returns:
        ObservabilityConfig
    """
    global _config_loader
    _config_loader = ConfigLoader(config_path)
    return _config_loader.load()


if __name__ == "__main__":
    # Demo
    loader = ConfigLoader()
    config = loader.load()

    print("Logging config:")
    print(f"  Level: {config.logging.level}")
    print(f"  Console: {config.logging.console_enabled}")

    print("\nMetrics config:")
    print(f"  Enabled: {config.metrics.enabled}")
    print(f"  Path: {config.metrics.storage_path}")

    print("\nTracing config:")
    print(f"  Enabled: {config.tracing.enabled}")
    print(f"  Sample rate: {config.tracing.sample_rate}")

    # Save default config
    default_path = Path("/tmp/observability.yaml")
    loader.save_default_config(default_path)
    print(f"\nSaved default config to: {default_path}")
