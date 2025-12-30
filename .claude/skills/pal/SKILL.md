---
name: pal
description: PAL (Program-Aided Language) - solve problems by writing executable code instead of text reasoning
version: 1.0.0
pattern: PAL (Program-Aided Language Models)
---

# PAL Skill - Code as Reasoning

You are now in **PAL Mode** - solve problems by writing and executing code instead of natural language reasoning.

## Mission

Use **code as your reasoning mechanism**:
- Write executable code instead of text explanations
- Let the runtime compute instead of computing mentally
- Generate precise, verifiable solutions

**Key Principle**: Code is more precise than text for logical reasoning.

---

## Process

### Step 1: Understand Problem

Restate the problem in precise, computational terms:
- What are the inputs?
- What is the expected output?
- What computation is needed?

### Step 2: Write Code Solution

Generate executable code that solves the problem:
- Define variables/data structures
- Implement logic clearly
- Use meaningful names
- Add comments only where logic is complex

### Step 3: Execute & Verify

Run the code and verify the result:
- Does output match expected?
- Are edge cases handled?
- Is the solution correct?

---

## When to Use PAL

**✅ Use PAL for:**
- Mathematical calculations
- Data transformations
- Multi-step logic
- Algorithm implementation
- Test generation
- Configuration validation

**❌ Don't use PAL for:**
- Creative writing
- Subjective decisions
- Natural language tasks
- Explanations to non-technical users

---

## Example: Calculation Problem

**User**: "A company has 3 pricing tiers: Basic ($10/mo, 100 users), Pro ($25/mo, 50 users), Enterprise ($100/mo, 10 users). What's the total MRR?"

### Step 1: Understand
```
Inputs: List of tiers with (price, user_count)
Output: Total monthly recurring revenue (MRR)
Computation: Sum of (price × users) for each tier
```

### Step 2: Write Code
```typescript
interface PricingTier {
  name: string;
  price: number;
  users: number;
}

const tiers: PricingTier[] = [
  { name: "Basic", price: 10, users: 100 },
  { name: "Pro", price: 25, users: 50 },
  { name: "Enterprise", price: 100, users: 10 },
];

const calculateMRR = (tiers: PricingTier[]): number => {
  return tiers.reduce((total, tier) => {
    return total + (tier.price * tier.users);
  }, 0);
};

const totalMRR = calculateMRR(tiers);
console.log(`Total MRR: $${totalMRR}`);
```

### Step 3: Execute
```
Total MRR: $3250
```

**Breakdown**:
- Basic: $10 × 100 = $1,000
- Pro: $25 × 50 = $1,250
- Enterprise: $100 × 10 = $1,000
- **Total: $3,250**

✓ Result verified with code execution (no mental arithmetic errors)

---

## Example: Data Transformation

**User**: "Convert this list of verticals to include only those with OQE score >= 75"

### Step 1: Understand
```
Input: Array of verticals with scores
Output: Filtered array (score >= 75)
Computation: Filter operation
```

### Step 2: Write Code
```typescript
interface Vertical {
  name: string;
  oqe_score: number;
  status: string;
}

const verticals: Vertical[] = [
  { name: "Home Health", oqe_score: 82, status: "go" },
  { name: "Dental", oqe_score: 65, status: "hold" },
  { name: "Accounting", oqe_score: 78, status: "go" },
  { name: "Landscaping", oqe_score: 45, status: "kill" },
];

const highScoreVerticals = verticals.filter(v => v.oqe_score >= 75);

console.log(`Found ${highScoreVerticals.length} verticals with score >= 75:`);
highScoreVerticals.forEach(v => {
  console.log(`- ${v.name}: ${v.oqe_score}`);
});
```

### Step 3: Execute
```
Found 2 verticals with score >= 75:
- Home Health: 82
- Accounting: 78
```

✓ Code provides exact, verifiable result

---

## Example: Algorithm Implementation

**User**: "Implement the OQE scoring algorithm with weighted dimensions"

### Step 1: Understand
```
Inputs: 5 dimension scores (0-100 each)
Weights: labor_intensity (30%), software_underspend (20%),
         replaceability (25%), moat_potential (15%), reachability (10%)
Output: Weighted composite score (0-100)
```

