---
name: status
version: 2.0.0
description: Show current project progress and status (with optional board view)
---

# Status: $ARGUMENTS

Read @features.json and @claude-progress.txt, then report.

---

## Options

- `/status` - Standard summary view
- `/status --board` - Kanban-style board view
- `/status --compact` - One-line summary

---

## Standard View (Default)

### Progress Summary
```
Total Features: X
Completed: Y (Z%)
In Progress: A
Remaining: B
```

### Current Status
- Last completed: [feature name]
- Currently working on: [feature name or "none"]
- Blockers: [list any blockers]

### Next Up
1. [Next feature by priority/dependency]
2. [Following feature]
3. [Following feature]

### Recent Activity
[Last 5 entries from claude-progress.txt]

### Health Check
- [ ] Tests passing
- [ ] No uncommitted changes (or list them)
- [ ] No merge conflicts

---

## Board View (/status --board)

Display features in Kanban-style columns:

```
Project Board: [project-name]

+------------------+------------------+------------------+
|    TODO (3)      |  IN PROGRESS (1) |    DONE (5)      |
+------------------+------------------+------------------+
| F010: API Auth   | F009: Login UI   | F001: Setup      |
| F011: Dashboard  |                  | F002: Database   |
| F012: Reports    |                  | F003: Models     |
|                  |                  | F004: API Base   |
|                  |                  | F005: Tests      |
+------------------+------------------+------------------+

Progress: [==========----] 5/8 (62%)

Worktrees Active: 1
  - F009: ../worktrees/F009-login-ui
```

### Board Generation Logic

1. Read features.json
2. Categorize by status:
   - passes: false, status: pending -> TODO
   - passes: false, status: in_progress -> IN PROGRESS
   - passes: true -> DONE
3. Format as columns
4. Show active worktrees
5. Calculate progress bar

---

## Compact View (/status --compact)

One-line summary:

```
govertical: 5/8 features (62%) | In Progress: F009 | Tests: PASS
```

---

## Integration with Worktrees

Show worktree status alongside features:

```
IN PROGRESS (1)
  F009: Login UI
    - Worktree: ../worktrees/F009-login-ui
    - Branch: feature/F009-login-ui
    - Status: 3 uncommitted changes
```

---

## Health Indicators

| Indicator | Good | Warning | Bad |
|-----------|------|---------|-----|
| Tests | All passing | Some skipped | Failing |
| Git | Clean | Uncommitted | Conflicts |
| Build | Success | Warnings | Failed |

---

## Next Actions Menu

**ALWAYS display this at the end of status output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT ACTIONS:
  [C] Continue - focused work on next task
  [A] Autonomous - batch execution mode
  [H] Handoff - save state and end session
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type C, A, or H (or describe your task):
```

**Recommendation Logic:**

Based on project state, recommend a specific command:

| Condition | Recommend |
|-----------|-----------|
| Tests failing | `/recover` - diagnose and fix |
| Feature just completed | `/verify` - confirm it works |
| Merge conflicts | `/resolve` - fix conflicts |
| 3+ similar pending tasks | `/autonomous` - batch mode |
| Complex next task | `/think` - plan approach |
| Architecture decision needed | `/decide` - structured analysis |
| Auth/security code next | `/anticipate` - risk check |
| Clean state, ready to work | `/continue` - start next task |

**MUST always display a recommendation:**
```
💡 Recommended: /command - reason
```
Never skip this. Default to `/continue` if nothing else applies.

---

**Show project status in the requested format, ending with the Next Actions menu.**
