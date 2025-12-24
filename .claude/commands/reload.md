---
description: Reload project context after /clear
---

<instructions>
Reload full project context and resume work.
</instructions>

<context_reload_sequence>
<step number="1">Read @CLAUDE.md - Engineering guidelines</step>
<step number="2">Read @features.json - Feature status</step>
<step number="3">Read @claude-progress.txt - Recent history</step>
<step number="4">Check git status - Uncommitted changes</step>
<step number="5">Run quick health check (tests passing?)</step>
</context_reload_sequence>

<status_report>
<format>
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
</format>
</status_report>

<completion>
"Context reloaded. Ready to continue from: [specific task]"

Then await user instruction or automatically continue if task was clearly in progress.
</completion>
