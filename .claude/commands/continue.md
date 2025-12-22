---
description: Continue working on next incomplete task
---

## Orientation
1. Run `pwd` to confirm directory
2. Read `git log --oneline -5` for recent changes
3. Read @claude-progress.txt for previous session notes
4. Read @features.json for current status

## Work Loop
1. Find next feature with "passes": false (respect dependencies)
2. Implement with tests
3. Run tests - fix any failures
4. Verify end-to-end (not just unit tests)
5. Update features.json: set "passes": true, update "verified_at"
6. Commit with conventional message (feat/fix/docs/refactor)
7. Update claude-progress.txt

## Verification Checklist
Before marking any feature "passes": true:
- [ ] Tests written and passing
- [ ] Tested end-to-end manually or with automation
- [ ] Edge cases checked
- [ ] No regressions in other features

Report what you completed, then continue to next task.

$ARGUMENTS
