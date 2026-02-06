#!/bin/bash
# SAM Observability Setup Script
#
# This script initializes observability for the SAM workflow.
# It creates necessary directories and configuration files.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==================================="
echo "SAM Observability Setup"
echo "==================================="
echo ""

# Default paths
SAM_DIR=".sam"
CONFIG_FILE="config/observability.yaml"

# Parse arguments
SKIP_CONFIG=false
for arg in "$@"; do
    case $arg in
        --skip-config)
            SKIP_CONFIG=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-config    Skip creating config file"
            echo "  --help           Show this help"
            echo ""
            exit 0
            ;;
    esac
done

# Create directories
echo -e "${GREEN}Creating observability directories...${NC}"

mkdir -p "$SAM_DIR/logs"
mkdir -p "$SAM_DIR/metrics"
mkdir -p "$SAM_DIR/traces"
mkdir -p "$SAM_DIR/errors"
mkdir -p "$SAM_DIR/observability"

echo "  ✓ $SAM_DIR/logs"
echo "  ✓ $SAM_DIR/metrics"
echo "  ✓ $SAM_DIR/traces"
echo "  ✓ $SAM_DIR/errors"
echo ""

# Create config file
if [ "$SKIP_CONFIG" = false ]; then
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "${YELLOW}Config file already exists: $CONFIG_FILE${NC}"
        echo "Skipping config creation."
    else
        echo -e "${GREEN}Creating observability configuration...${NC}"

        # Create config directory if needed
        mkdir -p "$(dirname "$CONFIG_FILE")"

        # Copy template or create default config
        if [ -f "templates/observability/OBSERVABILITY_CONFIG.yaml" ]; then
            cp templates/observability/OBSERVABILITY_CONFIG.yaml "$CONFIG_FILE"
        else
            # Create minimal config
            cat > "$CONFIG_FILE" << 'EOF'
# SAM Observability Configuration
version: "1.0"

logging:
  level: INFO
  format: json
  outputs:
    - type: console
      enabled: true
      format: text
    - type: file
      enabled: true
      path: .sam/logs/sam.log
      rotation:
        max_size_mb: 100
        max_files: 10
  components:
    sam-specs: INFO
    sam-develop: DEBUG
    sam-status: INFO

metrics:
  enabled: true
  storage: file
  storage_options:
    path: .sam/metrics/
    retention_days: 30
  collect:
    - timing
    - counters

tracing:
  enabled: true
  sample_rate: 1.0
  storage:
    type: file
    path: .sam/traces/

errors:
  enabled: true
  storage:
    path: .sam/errors/
    retention_days: 90

features:
  backward_compatible: true
  prometheus_integration: false
  sentry_integration: false
EOF
        fi

        echo "  ✓ $CONFIG_FILE"
    fi
    echo ""
fi

# Check Python dependencies
echo -e "${GREEN}Checking Python dependencies...${NC}"

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python not found${NC}"
    exit 1
fi

# Test imports
echo "Testing observability modules..."

if $PYTHON_CMD -c "import json, logging, contextlib, time, traceback, threading, dataclasses, pathlib" 2>/dev/null; then
    echo "  ✓ Standard library modules available"
else
    echo -e "${RED}Error: Required standard library modules not available${NC}"
    exit 1
fi

# Optional: pyyaml
if $PYTHON_CMD -c "import yaml" 2>/dev/null; then
    echo "  ✓ pyyaml available (for YAML config support)"
else
    echo -e "${YELLOW}  ⚠ pyyaml not found (optional - will use JSON format for config)${NC}"
    echo "    Install with: pip install pyyaml"
fi

# Optional: prometheus_client
if $PYTHON_CMD -c "import prometheus_client" 2>/dev/null; then
    echo "  ✓ prometheus_client available (for Prometheus metrics export)"
else
    echo "  ℹ prometheus_client not found (optional - for Prometheus integration)"
    echo "    Install with: pip install prometheus_client"
fi

# Optional: sentry_sdk
if $PYTHON_CMD -c "import sentry_sdk" 2>/dev/null; then
    echo "  ✓ sentry_sdk available (for Sentry error tracking)"
else
    echo "  ℹ sentry_sdk not found (optional - for Sentry integration)"
    echo "    Install with: pip install sentry-sdk"
fi

echo ""

# Create .gitignore entries
echo -e "${GREEN}Updating .gitignore...${NC}"

if [ -f ".gitignore" ]; then
    if ! grep -q "^\.sam/" .gitignore; then
        echo "" >> .gitignore
        echo "# SAM Observability" >> .gitignore
        echo ".sam/logs/" >> .gitignore
        echo ".sam/metrics/" >> .gitignore
        echo ".sam/traces/" >> .gitignore
        echo ".sam/errors/" >> .gitignore
        echo ".sam/diagnostic_bundle_*.zip" >> .gitignore
        echo "  ✓ Added .sam/ entries to .gitignore"
    else
        echo "  ℹ .sam/ already in .gitignore"
    fi
else
    echo "  ℹ No .gitignore file (skipping)"
fi

echo ""
echo -e "${GREEN}===================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}===================================${NC}"
echo ""
echo "Observability is ready to use."
echo ""
echo "Next steps:"
echo "  1. Customize configuration: $CONFIG_FILE"
echo "  2. Initialize observability in your code:"
echo "     from skills.shared.observability import initialize"
echo "     initialize()"
echo ""
echo "  3. Use the CLI:"
echo "     python3 -m skills.sam_observe.cli --help"
echo ""
echo "  4. View the dashboard:"
echo "     python3 -m skills.sam_observe.cli dashboard"
echo ""
