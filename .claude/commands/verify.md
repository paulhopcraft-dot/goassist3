---
description: Verify all passing features actually work
---

<instructions>
Use subagents to thoroughly verify all features marked "passes": true in @features.json.
</instructions>

<verification_steps>
For each feature:
1. Run related tests
2. Test end-to-end as a user would
3. Check edge cases
4. Verify acceptance_criteria are actually met
</verification_steps>

<failure_handling>
If anything is broken:
- Set "passes": false in features.json
- Note what's wrong in the feature's "notes" field
</failure_handling>

<output_format>
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
</output_format>
