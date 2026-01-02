---
name: autonomous
description: Work autonomously until done or blocked
---

# Autonomous Mode

Work continuously without asking, following AUTONOMOUS-GOVERNANCE.md rules.

## Pre-Flight
- [ ] On feature branch (not main)?
- [ ] Tests exist and pass?
- [ ] Clear completion criteria?
- [ ] Max 10 iterations set?

## Loop
```
REPEAT:
  1. Assess: What's the current state?
  2. Decide: What's the most valuable next step?
  3. Execute: Do it
  4. Verify: Did it work?
  5. Commit: Save progress every 5 iterations

UNTIL:
  - All tasks complete, OR
  - Blocked and need human input, OR
  - Max iterations reached
```

## Stop Conditions
- Same error 3 times
- Touching restricted paths (auth, payments, migrations)
- Tests start failing
- Unclear what to do next

## Report on Stop
```
AUTONOMOUS SESSION
==================
Iterations: X/10
Completed: [list]
Remaining: [list]
Status: [DONE/BLOCKED/MAX_ITERATIONS]
Next: [recommendation]
```

$ARGUMENTS
