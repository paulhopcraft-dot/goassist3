---
description: Blind validation - separate verifier runs tests
---

Perform independent validation using separate verifier agent.

## Principle: Builder Never Validates Own Work

The builder (current session) creates a test plan. A separate validator agent executes it independently and reports results.

## Process

### 1. Create Test Plan
Builder documents:
- What was built/changed
- Expected behavior
- Test commands to run
- Success criteria
- Files to check

### 2. Spawn Validator Agent
Use Task tool with validation agent:
- Provide test plan only
- No access to build context
- Fresh perspective

### 3. Validator Executes
Independently:
- Runs specified tests
- Checks for regressions
- Verifies success criteria
- Reports PASS/FAIL with evidence

### 4. Report Results
Validator returns:
```
VALIDATION RESULT: [PASS/FAIL]

Tests Run:
✅ Unit tests: 302/302 passed
✅ Integration tests: 81/81 passed
✅ Performance benchmarks: Met (<0.1ms, <2ms)

Regressions: None detected

Evidence:
[Test output, logs, metrics]
```

## When to Use
- After implementing new features
- Before merging to main
- When tests are critical (performance, security)
- After refactoring

## Execute Validation
[Create test plan and spawn validator agent for current changes]
