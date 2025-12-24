---
description: Validate features.json against schema
---

# Validate Features JSON

Check features.json for errors and inconsistencies.

## Validation Steps

### 1. Schema Validation
If features.schema.json exists, validate against it.

### 2. Logic Validation
Check for:
- **Duplicate IDs**: All feature IDs must be unique
- **Invalid dependencies**: Dependencies must reference existing feature IDs
- **Metadata sync**: metadata.total_features === features.length
- **Metadata sync**: metadata.completed === count of features where passes=true
- **Timestamp format**: All timestamps should be valid ISO 8601
- **Criteria consistency**: If all acceptance_criteria.passes=true, feature.passes should be true
- **Passes false by default**: Warn if new features start with passes=true

### 3. Report

```
✓ Schema validation passed
✓ No duplicate IDs
✓ All dependencies valid
✓ Metadata in sync
⚠ Warning: F003 has all criteria passing but feature.passes=false
⚠ Warning: F005 depends on F004 which is not yet complete
```

## Auto-fix

Offer to auto-fix common issues:
- Sync metadata counts
- Update last_updated timestamps
- Fix invalid date formats

$ARGUMENTS
