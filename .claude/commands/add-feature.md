---
description: Add a new feature to features.json
---

<instructions>
Add a new feature to the project backlog.
</instructions>

<required_information>
1. **Feature Name**: Short descriptive name
2. **Description**: What this feature does
3. **Acceptance Criteria**: Specific, testable conditions
4. **Dependencies**: Which features must be done first
5. **Priority**: high / medium / low
</required_information>

<feature_template>
```json
{
  "id": "F[NNN]",
  "name": "[Feature Name]",
  "description": "[What this feature does]",
  "acceptance_criteria": [
    {"criterion": "[Testable condition 1]", "passes": false, "verified_at": null},
    {"criterion": "[Testable condition 2]", "passes": false, "verified_at": null}
  ],
  "dependencies": ["F001", "F002"],
  "priority": "high",
  "passes": false,
  "branch": null,
  "notes": "",
  "last_updated": "[timestamp]"
}
```
</feature_template>

<steps>
1. Read current features.json
2. Determine next ID (F001, F002, etc.)
3. Add feature with all fields
4. Set "passes": false (always)
5. Update metadata.total_features
6. Save features.json
7. Report what was added
</steps>

<arguments>$ARGUMENTS</arguments>
