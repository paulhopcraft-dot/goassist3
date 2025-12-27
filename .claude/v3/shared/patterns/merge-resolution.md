# Merge Resolution Pattern

**Version**: 1.0.0
**Pattern Type**: AI-Assisted Conflict Resolution
**Source**: Auto-Claude integration (v3.4)

---

## Overview

This pattern defines how to automatically resolve Git merge conflicts using semantic understanding of code changes.

**Key Principle**: Understand intent, not just text. Two changes can modify the same lines but have compatible intents.

---

## Conflict Analysis Framework

### Step 1: Extract Versions

```
<<<<<<< HEAD
[main version]
=======
[feature version]
>>>>>>> feature/branch
```

Also retrieve:
- Common ancestor (git merge-base)
- Commit messages from both branches
- Related changes in same file

### Step 2: Classify Conflict Type

| Type | Description | Resolution Approach |
|------|-------------|---------------------|
| **Additive** | Both add different things | Keep both |
| **Modifying** | Both change same thing differently | Semantic merge |
| **Extending** | Feature extends main's change | Keep feature |
| **Superseding** | Main supersedes feature's change | Keep main |
| **Incompatible** | Truly conflicting logic | Manual required |

### Step 3: Determine Intent

For each version, ask:
1. What problem is this solving?
2. What behavior is it adding/changing?
3. Is it a fix, feature, or refactor?
4. What tests would validate it?

### Step 4: Assess Confidence

| Confidence | Criteria |
|------------|----------|
| HIGH (90%+) | Clear additive changes, obvious intent |
| MEDIUM (60-90%) | Some ambiguity but reasonable guess |
| LOW (<60%) | Conflicting business logic, need human |

---

## Resolution Strategies

### Strategy 1: Keep Both (Additive)

**When**: Changes are independent additions

**Example**:
```
<<<<<<< HEAD
import { validateEmail } from './validators';
=======
import { validatePassword } from './validators';
>>>>>>> feature/auth

// Resolution:
import { validateEmail, validatePassword } from './validators';
```

**Pattern**: Merge imports, function calls, array items

---

### Strategy 2: Keep Feature (Extending)

**When**: Feature branch extends main's work

**Example**:
```
<<<<<<< HEAD
function validate(email: string) {
  return isValidEmail(email);
}
=======
function validate(email: string, password: string) {
  return isValidEmail(email) && isValidPassword(password);
}
>>>>>>> feature/auth

// Resolution: Keep feature (extends with password)
function validate(email: string, password: string) {
  return isValidEmail(email) && isValidPassword(password);
}
```

---

### Strategy 3: Keep Main (Superseding)

**When**: Main has critical fix that feature lacks

**Example**:
```
<<<<<<< HEAD
// Fixed SQL injection vulnerability
const query = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
=======
// Original vulnerable code
const query = db.query(`SELECT * FROM users WHERE id = ${userId}`);
>>>>>>> feature/old

// Resolution: Keep main (security fix)
const query = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
```

---

### Strategy 4: Semantic Merge (Combining)

**When**: Both have valid changes that can be combined

**Example**:
```
<<<<<<< HEAD
function processUser(user: User) {
  logActivity(user.id);
  return user;
}
=======
function processUser(user: User) {
  validateUser(user);
  return user;
}
>>>>>>> feature/validation

// Resolution: Combine both intents
function processUser(user: User) {
  validateUser(user);
  logActivity(user.id);
  return user;
}
```

---

### Strategy 5: Manual Required

**When**: Cannot determine correct resolution

**Indicators**:
- Conflicting business logic
- Different architectural approaches
- Configuration values (URLs, keys)
- Deleted vs modified code

**Action**: Flag for human review with explanation

---

## Code Patterns for Merging

### Import Statements
- Combine imports from same module
- Preserve order (sorted or original)
- Remove duplicates

### Function Arguments
- Feature usually has more complete signature
- Check if main added required params
- Combine with defaults if needed

### Object Properties
- Merge properties from both
- Feature overrides for same key (usually)
- Check for type conflicts

### Array Elements
- Append from both (usually)
- Check for duplicates
- Preserve order semantics

### Control Flow
- Most complex - usually manual
- Check for mutually exclusive conditions
- Consider execution order

---

## Integration with ReAct

Use ReAct pattern for complex conflicts:

```
Iteration 1:
Thought: Conflict in user-service.ts lines 45-80. Both branches modify the same function.
Action: Read commit messages for both branches
Observation: Main added logging, feature added validation

Thought: These are complementary changes, not conflicting
Action: Merge both - add logging around validation
Observation: Combined version maintains both intents

Thought: Verify the merged code is syntactically valid
Action: Parse with TypeScript compiler
Observation: No syntax errors

Resolution: Keep combined version with high confidence
```

---

## Confidence Calculation

```
confidence = base_confidence
  × context_factor
  × change_size_factor
  × file_type_factor

Where:
- base_confidence: From strategy (0.6-1.0)
- context_factor: 1.0 if clear intent, 0.8 if ambiguous
- change_size_factor: 1.0 if <20 lines, 0.9 if <50, 0.7 if more
- file_type_factor: 1.0 for code, 0.8 for config, 0.5 for secrets
```

---

## Safety Rules

### Never Auto-Resolve:
- Files matching: `*.env*, *secret*, *credential*, *key*`
- Database migrations
- Package lock files
- Configuration with environment-specific values

### Always Confirm:
- Deleted code (someone removed, someone modified)
- Security-related files
- API contract changes
- More than 3 conflicts in one file

### Require Tests:
- After resolution, run related tests
- If tests fail, mark as manual required
- Suggest which test to run

---

## Output Format

```json
{
  "file": "src/auth/login.ts",
  "conflict_range": { "start": 45, "end": 62 },
  "head_version": "...",
  "feature_version": "...",
  "analysis": {
    "head_intent": "Added email validation",
    "feature_intent": "Added password validation",
    "conflict_type": "additive",
    "compatible": true
  },
  "resolution": {
    "strategy": "keep_both",
    "code": "...",
    "confidence": 0.95,
    "rationale": "Both add validation to different fields"
  },
  "risks": [],
  "requires_test": ["test/auth.test.ts"]
}
```

---

## References

- **Auto-Claude**: AI merge resolution feature
- **Git**: Three-way merge algorithm
- **Semantic Merge**: Beyond text-based merging
- **Our Implementation**: `.claude/commands/resolve.md`

---

**Created**: 2025-12-27
**Pattern Library**: claude-code-toolkit v3.4
**Status**: Foundation for AI-assisted merging
