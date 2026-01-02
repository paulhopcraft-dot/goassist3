---
name: status
description: Quick project status check
---

# Status Check

Read project state and report concisely.

## Check
1. `git status` - uncommitted changes?
2. `git log --oneline -3` - recent commits
3. Read `features.json` if exists - feature progress
4. Read `claude-progress.txt` if exists - session notes

## Report Format
```
PROJECT STATUS
==============
Branch: [current branch]
Changes: [clean/uncommitted count]
Tests: [run npm test if package.json exists]
Features: [X/Y complete] (if features.json exists)
Last session: [summary from progress file]

Next: [suggested action]
```

$ARGUMENTS
