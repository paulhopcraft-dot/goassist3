---
description: Post-Feature Reflection - Learn from implementation (from LLM Agents paper)
---

<instructions>
**Based on:** "Building Autonomous LLM Agents" paper, Section 4.3 (Reflection)

**Use this when:** After completing any feature, especially after failures or unexpected challenges.

**Purpose:** Critically evaluate performance, identify patterns, and improve future implementations.

think about what just happened and learn from it:

**Feature/Task completed:** $ARGUMENTS
</instructions>

<workflow>
<step number="1">
<title>Self-Evaluation (Expected vs Actual)</title>
<task>
Compare what you expected vs what actually happened:
</task>

<comparison>
<expected>
**Expected Outcome:**
- What was supposed to happen: [describe]
- Estimated effort: [time/complexity]
- Expected challenges: [list]
- Success criteria: [from acceptance criteria]
</expected>

<actual>
**Actual Outcome:**
- What actually happened: [describe]
- Actual effort: [time/complexity]
- Actual challenges: [list]
- Success criteria met: [✓ or ✗ for each]
</actual>

<variance>
**Variance Analysis:**
- ✅ What went better than expected? [list]
  - Why? [root cause analysis]
- ⚠️ What went worse than expected? [list]
  - Why? [root cause analysis]
- 🎯 What was accurate? [list]
  - Why did estimation work here?
</variance>
</comparison>
</step>

<step number="2">
<title>Error Detection and Analysis</title>
<task>
Identify and analyze all errors, even if you fixed them:
</task>

<template>
**For each error/problem encountered:**

**Error 1:**
- **Symptom:** [what you observed]
- **Root cause:** [why it happened]
- **Category:** [technical/logical/integration/human error]
- **How detected:** [tests failed, manual testing, code review]
- **How fixed:** [solution applied]
- **Prevention:** [how to avoid this in future]
- **Pattern?** [is this a repeated mistake?]

[Repeat for all errors]
</template>

