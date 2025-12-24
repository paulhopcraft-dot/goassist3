---
description: DPPM Planning - Decompose, Plan in Parallel, Merge (from LLM Agents paper)
---

<instructions>
**Based on:** "Building Autonomous LLM Agents" paper, Section 4.1 (DPPM) + Section 4.3 (Anticipatory Reflection)

**Use this when:** Complex tasks with multiple independent subtasks, or when you need robust planning with fallback options.

ultrathink through this task using DPPM methodology:

**Task:** $ARGUMENTS
</instructions>

<workflow>
<step number="1">
<title>Decompose into Subtasks</title>
<task>
Break the main task into 3-5 **independent** subtasks that can be worked on separately.
</task>

<criteria>
**Criteria for good subtasks:**
- Each has clear inputs/outputs
- Minimal dependencies on other subtasks
- Can be verified independently
- Meaningful unit of work (not too small)
</criteria>

<output_format>
```
Main Task: [restate the task]

Subtasks:
1. [Subtask name] - [what it accomplishes]
2. [Subtask name] - [what it accomplishes]
3. [Subtask name] - [what it accomplishes]
...
```
</output_format>
</step>

<step number="2">
<title>Plan Each Subtask in Parallel</title>
<task>
For **each subtask**, generate multiple plan options:
</task>

<template>
**For Subtask 1:**
- **Plan A (Primary):** [detailed approach]
  - Steps: [1, 2, 3...]
  - Dependencies: [what's needed before starting]
  - Success criteria: [how we know it worked]

- **Plan B (Alternative):** [backup approach if Plan A fails]
  - Steps: [1, 2, 3...]
  - When to use: [trigger conditions for switching]

- **Anticipatory Reflection (Devil's Advocate):**
  - ⚠️ What could go wrong? [potential failures]
  - 🛡️ Mitigation: [preventive measures]
  - 🔄 Recovery: [if it fails anyway, how to recover]

**Repeat for all subtasks.**
</template>
</step>

<step number="3">
<title>Merge into Global Plan</title>
<task>
Combine subtask plans into coherent execution order:
</task>

<execution_strategy>
<identify_dependencies>
**1. Identify dependencies:**
   - Which subtasks MUST run sequentially?
   - Which CAN run in parallel? (for future optimization)
</identify_dependencies>

<create_execution_graph>
**2. Create execution graph:**
```
Phase 1: [Subtask X] (no dependencies)
         ↓
Phase 2: [Subtask Y, Subtask Z] (depend on X, can run parallel)
         ↓
Phase 3: [Subtask W] (depends on Y+Z completion)
```
</create_execution_graph>

<risk_assessment>
**3. Risk assessment:**
   - Highest risk subtasks: [list]
   - Critical path (if any fails, entire task fails): [list]
   - Safe to fail (can work around): [list]
</risk_assessment>

<final_merged_plan>
**4. Final merged plan:**
```
Step 1: [action] - from Subtask X, Plan A
  If fails: [action from Plan B]
Step 2: [action] - from Subtask Y, Plan A
  If fails: [action from Plan B]
...
```
</final_merged_plan>
</execution_strategy>
</step>

<step number="4">
<title>Validation Check</title>
<verify>
Before execution, verify:

- [ ] All subtasks have Plan A + Plan B
- [ ] Dependencies are clear and minimal
- [ ] Success criteria are testable
- [ ] Each failure has a recovery strategy
- [ ] Critical path is identified
</verify>

<note>**If any checkbox unchecked, revise the plan.**</note>
</step>

<step number="5">
<title>Output Final Plan</title>
<present>
Present the executable plan:
</present>

<template>
```
=================================================
PARALLEL PLAN - READY FOR EXECUTION
=================================================

SUBTASKS: [list with IDs: ST1, ST2, ST3...]

EXECUTION ORDER:
Phase 1: ST1 → Phase 2: ST2, ST3 → Phase 3: ST4

DETAILED STEPS:
1. [concrete action] (from ST1-A)
   Success: [check]
   Failure → [fallback from ST1-B]

2. [concrete action] (from ST2-A)
   Success: [check]
   Failure → [fallback from ST2-B]
...

RISK MITIGATION:
- Critical: [ST X] - if fails, use Plan B: [...]
- Flexible: [ST Y] - can adapt or skip if needed

READY TO EXECUTE? [yes/no + reasoning]
=================================================
```
</template>
</step>
</workflow>

<usage_notes>
<when_to_use>
**When to use `/think:parallel` vs `/think`:**
- Use `/think:parallel` for:
  - Complex multi-step tasks
  - Tasks where failure is likely
  - Need robust planning with fallbacks

- Use `/think` for:
  - Simple linear tasks
  - Quick architecture brainstorming
  - Low-risk work
</when_to_use>

<parallel_execution>
**Parallel execution:**
This plan identifies *what* can be parallelized. For actual parallel execution (multiple Claude Code instances), use `/branch` to create feature branches and work on subtasks in separate windows.
</parallel_execution>
</usage_notes>

<example>
**Task:** Implement real-time audio streaming for GoAssist

**Decomposition:**
- ST1: WebSocket connection management
- ST2: Audio chunking and buffering
- ST3: Latency optimization
- ST4: Error handling and reconnection

**ST1 Plans:**
- Plan A: Use FastAPI WebSockets with asyncio
- Plan B: Fall back to Socket.IO if WebSockets fail
- Risk: Connection drops mid-stream
- Mitigation: Implement heartbeat + auto-reconnect

**ST2 Plans:**
- Plan A: 100ms chunks with 200ms buffer
- Plan B: Adaptive chunking based on latency
- Risk: Buffer overflow or underflow
- Mitigation: Dynamic buffer sizing

**Merged Execution:**
Phase 1: ST1-A (WebSocket setup)
Phase 2: ST2-A + ST3-A (parallel - chunking + optimization)
Phase 3: ST4-A (error handling wraps everything)

**Validation:** All subtasks have fallbacks, critical path = ST1, ready to execute.
</example>
