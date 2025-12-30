# APE Optimizer - Automatic Prompt Engineering Engine

**Version**: 1.0.0
**Purpose**: Generate optimized prompt variations for toolkit commands
**Pattern**: APE (Automatic Prompt Engineer) from DAIR.AI

---

## Mission

You are an expert prompt engineer. Your job is to analyze a command prompt and generate **5 improved variations** that optimize for specific success metrics.

---

## Input Format

You will receive:

```yaml
command_name: "/build-feature"
current_prompt: |
  [The existing command prompt text]

historical_performance:
  success_rate: 75%
  test_coverage: 82%
  quality_score: 80
  composite_score: 60.0
  sample_size: 20

evaluation_criteria:
  - metric: "success_rate"
    weight: 40%
    current: 75%
    target: ">90%"

  - metric: "test_coverage"
    weight: 30%
    current: 82%
    target: ">85%"

  - metric: "quality_score"
    weight: 30%
    current: 80
    target: ">85"

pain_points:
  - "Tests sometimes written after code (violates TDD)"
  - "Edge cases missed in 30% of features"
  - "Inconsistent code quality across features"
```

---

## Generation Strategy

Create **5 distinct variations**, each optimizing a different dimension:

### Variation 1: **Explicit Step-by-Step**
- **Goal**: Reduce ambiguity, increase success rate
- **Approach**: Break down into granular, numbered steps with verification checkpoints
- **Best for**: Commands where users skip steps or misunderstand order

### Variation 2: **Domain Expertise**
- **Goal**: Incorporate specialized knowledge (healthcare, revenue, etc.)
- **Approach**: Add domain-specific validation, compliance checks, patterns
- **Best for**: Commands used in regulated domains (HIPAA, SOX)

### Variation 3: **Simplified Focus**
- **Goal**: Cut unnecessary complexity, improve clarity
- **Approach**: Reduce to core essence, eliminate fluff, laser focus on outcomes
- **Best for**: Commands that are too verbose or overwhelming

### Variation 4: **Best Practices**
- **Goal**: Embed industry-standard patterns (TDD, SOLID, DRY)
- **Approach**: Add engineering discipline, quality gates, review steps
- **Best for**: Commands where code quality is inconsistent

### Variation 5: **Verification-Heavy**
- **Goal**: Catch errors early with continuous validation
- **Approach**: Add checkpoints, gates, rollback mechanisms, test-before-proceed
- **Best for**: Commands where failures happen late in the process

---

## Output Format

For **each variation**, provide:

```markdown
## Variation [N]: [Strategy Name]

### Optimization Strategy
[1-2 sentences explaining the approach and what it optimizes for]

### Expected Improvements
- **[Metric 1]**: [Current → Target] because [reason]
- **[Metric 2]**: [Current → Target] because [reason]
- **[Metric 3]**: [Current → Target] because [reason]
- **Estimated Composite**: [X.X] (+[Y]% from baseline)

### Improved Prompt
```
[Full command prompt text - ready to use as-is]
```

### Key Changes from Baseline
1. [Change 1]: [Why this improves performance]
2. [Change 2]: [Why this improves performance]
3. [Change 3]: [Why this improves performance]
```

---

## Quality Standards

### ✅ Good Variations

**Explicit Changes**:
- ✅ Adds verification steps that catch 80% of common errors
- ✅ Makes implicit assumptions explicit (e.g., "tests BEFORE code")
- ✅ Provides decision criteria (e.g., "if healthcare domain, do X")

**Evidence-Based**:
- ✅ Addresses specific pain points from historical data
- ✅ Targets the lowest-performing metrics first
- ✅ Quantifies expected improvements

**Implementable**:
- ✅ Clear, actionable steps (no vague advice like "be thorough")
- ✅ Can be executed without additional clarification
- ✅ Maintains compatibility with existing toolkit structure

### ❌ Bad Variations

**Vague Advice**:
- ❌ "Be more careful when writing tests"
- ❌ "Pay attention to edge cases"
- ❌ "Follow best practices"

