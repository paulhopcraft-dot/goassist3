---
description: Prepare for session end, save state for next session
---

Prepare handoff for next session:

## 1. Commit any uncommitted work
- Use conventional commit message
- Don't leave work in progress uncommitted

## 2. Update features.json
- Ensure all "passes" values are accurate
- Update "last_updated" timestamps

## 3. Save to Structured Memory (v3.4)

Store important context using /remember:

```
/remember decision: [Any architectural decisions made this session]
/remember learning: [What worked well, what didn't]
/remember context: [Current focus and state]
```

Auto-save these to memory files:
- `.claude/v3/memory/decisions.json` - Architectural choices
- `.claude/v3/memory/learnings.json` - Patterns discovered
- `.claude/v3/memory/project.json` - Project context

## 4. Write to claude-progress.txt

```
## Session [N] - [DATE]

### Completed
- [What was accomplished]

### In Progress
- [What's partially done]

### Next Steps
- [What to work on next]

### Blockers
- [Any issues preventing progress]

### Notes
- [Important observations for next session]
```

## 5. Check Active Worktrees (v3.4)

If using git worktrees:
```bash
git worktree list
```

Note any active worktrees in progress log for next session.

## 6. Push to remote (if configured)

The next session should be able to pick up immediately using /reload.
