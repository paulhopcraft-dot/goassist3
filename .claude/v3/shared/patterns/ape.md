# APE Pattern (Automatic Prompt Engineer)

**Version**: 1.0.0
**Pattern Type**: Advanced Prompting Technique
**Source**: Zhou et al., 2022 - "Large Language Models Are Human-Level Prompt Engineers"

---

## Overview

APE is a meta-prompting pattern that uses LLMs to **automatically generate and optimize prompts** instead of manual trial-and-error. The LLM proposes multiple prompt variations, evaluates each against test cases, and selects the best performer.

**Key Insight**: LLMs can write better prompts for themselves than humans can through manual iteration.

---

## Pattern Structure

```
1. GENERATE: LLM creates N prompt variations for a task
2. EVALUATE: Test each variation against evaluation criteria
3. SELECT: Choose the highest-scoring prompt
4. ITERATE: (Optional) Use best prompt as seed for next generation
```

---

## When to Use APE

✅ **Use APE when**:
- You have clear evaluation criteria (test cases, success metrics)
- Manual prompt tuning is time-consuming
- You want to optimize existing prompts systematically
- You need to improve multiple similar prompts at scale

❌ **Don't use APE when**:
- No clear evaluation criteria exist
- Single-use prompt (not worth optimization)
- Real-time prompt generation needed (APE is offline optimization)

---

## Implementation in Toolkit

### Use Case: Optimize Slash Commands

We have 35+ commands in the toolkit. APE can automatically improve them.

**Example: Optimizing `/build-feature` command**

```markdown
## Step 1: Generate Variations

**Meta-Prompt to LLM**:
```
Generate 5 improved variations of this command prompt:

CURRENT PROMPT:
"""
You are building a new feature. Follow TDD:
1. Write tests first
2. Implement feature
3. Verify tests pass
"""

EVALUATION CRITERIA:
- Features built successfully (pass/fail)
- Tests written before code (yes/no)
- Code quality score (0-100)

Generate 5 variations that improve success rate.
```

**LLM Generates**:
1. "Build the feature using strict TDD: RED (write failing test) → GREEN (minimal code to pass) → REFACTOR (improve code). Start with edge cases."
2. "Implement the feature with comprehensive test coverage: unit tests (70%), integration tests (20%), E2E tests (10%). Code only after tests exist."
3. "TDD workflow: (1) Define acceptance criteria as tests, (2) Implement feature incrementally, (3) Refactor with tests as safety net. Commit after each cycle."
4. "Test-Driven Development sequence: Example-based tests → Implementation → Property-based tests → Edge cases. Never write code without a failing test first."
5. "Build feature iteratively: Write simplest test → Minimal implementation → Verify → Add complexity. Maintain 100% test coverage throughout."

## Step 2: Evaluate

Run each variation on last 10 feature builds, measure:
- Success rate (features completed without errors)
- Test-first compliance (% of features where tests were written first)
- Code quality (avg score from code reviewer)

**Results**:
```
Variation 1: 85% success, 90% test-first, quality 82
Variation 2: 80% success, 95% test-first, quality 85
Variation 3: 90% success, 85% test-first, quality 88 ⭐ WINNER
Variation 4: 75% success, 80% test-first, quality 80
Variation 5: 82% success, 92% test-first, quality 84
```

## Step 3: Select

Variation 3 wins (highest composite score: 90% success × 88 quality = 79.2)

Update `/build-feature` command with optimized prompt.

## Step 4: Iterate (Optional)

Use Variation 3 as seed, generate 5 more variations, evaluate again.
Repeat until no improvement for 2 generations.
```

---

## APE in Our Toolkit

### Commands to Optimize (Priority Order)

**High Impact** (used frequently):
1. `/build-feature` - Core feature development
2. `/prd-check` - PRD compliance validation
3. `/verify` - Multi-agent verification
4. `/tdd` - Test-driven development
5. `/review` - Code review

