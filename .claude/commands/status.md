---
description: Show current project progress and status
---

<instructions>
Read @features.json and @claude-progress.txt, then report current project status.
</instructions>

<output_format>
## Progress Summary
```
Total Features: X
Completed: Y (Z%)
In Progress: A
Remaining: B
```

## Current Status
- Last completed: [feature name]
- Currently working on: [feature name or "none"]
- Blockers: [list any blockers]

## Next Up
1. [Next feature by priority/dependency]
2. [Following feature]
3. [Following feature]

## Recent Activity
[Last 5 entries from claude-progress.txt]

## Health Check
- [ ] Tests passing
- [ ] No uncommitted changes (or list them)
- [ ] No merge conflicts
</output_format>
