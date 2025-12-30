# PAL Pattern (Program-Aided Language Models)

**Version**: 1.0.0
**Pattern Type**: Advanced Prompting Technique
**Source**: Gao et al., 2022 - "PAL: Program-aided Language Models"

---

## Overview

PAL is a prompting pattern where **code becomes the reasoning mechanism** instead of natural language. Rather than explaining logic in text, the LLM writes executable code that performs the reasoning and produces the answer.

**Key Insight**: Code is more precise than text for logical reasoning. Offload computation to a runtime instead of asking the LLM to compute in its head.

---

## Pattern Structure

### Traditional (Text Reasoning)
```
Question: "A company has 23 employees. They hire 15 more, then 8 quit. How many employees now?"

Reasoning (in text):
"Start with 23 employees.
Add 15 new hires: 23 + 15 = 38
Subtract 8 who quit: 38 - 8 = 30
Therefore, 30 employees remain."

Answer: 30
```

### PAL (Code Reasoning)
```
Question: "A company has 23 employees. They hire 15 more, then 8 quit. How many employees now?"

Reasoning (in code):
```python
initial_employees = 23
new_hires = 15
quit_count = 8

after_hiring = initial_employees + new_hires  # 38
final_count = after_hiring - quit_count        # 30

answer = final_count
```

Execute code → Answer: 30
```

**Advantages**:
- ✅ No arithmetic errors (runtime computes)
- ✅ Complex logic is clearer in code
- ✅ Executable = verifiable
- ✅ Can handle multi-step computations perfectly

---

## When to Use PAL

✅ **Use PAL when**:
- Task involves computation (math, data transformation)
- Multi-step logic that benefits from intermediate variables
- Need deterministic, verifiable results
- Working with data structures (arrays, objects, graphs)
- Building systems (code generation is the task)

❌ **Don't use PAL when**:
- Task is purely creative (writing, brainstorming)
- Requires subjective judgment
- Natural language explanation is the goal
- No computation or logic needed

---

## PAL in Our Toolkit

### We're Already Using PAL!

**Our entire development workflow is PAL-based**:
- We generate TypeScript/JavaScript code to solve problems
- We write tests as executable specifications
- We use code to reason about features

**Example from govertical** (OQE scoring):

Instead of:
```
"Calculate labor intensity score by taking labor cost percentage
times 0.6 plus repetitive task ratio times 0.4"
```

We write:
```typescript
function calculateLaborIntensity(input: LaborIntensityInput): number {
  const laborCostScore = input.labor_cost_pct * 0.6;
  const repetitiveScore = input.repetitive_task_ratio * 0.4;
  return laborCostScore + repetitiveScore;
}
```

The code IS the reasoning. It's precise, executable, and testable.

---

## PAL Patterns in Development

### 1. Test-Driven Development (TDD)

**PAL Application**: Tests are executable specifications

```typescript
// Instead of text specification:
// "Feature should validate email format and reject invalid emails"

// PAL: Write executable test (code as spec)
describe('Email validation', () => {
  it('should accept valid email', () => {
    expect(validateEmail('user@example.com')).toBe(true);
  });

  it('should reject email without @', () => {
    expect(validateEmail('userexample.com')).toBe(false);
  });

  it('should reject email without domain', () => {
    expect(validateEmail('user@')).toBe(false);
  });
});
```

The tests ARE the specification. Code > Text.

---

### 2. Data Transformation Pipelines

**PAL Application**: Transform data through code, not descriptions

```typescript
// Instead of describing transformation:
// "For each vertical, calculate composite OQE score from 5 dimensions
//  weighted 30%, 20%, 25%, 15%, 10% respectively"

// PAL: Write transformation code
const WEIGHTS = {
  labor_intensity: 0.30,
  software_underspend: 0.20,
  replaceability: 0.25,
  moat_potential: 0.15,
  reachability: 0.10,
};

function calculateOQEScore(scores: DimensionScores): number {
  return (
    scores.labor_intensity * WEIGHTS.labor_intensity +
    scores.software_underspend * WEIGHTS.software_underspend +
    scores.replaceability * WEIGHTS.replaceability +
    scores.moat_potential * WEIGHTS.moat_potential +
    scores.reachability * WEIGHTS.reachability
  );
}
```

