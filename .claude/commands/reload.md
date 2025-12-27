---
description: Reload project context after /clear
---

Reload full project context and resume work.

## Context Reload Sequence

### Step 1: Load Core Files
1. Read @CLAUDE.md - Engineering guidelines
2. Read @features.json - Feature status
3. Read @claude-progress.txt - Recent history

### Step 2: Load Structured Memory (v3.4)

Retrieve context using /recall:

```
/recall project    # Project-level context
/recall decisions  # Recent architectural decisions
/recall learnings  # Patterns that worked
```

Check memory files:
- `.claude/v3/memory/project.json` - Project understanding
- `.claude/v3/memory/decisions.json` - Key decisions
- `.claude/v3/memory/learnings.json` - What works here

### Step 3: Check Worktrees (v3.4)

```bash
git worktree list
```

If worktrees exist, show active feature branches.

### Step 4: Health Check
- git status - Uncommitted changes?
- Run quick test if applicable

## Status Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project: [name]
Current Focus: [from progress/memory]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recent Work:
- [Last 3 completed items]

Status:
✅ X features passing
⏳ Y features in progress
📝 Z features remaining

Active Worktrees: [list if any]

Key Decisions Loaded: [count]
Learnings Applied: [count]

Next Task: [from progress log or memory]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Ready to Continue

"Context reloaded. Ready to continue from: [specific task]"

Then await user instruction or automatically continue if task was clearly in progress.
