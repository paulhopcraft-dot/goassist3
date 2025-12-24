---
description: Code review current work and suggest improvements
---

<instructions>
Review the code changes since last commit (or specified files).
</instructions>

<review_checklist>
<category name="Correctness">
- [ ] Logic is correct
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] No obvious bugs
</category>

<category name="Security">
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevented
- [ ] Auth/authz correct
</category>

<category name="Quality">
- [ ] Code is readable
- [ ] Functions are focused (single responsibility)
- [ ] No unnecessary complexity
- [ ] Tests cover the changes
</category>

<category name="Performance">
- [ ] No obvious N+1 queries
- [ ] No blocking calls in async code
- [ ] Appropriate caching considered
</category>
</review_checklist>

<output_format>
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
</output_format>

<arguments>$ARGUMENTS</arguments>