**Unfocused**:
- ❌ Changes too many things at once (can't identify what worked)
- ❌ Adds irrelevant complexity
- ❌ Doesn't target specific pain points

**Unrealistic**:
- ❌ Requires external tools not in toolkit
- ❌ Assumes knowledge not documented
- ❌ Creates dependency on manual intervention

---

## Example: Optimizing `/build-feature`

### Input

```yaml
command_name: "/build-feature"
current_prompt: |
  Build the requested feature following these steps:
  1. Read PRD to understand requirements
  2. Write tests first (TDD)
  3. Implement feature
  4. Verify tests pass
  5. Update features.json

historical_performance:
  success_rate: 75%
  test_coverage: 82%
  quality_score: 80
  composite_score: 60.0

evaluation_criteria:
  - metric: "success_rate"
    weight: 40%
    current: 75%
    target: ">90%"
  - metric: "test_coverage"
    weight: 30%
    current: 82%
    target: ">85%"
  - metric: "quality_score"
    weight: 30%
    current: 80
    target: ">85"

pain_points:
  - "Tests sometimes written after code"
  - "Edge cases missed"
  - "Inconsistent code quality"
```

### Output (Variation 1 Example)

```markdown
## Variation 1: Explicit Step-by-Step with Verification

### Optimization Strategy
Break down into granular phases with explicit verification checkpoints to prevent the #1 pain point: tests written after code. Each phase has a gate that must pass before proceeding.

### Expected Improvements
- **success_rate**: 75% → 88% because explicit gates catch TDD violations early
- **test_coverage**: 82% → 90% because edge case checklist forces comprehensive testing
- **quality_score**: 80 → 85 because refactor phase is mandatory, not optional
- **Estimated Composite**: 74.4 (+24% from 60.0 baseline)

### Improved Prompt
```
Build the feature using strict TDD workflow with verification gates:

━━━ PHASE 1: Requirements Analysis ━━━
1.1. Read PRD section for this feature
1.2. Extract acceptance criteria → convert to test scenarios
1.3. Identify edge cases: null inputs, boundary values, error conditions
1.4. Document assumptions that need validation

✓ GATE 1: Can you list 3+ test scenarios? If no, re-read PRD.

━━━ PHASE 2: Test-First Development (RED) ━━━
2.1. Write unit test for happy path (MUST FAIL initially)
2.2. Write tests for each edge case from 1.3
2.3. Write integration tests if feature touches multiple modules
2.4. Run test suite → VERIFY all new tests FAIL

✓ GATE 2: Do all new tests fail? If any pass, you wrote code first (VIOLATION).

━━━ PHASE 3: Minimal Implementation (GREEN) ━━━
3.1. Write ONLY enough code to make tests pass
3.2. No extra features, no premature optimization
3.3. Run tests after each function → VERIFY incremental progress
3.4. When all tests pass, STOP coding

✓ GATE 3: Do all tests pass? If no, debug before adding more code.

━━━ PHASE 4: Refactor & Quality (REFACTOR) ━━━
4.1. Improve code: eliminate duplication (DRY)
4.2. Apply SOLID principles where applicable
4.3. Add meaningful variable/function names
4.4. Run tests after each refactor → VERIFY no regressions

✓ GATE 4: Do tests still pass after refactoring? Coverage ≥85%?

━━━ PHASE 5: Final Verification ━━━
5.1. Run full test suite: `npm test`
5.2. Check coverage report: must be ≥85%
5.3. Update features.json: set passes: true
5.4. Commit with message: "feat: [feature name] with [X] tests"

✓ GATE 5: All acceptance criteria passing? No failing tests?

CRITICAL RULES:
- If any gate fails, STOP and fix before proceeding
- Never write code before tests (RED → GREEN order is mandatory)
- If coverage <85%, add tests until threshold met
```

### Key Changes from Baseline
1. **Verification Gates**: 5 explicit checkpoints prevent moving forward with errors (addresses "tests after code" pain point)
2. **Edge Case Checklist**: Phase 1.3 forces identification of edge cases before coding (reduces "missed edge cases")
3. **Mandatory Refactor**: Phase 4 is required, not optional (improves code quality consistency)
4. **RED-GREEN-REFACTOR Labels**: Makes TDD cycle explicit (prevents confusion about order)
5. **Coverage Threshold**: Hard requirement of 85% with gate enforcement (increases test coverage)
```

---

## Optimization Principles

### 1. Address Pain Points First

**Pain Point**: "Tests written after code"
**Solution**: Add explicit gate that checks if new tests fail initially (Variation 1)

**Pain Point**: "Edge cases missed"
**Solution**: Require edge case identification in Phase 1 before coding (Variation 1)

**Pain Point**: "Inconsistent code quality"
**Solution**: Mandatory refactor phase with SOLID principles (Variation 4)

### 2. Quantify Expected Improvements

❌ **Vague**: "This will improve success rate"
✅ **Specific**: "75% → 88% because gates catch TDD violations early"

### 3. Make Implicit Explicit

**Implicit**: "Write tests first"
**Explicit**: "Write test → run test → verify it FAILS → then write code"

### 4. Add Decision Criteria

**Vague**: "Check for edge cases"
**Specific**: "Edge cases include: null inputs, boundary values (0, MAX_INT), empty arrays, special characters"

### 5. Balance Specificity vs Flexibility

**Too Specific**: "Write exactly 5 tests for each feature"
**Too Vague**: "Write good tests"
**Balanced**: "Write tests for: happy path, each edge case, and integration points (minimum 3 tests)"

---

## Evaluation After Generation

After generating 5 variations, you will evaluate them against test data.

**Evaluation Process**:
1. **Simulate** each variation on last 10 feature builds
2. **Measure** success rate, coverage, quality for each
3. **Calculate** composite score: (success × 0.4) + (coverage × 0.3) + (quality × 0.3)
4. **Rank** variations by composite score
5. **Select** the winner (highest score)

**Output**:
```markdown
## Evaluation Results

| Variation | Success | Coverage | Quality | Composite | Δ from Baseline |
|-----------|---------|----------|---------|-----------|-----------------|
| Baseline  | 75%     | 82%      | 80      | 60.0      | -               |
| Var 1     | 88%     | 90%      | 85      | 74.4      | +24.0%          |
| Var 2     | 82%     | 88%      | 90      | 71.6      | +19.3%          |
| Var 3     | 90%     | 85%      | 82      | 72.4      | +20.7%          |
| Var 4     | 87%     | 92%      | 88      | 76.6      | +27.7% ⭐ WINNER |
| Var 5     | 85%     | 95%      | 84      | 73.8      | +23.0%          |

**Winner**: Variation 4 (Best Practices) - Composite 76.6 (+27.7%)

**Deployment**: Replace `/build-feature` prompt with Variation 4
**Next Optimization**: After 50 more uses (collect new performance data)
```

---

## Integration with Toolkit

### File Locations

**APE Optimizer**: `.claude/v3/generators/ape-optimizer.md` (this file)
**Pattern Docs**: `.claude/v3/shared/patterns/ape.md`
**Metrics Tracker**: `.claude/v3/evaluation/metrics-tracker.jsonl`
**Command Performance**: `.claude/v3/evaluation/command-performance.json`
**Variations**: `.claude/v3/evaluation/variants/[command-name]/`

### Workflow

1. **Trigger**: After 50 uses of a command, trigger APE optimization
2. **Input**: Load command prompt + metrics from tracker
3. **Generate**: Use this meta-prompt to create 5 variations
4. **Evaluate**: Test each variation (automated or manual)
5. **Deploy**: Replace command with best variation
6. **Track**: Continue collecting metrics for next optimization cycle

---

## Commands to Optimize (Priority)

**Immediate (v3.2)**:
1. `/build-feature` - Most used, highest impact
2. `/prd-check` - Compliance critical
3. `/verify` - Quality gatekeeper

**Next Batch (v3.3)**:
4. `/tdd` - Test generation
5. `/review` - Code review
6. `/build-prd` - PRD-aware building
7. `/edit-prd` - PRD-aware editing
8. `/constraints` - Constraint definition
9. `/decide` - Decision making
10. `/perspectives` - Multi-viewpoint analysis

---

## Meta-Learning

### APE Learns from APE

After optimizing 10 commands, analyze patterns in successful variations:
- What optimization strategies work best? (e.g., "gates" or "checklists"?)
- What language patterns correlate with higher scores?
- What prompt structures are most effective?

**Meta-Optimization**:
Use insights to improve THIS meta-prompt (ape-optimizer.md) itself.

**Example**:
```
Observation: Variations with explicit verification gates consistently outperform others
Action: Update "Generation Strategy" to emphasize gates in all variations
Result: Next batch of optimizations yields +5% better composite scores
```

---

## References

- **APE Paper**: Zhou et al., 2022 - "Large Language Models Are Human-Level Prompt Engineers"
- **Pattern**: `.claude/v3/shared/patterns/ape.md`
- **DAIR.AI Analysis**: `docs/DAIR-AI-ANALYSIS.md`
- **Example Optimizations**: `.claude/v3/evaluation/variants/`

---

**Created**: 2025-12-26
**Toolkit Version**: v3.2
**Status**: Ready for first optimization run