### Step 2: Write Code
```typescript
interface DimensionScores {
  labor_intensity: number;
  software_underspend: number;
  replaceability: number;
  moat_potential: number;
  reachability: number;
}

const OQE_WEIGHTS = {
  labor_intensity: 0.30,
  software_underspend: 0.20,
  replaceability: 0.25,
  moat_potential: 0.15,
  reachability: 0.10,
} as const;

function calculateOQEScore(scores: DimensionScores): number {
  const weightedScore =
    scores.labor_intensity * OQE_WEIGHTS.labor_intensity +
    scores.software_underspend * OQE_WEIGHTS.software_underspend +
    scores.replaceability * OQE_WEIGHTS.replaceability +
    scores.moat_potential * OQE_WEIGHTS.moat_potential +
    scores.reachability * OQE_WEIGHTS.reachability;

  return Math.round(weightedScore * 100) / 100; // Round to 2 decimals
}

// Validate weights sum to 1.0
const weightSum = Object.values(OQE_WEIGHTS).reduce((a, b) => a + b, 0);
console.assert(weightSum === 1.0, "Weights must sum to 1.0");

// Test with example
const exampleScores: DimensionScores = {
  labor_intensity: 90,
  software_underspend: 80,
  replaceability: 85,
  moat_potential: 75,
  reachability: 70,
};

const score = calculateOQEScore(exampleScores);
console.log(`OQE Score: ${score}`);
```

### Step 3: Execute
```
OQE Score: 83.75
```

**Calculation breakdown**:
- 90 × 0.30 = 27.0
- 80 × 0.20 = 16.0
- 85 × 0.25 = 21.25
- 75 × 0.15 = 11.25
- 70 × 0.10 = 7.0
- **Total: 82.5**

✓ Algorithm implemented precisely, testable, and self-documenting

---

## PAL for Test Generation

**User**: "Generate tests for the email validation function"

### Write Executable Tests (Code as Specification)

```typescript
describe('Email Validation', () => {
  // Happy path
  it('should accept valid email with standard format', () => {
    expect(validateEmail('user@example.com')).toBe(true);
  });

  // Edge cases: Missing components
  it('should reject email without @', () => {
    expect(validateEmail('userexample.com')).toBe(false);
  });

  it('should reject email without domain', () => {
    expect(validateEmail('user@')).toBe(false);
  });

  it('should reject email without local part', () => {
    expect(validateEmail('@example.com')).toBe(false);
  });

  // Edge cases: Special characters
  it('should accept email with dots in local part', () => {
    expect(validateEmail('first.last@example.com')).toBe(true);
  });

  it('should accept email with + in local part', () => {
    expect(validateEmail('user+tag@example.com')).toBe(true);
  });

  // Edge cases: Boundary conditions
  it('should reject empty string', () => {
    expect(validateEmail('')).toBe(false);
  });

  it('should reject whitespace', () => {
    expect(validateEmail('  ')).toBe(false);
  });

  // Edge cases: Multiple @
  it('should reject email with multiple @ symbols', () => {
    expect(validateEmail('user@@example.com')).toBe(false);
  });
});
```

✓ Tests ARE the specification. Executable, comprehensive, unambiguous.

---

## PAL for Debugging

**User**: "Debug why the vertical status transition is failing"

### Step 1: Reproduce with Code

```typescript
// Minimal reproduction case
const currentStatus: VerticalStatus = 'active';
const requestedStatus: VerticalStatus = 'cab0';

const VALID_TRANSITIONS: Record<VerticalStatus, VerticalStatus[]> = {
  observing: ['cab0'],
  cab0: ['cab1', 'killed'],
  cab1: ['cab2', 'killed'],
  cab2: ['active', 'killed'],
  active: ['killed'],  // <-- Active can only go to killed
  killed: ['observing'],
};

const canTransition = VALID_TRANSITIONS[currentStatus].includes(requestedStatus);
console.log(`Can transition from ${currentStatus} to ${requestedStatus}? ${canTransition}`);
```

### Step 2: Execute

```
Can transition from active to cab0? false
```

### Step 3: Identify Fix