**Medium Impact**:
6. `/build-prd` - Build with PRD enforcement
7. `/edit-prd` - Edit with PRD validation
8. `/constraints` - Define feature constraints
9. `/decide` - High-stakes decision making
10. `/perspectives` - Multi-viewpoint analysis

**Low Impact** (less frequent use):
11. `/autonomous` - Already comprehensive
12. `/react` - Just created (needs data first)

---

## Evaluation Metrics

### Success Metrics (What to Measure)

**For Feature-Building Commands**:
- Success rate (% completed without errors)
- Test coverage (% of code covered by tests)
- Code quality score (0-100 from code reviewer)
- Compliance violations (count of PRD/domain violations)
- Time to completion (median minutes)

**For Review Commands**:
- Issues found (count by severity)
- False positives (% of flagged issues that weren't real)
- Review completeness (% of code surface area reviewed)

**For Decision Commands**:
- Decision quality (user satisfaction rating)
- Options explored (count of alternatives considered)
- Reversals (% of decisions later reversed)

---

## APE Workflow for Toolkit

### Phase 1: Setup (One-Time)

**File**: `.claude/v3/generators/ape-optimizer.md`
```markdown
# APE Optimizer Meta-Prompt

## Mission
Generate improved prompt variations for toolkit commands.

## Input Format
- Current prompt text
- Evaluation criteria (metrics to optimize)
- Historical performance data (if available)

## Output Format
5 prompt variations with reasoning for each improvement

## Generation Strategy
- Variation 1: More explicit step-by-step
- Variation 2: Add domain expertise
- Variation 3: Incorporate best practices
- Variation 4: Simplify and focus
- Variation 5: Add verification steps
```

**File**: `.claude/v3/evaluation/metrics-tracker.jsonl`
```jsonl
{"command": "/build-feature", "timestamp": "2025-12-26T19:00:00Z", "success": true, "test_coverage": 87, "quality": 85}
{"command": "/build-feature", "timestamp": "2025-12-26T20:15:00Z", "success": true, "test_coverage": 92, "quality": 88}
```

### Phase 2: Generate Variations

Run APE optimizer on target command:
1. Read current command prompt
2. Load historical metrics (last 20 executions)
3. Generate 5 variations using meta-prompt
4. Save variations to `.claude/v3/evaluation/variants/`

### Phase 3: Evaluate

**Option A: Automated** (if test cases exist)
- Run each variation against last 10 feature builds
- Measure success rate, quality, compliance
- Calculate composite score

**Option B: Manual** (for new commands)
- User rates each variation (1-10)
- Collect qualitative feedback
- Select based on preference

### Phase 4: Deploy

- Replace command prompt with best variation
- Track new performance metrics
- Re-optimize after 20 more executions

---

## Example: `/build-feature` Optimization

### Current Prompt (Baseline)

```markdown
Build the requested feature following these steps:
1. Read PRD to understand requirements
2. Write tests first (TDD)
3. Implement feature
4. Verify tests pass
5. Update features.json
```

**Baseline Performance** (last 20 uses):
- Success rate: 75%
- Test coverage: 82%
- Quality score: 80
- **Composite: 60.0**

### APE-Generated Variations

**Variation 1** (More Explicit):
```markdown
Build the feature using strict TDD workflow:

PHASE 1: Requirements Analysis
- Read PRD section for this feature
- Extract acceptance criteria as test scenarios
- Identify edge cases and error conditions

PHASE 2: Test-First Development
- Write failing unit tests for happy path
- Write failing tests for edge cases
- Run tests to confirm they fail (RED)

PHASE 3: Minimal Implementation
- Write minimal code to pass tests (GREEN)
- Verify all tests pass
- Do NOT add untested features

PHASE 4: Refactor & Verify
- Improve code quality (DRY, SOLID)
- Ensure tests still pass (REFACTOR)
- Check test coverage ≥ 85%

PHASE 5: Integration
- Update features.json
- Run full test suite
- Verify no regressions
```

**Variation 2** (Domain Expertise):
```markdown
Build the feature with domain-specific compliance:

STEP 1: Compliance Check
- Read domain.json for domain (healthcare/revenue/general)
- If healthcare: Check HIPAA requirements in skill
- If revenue: Check SOX/GAAP requirements
- Load domain-specific patterns

STEP 2: Test-Driven Development
- Write acceptance tests from PRD criteria
- Write compliance tests (if regulated domain)
- Write unit tests for business logic
- Implement feature to pass all tests

STEP 3: Verification
- Run tests: `npm test`
- Run domain validator (if healthcare/revenue)
- Check code quality with reviewer
- Ensure compliance violations = 0

STEP 4: Documentation
- Update features.json with passes: true
- Document any domain-specific notes
- Commit with compliance metadata
```

**Variation 3** (Simplified Focus):
```markdown
Build the feature with laser focus on quality:

1. **Understand**: Read PRD acceptance criteria
2. **Test**: Write tests that prove each criterion passes
3. **Build**: Implement feature to pass all tests
4. **Verify**: Run tests, achieve 100% of criteria passing
5. **Record**: Update features.json, mark complete

Key Rules:
- Write tests BEFORE code (no exceptions)
- Each acceptance criterion = at least 1 test
- All tests must pass before marking complete
- If tests fail, fix immediately (don't commit failing tests)
```

**Variation 4** (Best Practices):
```markdown
Build the feature following engineering excellence:

PRE-FLIGHT:
- Read PRD section
- Check features.json for dependencies
- Verify no blocked features

TDD CYCLE (repeat until done):
- RED: Write failing test for next criterion
- GREEN: Minimal code to pass test
- REFACTOR: Improve without breaking tests
- VERIFY: Run full suite, check coverage

POST-BUILD:
- Code review (security, quality, patterns)
- Update features.json with verification
- Commit with descriptive message
- Check for learnings to capture
```

**Variation 5** (Verification-Heavy):
```markdown
Build the feature with continuous verification:

PHASE 1: Define Success
- Map each PRD criterion to a test
- Define pass/fail for each criterion
- Set coverage target (≥85%)

PHASE 2: Build with Checkpoints
- Write test → Implement → Verify (repeat)
- After each checkpoint: run full test suite
- If any test fails: stop, fix, then continue
- Never proceed with failing tests

PHASE 3: Final Verification
- Run tests: must show 100% criteria passing
- Check coverage: must be ≥ target
- Code review: must find 0 critical issues
- Update features.json ONLY if all pass

GATE: Do not commit unless all verifications pass.
```

### Evaluation (Simulated on Last 10 Builds)

```
Variation 1: Success 85%, Coverage 90%, Quality 88 → Composite: 74.8
Variation 2: Success 80%, Coverage 88%, Quality 90 → Composite: 72.0
Variation 3: Success 90%, Coverage 85%, Quality 85 → Composite: 76.5 ⭐
Variation 4: Success 88%, Coverage 92%, Quality 87 → Composite: 76.6 ⭐⭐ WINNER
Variation 5: Success 82%, Coverage 95%, Quality 86 → Composite: 70.5
```

**Winner**: Variation 4 (Best Practices) - 76.6 vs 60.0 baseline = **+27% improvement**

---

## Integration with Self-Learning

APE complements our self-learning system:

**Self-Learning** (Pattern Extraction):
- Observes what worked in past executions
- Generates domain-specific commands (e.g., `/build-payment`)

**APE** (Prompt Optimization):
- Improves how commands are phrased
- Optimizes for success metrics
- Self-optimizing prompt quality

**Combined Power**:
1. Self-learning creates `/build-payment` from observing payment features
2. APE optimizes `/build-payment` prompt for best performance
3. Result: Specialized command with optimized prompt = maximum effectiveness

---

## Metrics for Success

### APE Effectiveness

**Measure**:
- **Improvement**: (New score - Baseline score) / Baseline score × 100
- **Stability**: Std dev of scores across last 20 uses
- **Regression**: % of optimizations that performed worse than baseline

**Target**:
- Improvement: ≥ 20% for high-impact commands
- Stability: Std dev ≤ 10% of mean score
- Regression: ≤ 5% of optimizations

### Command Performance Tracking

**File**: `.claude/v3/evaluation/command-performance.json`
```json
{
  "/build-feature": {
    "version": "2.0-ape",
    "optimized_at": "2025-12-26",
    "baseline_score": 60.0,
    "current_score": 76.6,
    "improvement": "+27.7%",
    "executions": 45,
    "last_optimized": "2025-12-26",
    "next_optimization": "2026-01-10"
  }
}
```

---

## APE vs Other Patterns

| Pattern | Purpose | Automation | Scope |
|---------|---------|------------|-------|
| **Chain-of-Thought** | Better reasoning | Manual design | Single task |
| **ReAct** | Structured problem-solving | Manual cycles | Single session |
| **Meta-Prompting** | Self-improving prompts | Manual iteration | Single prompt |
| **APE** | Automatic prompt optimization | Fully automated | All prompts |
| **Self-Learning** | Pattern extraction | Observational | Domain patterns |

**APE Advantage**: Operates on prompts themselves, not just usage. Improves the toolkit at the meta-level.

---

## Implementation Roadmap

### v3.2 (APE Foundation)

**Week 1**: Pattern & Infrastructure
- ✅ Create `ape.md` pattern documentation
- Create APE optimizer meta-prompt
- Create evaluation metrics tracker
- Build variation generator

**Week 2**: Optimization Engine
- Build command optimizer (reads prompts, generates variations)
- Implement evaluation harness
- Create metrics aggregation
- Build selection algorithm

**Week 3**: First Optimizations
- Optimize `/build-feature` (highest impact)
- Optimize `/prd-check`
- Optimize `/verify`
- Measure improvements

### v3.3 (APE at Scale)

**Week 4-6**: Optimize All Commands
- Batch optimize 35 commands
- Track improvements
- Refine evaluation criteria
- Document learnings

### v3.4 (Continuous Optimization)

**Ongoing**: Auto-Re-optimization
- Re-optimize after every 50 uses
- A/B test variations in production
- Continuous improvement loop

---

## Template: APE Meta-Prompt

```markdown
# APE: Generate Prompt Variations

## Current Prompt
[Insert command prompt here]

## Historical Performance (Last 20 Uses)
- Success rate: [X]%
- [Metric 2]: [Value]
- [Metric 3]: [Value]
- Composite score: [Score]

## Evaluation Criteria
1. [Metric 1] - weight: [X]%
2. [Metric 2] - weight: [Y]%
3. [Metric 3] - weight: [Z]%

## Task
Generate 5 improved variations of this prompt that optimize for the evaluation criteria.

For each variation:
1. State the optimization strategy (e.g., "Add explicit verification steps")
2. Provide the full improved prompt
3. Explain expected improvement

## Output Format
### Variation 1: [Strategy Name]
**Strategy**: [Brief explanation]
**Expected Improvement**: [What will improve and why]
**Prompt**:
```
[Full improved prompt]
```

[Repeat for Variations 2-5]
```

---

## References

- **Paper**: "Large Language Models Are Human-Level Prompt Engineers" (Zhou et al., 2022)
- **DAIR.AI**: https://www.promptingguide.ai/techniques/ape
- **Our Analysis**: `docs/DAIR-AI-ANALYSIS.md`
- **Related Patterns**: `meta-prompting.md`, `self-learning.md`

---

**Created**: 2025-12-26
**Pattern Library**: claude-code-toolkit v3.2
**Status**: Foundation implementation in progress
