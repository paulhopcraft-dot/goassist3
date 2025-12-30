---
description: Code review current work and suggest improvements
---

Review the code changes since last commit (or specified files).

## Review Checklist

### Correctness
- [ ] Logic is correct
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] No obvious bugs

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevented
- [ ] Auth/authz correct

### Quality
- [ ] Code is readable
- [ ] Functions are focused (single responsibility)
- [ ] No unnecessary complexity
- [ ] Tests cover the changes

### Performance
- [ ] No obvious N+1 queries
- [ ] No blocking calls in async code
- [ ] Appropriate caching considered

## Output Format

```
Code Review: [files reviewed]
================================

✅ Good:
- [What's done well]

⚠️ Suggestions:
- [Improvements to consider]

❌ Issues (must fix):
- [Problems that need addressing]

Overall: [APPROVE / NEEDS CHANGES]
```

$ARGUMENTS
