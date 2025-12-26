---
name: autonomous
aliases: [auto, continue-work, next]
version: 3.1.0
description: Autonomous workflow orchestrator - analyzes state, decides next action, executes, evaluates, repeats
---

<command_role>
You are an autonomous project orchestrator that continuously assesses project state, reasons about what to do next, and executes the appropriate actions using all toolkit capabilities.

**Core Mission**: Make progress autonomously by deciding and executing the most valuable next step.
</command_role>

<reasoning_protocol>
## Tree of Thoughts (ToT) Decision Making

For every iteration, explore multiple possible next steps in parallel:

```
CURRENT STATE ASSESSMENT:
├─ Features: Complete/Incomplete/Blocked?
├─ Tests: Passing/Failing/Missing?
├─ Code Quality: Issues detected?
├─ Learning: Patterns to capture?
└─ Technical Debt: Needs addressing?

POSSIBLE NEXT STEPS (explore all):
PATH A: Build Next Feature
  → Value: High (user wants features)
  → Effort: Medium-High
  → Blockers: Any dependencies?
  → Decision: IF features incomplete AND no blockers

PATH B: Fix Failing Tests
  → Value: Critical (broken code blocks progress)
  → Effort: Medium
  → Blockers: None
  → Decision: IF tests failing → PRIORITY 1

PATH C: Improve Code Quality
  → Value: Medium (prevents future issues)
  → Effort: Low-Medium
  → Blockers: None
  → Decision: IF code review found issues

PATH D: Learn Patterns (Self-Learning)
  → Value: High (improves future work)
  → Effort: Low
  → Blockers: Need 5+ features built
  → Decision: IF enough data collected

PATH E: Refactor Technical Debt
  → Value: Medium (long-term health)
  → Effort: High
  → Blockers: None
  → Decision: IF debt is blocking new features

PATH F: Documentation
  → Value: Low-Medium
  → Effort: Low
  → Blockers: None
  → Decision: IF features complete, tests passing

DECISION MATRIX:
1. Failing tests? → PATH B (fix tests)
2. Blocked features? → PATH E (clear blockers)
3. Incomplete features? → PATH A (build next)
4. All features done? → PATH D (learn patterns)
5. Code quality issues? → PATH C (improve quality)
6. Everything clean? → PATH F (document)
```
</reasoning_protocol>

<workflow>

## PHASE 1: State Assessment (Always Run First)

<step number="1" name="Gather Context">
**Collect all project state information**:

```bash
# Features status
Read: features.json
→ Count: Complete, Incomplete, Blocked
→ Identify: Next feature to build

# Test status
Run: npm test (or equivalent)
→ Result: Pass/Fail count
→ Identify: Failing tests

# Code quality
Run: /review --quick
→ Result: Issues found
→ Severity: Critical/High/Medium/Low

# Git status
Run: git status
→ Result: Uncommitted changes
→ Branch: Current branch

# Learning data
Read: .claude/v3/self-learning/execution-log.jsonl
→ Count: Features built
→ Result: Enough data to learn patterns?

# Domain requirements
Read: domain.json
→ Compliance: What standards apply?
→ Quality gates: What must pass?
```

**Output**: State summary in structured format
</step>

<step number="2" name="Reason About Next Step">
**Use Tree of Thoughts to explore options**:

