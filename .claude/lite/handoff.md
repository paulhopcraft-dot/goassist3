---
name: handoff
description: End session cleanly
---

# Session Handoff

Save state for next session.

## Steps
1. Commit any uncommitted work
2. Update `claude-progress.txt`:
   ```
   ## Session [N] - [DATE]

   ### Completed
   - [what was done]

   ### Next Steps
   - [what to do next]

   ### Notes
   - [important context]
   ```
3. Push to remote if configured
4. Report handoff complete

Next session: run `/status` to resume.

$ARGUMENTS
