# Deployment Gate Templates

This document provides templates and procedures for deployment gate validation. Deployment gates ensure that only code meeting quality standards reaches production.

## Overview

Deployment gates are automated and manual checks that must pass before code can be deployed to an environment. They provide a final safety net to catch issues before they reach users.

### Gate Levels

| Gate Level | Purpose | When It Runs |
|------------|---------|--------------|
| **Pre-deployment** | Verify all quality checks pass | Before every deployment |
| **Smoke Tests** | Verify basic functionality | Immediately after deployment |
| **Rollback** | Enable quick recovery if issues found | Automated on smoke test failure |

---

## Pre-deployment Checklist

### Automated Checks

These checks run automatically in CI/CD before deployment:

```yaml
# Example deployment gate configuration
deployment_gate:
  pre_deployment:
    - quality_gate: PASSED
    - security_scan: CLEAN
    - coverage_threshold: 80%
    - e2e_tests: PASSED
    - contract_tests: PASSED
```

### Manual Verification

For production deployments, complete these manual checks:

- [ ] **Review security scan results**
  - No critical vulnerabilities
  - No high-severity issues in production code
  - Moderate vulnerabilities documented and accepted

- [ ] **Review test coverage report**
  - Overall coverage ≥ 80%
  - No critical files with < 60% coverage
  - New code has ≥ 90% coverage

- [ ] **Review E2E test results**
  - All critical user paths passing
  - No flaky tests identified
  - Performance metrics within acceptable range

- [ ] **Review contract test violations**
  - No breaking API changes
  - All contracts honored
  - Deprecation notices issued for any API changes