Code IS the transformation logic. Self-documenting and executable.

---

### 3. Business Logic

**PAL Application**: Complex rules as code structures

```typescript
// Instead of text rules:
// "Status transitions: observing can go to cab0, cab0 can go to cab1 or killed,
//  cab1 can go to cab2 or killed, cab2 can go to active or killed,
//  active can go to killed, killed can go to observing after 90 days"

// PAL: State machine in code
const VALID_TRANSITIONS: Record<VerticalStatus, VerticalStatus[]> = {
  observing: ['cab0'],
  cab0: ['cab1', 'killed'],
  cab1: ['cab2', 'killed'],
  cab2: ['active', 'killed'],
  active: ['killed'],
  killed: ['observing'], // After cooldown
};

function canTransition(from: VerticalStatus, to: VerticalStatus): boolean {
  return VALID_TRANSITIONS[from].includes(to);
}
```

Code encodes the rules. No ambiguity, fully testable.

---

## PAL vs Text Reasoning

### Example: Complex Calculation

**Question**: "A SaaS company has 3 pricing tiers. Basic ($10/mo, 100 users), Pro ($25/mo, 50 users), Enterprise ($100/mo, 10 users). What's total MRR?"

**Text Reasoning** (error-prone):
```
"Basic tier: $10 per month times 100 users equals $1000
Pro tier: $25 per month times 50 users equals $1250
Enterprise tier: $100 per month times 10 users equals $1000
Total MRR: $1000 plus $1250 plus $1000 equals $3250"
```

**PAL Reasoning** (reliable):
```python
tiers = [
    {"name": "Basic", "price": 10, "users": 100},
    {"name": "Pro", "price": 25, "users": 50},
    {"name": "Enterprise", "price": 100, "users": 10},
]

mrr = sum(tier["price"] * tier["users"] for tier in tiers)
# mrr = 1000 + 1250 + 1000 = 3250

answer = mrr
```

PAL guarantees correctness. No mental arithmetic errors.

---

## PAL in Command Prompts

### When Writing Commands

**Use PAL thinking** for commands that generate code:

**Example: `/build-feature` command**

Instead of saying:
```
"Implement the feature by carefully considering the requirements..."
```

Use PAL framing:
```
"Write executable code that implements the feature:

1. Define types (interfaces/types for data structures)
2. Write tests (executable specifications)
3. Implement functions (code that satisfies tests)
4. Verify (run tests to prove correctness)

The code IS the implementation. Make it executable."
```

---

## PAL for Debugging

**Problem**: Test failing with obscure error

**Text Reasoning** (vague):
```
"The test is failing because the function might not be
handling the edge case correctly. We should check the logic..."
```

**PAL Reasoning** (precise):
```typescript
// Reproduce the failure with minimal code
const input = { vertical_id: "test", labor_intensity: 9 }; // Failing input
const result = scoreVertical(input);
// Error: Cannot read 'labor_cost_pct' of undefined

// Hypothesis: input.labor_intensity is number, expects object
// Test hypothesis:
console.log(typeof input.labor_intensity); // "number" ✓
console.log(input.labor_intensity.labor_cost_pct); // TypeError ✓

// Fix: Change input structure
const correctedInput = {
  vertical_id: "test",
  labor_intensity: {
    labor_cost_pct: 90,
    repetitive_task_ratio: 85,
  },
};
const correctedResult = scoreVertical(correctedInput);
// Success ✓
```

Code demonstrates the problem and solution. Executable proof.

---

## PAL Best Practices

### 1. Write Code for Logic, Text for Explanation