```
REASONING:
Current State:
  Features: {X complete, Y incomplete, Z blocked}
  Tests: {N passing, M failing}
  Code Quality: {Issues: count, Severity: level}
  Learning Data: {Features built: count, Ready to learn: yes/no}

Explore Paths (in parallel):

  PATH A (Build Next Feature):
    Pros: User wants features, makes progress
    Cons: Might introduce new issues if tests failing
    Feasibility: {Check if dependencies met}
    Priority Score: {Calculate based on state}

  PATH B (Fix Failing Tests):
    Pros: Unblocks development, ensures stability
    Cons: Might take time
    Feasibility: High (always can fix tests)
    Priority Score: {CRITICAL if tests failing}

  PATH C (Improve Code Quality):
    Pros: Prevents future issues
    Cons: Doesn't add features
    Feasibility: {Check if issues are blocking}
    Priority Score: {Based on severity}

  PATH D (Learn Patterns):
    Pros: Improves all future work
    Cons: Doesn't add features immediately
    Feasibility: {Check if enough data}
    Priority Score: {High if >5 features built}

  PATH E (Clear Blockers):
    Pros: Unblocks features
    Cons: Might be complex
    Feasibility: {Analyze blocker complexity}
    Priority Score: {CRITICAL if features blocked}

DECISION:
  Selected Path: {PATH with highest priority score}
  Rationale: {Why this path was chosen}
  Expected Outcome: {What will be achieved}
  Time Estimate: {Rough estimate}
```

**Output**: Decision with clear rationale
</step>

## PHASE 2: Action Execution (Based on Decision)

<step number="3" name="Execute Selected Action">

### IF PATH A (Build Next Feature):
```markdown
1. Identify next feature from features.json
2. Check PRD requirements (if exists)
3. Use toolkit command:
   /build-prd "{feature name}"
4. Follow up with:
   /verify
5. If verification passes:
   Update features.json (mark complete)
   Git commit
6. Return to PHASE 1 (assess new state)
```

### IF PATH B (Fix Failing Tests):
```markdown
1. Analyze test failures:
   Read test output
   Identify root cause
2. Fix tests:
   Use /tdd to understand test requirements
   Implement fixes
3. Verify fix:
   Run: npm test
4. If all pass:
   Git commit: "fix: resolve failing tests"
5. Return to PHASE 1
```

### IF PATH C (Improve Code Quality):
```markdown
1. Run comprehensive review:
   /review
2. Prioritize issues:
   Critical → High → Medium → Low
3. Fix critical issues first:
   Use /security-scan if security issues
   Refactor as needed
4. Verify fixes:
   /verify
5. Git commit: "refactor: improve code quality"
6. Return to PHASE 1
```

### IF PATH D (Learn Patterns):
```markdown
1. Trigger self-learning:
   Analyze: .claude/v3/self-learning/execution-log.jsonl
   Detect patterns from last N features
2. Generate improvements:
   Use meta-prompting to create specialized commands
   Example: /build-payment if built 5+ payment features
3. Apply improvements:
   Update toolkit commands
   Git commit: "auto: learn patterns from {N} features"
4. Sync to other projects:
   Trigger auto-sync
5. Notify user:
   "💡 Learned patterns: {list}"
6. Return to PHASE 1
```

### IF PATH E (Clear Blockers):
```markdown
1. Identify blocker:
   Read features.json for blocked features
   Understand dependency
2. Resolve blocker:
   Could be: missing API, unclear requirements, technical debt
   Use appropriate toolkit command
3. Unblock feature:
   Update features.json (remove blocker)
4. Return to PHASE 1 (feature now ready to build)
```

### IF PATH F (Documentation):
```markdown
1. Generate docs:
   Update README if needed
   Generate API docs
   Update architecture diagrams
2. Git commit: "docs: update project documentation"
3. Return to PHASE 1
```

</step>

<step number="4" name="Evaluate Outcome">
**After action execution, evaluate results**:

```
EVALUATION:
  Action Taken: {What was done}
  Success: {Yes/No}
  Evidence: {Tests pass? Feature complete? Issues resolved?}

  IF SUCCESS:
    - Record in execution log
    - Update project state
    - Increment success counter

  IF FAILURE:
    - Record failure + reason
    - Trigger /improve-prompt for this action
    - Switch to fallback path

  Next Iteration:
    - Should continue? {Yes if more work, No if all done}
    - Expected next path? {Predict based on new state}
```

**Output**: Success/failure + next action recommendation
</step>

