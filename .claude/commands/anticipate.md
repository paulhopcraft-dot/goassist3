---
description: Devil's Advocate - Anticipatory Reflection before execution (from LLM Agents paper)
---

# /anticipate - Anticipatory Reflection (Devil's Advocate)

**Based on:** "Building Autonomous LLM Agents" paper, Section 4.3 (DEVIL'S ADVOCATE)

**Use this when:** Before implementing any feature, especially complex or risky ones.

**Purpose:** Proactively identify potential failures and plan mitigation strategies BEFORE writing code.

---

## Instructions

think hard about potential failures for this task:

**Task/Feature:** $ARGUMENTS

---

## Step 1: Challenge Your Assumptions

Play Devil's Advocate - what assumptions am I making that could be wrong?

**List every assumption:**
1. [Assumption 1]
   - Why I believe this: [reasoning]
   - ❌ How it could be wrong: [counter-scenario]
   - 📊 Validation: [how to verify before implementing]

2. [Assumption 2]
   - Why I believe this: [reasoning]
   - ❌ How it could be wrong: [counter-scenario]
   - 📊 Validation: [how to verify before implementing]

[Continue for all assumptions]

**Red flags:**
- Assumptions about external APIs (they always work, they're fast, etc.)
- Assumptions about data format/quality
- Assumptions about user behavior
- Assumptions about system resources (memory, CPU, network)
- Assumptions about third-party libraries

---

## Step 2: Enumerate Failure Modes

What can go wrong during implementation or execution?

**Technical Failures:**
1. **Failure:** [specific failure mode]
   - Likelihood: [high/medium/low]
   - Impact: [critical/major/minor]
   - Trigger: [what causes this]
   - Detection: [how we'd know it happened]
   - Mitigation: [preventive measure]
   - Recovery: [if it happens anyway, how to recover]

[Repeat for all technical failures]

**Examples:**
- Network timeout
- Out of memory
- Invalid input data
- Race condition
- Dependency unavailable
- Rate limit exceeded
- Authentication failure

**Logical Failures:**
1. **Failure:** [logic error]
   - How it manifests: [symptoms]
   - Root cause: [why the logic is flawed]
   - Edge cases: [scenarios that break it]
   - Fix: [corrected logic]

**Examples:**
- Off-by-one errors
- Null/undefined handling
- Type mismatches
- Incorrect algorithms
- Missing edge case handling

**Integration Failures:**
1. **Failure:** [integration issue]
   - Between: [component A] and [component B]
   - Symptom: [what we'd see]
   - Cause: [interface mismatch, timing, etc.]
   - Test: [how to catch this before production]

**Examples:**
- API contract mismatch
- Data format incompatibility
- Version conflicts
- Timing/race conditions
- State synchronization issues

---

## Step 3: Stress Test Your Plan

Challenge the implementation strategy:

**Performance:**
- 🔥 What if 100x more load than expected?
- ⏱️ What if latency spikes to 10x normal?
- 💾 What if we run out of memory?
- 🌐 What if network is slow/unstable?

**Reliability:**
- What if the service crashes mid-operation?
- What if we need to rollback?
- What if data gets corrupted?
- What if dependencies are down?

**Security:**
- What if input is malicious?
- What if someone tries to exploit this?
- What if credentials leak?
- What if there's an injection attack vector?

**Maintainability:**
- Can someone else understand this in 6 months?
- Is this testable?
- Is this debuggable when it breaks?
- Will this code rot quickly?

---

## Step 4: Generate Alternative Approaches

For each major risk, propose an alternative approach:

**Risk 1:** [high-impact failure]
- **Original approach:** [Plan A]
- **Alternative 1:** [Plan B - safer but maybe slower/more complex]
  - Pros: [advantages]
  - Cons: [trade-offs]
- **Alternative 2:** [Plan C - different paradigm]
  - Pros: [advantages]
  - Cons: [trade-offs]
- **Recommendation:** [which to use and why]

---

## Step 5: Pre-Implementation Checklist

Before writing any code, validate:

**Environment:**
- [ ] All dependencies are available and correct version
- [ ] Required credentials/keys are set
- [ ] Test environment matches production constraints
- [ ] Can rollback if needed

**Design:**
- [ ] Edge cases identified and handled
- [ ] Failure modes have recovery strategies
- [ ] Performance under load is acceptable
- [ ] Security vulnerabilities addressed

**Validation:**
- [ ] Acceptance criteria are testable
- [ ] Unit tests can be written before implementation
- [ ] Integration tests are feasible
- [ ] Monitoring/logging is planned

**Fallback:**
- [ ] Plan B exists for critical components
- [ ] Graceful degradation is possible
- [ ] Error messages are actionable
- [ ] Can detect and alert on failures

**If any checkbox is unchecked, address it before implementing.**

---

## Step 6: Output Risk Assessment

Present the final risk assessment:

```
=================================================
ANTICIPATORY REFLECTION - RISK ASSESSMENT
=================================================

TASK: [restate task]

CRITICAL ASSUMPTIONS (must validate):
1. [assumption] - Validate by: [method]
2. [assumption] - Validate by: [method]

HIGH-RISK FAILURE MODES:
1. [failure] - Mitigation: [preventive measure]
2. [failure] - Mitigation: [preventive measure]

ALTERNATIVE APPROACHES (if Plan A fails):
- Plan B: [alternative]
- Plan C: [alternative]

PRE-IMPLEMENTATION ACTIONS:
1. [action to de-risk before coding]
2. [action to de-risk before coding]

MONITORING PLAN:
- Metrics to track: [list]
- Alerts to set: [list]
- Log points: [where to add logging]

RECOMMENDATION: [proceed/revise plan/choose alternative]

CONFIDENCE LEVEL: [high/medium/low]
  Reasoning: [why this confidence level]
=================================================
```

---

## Step 7: Update Planning Docs

Document this analysis:

**Add to PROJECT_INDEX.json:**
```json
{
  "memory": {
    "risk_assessments": [
      {
        "feature": "[feature ID]",
        "date": "[date]",
        "critical_risks": ["risk1", "risk2"],
        "mitigations": ["mitigation1", "mitigation2"],
        "confidence": "medium"
      }
    ]
  }
}
```

**Add to features.json (for the feature):**
```json
{
  "id": "F00X",
  "risks_identified": true,
  "mitigation_plan": "See PROJECT_INDEX.json risk_assessments",
  "confidence": "medium"
}
```

---

## Usage Pattern

**Recommended workflow:**

```bash
# 1. Plan the feature
/think:parallel "Implement audio streaming"

# 2. Challenge the plan (THIS COMMAND)
/anticipate "Audio streaming implementation from plan"

# 3. If risks are acceptable → implement
/continue

# 4. If risks are too high → revise
/think:parallel "Revised approach addressing risks..."
/anticipate "Revised audio streaming plan"
```

---

## Example

**Task:** Implement WebSocket audio streaming

**Assumptions challenged:**
1. "WebSocket connection stays stable"
   - ❌ Could be wrong: Mobile networks drop often
   - Validation: Test on 3G/4G with packet loss
   - Mitigation: Add reconnection logic

2. "Audio chunks arrive in order"
   - ❌ Could be wrong: Network reordering
   - Validation: Test under network jitter
   - Mitigation: Add sequence numbers + reordering buffer

**High-risk failures:**
1. Connection drops mid-stream
   - Likelihood: High (mobile networks)
   - Mitigation: Heartbeat + auto-reconnect
   - Recovery: Resume from last acknowledged chunk

2. Buffer overflow (chunks arrive faster than processed)
   - Likelihood: Medium
   - Mitigation: Backpressure + adaptive buffering
   - Recovery: Drop oldest chunks, log warning

**Alternative approaches:**
- Plan A: Raw WebSocket (current)
- Plan B: Socket.IO (built-in reconnection)
- Plan C: WebRTC DataChannel (lower latency but more complex)
- Recommendation: Start with Plan A, keep Plan B ready

**Pre-implementation actions:**
1. Set up test environment with simulated packet loss
2. Write heartbeat mechanism first
3. Add comprehensive logging
4. Create reconnection test suite

**Confidence: Medium** - Network reliability is outside our control, but mitigations are solid.