**Good**:
```typescript
// Calculate weighted score
function calculateWeightedScore(scores: number[], weights: number[]): number {
  return scores.reduce((sum, score, i) => sum + score * weights[i], 0);
}
```

**Bad**:
```
"To calculate the weighted score, you multiply each score by its
corresponding weight and then add them all together."
```

**Why**: Code is executable. Text can be misinterpreted.

---

### 2. Use Code to Validate Assumptions

**Good**:
```typescript
// Validate assumption: weights sum to 1.0
const WEIGHTS = [0.30, 0.20, 0.25, 0.15, 0.10];
const sum = WEIGHTS.reduce((a, b) => a + b, 0);
console.assert(sum === 1.0, "Weights must sum to 1.0");
```

**Bad**:
```
"Make sure the weights add up to 100%"
```

**Why**: Assertion proves the constraint is met.

---

### 3. Generate Examples Programmatically

**Good**:
```typescript
// Generate test cases programmatically
const testCases = [
  { input: 0, expected: "kill" },
  { input: 50, expected: "hold" },
  { input: 75, expected: "go" },
  { input: 100, expected: "go" },
];

testCases.forEach(({ input, expected }) => {
  it(`should return ${expected} for score ${input}`, () => {
    expect(getDecision(input)).toBe(expected);
  });
});
```

**Bad**:
```
"Test with scores 0, 50, 75, and 100"
```

**Why**: Code generates tests. No manual work, less error-prone.

---

### 4. Make Invariants Executable

**Good**:
```typescript
// Invariant: Active vertical must exist before transitions
function transitionToActive(verticalId: string): void {
  const current = getActiveVertical();
  if (current !== null) {
    throw new Error("Cannot have multiple active verticals");
  }
  updateVerticalStatus(verticalId, 'active');
}
```

**Bad**:
```
"Only one vertical can be active at a time"
```

**Why**: Code enforces the invariant. Can't be violated.

---

## PAL in Autonomous Mode

### Current Practice (Already PAL)

Our autonomous mode uses PAL implicitly:

**PHASE 2: Reasoning (Tree of Thoughts)**
- We reason about paths, but execute code to implement them

**PHASE 3: Execute Action**
```typescript
// Instead of describing what to do:
// "Read the features.json file and count incomplete features"

// PAL: Write code to do it
const features = JSON.parse(fs.readFileSync('features.json', 'utf-8'));
const incomplete = features.features.filter(f => !f.passes);
console.log(`${incomplete.length} features incomplete`);
```

**PHASE 4: Evaluate**
```typescript
// Instead of guessing if tests pass:
// "I think the tests probably passed"

// PAL: Run tests and check result
const testResult = execSync('npm test', { encoding: 'utf-8' });
const allPassed = !testResult.includes('failing');
```

---

## PAL vs Other Patterns

| Pattern | Reasoning Medium | Execution | Best For |
|---------|-----------------|-----------|----------|
| **Chain-of-Thought** | Natural language | None | Abstract reasoning |
| **ReAct** | Text + Tools | External tools | Multi-step investigation |
| **PAL** | Code | Runtime | Computation, logic |
| **APE** | Meta-prompts | Evaluation | Prompt optimization |

**PAL Advantage**: Precision. Code doesn't have ambiguity.

---

## Integration with Toolkit

### Formalize PAL Awareness

**Commands that should emphasize PAL**:
1. `/build-feature` - Generate code, not descriptions
2. `/tdd` - Tests as executable specs
3. `/verify` - Code-based validation
4. `/review` - Analyze code structure

**Example Enhancement for `/build-feature`**:
```markdown
Build the feature using PAL (Program-Aided Language):

WRITE CODE, NOT DESCRIPTIONS:
- Types/interfaces (executable specifications)
- Tests (executable acceptance criteria)
- Implementation (executable logic)
- Validation (executable verification)

DO NOT write paragraphs explaining logic.
DO write code that implements logic.

The code IS the reasoning.
```

---

## PAL Skill (Optional)

Similar to `/react`, we could create `/pal` for explicit code-based reasoning:

