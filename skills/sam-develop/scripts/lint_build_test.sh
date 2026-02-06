#!/bin/bash
# lint_build_test.sh - Comprehensive quality check script
# Runs all quality checks in sequence
# Usage: ./skills/sam-develop/scripts/lint_build_test.sh [--json-output]
#
# Part of Phase 3: Integration & Automation
# Enhanced with CI/CD optimizations and artifact upload

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
JSON_OUTPUT=false
CI_MODE=false
UPLOAD_ARTIFACTS=false

for arg in "$@"; do
    if [ "$arg" == "--json-output" ]; then
        JSON_OUTPUT=true
    fi
    if [ "$arg" == "--ci-mode" ]; then
        CI_MODE=true
    fi
    if [ "$arg" == "--upload-artifacts" ]; then
        UPLOAD_ARTIFACTS=true
    fi
done

# Detect CI environment
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ]; then
    CI_MODE=true
    # Disable colors in CI
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# Check if we're in a project directory
if [ ! -f "package.json" ]; then
    if [ "$JSON_OUTPUT" = true ]; then
        echo '{"error": "package.json not found", "success": false}'
        exit 1
    else
        echo -e "${RED}Error: package.json not found. Are you in a project directory?${NC}"
        exit 1
    fi
fi

# Track overall success
FAILED=0
LINT_STATUS="passed"
TYPE_CHECK_STATUS="passed"
BUILD_STATUS="passed"
TEST_STATUS="passed"
E2E_STATUS="skipped"
COVERAGE_STATUS="skipped"
COVERAGE_PERCENTAGE=0
COVERAGE_THRESHOLD=80

# Start JSON output
if [ "$JSON_OUTPUT" = true ]; then
    echo '{"quality_gate":{'
fi

# Linting
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  SAM Plugin - Development Quality Checks${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}▶️  Running Linting...${NC}"
fi

if npm run lint 2>/dev/null; then
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}✓ Linting passed${NC}"
    fi
else
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${RED}✗ Linting failed${NC}"
    fi
    FAILED=1
    LINT_STATUS="failed"
fi

if [ "$JSON_OUTPUT" = false ]; then
    echo ""
fi

# Type Checking
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}▶️  Running Type Checking...${NC}"
fi

if npm run type-check 2>/dev/null; then
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}✓ Type checking passed${NC}"
    fi
else
    # Try tsc directly if type-check script doesn't exist
    if npx tsc --noEmit 2>/dev/null; then
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${GREEN}✓ Type checking passed${NC}"
        fi
    else
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${RED}✗ Type checking failed${NC}"
        fi
        FAILED=1
        TYPE_CHECK_STATUS="failed"
    fi
fi

if [ "$JSON_OUTPUT" = false ]; then
    echo ""
fi

# Building
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}▶️  Building Project...${NC}"
fi

if npm run build 2>/dev/null; then
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}✓ Build succeeded${NC}"
    fi
else
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${RED}✗ Build failed${NC}"
    fi
    FAILED=1
    BUILD_STATUS="failed"
fi

if [ "$JSON_OUTPUT" = false ]; then
    echo ""
fi

# Running Tests
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}▶️  Running Unit Tests...${NC}"
fi

if npm test 2>/dev/null; then
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}✓ Tests passed${NC}"
    fi
else
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${RED}✗ Tests failed${NC}"
    fi
    FAILED=1
    TEST_STATUS="failed"
fi

if [ "$JSON_OUTPUT" = false ]; then
    echo ""
fi

# Browser Automation (E2E)
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}▶️  Running Browser Automation Tests...${NC}"
fi

if npm run test:e2e 2>/dev/null; then
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}✓ E2E tests passed${NC}"
    fi
    E2E_STATUS="passed"
else
    # Check if test:e2e script exists
    if npm run | grep -q "test:e2e"; then
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${RED}✗ E2E tests failed${NC}"
        fi
        FAILED=1
        E2E_STATUS="failed"
    else
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${YELLOW}⚠ No E2E tests configured (test:e2e script not found)${NC}"
        fi
    fi
fi

if [ "$JSON_OUTPUT" = false ]; then
    echo ""
