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

## Semi-Autonomous Mode (Default)

Operate proactively. Assess → Decide → Execute (or Ask) → Evaluate.

### New Task Behavior
When the user requests a new task, ALWAYS:
1. **Outline the plan** - Brief summary of approach (3-5 steps max)
2. **Propose commands** - List relevant `/commands` that will help
3. **Ask to proceed** - Get approval before starting

### "It's Up To You" Response
When user says "it's up to you", "you decide", "your call", or similar:
1. **Assess** the project state (run /status mentally)
2. **Identify** the most valuable next task
3. **Present a plan** using the same format above
4. **Ask to proceed** - still get approval before executing

Never just start working without showing the plan first.

Example response format:
```
PLAN:
1. [Step 1]
2. [Step 2]
3. [Step 3]

COMMANDS I'LL USE:
- /status - Check current state
- /review - After implementation
- [other relevant commands]

Ready to proceed?
```

### Auto-Execute (No Approval Needed)
- `/status` - Check project state
- `/review` - Code review
- `git status`, `git diff` - Read-only git
- Run tests - Verification
- Read files, search code - Research

### Ask Before Executing
- `git commit` - Any commits
- `git push` - Pushing to remote
- File edits - Code changes
- Refactoring - Structural changes
- Deleting code - Destructive actions

### Session Start Behavior
On every session start, automatically:
1. Run `/status` to assess current state
2. Check for failing tests → suggest fixing
3. Check for uncommitted changes → suggest committing
4. Check code quality if >500 lines changed → suggest `/review`
5. Identify next action and propose it

### Proactive Suggestions
Suggest actions when appropriate:
- Feature complete? → "Ready for `/verify`?"
- Tests passing, code clean? → "Ready to commit?"
- Large file changed? → "Should I `/review` this?"
- Session ending? → "Run `/handoff` to save state?"

## Full Autonomous Mode

For extended unattended execution, see **AUTONOMOUS-GOVERNANCE.md**.

Use `/autonomous` for governed autonomous loops with:
- Safety guardrails and restricted paths
- Iteration limits and checkpoints
- Pre-flight checklists and validation
- Automatic progress reporting
