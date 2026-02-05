# Development Guidelines

## Purpose

This document provides comprehensive guidelines for the development phase of the SAM workflow. It ensures consistent, high-quality implementation across all features.

## Code Quality Standards

### Linting

All code must pass linting before being considered complete.

```bash
npm run lint
```

**Common Linting Rules:**
- No unused variables
- No console.log in production code
- Consistent indentation (2 or 4 spaces)
- No trailing whitespace
- Single quotes for strings (or double, be consistent)

### Type Checking

For TypeScript projects, all type errors must be resolved.

```bash
npm run type-check
# or
npx tsc --noEmit
```

**Type Safety Principles:**
- Avoid `any` types
- Use explicit return types for functions
- Define interfaces for data structures
- Use strict mode

### Building

The production build must succeed without errors.

```bash
npm run build
```

**Build Requirements:**
- No compilation errors
- No unresolved imports
- Bundle size within acceptable limits
- Source maps generated

## Testing Standards

### Unit Tests

Unit tests verify individual functions and components in isolation.

```bash
npm test
```

**Coverage Targets:**
- Minimum: 80% code coverage
- Ideal: 90%+ code coverage
- Critical paths: 100% coverage

**Unit Test Guidelines:**
- Test public interfaces, not implementation details
- Mock external dependencies
- Test edge cases and error conditions
- Use descriptive test names

### Integration Tests

Integration tests verify that multiple components work together.

```bash
npm run test:integration
```

**Integration Test Scope:**
- API endpoint tests
- Database integration
- External service mocks
- Multi-component workflows

### E2E Tests

End-to-end tests verify complete user flows using browser automation.

```bash
npm run test:e2e
```

**E2E Test Guidelines:**
- Test critical user paths
- Test across browsers (Chrome, Firefox, Safari)
- Test on mobile viewport sizes
- Use Page Object Model for maintainability

## Git Workflow

### Branch Naming

Use descriptive branch names with the feature ID:

```
feature/001_user_auth
feature/002_user_profiles-add-avatar
bugfix/001_user_auth-fix-token-expiry
```

### Commit Messages

Follow Conventional Commits specification:

```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore
```

## Security Best Practices

### Input Validation

- Validate all user input
- Sanitize data before storage
- Use prepared statements for database queries
- Validate file uploads (type, size)

### Authentication & Authorization

- Use HTTPS only
- Implement rate limiting
- Use secure session management
- Validate JWT signatures
- Implement proper password hashing (bcrypt, argon2)

### Data Protection

- Encrypt sensitive data at rest
- Never log sensitive information
- Use environment variables for secrets
- Implement proper CORS policies

## Performance Guidelines

### Database

- Use indexes for frequently queried columns
- Avoid N+1 queries
- Use connection pooling
- Implement query result caching

### Frontend

- Code splitting for large bundles
- Lazy load images
- Memoize expensive computations
- Debounce/throttle user input
- Use virtual scrolling for long lists

### API

- Implement pagination for list endpoints
- Use compression (gzip, brotli)
- Cache GET requests when appropriate
- Implement rate limiting

## Accessibility Standards

### WCAG 2.1 AA Compliance

**Keyboard Navigation:**
- All functionality available via keyboard
- Visible focus indicators
- Logical tab order

**Screen Reader Support:**
- Proper ARIA labels
- Semantic HTML
- Alt text for images
- Descriptive link text

**Visual:**
- Color contrast ratio 4.5:1 minimum
- Don't rely on color alone
- Support text scaling up to 200%

## Error Handling

### Principles

1. **Fail Fast**: Detect and report errors early
2. **Graceful Degradation**: Provide fallbacks when possible
3. **User-Friendly Messages**: Show understandable error messages
4. **Logging**: Log errors for debugging

## Deployment Checklist

### Pre-deployment

- [ ] All tests pass
- [ ] Build succeeds
- [ ] No console errors
- [ ] Accessibility audit passed
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Environment variables configured
- [ ] Database migrations prepared

### Deployment

- [ ] Database backups created
- [ ] Migrations applied
- [ ] New code deployed
- [ ] CDN cache cleared
- [ ] Monitoring configured
- [ ] Error tracking enabled

### Post-deployment

- [ ] Smoke tests passed
- [ ] Key user flows verified
- [ ] Metrics dashboard checked
- [ ] Rollback plan documented
- [ ] User notification sent (if applicable)

## Progress Tracking

### Checkbox Updates

When completing a task in the technical spec:

1. Update the checkbox: `[ ]` → `[x]`
2. Add completion note (optional)
3. Commit the change

### Daily Progress

At the end of each development session:

1. Update all completed checkboxes
2. Run verification script
3. Commit changes with descriptive message
4. Update status report if needed
