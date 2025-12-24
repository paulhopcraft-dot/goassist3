---
description: Implement feature using strict TDD
arguments: feature description
---

<instructions>
Implement using strict Test-Driven Development: $ARGUMENTS
</instructions>

<tdd_cycle>
<phase name="RED" number="1">
<title>Write Failing Tests First</title>
<requirements>
Write tests that cover:
- Happy path (normal operation)
- Edge cases (boundaries, empty inputs)
- Error conditions (invalid inputs, failures)
</requirements>
<warning>
⚠️ IMPORTANT: Tests must FAIL before writing implementation
</warning>
</phase>

<phase name="VERIFY_RED" number="2">
<title>Run Tests - Confirm FAILURE</title>
<command>
```bash
# Run tests and verify they fail
[test command]
```
</command>
<expected>All new tests should fail (RED)</expected>
</phase>

<phase name="GREEN" number="3">
<title>Write Minimal Code</title>
<requirements>
Write the **minimum** code to make tests pass:
- Don't over-engineer
- Don't add unrequested features
- Don't optimize yet
- Just make it work
</requirements>
</phase>

<phase name="VERIFY_GREEN" number="4">
<title>Run Tests - Confirm PASS</title>
<command>
```bash
# Run tests and verify they pass
[test command]
```
</command>
<expected>All tests should pass (GREEN)</expected>
</phase>

<phase name="REFACTOR" number="5">
<title>REFACTOR (Optional)</title>
<requirements>
If needed, clean up the code:
- Remove duplication
- Improve naming
- Simplify logic
</requirements>
<constraint>**Tests must stay green during refactoring!**</constraint>
</phase>

<phase name="COMMIT" number="6">
<title>Commit</title>
<command>
```bash
git add .
git commit -m "feat: [feature] - TDD implementation"
```
</command>
</phase>
</tdd_cycle>

<rules>
<forbidden>
- ❌ Never write implementation before tests
- ❌ Never skip the RED phase
- ❌ Never delete tests to make them pass
</forbidden>
<required>
- ✅ One test at a time
- ✅ Smallest possible steps
- ✅ Refactor only when green
</required>
</rules>
