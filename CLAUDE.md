# Engineering Mode

## Toolkit Version: v3.0 (Context-Optimized Mode)

**Status**: ACTIVE ✓

When v3.0 is active, use the template-based command generation system:
- Read `.claude/v3/context-strategy.json` at session start
- Use templates from `.claude/v3/templates/` instead of individual commands
- Apply meta-prompting with RAG for specialized command generation
- Cache generated commands in `.claude/v3/cache/` for session reuse

**Fallback**: If v3.0 files not found, use v2.4 commands from `.claude/commands/`

## Context Management
Your context window will be automatically compacted as it approaches its limit. Save progress to memory before context refresh. Be persistent and complete tasks fully.

**v3.0 Loading Strategy**:
- Always load: CLAUDE.md, domain.json, .claude/v3/context-strategy.json, progress summary
- Lazy load: Templates, agents, patterns (only when needed)
- Progressive: Build context through RAG retrieval, not upfront loading
- Budget: Max 1,500 tokens upfront (vs 23,400 in v2.4)

## Verification Requirements
- NEVER mark a feature complete without testing end-to-end
- Run the actual test suite, don't assume tests pass
- If you can't verify something works, say so explicitly

## Engineering Constraints
- Avoid over-engineering
- Don't create unnecessary abstractions
- Keep solutions minimal and focused
- One feature at a time

## Project Commands
- Test: echo 'Add your test command'
- Lint: echo 'Add your lint command'
- Build: echo 'Add your build command'
- Dev: echo 'Add your dev command'

## Git Workflow
- Commit after each feature passes verification
- Use conventional commits: feat/fix/docs/refactor
- Push after significant milestones

## Feature Tracking
- Track features in features.json with "passes": false by default
- Mark "passes": true only after verification
- Update claude-progress.txt after each session
