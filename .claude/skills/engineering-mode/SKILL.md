---
name: engineering-mode
description: Global engineering constraints for all projects. Activates automatically for any coding, architecture, debugging, or implementation task. Enforces code quality, safety boundaries, error handling, and workflow discipline.
---

# Engineering Mode

Global rules for Claude Code across all projects.

## Contract Hierarchy
This defines **global rules**. Project-specific contracts may override where explicitly stated.

## Stack Defaults
- **Backend**: FastAPI + Pydantic v2
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **Vector DB**: Pinecone
- **GPU Compute**: RunPod (serverless preferred)
- **ORM**: Drizzle (TypeScript) or SQLAlchemy (Python)

## Code Standards

### Always
- Type hints on all function signatures
- Pydantic models for request/response validation
- Async by default for I/O operations
- Environment variables via `pydantic-settings`
- Structured logging (not print statements)
- Explicit error handling with custom exception classes

### Never
- Hardcoded secrets or API keys
- `except Exception: pass` (silent failures)
- Synchronous blocking calls in async contexts
- Raw SQL without parameterization
- Committing `.env` files or credentials

## Workflow Rules

### Before Writing Code
1. Read existing code in the target area first
2. Check features.json for current state
3. Understand dependencies before modifying

### During Implementation
- One feature at a time
- Write tests alongside code
- Run tests after each change
- Commit working code frequently

### After Completion
- Verify end-to-end (not just unit tests)
- Update features.json
- Update claude-progress.txt
- Conventional commit message

## Prohibited Actions
- Modifying files outside current repo without approval
- Deleting tests to make them "pass"
- Marking features complete without verification
- Ignoring failing tests
- Over-engineering beyond requirements

## Required Practices
- All features tracked in features.json with "passes": false default
- Test coverage for new code
- Error handling with specific exceptions
- Rollback plan for database changes

## Chain of Verification (CoV) Protocol

Before completing any task:

1. **Generate** - Produce the implementation
2. **Audit** - Review for:
   - Logic errors
   - Security issues
   - Missing edge cases
   - Deviation from requirements
3. **Correct** - Fix any issues found
4. **Verify** - Run tests, confirm functionality
5. **Report** - State what works and what doesn't

Never ship the first draft. Always audit, then output the corrected final.

## Escalation Rules

STOP and ask if:
- Requirements are ambiguous
- Change would affect multiple systems
- Security implications are unclear
- Unsure about the right approach
- Blocked for >10 minutes

## Git Discipline
- Conventional commits: feat/fix/docs/refactor/test
- Never commit secrets or credentials
- Commit after each verified feature
- Meaningful commit messages explaining WHY