<error_categories>
**Error categories to check:**
- Syntax/type errors (should be caught early)
- Logic errors (algorithm flaws)
- Integration errors (components don't work together)
- Performance issues (too slow, too much memory)
- Security vulnerabilities (missed validation)
- Test coverage gaps (edge cases not tested)
</error_categories>
</step>

<step number="3">
<title>Pattern Recognition</title>
<task>
Look for patterns across recent work:
</task>

<patterns>
<repeated_successes>
**Repeated Successes (keep doing these):**
1. [Pattern] - Seen in: [F00X, F00Y, F00Z]
   - Why it works: [analysis]
   - When to apply: [conditions]
   - Example: [concrete instance]
</repeated_successes>

<repeated_failures>
**Repeated Failures (stop doing these):**
1. [Pattern] - Seen in: [F00X, F00Y, F00Z]
   - Why it fails: [analysis]
   - Alternative approach: [what to do instead]
   - Example: [concrete instance]
</repeated_failures>

<emerging_patterns>
**Emerging Patterns (watch these):**
1. [Pattern] - Seen in: [F00X, F00Y]
   - Could become problem if: [conditions]
   - Monitor for: [signals]
</emerging_patterns>

<common_patterns>
**Check these common patterns:**
- Do I always underestimate [X type of task]?
- Do I repeatedly make [X type of error]?
- Do certain tools/libraries always cause problems?
- Are integration points consistently problematic?
- Do performance issues always appear in [X component]?
</common_patterns>
</patterns>
</step>

<step number="4">
<title>Correction and Improvement</title>
<task>
Generate actionable improvements:
</task>

<improvements>
<immediate_fixes>
**Immediate Fixes (do now):**
1. [Action] - Fixes: [problem]
   - Effort: [time estimate]
   - Priority: [high/medium/low]
   - Do it now? [yes/no + reasoning]
</immediate_fixes>

<process_improvements>
**Process Improvements (update workflow):**
1. [Change to development process]
   - Prevents: [problem]
   - Adds to: [which command/rule]
   - Example: "Always run security scan before commit"
</process_improvements>

<knowledge_updates>
**Knowledge Updates (add to memory):**
1. [New knowledge gained]
   - Store in: [PROJECT_INDEX.json / features.json / engineering rules]
   - Applies to: [which future features]
</knowledge_updates>

<tool_changes>
**Tool/Library Changes:**
1. [Library/tool to add or remove]
   - Reason: [why]
   - Replaces: [current approach]
   - Migration effort: [estimate]
</tool_changes>
</improvements>
</step>

<step number="5">
<title>Wisdom Extraction</title>
<task>
Distill learnings into reusable wisdom:
</task>

<learnings>
**What I learned:**

<technical>
**Technical:**
- [Specific technical insight]
  - Context: [when this applies]
  - Example: [concrete case]
</technical>

<process>
**Process:**
- [Process improvement]
  - Why it matters: [impact]
  - How to implement: [steps]
</process>

<architecture>
**Architecture:**
- [Architectural principle]
  - Trade-offs: [pros/cons]
  - When to apply: [conditions]
</architecture>

<cognitive>
**Human/Cognitive:**
- [Meta-learning about how you work]
  - Example: "I code better in morning" or "Complex tasks need more upfront planning"
</cognitive>
</learnings>
</step>

<step number="6">
<title>Update Memory Systems</title>
<task>
Store learnings for future reference:
</task>

<project_index>
**6.1 Update PROJECT_INDEX.json**

```json
{
  "memory": {
    "experiences": [
      {
        "feature_id": "F00X",
        "date": "YYYY-MM-DD",
        "task": "[brief description]",
        "outcome": "success|failure|partial",
        "duration_estimate": "[original estimate]",
        "duration_actual": "[actual time]",
        "challenges": ["challenge1", "challenge2"],
        "lessons": [
          {
            "lesson": "[what I learned]",
            "category": "technical|process|architecture",
            "applies_to": "[which future features]",
            "confidence": "high|medium|low"
          }
        ],
        "patterns_observed": ["pattern1", "pattern2"],
        "would_do_differently": "[specific changes for next time]"
      }
    ]
  }
}
```
</project_index>

<features_json>
**6.2 Update features.json**

Mark feature as truly complete only after reflection:

```json
{
  "id": "F00X",
  "passes": true,
  "reflected": true,
  "reflection_date": "YYYY-MM-DD",
  "lessons_learned": ["lesson1", "lesson2"],
  "pattern_tags": ["tag1", "tag2"]
}
```
</features_json>

<engineering_rules>
**6.3 Update Engineering Rules (if needed)**

If reflection reveals a systematic issue, add to `.claude/rules/engineering-v2.md`:

```markdown
## New Rule: [Rule Name]

**Reason:** Learned from F00X implementation

**Rule:** [specific rule]

**Example:** [concrete example]

**Applies to:** [which features/components]
```
</engineering_rules>
</step>

<step number="7">
<title>Commit Reflection</title>
<task>
Update session state:
</task>

<progress_update>
**Update claude-progress.txt**

```markdown
## Session X - [Date]

### Completed
- F00X: [feature name]
  - Outcome: [success/failure/partial]
  - Reflection: [1-2 sentence summary]
  - Key lesson: [most important takeaway]

### Patterns Observed
- [Pattern 1]
- [Pattern 2]

### Action Items from Reflection
- [ ] [Immediate fix]
- [ ] [Process change]
- [ ] [Update documentation]

### Next Steps
- [What to work on next, informed by reflection]
```
</progress_update>
</step>

<step number="8">
<title>Generate Reflection Summary</title>
<present>
Present the complete reflection:
</present>

<template>
```
=================================================
REFLECTION SUMMARY - F00X
=================================================

TASK: [feature description]

OUTCOME: [success/failure/partial]
  Expected: [X hours, Y files changed]
  Actual: [X hours, Y files changed]
  Variance: [explanation]

ERRORS ENCOUNTERED: [count]
  Critical: [count] - [list]
  Minor: [count] - [list]
  All resolved: [yes/no]

PATTERNS IDENTIFIED:
  ✅ Repeated Success: [pattern]
  ❌ Repeated Failure: [pattern]
  ⚠️ Emerging Issue: [pattern]

KEY LEARNINGS:
  1. [Most important lesson]
  2. [Second most important lesson]
  3. [Third most important lesson]

IMPROVEMENTS APPLIED:
  ✓ [Immediate fix 1]
  ✓ [Immediate fix 2]

IMPROVEMENTS DEFERRED:
  - [Process change] - Added to backlog
  - [Refactoring] - Low priority

REUSABLE WISDOM:
  "[One-sentence wisdom applicable to future work]"

CONFIDENCE FOR NEXT SIMILAR TASK: [high/medium/low]
  Reasoning: [why]

MEMORY UPDATED: [yes - where: PROJECT_INDEX, features.json, rules]

=================================================
```
</template>
</step>

<step number="9">
<title>Share Learnings (Optional)</title>
<task>
If working in a team or documenting publicly:
</task>

<lessons_md>
**Create LESSONS.md entry:**

```markdown
## F00X: [Feature Name] - [Date]

### What We Built
[Brief description]

### Challenge
[Main problem encountered]

### Solution
[How we solved it]

### Lesson
[Transferable wisdom]

### Applies To
[Other features/projects that could benefit]

### References
- Code: [link to commit]
- Tests: [link to test file]
- Discussion: [link if applicable]
```
</lessons_md>
</step>
</workflow>

<usage_pattern>
**Recommended workflow:**

```bash
# After completing a feature with /continue
/reflect "F00X - Audio streaming implementation"

# Review reflection output

# Apply immediate fixes if needed
[fix critical issues identified]

# Continue to next feature (now informed by reflection)
/continue
```

**Frequency:**
- ✅ After every feature (ideal)
- ✅ After any failure (mandatory)
- ✅ After unexpected difficulty (mandatory)
- ✅ After major milestone (mandatory)
- ⚠️ At minimum: weekly reflection session
</usage_pattern>

<example>
**Feature:** F007 - VAD/XTTS/Turn Manager integration

**Expected vs Actual:**
- Expected: 4 hours, straightforward integration
- Actual: 8 hours, complex race conditions
- Variance: Underestimated concurrent state management

**Errors:**
1. Race condition in turn manager
   - Root cause: Shared state without locking
   - Fix: Added asyncio.Lock
   - Prevention: Always consider concurrency in design phase

2. XTTS latency spike
   - Root cause: Model loaded on every request
   - Fix: Preload model at startup
   - Prevention: Profile performance earlier

**Patterns:**
- ✅ Test-first approach caught race condition early
- ❌ Always underestimate concurrent code complexity (3rd time)
- ⚠️ Integration tests catching more bugs than unit tests lately

**Learnings:**
1. "Concurrent code takes 2x longer than expected" - update estimates
2. "Profile performance before integration, not after" - add to process
3. "asyncio.Lock is essential for shared state" - add to rules

**Improvements:**
- ✓ Added locking pattern to engineering rules
- ✓ Created performance profiling checklist
- Deferred: Refactor other components for thread safety (low priority)

**Memory updated:**
- PROJECT_INDEX.json: Added experience with concurrency lessons
- features.json: F007 marked reflected=true
- engineering-v2.md: Added "Concurrent Code Rule"

**Confidence for next concurrent task:** Medium → High (learned the patterns)

**Reusable wisdom:** "Concurrent code complexity grows exponentially - design for it upfront, don't retrofit."
</example>
