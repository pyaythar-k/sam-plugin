#!/bin/bash
# setup-pre-commit.sh - Install and configure pre-commit hooks for SAM
# Part of Phase 3: Integration & Automation
#
# Usage:
#   ./scripts/setup-pre-commit.sh
#   ./scripts/setup-commit.sh --force

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
FORCE=false
SKIP_DEPS=false

for arg in "$@"; do
    if [ "$arg" == "--force" ]; then
        FORCE=true
    fi
    if [ "$arg" == "--skip-deps" ]; then
        SKIP_DEPS=true
    fi
done

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  SAM Plugin - Pre-commit Hooks Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}⚠ pre-commit not found${NC}"
    echo "Installing pre-commit..."

    if [ "$SKIP_DEPS" = false ]; then
        pip install pre-commit
        pip install pre-commit-hooks
    else
        echo -e "${RED}Error: pre-commit is required but installation was skipped${NC}"
        echo "Run without --skip-deps or install manually: pip install pre-commit"
        exit 1
    fi
fi

echo -e "${GREEN}✓ pre-commit installed${NC}"

# Check if .pre-commit-config.yaml exists
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo -e "${RED}Error: .pre-commit-config.yaml not found${NC}"
    echo "This script should be run from the project root directory"
    exit 1
fi

echo -e "${GREEN}✓ .pre-commit-config.yaml found${NC}"

# Install pre-commit hooks
if [ "$FORCE" = true ]; then
    echo -e "${YELLOW}Force reinstalling hooks...${NC}"
    pre-commit uninstall --all
    pre-commit install --install-hooks --overwrite
else
    echo -e "${BLUE}Installing hooks...${NC}"
    pre-commit install --install-hooks
fi

echo -e "${GREEN}✓ Hooks installed${NC}"

# Validate configuration
echo ""
echo -e "${BLUE}Validating configuration...${NC}"
if pre-commit validate-config; then
    echo -e "${GREEN}✓ Configuration is valid${NC}"
else
    echo -e "${RED}Error: Invalid configuration${NC}"
    exit 1
fi

# Run initial check on all files
echo ""
echo -e "${BLUE}Running initial check on all files...${NC}"
echo -e "${YELLOW}(This may take a while on first run)${NC}"

if pre-commit run --all-files; then
    echo -e "${GREEN}✓ All checks passed${NC}"
else
    echo -e "${YELLOW}⚠ Some checks failed${NC}"
    echo "Fix the issues and run: pre-commit run --all-files"
fi

# Create pre-commit cache directory
CACHE_DIR=".cache/pre-commit"
mkdir -p "$CACHE_DIR"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Pre-commit hooks are now installed and will run automatically on git commit."
echo ""
echo "Available commands:"
echo "  • Run hooks manually:          pre-commit run --all-files"
echo "  • Run hooks on specific files: pre-commit run --files path/to/file"
echo "  • Update hooks:                pre-commit autoupdate"
echo "  • Uninstall hooks:             pre-commit uninstall"
echo "  • Skip hooks (one-time):       git commit --no-verify -m 'message'"
echo ""
echo "Hooks configured:"
echo "  • Format with Prettier"
echo "  • Lint with ESLint"
echo "  • Type checking"
echo "  • SAM quality gate (manual only)"
echo "  • Coverage check (pre-push)"
echo "  • Contract tests (pre-push)"
echo "  • Security checks (Bandit)"
echo ""
echo -e "${YELLOW}Note: Hooks will run automatically on every commit.${NC}"
echo -e "${YELLOW}Some slower hooks run on pre-push instead.${NC}"
