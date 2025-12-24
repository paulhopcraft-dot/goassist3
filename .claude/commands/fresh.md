---
description: Context reset with state preservation
---

<instructions>
Perform a context reset while preserving all project state.
</instructions>

<pre_reset_checklist>
<step number="1">Read current @features.json</step>
<step number="2">Read current @claude-progress.txt</step>
<step number="3">Review uncommitted changes (git status)</step>
<step number="4">Note current task/position</step>
</pre_reset_checklist>

<state_preservation>
<task>Update @claude-progress.txt</task>
<content>
- Current date/time
- Task in progress (if any)
- Recent accomplishments (last 3-5 items)
- Next planned task
- Any blockers or notes
</content>

<format>
```
[YYYY-MM-DD HH:MM] - Context reset
- Completed: [list recent work]
- In progress: [current task]
- Next: [planned task]
- Notes: [any important context]
```
</format>
</state_preservation>

<instructions_for_user>
After state is saved, instruct user:

"✅ State preserved to claude-progress.txt.

**Next steps:**
1. Run `/clear` to reset context
2. After clear, I'll automatically reload project context
3. Continue from: [current task]"

Then wait for user to run /clear.
</instructions_for_user>
