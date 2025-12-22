---
description: Context reset with state preservation
---

Perform a context reset while preserving all project state.

## Pre-Reset Checklist
1. Read current @features.json
2. Read current @claude-progress.txt  
3. Review uncommitted changes (git status)
4. Note current task/position

## State Preservation
Update @claude-progress.txt with:
- Current date/time
- Task in progress (if any)
- Recent accomplishments (last 3-5 items)
- Next planned task
- Any blockers or notes

Format:
```
[YYYY-MM-DD HH:MM] - Context reset
- Completed: [list recent work]
- In progress: [current task]
- Next: [planned task]
- Notes: [any important context]
```

## Instructions for User
After state is saved, instruct user:

"✅ State preserved to claude-progress.txt. 

**Next steps:**
1. Run `/clear` to reset context
2. After clear, I'll automatically reload project context
3. Continue from: [current task]"

Then wait for user to run /clear.