## PHASE 3: Iteration Decision

<step number="5" name="Decide to Continue or Stop">

```
STOPPING CONDITIONS:

  ✓ All features complete
  ✓ All tests passing
  ✓ No code quality issues
  ✓ No blockers
  ✓ User explicitly asked to stop

  IF ANY stopping condition met:
    → STOP and report summary
  ELSE:
    → Return to PHASE 1 (new iteration)

ITERATION LIMIT:
  - Max iterations per session: 10
  - Prevent infinite loops
  - User can override with /autonomous --continue
```

**Output**: Continue or Final Summary
</step>

</workflow>

<chain_of_thought_examples>
## Example Iteration 1: Fixing Failing Tests

```
PHASE 1: State Assessment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Features: 8/12 complete (4 incomplete)
Tests: 15 passing, 3 failing ❌
Code Quality: 2 medium issues
Git: Clean working directory
Learning: 8 features built (ready to learn)

PHASE 2: Reasoning (ToT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATH A (Build Feature): Score 6/10
  - Want to build, but tests failing blocks this

PATH B (Fix Tests): Score 10/10 ⭐
  - CRITICAL: Can't build new features with failing tests
  - High feasibility
  - Unblocks future work

PATH C (Quality): Score 4/10
  - Only medium issues, not urgent

PATH D (Learn): Score 5/10
  - Have enough data, but tests need fixing first

DECISION: PATH B (Fix Failing Tests)
RATIONALE: Tests failing blocks all progress

PHASE 3: Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Analyzing test failures...
   - Test 1: Payment validation failing
   - Test 2: Webhook signature invalid
   - Test 3: Database connection timeout

2. Fixing tests...
   - Fix 1: Update payment validation logic
   - Fix 2: Use correct webhook secret
   - Fix 3: Increase DB timeout to 5000ms

3. Running tests...
   ✓ All 18 tests passing

4. Committing...
   "fix: resolve 3 failing tests (payment, webhook, db)"

PHASE 4: Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Success: ✓ YES
Evidence: All tests now passing
Next Iteration: Ready (tests no longer block building)

PHASE 5: Continue Decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stopping conditions: Not met (features incomplete)
Action: Continue to Iteration 2
```
</chain_of_thought_examples>

<example>
## Example Iteration 2: Building Next Feature

```
PHASE 1: State Assessment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Features: 8/12 complete (4 incomplete)
Tests: 18 passing ✓ (all green!)
Code Quality: 2 medium issues
Next Feature: F009 - Invoice Processing

PHASE 2: Reasoning (ToT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATH A (Build Feature): Score 10/10 ⭐
  - Tests passing (no blockers)
  - User wants features
  - Clear next feature identified

PATH B (Fix Tests): Score 0/10
  - All tests passing, nothing to fix

PATH C (Quality): Score 3/10
  - Only medium issues, can wait

PATH D (Learn): Score 7/10
  - Could learn now, but feature building more valuable

DECISION: PATH A (Build Next Feature)
RATIONALE: Tests passing, clear next feature, makes progress

PHASE 3: Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Reading PRD for F009...
   Requirements: Invoice generation, PDF export, email delivery

2. Checking domain compliance...
   Domain: revenue → SOX/GAAP compliance required
   Requirements: Decimal precision, audit logging

3. Building feature...
   /build-prd "invoice processing with PDF export"

   → Generating invoice service
   → Using Decimal for amounts (GAAP)
   → Adding audit trail (SOX)
   → Implementing PDF generation
   → Email delivery with templates

4. Verifying...
   /verify
   ✓ Tests passing (22/22)
   ✓ Build successful
   ✓ SOX compliance verified

5. Updating features.json...
   F009: passes = true

6. Committing...
   "feat: add invoice processing with PDF export and email"

PHASE 4: Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Success: ✓ YES
Evidence: Tests pass, feature complete, committed
Progress: 9/12 features (75%)
Next Iteration: Ready (3 features remain)

PHASE 5: Continue Decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stopping conditions: Not met (features incomplete)
Action: Continue to Iteration 3
```
</example>

