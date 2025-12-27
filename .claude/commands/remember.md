---
name: remember
version: 1.0.0
description: Store important context in structured memory for cross-session persistence
---

# Remember: $ARGUMENTS

## Overview

Store important context, decisions, and learnings in structured memory. This information persists across sessions and can be recalled later.

---

## Memory Types

### 1. Decision Memory
Store architectural or design decisions:

```bash
/remember decision "Use Decimal for all monetary values" --rationale "SOX compliance requires GAAP precision" --applies-to govertical,gpnet3
```

**Stored as**:
```json
{
  "id": "d_001",
  "type": "decision",
  "content": "Use Decimal for all monetary values",
  "rationale": "SOX compliance requires GAAP precision",
  "applies_to": ["govertical", "gpnet3"],
  "created": "2025-12-27T10:00:00Z",
  "session": "session-42"
}
```

---

### 2. Entity Memory
Track important code entities:

```bash
/remember entity "scoreVertical" --file src/db/repositories/verticals.ts --notes "Changed signature in v2, expects nested input"
```

**Stored as**:
```json
{
  "id": "e_001",
  "type": "entity",
  "name": "scoreVertical",
  "file": "src/db/repositories/verticals.ts",
  "notes": ["Changed signature in v2", "Expects nested input"],
  "last_modified": "2025-12-27",
  "relationships": []
}
```

---

### 3. Learning Memory
Store patterns learned from experience:

```bash
/remember learning "Always check audit logging for financial features" --source "Failed tests in session 15"
```

**Stored as**:
```json
{
  "id": "l_001",
  "type": "learning",
  "pattern": "Always check audit logging for financial features",
  "source": "Failed tests in session 15",
  "success_rate": null,
  "created": "2025-12-27"
}
```

---

### 4. Context Memory
Store session-specific context:

```bash
/remember context "Working on OQE scoring algorithm refactor" --priority high
```

**Stored as**:
```json
{
  "id": "c_001",
  "type": "context",
  "content": "Working on OQE scoring algorithm refactor",
  "priority": "high",
  "session": "session-42",
  "active": true
}
```

---

## Quick Remember

Simple syntax for common cases:

```bash
# Remember a decision
/remember "We chose SQLite over PostgreSQL for simplicity"

# Remember with type
/remember decision "API uses REST, not GraphQL"

# Remember with tags
/remember "OQE weights: L=30%, S=20%, R=25%, M=15%, R=10%" --tags oqe,scoring,weights
```

---

## Process

1. **Parse Input**: Extract memory type, content, and metadata
2. **Generate ID**: Unique identifier (d_001, e_001, l_001, c_001)
3. **Store**: Write to appropriate JSON file
4. **Index**: Add to search index for /recall
5. **Confirm**: Show what was stored

---

## Storage Locations

| Type | File |
|------|------|
| Decisions | `.claude/v3/memory/decisions.json` |
| Entities | `.claude/v3/memory/entities.json` |
| Learnings | `.claude/v3/memory/learnings.json` |
| Context | `.claude/v3/memory/sessions/session-{N}.json` |
| Project | `.claude/v3/memory/project.json` |

---

## Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Memory Stored
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type: decision
ID: d_005
Content: Use Decimal for all monetary values
Rationale: SOX compliance requires GAAP precision
Applies to: govertical, gpnet3

Recall with: /recall d_005
Search with: /recall "monetary" or /recall --type decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Integration with /handoff

When running `/handoff`, automatically:
1. Save current session context to memory
2. Extract key decisions made
3. Note unfinished work

---

## Examples

```bash
# Remember a decision
/remember decision "Use vitest instead of jest" --rationale "Faster, native ESM support"

# Remember an important function
/remember entity "calculateOQEScore" --file src/scoring/oqe.ts --notes "Core algorithm, do not modify without tests"

# Remember a lesson learned
/remember learning "Run npm test before committing" --source "Broken build on commit abc123"

# Remember current work context
/remember context "Implementing F005 payment processing" --priority high
```

---

**Store the provided context in structured memory.**
