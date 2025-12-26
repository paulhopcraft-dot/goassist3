---
pattern: Chain-of-Thought (CoT)
version: 3.0.0
description: Explicit step-by-step reasoning pattern
shared_by: [code-reviewer, test-specialist, healthcare-validator]
---

# Chain-of-Thought Reasoning Pattern

**Purpose**: Show explicit reasoning, not just conclusions

**Structure**:
```
1. REASONING: Why is this important/risky?
2. OBSERVATION: What did I find?
3. ANALYSIS: What does this mean?
4. CONCLUSION: What action is needed?
```

**Example** (Security Finding):
```
Analyzing function `processPayment(amount, userId)`:

1. REASONING: This function handles money → High security risk
   - Need to verify: input validation, SQL injection, auth checks

2. OBSERVATION: Direct SQL query `SELECT * FROM users WHERE id = ${userId}`
   - RISK ASSESSMENT: String interpolation detected
   - SEVERITY: CRITICAL - SQL injection vulnerability

3. ANALYSIS: What if userId = "1 OR 1=1"?
   - OUTCOME: Would return all users → Auth bypass confirmed

4. CONCLUSION: Critical vulnerability found, must block merge
   - FIX: Use parameterized query: `WHERE id = $1` with [userId]
```

**Benefits**:
- Helps developers understand WHY issues matter
- Educational (teaches security concepts)
- Transparent reasoning (not a black box)
- Builds trust in agent recommendations

**Usage in Agents**:
- code-reviewer: Use for all security, quality, performance findings
- test-specialist: Use when explaining test strategy selection
- healthcare-validator: Use when identifying HIPAA violations

**Token Savings**:
- v2.4: CoT example duplicated in 3 agent files = 3 × 150 = 450 tokens
- v3.0: CoT example in one shared file = 150 tokens
- Savings: 67% reduction
