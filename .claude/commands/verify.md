---
description: Verify all passing features actually work
---

Use subagents to thoroughly verify all features marked "passes": true in @features.json.

For each feature:
1. Run related tests
2. Test end-to-end as a user would
3. Check edge cases
4. Verify acceptance_criteria are actually met

If anything is broken:
- Set "passes": false in features.json
- Note what's wrong in the feature's "notes" field

## Report Format
```
Feature Verification Report
===========================

Verified: X features
Actually Working: Y
Found Broken: Z

Broken Features:
- F00X: [name] - [what's wrong]
- F00X: [name] - [what's wrong]

Remaining Unverified: A
```
