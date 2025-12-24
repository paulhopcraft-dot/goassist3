---
description: Blind validation - separate verifier runs tests
---

<instructions>
Perform independent validation using separate verifier agent.
</instructions>

<principle>
**Builder Never Validates Own Work**

The builder (current session) creates a test plan. A separate validator agent executes it independently and reports results.
</principle>

<process>
<step number="1">
<title>Create Test Plan</title>
<builder_documents>
Builder documents:
- What was built/changed
- Expected behavior
- Test commands to run
- Success criteria
- Files to check
</builder_documents>
</step>

<step number="2">
<title>Spawn Validator Agent</title>
<use_task_tool>
Use Task tool with validation agent:
- Provide test plan only
- No access to build context
- Fresh perspective
</use_task_tool>
</step>

<step number="3">
<title>Validator Executes</title>
<independently>
Independently:
- Runs specified tests
- Checks for regressions
- Verifies success criteria
- Reports PASS/FAIL with evidence
</independently>
</step>

<step number="4">
<title>Report Results</title>
<validator_returns>
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
</validator_returns>
</step>
</process>

<when_to_use>
- After implementing new features
- Before merging to main
- When tests are critical (performance, security)
- After refactoring
</when_to_use>

<execution>
[Create test plan and spawn validator agent for current changes]
</execution>