```typescript
// Problem: active → cab0 is not a valid transition
// Fix: Only allow active → killed per state machine rules
// User must kill the vertical first, then transition from killed → observing

console.log(`Valid transitions from ${currentStatus}:`, VALID_TRANSITIONS[currentStatus]);
// Output: Valid transitions from active: ['killed']
```

✓ Code reveals the exact issue. No guessing, precise diagnosis.

---

## Integration with Autonomous Mode

PAL enhances autonomous mode execution:

**PHASE 3: Execute Action**
- Use PAL to implement features (code, not descriptions)
- Generate tests as executable specs
- Write configuration as code

**PHASE 4: Evaluate**
- Run code to verify (don't guess)
- Execute tests to prove correctness
- Use assertions to validate assumptions

---

## Best Practices

### 1. Write Self-Documenting Code

```typescript
// Good: Code explains itself
function calculateWeightedScore(scores: number[], weights: number[]): number {
  return scores.reduce((sum, score, i) => sum + score * weights[i], 0);
}

// Bad: Need comments to explain
function calc(s: number[], w: number[]): number {
  // Multiply each score by weight and sum
  return s.reduce((a, b, i) => a + b * w[i], 0);
}
```

### 2. Use Types as Documentation

```typescript
// Types document the structure
interface OQEScoringInput {
  vertical_id: string;
  labor_intensity: {
    labor_cost_pct: number;
    repetitive_task_ratio: number;
  };
  software_underspend: {
    saas_spend_pct: number;
    tool_fragmentation_score: number;
  };
  // ... more fields
}

// Function signature is self-documenting
function scoreVertical(input: OQEScoringInput): OQEResult {
  // Implementation
}
```

### 3. Validate with Assertions

```typescript
// Make assumptions explicit and testable
const WEIGHTS = [0.30, 0.20, 0.25, 0.15, 0.10];
const sum = WEIGHTS.reduce((a, b) => a + b, 0);
console.assert(Math.abs(sum - 1.0) < 0.001, "Weights must sum to 1.0");
```

### 4. Generate Examples Programmatically

```typescript
// Don't manually list test cases
// Generate them with code
const scores = [0, 25, 50, 75, 100];
const expectedDecisions = ['kill', 'kill', 'hold', 'go', 'go'];

scores.forEach((score, i) => {
  it(`should return ${expectedDecisions[i]} for score ${score}`, () => {
    expect(getDecision(score)).toBe(expectedDecisions[i]);
  });
});
```

---

## Stopping Conditions

**Stop using PAL when**:
- Task requires natural language explanation
- User is non-technical (explain in text, not code)
- Creative/subjective work (writing, design)
- No computation or logic involved

**Otherwise, default to PAL**: Code > Text for precision.

---

## Example Session

**User**: "Calculate the composite score for these OQE dimensions: labor 90, software 80, replaceability 85, moat 75, reachability 70"

**PAL Response**:

Step 1: Understand the problem
```
Input: 5 dimension scores
Weights: L=30%, S=20%, R=25%, M=15%, R=10%
Output: Weighted composite score
```

Step 2: Write code
```typescript
const scores = {
  labor: 90,
  software: 80,
  replaceability: 85,
  moat: 75,
  reachability: 70,
};

const weights = {
  labor: 0.30,
  software: 0.20,
  replaceability: 0.25,
  moat: 0.15,
  reachability: 0.10,
};

const composite =
  scores.labor * weights.labor +
  scores.software * weights.software +
  scores.replaceability * weights.replaceability +
  scores.moat * weights.moat +
  scores.reachability * weights.reachability;

console.log(`Composite Score: ${composite}`);
```

Step 3: Execute
```
Composite Score: 82.5
```

**Breakdown**:
- Labor: 90 × 0.30 = 27.0
- Software: 80 × 0.20 = 16.0
- Replaceability: 85 × 0.25 = 21.25
- Moat: 75 × 0.15 = 11.25
- Reachability: 70 × 0.10 = 7.0
- **Total: 82.5**

Decision: **GO** (score >= 75)

---

## Start Now

**Given problem**: [User's computational/logical problem]

Begin with:

## Step 1: Understand
```
[Restate problem in computational terms]
```

## Step 2: Write Code
```[language]
[Executable solution]
```

## Step 3: Execute & Verify
```
[Output and verification]
```

---

**GO! Solve the problem with code.**
