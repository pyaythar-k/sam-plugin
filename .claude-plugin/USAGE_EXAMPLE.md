# SAM Plugin - Usage Example

This document demonstrates the complete workflow of the SAM Plugin with a sample feature.

## Example: Adding User Authentication

### Phase 1: Feature Discovery

```
You: /sam-discover "Add user authentication with email and social login"

Claude (cdd-discover):
→ Spawning 4 parallel web research subagents...
   ✅ Subagent 1: Industry best practices for authentication (complete)
   ✅ Subagent 2: Technical implementation patterns (complete)
   ✅ Subagent 3: Competitive analysis - auth UI patterns (complete)
   ✅ Subagent 4: Security requirements - OWASP auth guidelines (complete)

→ Domain research complete. Now I need to clarify some details...

[Asks questions using AskUserQuestion tool]
Q: Which social providers do you want to support?
   Options: Google, GitHub, Apple, Facebook

You: Google and GitHub

Q: What's your current tech stack?
   Options: Next.js, React, Vue, Svelte

You: Next.js with TypeScript

[Interactive interview continues until 100% clarity]

→ Feature documentation created: .sam/001_user_auth/FEATURE_DOCUMENTATION.md

📋 Next: Run /sam-stories to generate user stories
```

### Phase 2: User Stories

```
You: /sam-stories 001_user_auth

Claude (cdd-stories):
→ Reading feature documentation...
→ Analyzing requirements for story decomposition...

→ Generating INVEST-compliant user stories...
   ✅ 001_basic_email_login.md
   ✅ 002_social_login.md
   ✅ 003_password_reset.md
   ✅ 004_session_management.md
   ✅ 005_logout.md

→ Spawning verifier subagent for gap analysis...
   ✅ Verification complete: 100% coverage confirmed

📁 Location: .sam/001_user_auth/USER_STORIES/
📋 Next: Run /sam-specs to generate technical specifications
```

### Phase 3: Technical Specifications

```
You: /sam-specs 001_user_auth

Claude (cdd-specs):
→ Reading 5 user stories...
→ Identifying technical requirements...

→ Consulting Context7 for latest documentation:
   📚 Querying /vercel/next.js for auth patterns...
   📚 Querying /authjs/next-auth for best practices...
   📚 Querying /supabase/supabase for database schema...

→ Generating comprehensive technical specification...
   ✅ Architecture Overview: Next.js App Router + NextAuth.js
   ✅ Database Schema: Users, Sessions, Accounts tables
   ✅ API Specification: 8 endpoints documented
   ✅ Component Architecture: 12 components with hierarchy
   ✅ Implementation Tasks: 28 tasks with checkbox tracking

→ Technical specification created: .sam/001_user_auth/TECHNICAL_SPEC.md

📋 Tasks: 28 implementation tasks with checkbox tracking
📋 Next: Run /sam-develop to start implementation
```

### Phase 4: Development

```
You: /sam-develop 001_user_auth

Claude (cdd-develop):
→ Reading technical specification...
→ Planning task execution...

→ Wave 1: Spawning 3 parallel subagents...
   Subagent A: Project setup (tasks 1.1-1.3)
   Subagent B: Database schema (tasks 1.4-1.6)
   Subagent C: Auth configuration (tasks 1.7-1.9)

   ✅ Subagent A complete - Running quality gates...
      ✓ Linting passed (0 errors, 0 warnings)
      ✓ Build successful
      ✓ Tests passing
      ✓ Task 1.1-1.3 marked complete [x]

   ✅ Subagent B complete - Running quality gates...
      ✓ Linting passed
      ✓ Build successful
      ✓ Tests passing
      ✓ Task 1.4-1.6 marked complete [x]

   ✅ Subagent C complete - Running quality gates...
      ✓ Linting passed
      ✓ Build successful
      ✓ Tests passing
      ✓ Task 1.7-1.9 marked complete [x]

→ Wave 2: Spawning 2 parallel subagents...
   [Continues until all tasks complete]

→ All 28 tasks complete with quality gates passed!

→ Spawning verification agent...
   Analyzing coverage:
   - User Stories: 100% (15/15 criteria met)
   - Technical Tasks: 100% (28/28 tasks completed)
   - Code Quality: ✅ All gates passed
   - Test Coverage: 94%
   - Browser Automation: ✅ All UI paths covered

→ Verification report created: .sam/001_user_auth/VERIFICATION_REPORT.md

✅ Feature 001_user_auth is production-ready! 🚀
```

### Status Check

```
You: /sam-status

═══════════════════════════════════════
📊 CDD PROJECT STATUS
═══════════════════════════════════════

📅 Generated: 2025-02-05 14:32

📈 Overview:
   • Total Features: 1
   • Completed: 1
   • Overall Progress: 100%

──────────────────────────────────────────
FEATURES
──────────────────────────────────────────

✅ 001_user_auth - User Authentication
   Progress: 100% | Phase: Complete
   Phases: 🔍 📝 🏗️ 💻 ✅
   ➤ ✅ Feature is production-ready!

═══════════════════════════════════════
```

## Output Structure

After completion, your project has:

```
project-root/
└── .sam/
    └── 001_user_auth/
        ├── FEATURE_DOCUMENTATION.md       ← Phase 1 output
        ├── USER_STORIES/
        │   ├── 001_basic_email_login.md  ← Phase 2 output
        │   ├── 002_social_login.md
        │   ├── 003_password_reset.md
        │   ├── 004_session_management.md
        │   └── 005_logout.md
        ├── TECHNICAL_SPEC.md             ← Phase 3 output
        │   └── [All 28 tasks marked [x]]
        └── VERIFICATION_REPORT.md        ← Phase 4 output
            └── 100% coverage confirmed
```

## Key Benefits

1. **Zero Ambiguity**: Interactive interview ensures 100% clarity before coding
2. **Latest Best Practices**: Context7 integration ensures specs use current documentation
3. **Quality Gates**: Mandatory linting/building/testing after every task
4. **100% Coverage**: Verification ensures no gaps between specs and implementation
5. **Visual Progress**: Checkbox tracking shows exactly what's done

## Next Actions

After feature completion:

1. **Deploy**: Feature is verified production-ready
2. **Start Next Feature**: `/sam-discover "new feature description"`
3. **Monitor**: Use `/sam-status` anytime for progress updates
