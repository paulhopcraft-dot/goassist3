---
description: Reload project context after /clear
---

Reload full project context and resume work.

## Context Reload Sequence
1. Read @CLAUDE.md - Engineering guidelines
2. Read @features.json - Feature status
3. Read @claude-progress.txt - Recent history
4. Check git status - Uncommitted changes
5. Run quick health check (tests passing?)

## Status Report
Provide concise summary:

```
📋 Project: GoAssist v2.1
🎯 Current Focus: [from progress log]

Recent Work:
- [Last 3 completed items]

Status:
✅ X features passing
⏳ Y features in progress  
📝 Z features remaining

Next Task: [from progress log or next incomplete feature]
```

## Ready to Continue
"Context reloaded. Ready to continue from: [specific task]"

Then await user instruction or automatically continue if task was clearly in progress.
