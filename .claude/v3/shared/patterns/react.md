# ReAct Pattern (Reasoning + Acting)

**Version**: 1.0.0
**Pattern Type**: Advanced Prompting Technique
**Source**: Yao et al., 2022 - "ReAct: Synergizing Reasoning and Acting in Language Models"

---

## Overview

ReAct is a prompting pattern that combines **reasoning traces** with **task-specific actions** in an interleaved manner. Instead of just thinking or just acting, the model alternates between both to solve problems more effectively.

**Key Insight**: Pure reasoning (CoT) lacks access to external information. Pure acting lacks strategic planning. ReAct combines both strengths.

---

## Pattern Structure

```
Thought: [Free-form reasoning about what to do next]
Action: [Specific action to take - tool call, API request, etc.]
Observation: [Result/feedback from the action]

→ Repeat until task complete
```

---

## When to Use ReAct

✅ **Use ReAct when**:
- Task requires external information (API calls, file reads, web searches)
- Problem needs multi-step reasoning with verification
- You need to adjust strategy based on intermediate results
- Combining knowledge with real-world data

❌ **Don't use ReAct when**:
- Task is purely computational (use PAL instead)
- No external tools needed (use CoT instead)
- Single-step query (use zero-shot instead)

---

## Implementation

### Basic ReAct Loop

```markdown
## Iteration 1

**Thought**: I need to identify which tests are failing to understand the problem.

**Action**: Run `npm test` to see test results
```bash
cd /project && npm test
```

**Observation**: 4 tests failing in verticals.test.ts - OQE signature mismatch error

---

## Iteration 2

**Thought**: The error mentions signature mismatch. I need to check the function signature to understand the expected format.

**Action**: Read the scoreVertical function definition
```
Read file: src/db/repositories/verticals.ts (lines 100-120)
```

**Observation**: Function expects `scoreVertical(input: OQEScoringInput)` where input is a nested object structure, not separate parameters.

---

## Iteration 3

**Thought**: Tests are calling the function with wrong signature. I need to update test data to match the expected nested structure.

**Action**: Update test file with correct input format
```
Edit file: src/db/repositories/verticals.test.ts
- Old: scoreVertical(vertical.vertical_id, { labor_intensity: 9, ... })
+ New: scoreVertical({ vertical_id: ..., labor_intensity: { labor_cost_pct: 90, ... } })
```

**Observation**: Test file updated with correct nested structure for all 4 failing tests.

---

## Iteration 4

**Thought**: Need to verify the fix worked by running tests again.

**Action**: Run tests
```bash
npm test
```

**Observation**: ✓ All 16 tests passing! Problem solved.

**Result**: COMPLETE ✓
```

---

## ReAct vs Other Patterns

| Pattern | Reasoning | External Tools | Best For |
|---------|-----------|----------------|----------|
| **Chain-of-Thought** | ✓ Yes | ✗ No | Pure reasoning tasks |
| **ReAct** | ✓ Yes | ✓ Yes | Multi-step + external data |
| **PAL** | Via code | Via execution | Mathematical/computational |
| **Zero-Shot** | ✗ Minimal | ✗ No | Simple, direct queries |

---

## ReAct in Autonomous Mode

Our autonomous mode already implements ReAct implicitly! Here's how:

**PHASE 1 (Observation)**: Assess project state
**PHASE 2 (Thought)**: Tree of Thoughts reasoning
**PHASE 3 (Action)**: Execute chosen action
**PHASE 4 (Observation)**: Evaluate results
**PHASE 5 (Thought)**: Decide to continue or stop

The loop repeats until work is complete.

---

## Best Practices

### 1. Explicit Thought Articulation
✅ **Good**: "I need to check the function signature because the error mentions a mismatch"
❌ **Bad**: "Let me read the file"

### 2. Specific Actions
✅ **Good**: "Read src/db/repositories/verticals.ts lines 100-120"
❌ **Bad**: "Look at the code"

### 3. Detailed Observations
✅ **Good**: "Function expects nested object structure with labor_intensity containing labor_cost_pct field"
❌ **Bad**: "Found the function"

### 4. Iteration Counting
Always number iterations explicitly: "Iteration 1", "Iteration 2", etc.
This helps track progress and prevent infinite loops.

---

## Advanced: Multi-Tool ReAct

When tasks require multiple tools:

```
Thought: Need to understand both the implementation and the tests

Action 1: Read implementation
Action 2: Read tests
Action 3: Compare signatures

Observation: Found mismatch - implementation expects nested object, tests pass flat parameters
```

---

## Failure Handling

**When Action Fails**:
```
Thought: Previous approach didn't work, need different strategy
Action: [Try alternative approach]
Observation: [New result]
```

**When Stuck After 3 Iterations**:
```
Thought: Not making progress, need to reassess problem
Action: Step back and gather more context
Observation: [Broader view]
```

---

## Template

```markdown
## Iteration [N]

**Thought**: [What I'm thinking about doing and why]

**Action**: [Specific tool/command to execute]
[Tool call details]

**Observation**: [What happened / what I learned]

[If not done, continue to Iteration N+1]
```

---

## Example: Debug Failing Tests

**Full ReAct Sequence**:

```
Iteration 1:
Thought: Need to see which tests are failing
Action: npm test
Observation: 4/16 tests failing - signature mismatch

Iteration 2:
Thought: Need to understand expected signature
Action: Read verticals.ts:100-120
Observation: Expects nested OQEScoringInput object

Iteration 3:
Thought: Tests using wrong format, need to fix
Action: Update tests with correct structure
Observation: All test files updated

Iteration 4:
Thought: Verify fix worked
Action: npm test
Observation: ✓ 16/16 passing

Result: COMPLETE
```

---

## Integration with Other Patterns

### ReAct + CoT
Use CoT within Thought steps for complex reasoning:
```
Thought: [Chain-of-thought reasoning about strategy]
  → First, I should...
  → Then, considering X...
  → Therefore, the best approach is...
Action: [Execute chosen approach]
```

### ReAct + Self-Consistency
Generate multiple thought paths, compare observations:
```
Thought A: Could fix by changing implementation
Thought B: Could fix by updating tests
Thought C: Could fix by adding adapter layer

Action: Evaluate each approach
Observation: Option B is simplest and safest
```

### ReAct + Tool Use
Natural fit - ReAct was designed for tool integration:
- Bash commands
- File operations (Read, Edit, Write)
- Web searches (WebFetch, WebSearch)
- Agent invocation (Task tool)

---

## Metrics for Success

Track ReAct effectiveness:
- **Iterations to Solution**: Fewer = better reasoning
- **Action Success Rate**: % of actions that produce useful observations
- **Thought Quality**: Clear reasoning → better actions
- **Observation Detail**: Rich observations → better next thoughts

---

## References

- **Paper**: "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)
- **Our Implementation**: `.claude/skills/autonomous/SKILL.md`
- **Related Patterns**: `cot.md`, `pal.md`
- **DAIR.AI Guide**: https://www.promptingguide.ai/techniques/react

---

**Created**: 2025-12-26
**Pattern Library**: claude-code-toolkit v3.1
