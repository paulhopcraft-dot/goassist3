---
name: react
description: ReAct problem solving with explicit Thought-Action-Observation cycles
version: 1.0.0
pattern: ReAct (Reasoning + Acting)
---

# ReAct Skill - Explicit Reasoning & Acting

You are now in **ReAct Mode** - a structured problem-solving approach that explicitly separates reasoning from action.

## Mission

Solve the given problem using the ReAct pattern:
1. **Thought**: Reason about what to do next
2. **Action**: Execute a specific action using available tools
3. **Observation**: Note what you learned from the action
4. **Repeat**: Continue until problem is solved

**Key Principle**: Make reasoning transparent by articulating thoughts before acting.

---

## ReAct Loop Structure

For each iteration, follow this exact format:

```markdown
## Iteration [N]

**Thought**: [Explicit reasoning about what to do and why]
- What do I know so far?
- What do I need to find out?
- What's the best next action?

**Action**: [Specific tool/command to execute]
[Execute using appropriate tool: Bash, Read, Edit, Write, Grep, Glob, etc.]

**Observation**: [What the action revealed]
- What did I learn?
- Does this bring me closer to the solution?
- What should I do next?

---
```

Then either:
- **Continue** to next iteration if not done
- **Conclude** if problem is solved

---

## When to Use Each Tool

### Information Gathering
- **Thought**: "Need to understand the error"
- **Action**: `Bash: npm test` or `Read: error.log`

### Code Inspection
- **Thought**: "Need to see function signature"
- **Action**: `Read: src/module.ts (lines 100-150)`

### Pattern Finding
- **Thought**: "Need to find all occurrences"
- **Action**: `Grep: pattern="scoreVertical" output_mode="content"`

### Code Changes
- **Thought**: "Need to fix the signature"
- **Action**: `Edit: old="scoreVertical(id, data)" new="scoreVertical(data)"`

### Verification
- **Thought**: "Need to verify fix worked"
- **Action**: `Bash: npm test`

---

## Example ReAct Session

**Problem**: Fix failing tests in govertical project

### Iteration 1

**Thought**: I need to first identify which tests are failing and what the error messages are. This will tell me what's wrong.

**Action**: Run test suite
```bash
cd /project && npm test
```

**Observation**:
- 4 out of 16 tests failing
- All failures in `verticals.test.ts`
- Error: "Cannot read properties of undefined (reading 'labor_cost_pct')"
- This suggests a data structure mismatch

**Decision**: Need to examine the function being tested to understand expected structure

---

### Iteration 2

**Thought**: The error mentions `labor_cost_pct` is undefined, which suggests the function expects a nested object but is receiving something else. I should read the `scoreVertical` function to see its signature.

**Action**: Read function implementation
```
Read: src/db/repositories/verticals.ts (lines 100-120)
```

**Observation**:
- Function signature: `scoreVertical(input: OQEScoringInput)`
- Input expects nested structure: `{ labor_intensity: { labor_cost_pct: number, ... }, ... }`
- Function accesses `input.labor_intensity.labor_cost_pct` directly
- Tests must be passing flat structure instead of nested

**Decision**: Update tests to use correct nested structure

---

### Iteration 3

**Thought**: Now I know the problem - tests are using flat structure but function expects nested. I need to update all 4 test cases to use the proper nested object format with all sub-fields.

**Action**: Update test data format
```
Edit: src/db/repositories/verticals.test.ts
Old: scoreVertical(vertical.vertical_id, { labor_intensity: 9, ... })
New: scoreVertical({
  vertical_id: vertical.vertical_id,
  labor_intensity: { labor_cost_pct: 90, repetitive_task_ratio: 85 },
  ...
})
```

**Observation**:
- Updated all 4 failing tests
- Each test now provides full nested structure
- All required fields included

**Decision**: Run tests to verify the fix

---

### Iteration 4

**Thought**: The test data is now corrected. Running tests should show all 16 passing if the fix is complete.

**Action**: Run test suite
```bash
npm test
```

**Observation**:
- ✓ All 16 tests passing
- No errors
- Test output shows successful execution

**Result**: ✓ PROBLEM SOLVED

---

## Best Practices

### 1. Clear Thoughts
Each thought should explain:
- Current understanding
- What you need to know
- Why the chosen action makes sense

### 2. Specific Actions
Avoid vague actions like "check the code"
Use specific tool calls: "Read src/file.ts:100-150"

### 3. Rich Observations
Don't just say "found it"
Explain what you found and what it means

### 4. Iteration Limit
- Stop after 10 iterations if not making progress
- Reassess strategy if stuck

---

## Failure Recovery

**If Action Fails**:
```
Thought: Previous action failed because [reason].
         Need to try different approach: [alternative]
Action: [New approach]
Observation: [Result]
```

**If Stuck After 3 Iterations**:
```
Thought: Not making progress. Let me step back and gather more context.
         The core problem is [restate problem].
         I've tried [approaches].
         What I'm missing is [gap in knowledge].
Action: [Gather missing information]
```

---

## Integration with Autonomous Mode

ReAct complements autonomous mode:

**Autonomous Mode** = High-level workflow (PHASE 1-5)
**ReAct Mode** = Detailed execution within PHASE 3

Use ReAct when autonomous mode encounters:
- Complex debugging
- Multi-step fixes
- Unfamiliar codebases
- Verification needed

---

## Stopping Conditions

**Stop iterating when**:
- ✓ Problem solved (verified)
- ✓ Tests passing
- ✓ Feature complete
- ✗ 10 iterations reached (reassess)
- ✗ Action repeatedly fails (try different approach)

---

## Start Now

**Given problem**: [User's request]

Begin with:

## Iteration 1

**Thought**: [Analyze the problem and decide first action]

**Action**: [Execute appropriate tool]

**Observation**: [Note results]

---

**GO!**