- [ **Review load test results** (if applicable)
  - System handles expected load
  - Response times within SLA
  - No memory leaks or resource exhaustion

### Deployment Approval

For production deployments, obtain approval from:

- [ ] Engineering Lead
- [ ] Product Owner (for feature changes)
- [ ] Security Team (for security-relevant changes)

---

## Smoke Tests

Smoke tests verify that the deployment succeeded and basic functionality works.

### Health Check Endpoints

```bash
# Example health check endpoints
curl -f https://api.example.com/health || exit 1
curl -f https://api.example.com/health/db || exit 1
curl -f https://api.example.com/health/redis || exit 1
```

**Expected responses:**
- `/health` → 200 OK with overall status
- `/health/db` → 200 OK with database connectivity
- `/health/redis` → 200 OK with cache connectivity

### Critical User Paths

Test the most critical user workflows:

1. **Authentication**
   - [ ] User can log in
   - [ ] User can log out
   - [ ] Session persists across requests

2. **Core Functionality**
   - [ ] Primary user action succeeds (e.g., create resource)
   - [ ] Data persists to database
   - [ ] API returns correct responses

3. **External Services**
   - [ ] Third-party integrations working
   - [ ] Webhooks firing correctly
   - [ ] Background jobs processing

### Database Verification

```sql
-- Verify database connectivity and basic queries
SELECT COUNT(*) FROM users;
SELECT NOW() AS current_time;
-- Verify migrations applied
SELECT * FROM schema_migrations ORDER BY version DESC LIMIT 1;
```

### External Service Availability

```bash
# Check critical external services
curl -f https://payment-processor.example.com/health || echo "Payment service down"
curl -f https://email-service.example.com/health || echo "Email service down"
```

---

## Rollback Procedures

### Automatic Rollback

Configure automatic rollback triggers:

```yaml
# Example automatic rollback configuration
rollback:
  triggers:
    - health_check_fails: true
    - error_rate_threshold: 5%
    - response_time_threshold: 2000ms
    - smoke_test_failures: 1

  cooldown_period: 300  # Wait 5 minutes before rolling back
  notification_channels: ["slack", "email"]
```

### Manual Rollback

If automatic rollback doesn't trigger, you can manually rollback:

#### Option 1: SAM Rollback Manager

```bash
# List available rollback checkpoints
python3 skills/sam-develop/scripts/rollback_manager.py .sam/{feature_id} --list-checkpoints

# Rollback to most recent checkpoint
python3 skills/sam-develop/scripts/rollback_manager.py .sam/{feature_id} --rollback

# Rollback to specific checkpoint
python3 skills/sam-develop/scripts/rollback_manager.py .sam/{feature_id} --rollback 20250206_143000
```

#### Option 2: Git-based Rollback

```bash
# Find the commit before the deployment
git log --oneline -10

# Rollback to that commit
git revert HEAD
# OR
git reset --hard <commit-sha>

# Push the rollback
git push origin main --force-with-lease
```

#### Option 3: Infrastructure Rollback

```bash
# If using infrastructure-as-code
terraform plan -rollback
terraform apply -rollback

# If using Kubernetes
kubectl rollout undo deployment/app-name

# If using Docker
docker-compose down
git checkout <previous-commit>
docker-compose up -d
```

### Database Migration Rollback

```bash
# If migrations need rollback
npm run migrate:rollback

# OR
python manage.py migrate app_name previous_migration

# Verify rollback
npm run migrate:status
```

### Feature Flag Toggle

If the feature uses feature flags:

```bash
# Disable the feature via flag
curl -X POST https://flags.example.com/api/v1/features/new-feature/disable \
  -H "Authorization: Bearer $FLAG_API_KEY"

# Verify feature is disabled
curl https://flags.example.com/api/v1/features/new-feature
```

---

## Post-deployment Verification

After deployment (and rollback if needed), verify:

### Monitoring Dashboards

- [ ] Error rate within normal range
- [ ] Response times within SLA
- [ ] CPU/memory usage normal
- [ ] Database performance normal
- [ ] No spike in 5xx errors

### Log Analysis

```bash
# Check for errors in recent logs
kubectl logs -l app=app-name --tail=1000 | grep -i error

# Check for specific error patterns
kubectl logs -l app=app-name --tail=1000 | grep -i "connection refused"

# Check for slow queries
kubectl logs -l app=app-name --tail=1000 | grep "slow query"
```

### User Feedback

- [ ] Monitor support channels for issues
- [ ] Check error tracking (e.g., Sentry)
- [ ] Review application performance monitoring

---

## Deployment Gate Script

Save this as `scripts/deployment-gate.sh`:

```bash
#!/bin/bash
# deployment-gate.sh - Run pre-deployment checks

set -e

echo "🔍 Running deployment gate checks..."

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# 1. Quality gate
echo ""
echo "▶️  Checking quality gate..."
if ./skills/sam-develop/scripts/lint_build_test.sh --json-output > quality-gate.json; then
    echo -e "${GREEN}✓ Quality gate passed${NC}"
else
    echo -e "${RED}✗ Quality gate failed${NC}"
    FAILED=1
fi

# 2. Coverage check
echo ""
echo "▶️  Checking coverage threshold..."
if python3 skills/sam-develop/scripts/coverage_enforcer.py . --check --threshold 80; then
    echo -e "${GREEN}✓ Coverage threshold met${NC}"
else
    echo -e "${RED}✗ Coverage below threshold${NC}"
    FAILED=1
fi

# 3. Security check
echo ""
echo "▶️  Running security scan..."
if npm audit --audit-level=high; then
    echo -e "${GREEN}✓ Security scan passed${NC}"
else
    echo -e "${YELLOW}⚠ Security issues found${NC}"
    # Don't fail on moderate issues
fi

# 4. Contract tests
echo ""
echo "▶️  Running contract tests..."
if python3 skills/sam-develop/scripts/contract_test_runner.py . --verify-contracts; then
    echo -e "${GREEN}✓ Contract tests passed${NC}"
else
    echo -e "${RED}✗ Contract tests failed${NC}"
    FAILED=1
fi

# Final result
echo ""
echo "═══════════════════════════════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All deployment gate checks passed${NC}"
    echo "Proceed with deployment"
    exit 0
else
    echo -e "${RED}❌ Deployment gate failed${NC}"
    echo "Fix issues before deploying"
    exit 1
fi
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      environment:
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deployment-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run deployment gate
        run: ./scripts/deployment-gate.sh

      - name: Deploy
        if: success()
        run: ./scripts/deploy.sh ${{ inputs.environment }}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
deploy:production:
  stage: deploy
  script:
    - ./scripts/deployment-gate.sh
    - ./scripts/deploy.sh production
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
  when: manual
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/deployment-gate.sh` | Run all pre-deployment checks |
| `./skills/sam-develop/scripts/rollback_manager.py .sam/{feature} --list-checkpoints` | List rollback checkpoints |
| `./skills/sam-develop/scripts/rollback_manager.py .sam/{feature} --rollback` | Rollback to last checkpoint |
| `kubectl rollout undo deployment/app-name` | Kubernetes rollback |
| `git revert HEAD` | Revert last commit |
