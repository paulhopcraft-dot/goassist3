---
description: Implement feature using strict TDD
arguments: feature description
---

Implement using strict Test-Driven Development: $ARGUMENTS

## TDD Cycle

### 1. RED - Write Failing Tests First

Write tests that cover:
- Happy path (normal operation)
- Edge cases (boundaries, empty inputs)
- Error conditions (invalid inputs, failures)

```
⚠️ IMPORTANT: Tests must FAIL before writing implementation
```

### 2. Run Tests - Confirm FAILURE

```bash
# Run tests and verify they fail
[test command]
```

Expected: All new tests should fail (RED)

### 3. GREEN - Write Minimal Code

Write the **minimum** code to make tests pass:
- Don't over-engineer
- Don't add unrequested features
- Don't optimize yet
- Just make it work

### 4. Run Tests - Confirm PASS

```bash
# Run tests and verify they pass
[test command]
```

Expected: All tests should pass (GREEN)

### 5. REFACTOR (Optional)

If needed, clean up the code:
- Remove duplication
- Improve naming
- Simplify logic

**Tests must stay green during refactoring!**

### 6. Commit

```bash
git add .
git commit -m "feat: [feature] - TDD implementation"
```

## Rules

- ❌ Never write implementation before tests
- ❌ Never skip the RED phase
- ❌ Never delete tests to make them pass
- ✅ One test at a time
- ✅ Smallest possible steps
- ✅ Refactor only when green
