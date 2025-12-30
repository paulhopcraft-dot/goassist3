---
description: DPPM Planning - Decompose, Plan in Parallel, Merge (from LLM Agents paper)
---

# /think:parallel - Parallel Planning with Anticipatory Reflection

**Based on:** "Building Autonomous LLM Agents" paper, Section 4.1 (DPPM) + Section 4.3 (Anticipatory Reflection)

**Use this when:** Complex tasks with multiple independent subtasks, or when you need robust planning with fallback options.

---

## Instructions

ultrathink through this task using DPPM methodology:

**Task:** $ARGUMENTS

---

## Step 1: Decompose into Subtasks

Break the main task into 3-5 **independent** subtasks that can be worked on separately.

**Criteria for good subtasks:**
- Each has clear inputs/outputs
- Minimal dependencies on other subtasks
- Can be verified independently
- Meaningful unit of work (not too small)

**Output format:**
```
Main Task: [restate the task]

Subtasks:
1. [Subtask name] - [what it accomplishes]
2. [Subtask name] - [what it accomplishes]
3. [Subtask name] - [what it accomplishes]
...
```

---

## Step 2: Plan Each Subtask in Parallel

For **each subtask**, generate multiple plan options:

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

---

## Step 3: Merge into Global Plan

Combine subtask plans into coherent execution order:

**Execution Strategy:**

1. **Identify dependencies:**
   - Which subtasks MUST run sequentially?
   - Which CAN run in parallel? (for future optimization)

2. **Create execution graph:**
```
Phase 1: [Subtask X] (no dependencies)
         ↓
Phase 2: [Subtask Y, Subtask Z] (depend on X, can run parallel)
         ↓
Phase 3: [Subtask W] (depends on Y+Z completion)
```

3. **Risk assessment:**
   - Highest risk subtasks: [list]
   - Critical path (if any fails, entire task fails): [list]
   - Safe to fail (can work around): [list]

4. **Final merged plan:**
```
Step 1: [action] - from Subtask X, Plan A
  If fails: [action from Plan B]
Step 2: [action] - from Subtask Y, Plan A
  If fails: [action from Plan B]
...
```

---

## Step 4: Validation Check

Before execution, verify:

- [ ] All subtasks have Plan A + Plan B
- [ ] Dependencies are clear and minimal
- [ ] Success criteria are testable
- [ ] Each failure has a recovery strategy
- [ ] Critical path is identified

**If any checkbox unchecked, revise the plan.**

---

## Step 5: Output Final Plan

Present the executable plan:

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

---

## Notes

**When to use `/think:parallel` vs `/think`:**
- Use `/think:parallel` for:
  - Complex multi-step tasks
  - Tasks where failure is likely
  - Need robust planning with fallbacks
  
- Use `/think` for:
  - Simple linear tasks
  - Quick architecture brainstorming
  - Low-risk work

**Parallel execution:**
This plan identifies *what* can be parallelized. For actual parallel execution (multiple Claude Code instances), use `/branch` to create feature branches and work on subtasks in separate windows.

---

## Example

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