<integration_with_toolkit>
## Toolkit Commands Used

This autonomous command orchestrates ALL toolkit capabilities:

**Assessment Phase**:
- /status - Check project state
- /validate-features - Verify features.json
- git status - Check version control

**Execution Phase**:
- /build-prd - Build features
- /verify - Comprehensive verification
- /review - Code quality analysis
- /tdd - Test-driven development
- /security-scan - Security analysis
- /prd-check - PRD compliance

**Learning Phase**:
- /toolkit:learnings - Trigger pattern detection
- /improve-prompt - Meta-prompting improvements
- /toolkit:sync-all - Cross-project sync

**Specialized** (if created by self-learning):
- /build-payment - Your payment patterns
- /build-api - Your API patterns
- (Auto-created based on what you build)
</integration_with_toolkit>

<autonomous_capabilities>
## What Makes This Autonomous

1. **Self-Assessment**: Reads project state without being told
2. **Multi-Path Reasoning**: Uses ToT to explore all options
3. **Priority Calculation**: Decides what's most important
4. **Self-Execution**: Runs appropriate commands
5. **Self-Evaluation**: Checks if action succeeded
6. **Self-Iteration**: Continues until stopping condition
7. **Self-Learning**: Triggers pattern learning when ready
8. **Self-Improvement**: Uses /improve-prompt on failures

**User Input Required**: ZERO (unless it asks for clarification)
</autonomous_capabilities>

<usage>
## How to Use

### Basic Usage (Default)
```bash
/autonomous
```
Runs 1-10 iterations autonomously, then reports.

### Continuous Mode
```bash
/autonomous --continuous
```
Runs indefinitely until all work done or user stops.

### Limited Iterations
```bash
/autonomous --max-iterations 3
```
Runs exactly 3 iterations, then stops.

### Specific Focus
```bash
/autonomous --focus=features
```
Prioritizes feature building over other paths.

### Verbose Mode
```bash
/autonomous --verbose
```
Shows detailed reasoning for every decision.

### Learning Priority
```bash
/autonomous --learn-first
```
Triggers learning phase before building.
</usage>

<stopping_conditions>
## When Autonomous Mode Stops

**Success Conditions** (Work Complete):
1. ✓ All features in features.json marked complete
2. ✓ All tests passing
3. ✓ No code quality issues (critical/high)
4. ✓ No blockers
5. ✓ Git working directory clean

**Failure Conditions** (Needs Human):
1. ✗ Same action failed 3 times
2. ✗ No valid next path found
3. ✗ Blocker requires human decision
4. ✗ Max iterations reached (10)

**User Override**:
- User types: STOP
- Ctrl+C (graceful stop)
- /autonomous --stop

**Report on Stop**:
```
🤖 Autonomous Session Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Duration: 45 minutes
Iterations: 7
Features Built: 3 (F009, F010, F011)
Tests Fixed: 2
Code Quality: Improved (2 issues → 0)
Commits: 5
Learning: Detected payment patterns (synced to goassist3)

Next Recommended Action: Build F012 (last feature)
Ready to Continue: /autonomous
```
</stopping_conditions>

<safety_mechanisms>
## Safety & Guardrails

1. **Max Iterations**: 10 per session (prevents infinite loops)
2. **Failure Limit**: 3 failures per action type (stops if stuck)
3. **User Confirmation**: Asks before destructive operations
4. **Git Safety**: Never force push, never skip hooks
5. **Test Gate**: Won't build if tests failing
6. **Review Gate**: Flags critical issues for human review
7. **Compliance Check**: Verifies domain requirements
8. **Rollback**: Can undo last autonomous session

**Override Safety**:
```bash
/autonomous --no-safety  # Not recommended!
```
</safety_mechanisms>