**Use case**: "Solve this problem by writing code"

```markdown
# PAL Skill

You are now in **PAL Mode** - solve problems by writing and executing code.

## Process

1. **Understand Problem**: Restate in precise terms
2. **Write Code**: Generate executable solution
3. **Execute**: Run code, capture output
4. **Verify**: Check output matches expected result

## Example

User: "Calculate MRR from pricing tiers"

**Step 1: Understand**
```
Given: List of tiers with price and user count
Goal: Total monthly recurring revenue
```

**Step 2: Write Code**
```python
tiers = [...]
mrr = sum(t['price'] * t['users'] for t in tiers)
```

**Step 3: Execute**
```
3250
```

**Step 4: Verify**
```
✓ MRR = $3,250 (matches expected calculation)
```
```

---

## Examples from Our Work

### Example 1: OQE Scoring (govertical)

**Text Approach** (what we DON'T do):
```
"The OQE score is calculated by taking the labor intensity dimension
times thirty percent, plus the software underspend dimension times
twenty percent, plus..."
```

**PAL Approach** (what we DO):
```typescript
const OQE_WEIGHTS = {
  labor_intensity: 0.30,
  software_underspend: 0.20,
  replaceability: 0.25,
  moat_potential: 0.15,
  reachability: 0.10,
};

function scoreVertical(input: OQEScoringInput): OQEResult {
  const scores = {
    labor_intensity: calculateLaborIntensity(input.labor_intensity),
    software_underspend: calculateSoftwareUnderspend(input.software_underspend),
    replaceability: calculateReplaceability(input.replaceability),
    moat_potential: calculateMoatPotential(input.moat_potential),
    reachability: calculateReachability(input.reachability),
  };

  const total_score = Object.entries(scores).reduce(
    (sum, [dimension, score]) => sum + score * OQE_WEIGHTS[dimension],
    0
  );

  return {
    scores,
    total_score,
    decision: total_score >= 75 ? 'go' : total_score >= 50 ? 'hold' : 'kill',
  };
}
```

Code IS the algorithm. Self-documenting, testable, precise.

---

### Example 2: Test Infrastructure (govertical)

**Instead of describing tests**:
```
"We need tests that check if the vertical can be created,
retrieved, and if the status can be updated..."
```

**PAL: Write executable tests**:
```typescript
describe('Vertical Repository', () => {
  it('should create a vertical with default observing status', () => {
    const vertical = createVertical('Home Health Care');
    expect(vertical.status).toBe('observing');
  });

  it('should retrieve a vertical by ID', () => {
    const created = createVertical('Accounting Firms');
    const retrieved = getVertical(created.vertical_id);
    expect(retrieved?.vertical_id).toBe(created.vertical_id);
  });
});
```

Tests ARE the specification. Executable documentation.

---

## Metrics for Success

### PAL Adoption in Toolkit

**Track**:
- % of commands that emphasize code generation over text
- % of reasoning done via code vs. natural language
- Test coverage (executable specs)

**Target**:
- Code-first reasoning: >80% for technical commands
- Test coverage: >85% for all features
- Documentation: Code examples > text explanations

---

## References

- **Paper**: "PAL: Program-aided Language Models" (Gao et al., 2022)
- **DAIR.AI**: https://www.promptingguide.ai/techniques/pal
- **Our Practice**: All of govertical, gpnet3, goassist3 codebases
- **Related Patterns**: `react.md`, `cot.md`

---

## Summary

**PAL is already our default mode**:
- We write code to solve problems
- We use tests as specifications
- We rely on executable logic, not text descriptions

**This pattern formalizes what we do well**:
- When building features → Write code, not paragraphs
- When testing → Write executable specs
- When debugging → Write minimal repro code
- When documenting → Show code examples

**Code is reasoning. Execution is proof.**

---

**Created**: 2025-12-26
**Pattern Library**: claude-code-toolkit v3.2
**Status**: Documents existing practice, now formalized
