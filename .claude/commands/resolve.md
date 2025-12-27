---
name: resolve
version: 1.0.0
description: AI-assisted merge conflict resolution
---

# Resolve: $ARGUMENTS

## Overview

Automatically detect and resolve Git merge conflicts using AI-powered semantic understanding.

---

## Commands

### Auto-Resolve: `/resolve`

Detect and resolve all conflicts in current merge:

```bash
# Check for conflicts
git diff --name-only --diff-filter=U
```

For each conflicting file:
1. Read the conflict markers
2. Understand intent of both changes
3. Propose resolution
4. Apply if confirmed

---

### Preview: `/resolve --preview`

Show proposed resolutions without applying:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conflict Resolution Preview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: src/auth/login.ts
Conflict: Lines 45-62

<<<<<<< HEAD (main)
function validateUser(email: string) {
  return validateEmail(email);
}
=======
function validateUser(email: string, password: string) {
  return validateEmail(email) && validatePassword(password);
}
>>>>>>> feature/F001-auth

Analysis:
- Main: Added email validation
- Feature: Added password validation to same function
- Intent: Both add validation, not conflicting

Proposed Resolution:
function validateUser(email: string, password: string) {
  return validateEmail(email) && validatePassword(password);
}

Confidence: HIGH (95%)
Rationale: Feature branch extends main's work, keep feature version

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Interactive: `/resolve --interactive`

Step through each conflict with prompts:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conflict 1 of 3: src/auth/login.ts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Shows conflict and proposed resolution]

Options:
  [A] Accept proposed resolution
  [M] Keep main version
  [F] Keep feature version
  [E] Edit manually
  [S] Skip (leave conflicted)

Choice: _
```

---

### Specific File: `/resolve <file>`

Resolve conflicts in a specific file:

```bash
/resolve src/auth/login.ts
```

---

## Resolution Strategies

### Strategy 1: Keep Both (Most Common)
When changes are additive and non-overlapping:
- Main added logging
- Feature added validation
- Resolution: Keep both additions

### Strategy 2: Keep Feature
When feature extends or replaces main:
- Feature has newer implementation
- Main was intermediate state
- Resolution: Use feature version

### Strategy 3: Keep Main
When feature change is outdated:
- Main has critical fix
- Feature predates fix
- Resolution: Use main, reapply feature logic

### Strategy 4: Semantic Merge
When both have valid changes to same code:
- Understand intent of both
- Combine logically
- Resolution: New code combining both intents

### Strategy 5: Manual Required
When changes are truly incompatible:
- Conflicting business logic
- Architectural disagreement
- Resolution: Flag for human review

---

## Analysis Process

For each conflict:

1. **Extract Versions**
   - HEAD (main) version
   - MERGE_HEAD (feature) version
   - Common ancestor (if available)

2. **Understand Intent**
   - What was main trying to do?
   - What was feature trying to do?
   - Are they complementary or conflicting?

3. **Assess Confidence**
   - HIGH: Clear resolution (>90% confidence)
   - MEDIUM: Reasonable guess (60-90%)
   - LOW: Need human input (<60%)

4. **Propose Resolution**
   - Show proposed code
   - Explain rationale
   - Highlight any risks

---

## Output Schema

```json
{
  "status": "resolved" | "partial" | "manual_required",
  "files_resolved": [
    {
      "file": "src/auth/login.ts",
      "conflicts": 1,
      "strategy": "keep_feature",
      "confidence": 0.95,
      "rationale": "Feature extends main's validation"
    }
  ],
  "files_manual": [
    {
      "file": "src/config.ts",
      "reason": "Conflicting configuration values",
      "suggestion": "Review business requirements"
    }
  ],
  "summary": {
    "total_conflicts": 3,
    "auto_resolved": 2,
    "manual_required": 1
  }
}
```

---

## Integration with Worktree

When merging a worktree:

```bash
/worktree merge F001-auth

# If conflicts detected:
# Automatically runs /resolve --preview
# Shows proposed resolutions
# Asks for confirmation
# Applies resolutions
# Completes merge
```

---

## Safety

### Never Auto-Apply If:
- Confidence < 60%
- File is configuration/secrets
- Conflict involves deleted code
- More than 50 lines conflicted

### Always Require Confirmation For:
- Database migrations
- API contracts
- Security-related code
- Package dependencies

---

## Example Session

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/resolve
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyzing conflicts...

Found 3 conflicts in 2 files:

File: src/auth/login.ts (2 conflicts)
  ├── Line 45-62: Function signature change
  │   Strategy: Keep feature (extends validation)
  │   Confidence: HIGH (95%)
  │
  └── Line 120-135: Import statements
      Strategy: Keep both (additive)
      Confidence: HIGH (98%)

File: src/config.ts (1 conflict)
  └── Line 15-20: API endpoint URL
      Strategy: MANUAL REQUIRED
      Reason: Different environments, need clarification

Auto-resolvable: 2/3 conflicts

Apply auto-resolutions? (y/N): y

✓ Resolved: src/auth/login.ts (2 conflicts)
⚠ Manual: src/config.ts (1 conflict)

Remaining:
  Edit src/config.ts to resolve API endpoint conflict
  Then run: git add src/config.ts && git commit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**Resolve merge conflicts with AI assistance.**