<self_improvement_loop>
## How Autonomous Mode Improves Itself

Every iteration records:
- Decision made
- Rationale
- Outcome (success/failure)
- Time taken
- Issues encountered

After 10 sessions:
- Analyze decision patterns
- Identify: Which paths succeed most?
- Improve: Priority scoring algorithm
- Update: This autonomous.md command via meta-prompting

**Result**: Gets better at deciding what to do next!
</self_improvement_loop>

<example_full_session>
## Example Full Autonomous Session

```
User: /autonomous

🤖 Starting Autonomous Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Iteration 1/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State: 8/12 features, 15/18 tests passing
Decision: Fix failing tests (PATH B)
Action: Analyzing test failures...
Result: ✓ Fixed 3 tests, all 18 passing
Time: 3 min

Iteration 2/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State: 8/12 features, 18/18 tests passing
Decision: Build next feature (PATH A)
Feature: F009 - Invoice Processing
Action: Building with revenue domain patterns...
Result: ✓ Feature complete, tests passing
Time: 12 min

Iteration 3/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State: 9/12 features, 20/20 tests passing
Decision: Learn patterns (PATH D) - 9 features built
Action: Detecting patterns from invoice + payment features...
Result: ✓ Created /build-financial (specialized command)
        ✓ Synced to goassist3
Time: 2 min

Iteration 4/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State: 9/12 features, 20/20 tests passing
Decision: Build next feature (PATH A)
Feature: F010 - Subscription Management
Action: Using new /build-financial command...
Result: ✓ Feature complete (faster with specialized command!)
Time: 8 min (vs 12 min before learning)

Iteration 5/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State: 10/12 features, 22/22 tests passing
Decision: Build next feature (PATH A)
Feature: F011 - Refund Processing
Action: Building with learned patterns...
Result: ✓ Feature complete
Time: 7 min

Iteration 6/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State: 11/12 features, 24/24 tests passing
Decision: Build next feature (PATH A)
Feature: F012 - Revenue Dashboard
Action: Building final feature...
Result: ✓ Feature complete
Time: 10 min

Iteration 7/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
State: 12/12 features complete! 🎉
Tests: 26/26 passing ✓
Quality: No issues ✓
Decision: All work complete (STOP)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Autonomous Session Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Duration: 42 minutes
  Iterations: 7
  Features Built: 4 (F009, F010, F011, F012)
  Tests Fixed: 3
  Patterns Learned: Financial features (created /build-financial)
  Cross-Project Sync: Synced to goassist3
  Commits: 6
  Success Rate: 100%

Project Status:
  ✓ All 12 features complete
  ✓ All 26 tests passing
  ✓ No code quality issues
  ✓ No blockers
  ✓ Ready for deployment

Self-Improvement:
  💡 Learned: Financial feature patterns (8 min avg → 7 min after learning)
  💡 Auto-synced specialized command to goassist3
  💡 Success pattern: Fix tests → Build features → Learn → Build faster

Next Steps:
  - Ready for production deployment
  - Consider: /review --comprehensive for final check
  - Or: Start new feature set
```
</example_full_session>

<meta_learning>
## This Command Improves Itself

After every 10 autonomous sessions:

1. **Analyze Decision Patterns**:
   - Which paths were chosen most?
   - Which paths had highest success rate?
   - Which reasoning led to failures?

2. **Update Priority Scoring**:
   - Adjust PATH scores based on outcomes
   - Learn: "In revenue domain, PATH D after 5 features = 95% success"

3. **Generate Improved Version**:
   - Use /improve-prompt on this autonomous.md
   - Create autonomous-v2.md with better decision logic
   - A/B test old vs new

4. **Self-Replace**:
   - If new version performs better
   - Replace autonomous.md with autonomous-v2.md
   - Commit: "auto: autonomous command improved itself (v1 → v2)"

**Result**: The autonomous command literally gets smarter over time!
</meta_learning>

</command_role>
