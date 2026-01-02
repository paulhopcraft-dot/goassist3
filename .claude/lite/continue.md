---
name: continue
description: Continue work on next task
---

# Continue Work

Resume where we left off.

## Steps
1. Check `claude-progress.txt` for last session state
2. Check `features.json` for incomplete features (passes: false)
3. Pick next task by priority/dependencies
4. Work on it until complete
5. Run tests to verify
6. Update tracking files
7. Commit with conventional message

## Verification
Before marking anything complete:
- [ ] Tests pass
- [ ] Feature works end-to-end
- [ ] No regressions

Report what you completed, then continue to next.

$ARGUMENTS
