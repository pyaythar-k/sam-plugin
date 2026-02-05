#!/bin/bash
# lint_build_test.sh - Comprehensive quality check script
# Runs all quality checks in sequence
# Usage: ./skills/sam-develop/scripts/lint_build_test.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a project directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found. Are you in a project directory?${NC}"
    exit 1
fi

# Track overall success
FAILED=0

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  SAM Plugin - Development Quality Checks${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""

# Linting
echo -e "${YELLOW}▶️  Running Linting...${NC}"
if npm run lint 2>/dev/null; then
    echo -e "${GREEN}✓ Linting passed${NC}"
else
    echo -e "${RED}✗ Linting failed${NC}"
    FAILED=1
fi
echo ""

# Type Checking
echo -e "${YELLOW}▶️  Running Type Checking...${NC}"
if npm run type-check 2>/dev/null; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
else
    # Try tsc directly if type-check script doesn't exist
    if npx tsc --noEmit 2>/dev/null; then
        echo -e "${GREEN}✓ Type checking passed${NC}"
    else
        echo -e "${RED}✗ Type checking failed${NC}"
        FAILED=1
    fi
fi
echo ""

# Building
echo -e "${YELLOW}▶️  Building Project...${NC}"
if npm run build 2>/dev/null; then
    echo -e "${GREEN}✓ Build succeeded${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    FAILED=1
fi
echo ""

# Running Tests
echo -e "${YELLOW}▶️  Running Unit Tests...${NC}"
if npm test 2>/dev/null; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
    FAILED=1
fi
echo ""

# Browser Automation (E2E)
echo -e "${YELLOW}▶️  Running Browser Automation Tests...${NC}"
if npm run test:e2e 2>/dev/null; then
    echo -e "${GREEN}✓ E2E tests passed${NC}"
else
    # Check if test:e2e script exists
    if npm run | grep -q "test:e2e"; then
        echo -e "${RED}✗ E2E tests failed${NC}"
        FAILED=1
    else
        echo -e "${YELLOW}⚠ No E2E tests configured (test:e2e script not found)${NC}"
    fi
fi
echo ""

# Final result
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix the errors above.${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    exit 1
fi
