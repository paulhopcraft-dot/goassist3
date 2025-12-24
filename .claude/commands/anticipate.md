---
description: Devil's Advocate - Anticipatory Reflection before execution (from LLM Agents paper)
---

<instructions>
**Based on:** "Building Autonomous LLM Agents" paper, Section 4.3 (DEVIL'S ADVOCATE)

**Use this when:** Before implementing any feature, especially complex or risky ones.

**Purpose:** Proactively identify potential failures and plan mitigation strategies BEFORE writing code.

think hard about potential failures for this task:

**Task/Feature:** $ARGUMENTS
</instructions>

<workflow>
<step number="1">
<title>Challenge Your Assumptions</title>
<task>
Play Devil's Advocate - what assumptions am I making that could be wrong?
</task>

<template>
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
</template>

<red_flags>
**Red flags:**
- Assumptions about external APIs (they always work, they're fast, etc.)
- Assumptions about data format/quality
- Assumptions about user behavior
- Assumptions about system resources (memory, CPU, network)
- Assumptions about third-party libraries
</red_flags>
</step>

<step number="2">
<title>Enumerate Failure Modes</title>
<task>
What can go wrong during implementation or execution?
</task>

<technical_failures>
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
</technical_failures>

<logical_failures>
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
</logical_failures>

<integration_failures>
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
</integration_failures>
</step>

<step number="3">
<title>Stress Test Your Plan</title>
<task>
Challenge the implementation strategy:
</task>

<stress_tests>
<performance>
**Performance:**
- 🔥 What if 100x more load than expected?
- ⏱️ What if latency spikes to 10x normal?
- 💾 What if we run out of memory?
- 🌐 What if network is slow/unstable?
</performance>

<reliability>
**Reliability:**
- What if the service crashes mid-operation?
- What if we need to rollback?
- What if data gets corrupted?
- What if dependencies are down?
</reliability>

<security>
**Security:**
- What if input is malicious?
- What if someone tries to exploit this?
- What if credentials leak?
- What if there's an injection attack vector?
</security>

<maintainability>
**Maintainability:**
- Can someone else understand this in 6 months?
- Is this testable?
- Is this debuggable when it breaks?
- Will this code rot quickly?
</maintainability>
</stress_tests>
</step>

<step number="4">
<title>Generate Alternative Approaches</title>
<task>
For each major risk, propose an alternative approach:
</task>

<template>
**Risk 1:** [high-impact failure]
- **Original approach:** [Plan A]
- **Alternative 1:** [Plan B - safer but maybe slower/more complex]
  - Pros: [advantages]
  - Cons: [trade-offs]
- **Alternative 2:** [Plan C - different paradigm]
  - Pros: [advantages]
  - Cons: [trade-offs]
- **Recommendation:** [which to use and why]
</template>
</step>

<step number="5">
<title>Pre-Implementation Checklist</title>
<verify>
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
</verify>

<note>**If any checkbox is unchecked, address it before implementing.**</note>
</step>

<step number="6">
<title>Output Risk Assessment</title>
<present>
Present the final risk assessment:
</present>

<template>
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
</template>
</step>

<step number="7">
<title>Update Planning Docs</title>
<document>
Document this analysis:
</document>

<project_index>
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
</project_index>

<features_json>
**Add to features.json (for the feature):**
```json
{
  "id": "F00X",
  "risks_identified": true,
  "mitigation_plan": "See PROJECT_INDEX.json risk_assessments",
  "confidence": "medium"
}
```
</features_json>
</step>
</workflow>

<usage_pattern>
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
</usage_pattern>

<example>
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
</example>
