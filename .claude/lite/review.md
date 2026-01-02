---
name: review
description: Quick code review
---

# Code Review

Review recent changes for issues.

## Check
- `git diff` - what changed?
- `git diff --cached` - what's staged?

## Checklist
- [ ] Logic correct?
- [ ] Edge cases handled?
- [ ] No hardcoded secrets?
- [ ] Tests cover changes?
- [ ] No obvious performance issues?

## Report
```
CODE REVIEW
===========
Files: [list]

Good:
- [positives]

Issues:
- [problems to fix]

Verdict: [APPROVE / NEEDS CHANGES]
```

$ARGUMENTS
