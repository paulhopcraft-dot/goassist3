---
name: recall
version: 1.0.0
description: Retrieve relevant memories from structured storage
---

# Recall: $ARGUMENTS

## Overview

Search and retrieve memories stored with `/remember`. Finds relevant context, decisions, learnings, and entities.

---

## Search Methods

### By ID
```bash
/recall d_005
```

Returns specific memory by ID.

---

### By Keyword
```bash
/recall "payment"
```

Searches all memories for keyword.

**Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Search Results: "payment"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[d_003] Decision (2025-12-25)
  Use Stripe for payment processing
  Rationale: Best API, PCI compliance handled

[e_012] Entity: processPayment
  File: src/payments/processor.ts
  Notes: Handles all payment flows, wraps Stripe SDK

[l_007] Learning
  Always verify payment webhook signatures
  Source: Security audit findings

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 3 memories matching "payment"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### By Type
```bash
/recall --type decision
/recall --type entity
/recall --type learning
/recall --type context
```

Lists all memories of a specific type.

---

### By Tag
```bash
/recall --tag oqe
/recall --tag scoring,weights
```

Finds memories with matching tags.

---

### By Project
```bash
/recall --project govertical
```

Finds memories that apply to a specific project.

---

### Recent
```bash
/recall --recent
/recall --recent 10
```

Shows most recent N memories (default: 5).

---

### Session
```bash
/recall --session 42
/recall --session current
```

Shows memories from a specific session.

---

## Filters

Combine search with filters:

```bash
/recall "api" --type decision --project govertical
```

---

## Output Formats

### Default (Summary)
```bash
/recall "scoring"
```

Shows brief summaries.

### Full
```bash
/recall "scoring" --full
```

Shows complete memory contents.

### JSON
```bash
/recall "scoring" --json
```

Returns raw JSON for programmatic use.

---

## Context Injection

Recall can inject memories into current context:

```bash
/recall --inject "payment"
```

Adds relevant memories to current conversation context.

---

## Integration with /reload

When running `/reload`, automatically:
1. Load relevant project memories
2. Restore last session context
3. Show important decisions
4. List recent learnings

---

## Process

1. **Parse Query**: Extract search terms, type, filters
2. **Search**: Scan memory files for matches
3. **Rank**: Sort by relevance (exact > partial > tag)
4. **Format**: Present results based on output format
5. **Optionally Inject**: Add to current context

---

## Memory Locations Searched

| Type | File |
|------|------|
| Decisions | `.claude/v3/memory/decisions.json` |
| Entities | `.claude/v3/memory/entities.json` |
| Learnings | `.claude/v3/memory/learnings.json` |
| Context | `.claude/v3/memory/sessions/*.json` |
| Project | `.claude/v3/memory/project.json` |

---

## Examples

```bash
# Find all OQE-related memories
/recall "oqe"

# Find all architecture decisions
/recall --type decision

# Find payment-related entities
/recall "payment" --type entity

# Find recent learnings
/recall --type learning --recent 10

# Get memory by ID
/recall d_003

# Inject context from last session
/recall --session last --inject

# Find decisions for this project
/recall --type decision --project govertical
```

---

## No Results

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No memories found for "xyzabc"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Suggestions:
- Try broader keywords
- Check spelling
- Use /recall --recent to see recent memories
- Use /remember to store new memories

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**Search and retrieve relevant memories.**
