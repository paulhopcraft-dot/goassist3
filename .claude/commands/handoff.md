---
description: Prepare for session end, save state for next session
---

<instructions>
Prepare handoff for next session. The next session should be able to pick up immediately from claude-progress.txt.
</instructions>

<steps>
1. **Commit any uncommitted work**
   - Use conventional commit message
   - Don't leave work in progress uncommitted

2. **Update features.json**
   - Ensure all "passes" values are accurate
   - Update "last_updated" timestamps

3. **Write to claude-progress.txt**
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

4. **Push to remote** (if configured)
</steps>