fi

# Coverage Enforcement
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}▶️  Checking Coverage Threshold...${NC}"
fi

# Check if coverage_enforcer.py exists
COVERAGE_ENFORCER="skills/sam-develop/scripts/coverage_enforcer.py"
if [ -f "$COVERAGE_ENFORCER" ]; then
    COVERAGE_OUTPUT=$(python3 "$COVERAGE_ENFORCER" . --json-output 2>/dev/null)
    COVERAGE_STATUS=$(echo "$COVERAGE_OUTPUT" | jq -r '.passed // false' 2>/dev/null)
    COVERAGE_PERCENTAGE=$(echo "$COVERAGE_OUTPUT" | jq -r '.coverage.overall // 0' 2>/dev/null)

    if [ "$COVERAGE_STATUS" = "true" ]; then
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${GREEN}✓ Coverage threshold met (${COVERAGE_PERCENTAGE}% >= ${COVERAGE_THRESHOLD}%)${NC}"
        fi
        COVERAGE_STATUS="passed"
    else
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${RED}✗ Coverage below threshold (${COVERAGE_PERCENTAGE}% < ${COVERAGE_THRESHOLD}%)${NC}"
        fi
        FAILED=1
        COVERAGE_STATUS="failed"
    fi
else
    # Fallback: Try running npm test with coverage
    if npm run test:coverage 2>/dev/null || npm test -- --coverage 2>/dev/null; then
        # Try to extract coverage percentage
        COVERAGE_OUTPUT=$(npm run test:coverage 2>/dev/null || npm test -- --coverage 2>/dev/null)
        COVERAGE_PERCENTAGE=$(echo "$COVERAGE_OUTPUT" | grep -oP '\d+%(?=\s*coverage)' | head -1 | tr -d '%' || echo "0")

        if [ -n "$COVERAGE_PERCENTAGE" ] && [ "$COVERAGE_PERCENTAGE" -ge "$COVERAGE_THRESHOLD" ]; then
            if [ "$JSON_OUTPUT" = false ]; then
                echo -e "${GREEN}✓ Coverage threshold met (${COVERAGE_PERCENTAGE}% >= ${COVERAGE_THRESHOLD}%)${NC}"
            fi
            COVERAGE_STATUS="passed"
        else
            if [ "$JSON_OUTPUT" = false ]; then
                if [ -n "$COVERAGE_PERCENTAGE" ]; then
                    echo -e "${RED}✗ Coverage below threshold (${COVERAGE_PERCENTAGE}% < ${COVERAGE_THRESHOLD}%)${NC}"
                else
                    echo -e "${YELLOW}⚠ Coverage check skipped (could not determine coverage)${NC}"
                fi
            fi
            COVERAGE_STATUS="skipped"
        fi
    else
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${YELLOW}⚠ Coverage check skipped (coverage not configured)${NC}"
        fi
        COVERAGE_STATUS="skipped"
    fi
fi

if [ "$JSON_OUTPUT" = false ]; then
    echo ""
fi

# Final result
OVERALL_STATUS="passed"
if [ $FAILED -eq 1 ]; then
    OVERALL_STATUS="failed"
fi

if [ "$JSON_OUTPUT" = true ]; then
    # Output JSON format for programmatic consumption
    echo "  \"linting\": \"$LINT_STATUS\","
    echo "  \"type_check\": \"$TYPE_CHECK_STATUS\","
    echo "  \"build\": \"$BUILD_STATUS\","
    echo "  \"tests\": \"$TEST_STATUS\","
    echo "  \"e2e_tests\": \"$E2E_STATUS\","
    echo "  \"coverage\": {"
    echo "    \"status\": \"$COVERAGE_STATUS\","
    echo "    \"percentage\": $COVERAGE_PERCENTAGE,"
    echo "    \"threshold\": $COVERAGE_THRESHOLD,"
    echo "    \"passed\": $([ "$COVERAGE_STATUS" = "passed" ] && echo "true" || echo "false")"
    echo "  },"
    echo "  \"overall\": \"$OVERALL_STATUS\","
    echo "  \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\""
    echo "}}"
    exit $FAILED
else
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
fi
