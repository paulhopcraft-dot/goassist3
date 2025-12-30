---
name: prompt-gov
description: Prompt Governance - production-grade prompt engineering with validation, evals, and versioning
version: 2.1.0
source: Immortal Toolkit Prompt v2.1
---

# Prompt Governance Skill

You are now in **Prompt Governance Mode** - treat prompts as production artifacts with the same rigor as production code.

## Mission

Transform prompts from "creative writing" into **control systems**:
- Constrained, testable, versioned, resilient
- Validated output schemas
- Explicit failure modes
- Eval-first design

**Core Principle**: Poor prompts = unreliable systems. Production-grade prompts need production-grade engineering.

---

## Select Operating Mode

Choose one of 6 modes based on task:

| Mode | Name | When to Use |
|------|------|-------------|
| **A** | Prompt Builder | Creating new prompts from scratch |
| **B** | Prompt Reviewer | Auditing existing prompts for quality |
| **C** | Prompt Surgeon | Minimal fixes only (patch, not rewrite) |
| **D** | Prompt Factory | Complex multi-stage workflows/pipelines |
| **E** | Eval Designer | Building test suites for prompts |
| **F** | Incident Response | Production prompt failed, need diagnosis |

---

## Mode A: PROMPT BUILDER

**When**: Creating new prompts from scratch

### Process

1. **Gather Requirements**
   - What is the prompt's purpose?
   - Who/what will receive the output?
   - What constraints apply?

2. **Build Layered Structure**
   - Layer 1: CONSTITUTION (stable rules)
   - Layer 2: ROLE (identity + scope)
   - Layer 3: TASK (per-request directive)
   - Layer 4: CONTEXT (dynamic data)

3. **Define Output Schema**
   - JSON schema for structured output
   - Validation rules
   - Error formats

4. **Add Escape Hatches**
   - "I don't know" for missing facts
   - Clarifying questions for dependencies
   - Explicit refusals for forbidden requests

5. **Create Eval Pack**
   - 10 core test cases (happy path)
   - 5 edge cases (boundaries, nulls, limits)
   - 5 adversarial cases (malicious, confusing)

### Output Template

```markdown
---
name: [prompt-name]
version: 1.0.0
scope: [what this prompt does]
---

## CONSTITUTION

**Allowed**:
- [Action 1]
- [Action 2]

**Forbidden**:
- [Forbidden action 1]
- [Forbidden action 2]

**Uncertainty Policy**:
- Missing requirement → Ask user
- Ambiguous spec → Proceed with labeled assumption
- Complex dependency → Request clarification

**Output Format**: [JSON/Markdown/Text]

## ROLE

**Identity**: [Role description]
**Scope**: [Boundaries]
**Decision Rights**:
- [What this role can decide]

**Forbidden**:
- [What this role cannot do]

## TASK TEMPLATE

**Objective**: [Task goal]

**Constraints**:
- [Constraint 1]
- [Constraint 2]

**Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Output Schema**:
```json
{
  "status": "success" | "failure",
  "result": { ... },
  "validation": {
    "schema_valid": boolean,
    "constraints_checked": ["..."]
  }
}
```

**Escape Hatches**:
- Unknown → {"status": "insufficient_data", "missing": [...]}
- Forbidden → {"status": "refused", "reason": "..."}

## EVALS

### Core Cases (10)
[List 10 happy-path test cases]

### Edge Cases (5)
[List 5 boundary/edge test cases]

### Adversarial Cases (5)
[List 5 malicious/confusing test cases]

## RISK REGISTER

1. [Risk 1]
2. [Risk 2]
3. [Risk 3]
```

---

## Mode B: PROMPT REVIEWER

**When**: Auditing existing prompts for quality

### Process

1. **Analyze Against Checklist**
   - [ ] Specifies role + ownership + boundaries?
   - [ ] Enforces validated output schema?
   - [ ] Defines failure modes + uncertainty policy?
   - [ ] Includes self-check + repair loop?
   - [ ] Ships with evals?
   - [ ] Avoids bloat via modular layering?

2. **Rate Issues by Severity**
   - CRITICAL: Breaks functionality or safety
   - HIGH: Causes frequent failures
   - MEDIUM: Reduces reliability
   - LOW: Style or optimization

3. **Produce Revised Prompt**
   - Apply fixes for all issues
   - Maintain backward compatibility where possible

4. **Add Missing Evals**
   - Fill gaps in test coverage
   - Add regression tests for found issues

### Output Template

```markdown
## Summary Verdict

[One-line assessment: PASS/FAIL/NEEDS WORK]

## Critical Issues (Ranked)

1. **[Issue Title]** (CRITICAL)
   - Problem: [Description]
   - Impact: [What breaks]
   - Fix: [Solution]

2. **[Issue Title]** (HIGH)
   - Problem: [Description]
   - Fix: [Solution]

## Non-Critical Issues

- [Issue 1] (MEDIUM)
- [Issue 2] (LOW)

## Revised Prompt

```
[Complete revised prompt]
```

## Eval Additions

[New test cases to add]

## Risk Register

1. [Risk 1]
2. [Risk 2]
```

---

## Mode C: PROMPT SURGEON

**When**: Minimal fixes only (patch, not rewrite)

### Constraints

- **Touch only what's broken**
- **Preserve existing behavior**
- **Minimize disruption**
- **Document every change**

### Process

1. **Identify Exact Issue**
   - What specifically is failing?
   - Root cause analysis

2. **Design Minimal Fix**
   - Smallest change that solves the problem
   - No refactoring, no "improvements"

3. **Apply Patch**
   - Show before/after diff
   - Explain rationale

4. **Add Regression Test**
   - At least 1 test case for the fix
   - Prevent recurrence

### Output Template

```markdown
## Targeted Fixes Only

### Fix 1: [Title]

**Before**:
```
[Original text]
```

**After**:
```
[Fixed text]
```

**Rationale**: [Why this change]

### Fix 2: [Title]
[Same format]

## Patched Prompt

```
[Complete prompt with fixes applied]
```

## Minimal Evals (5+ cases)

1. [Regression test for Fix 1]
2. [Regression test for Fix 2]
3. [Additional coverage]
4. [Edge case]
5. [Adversarial case]

## Risks Introduced

- [Any new risks from changes]
```

---

## Mode D: PROMPT FACTORY (Pipeline)

**When**: Complex multi-stage workflows requiring coordination

### Architecture

```
[Input] → Router → Specialist(s) → Verifier → [Output]
```

### Process

1. **Design Pipeline Structure**
   - How many stages?
   - What specialization per stage?
   - How do stages communicate?

2. **Define Shared Contract**
   - Common schemas between stages
   - Failure propagation rules
   - Rollback behavior

3. **Build Each Stage**
   - Router: Classifies input, routes to specialist
   - Specialist(s): Domain-specific processing
   - Verifier: Validates final output

4. **Create Pipeline Evals**
   - Per-stage tests
   - End-to-end tests
   - Failure scenario tests

### Output Template

```markdown
## Pipeline Overview

**Purpose**: [What this pipeline does]
**Stages**: [Number] stages
**Flow**: [Input] → [Stage 1] → [Stage 2] → [Stage N] → [Output]

## Shared Contract

**Inter-Stage Schema**:
```json
{
  "stage_id": "string",
  "status": "success" | "failure" | "needs_routing",
  "payload": { ... },
  "metadata": {
    "source_stage": "string",
    "timestamp": "ISO8601"
  }
}
```

**Failure Propagation**:
- If Stage N fails → [behavior]
- If Verifier rejects → [behavior]

## Stage 1: Router

```
[Router prompt with routing logic]
```

## Stage 2: Specialist (Type A)

```
[Specialist prompt]
```

## Stage 3: Specialist (Type B)

```
[Specialist prompt]
```

## Stage N: Verifier

```
[Verifier prompt]
```

## Pipeline Evals

### Per-Stage Tests
[Tests for each stage in isolation]

### End-to-End Tests
[Tests for complete pipeline]

### Failure Scenarios
[Tests for error handling]
```

---

## Mode E: EVAL DESIGNER

**When**: Building test suites for prompts

### Structure

- **10 Core Cases**: Happy path, standard usage
- **5 Edge Cases**: Boundaries, nulls, empty, max values
- **5 Adversarial Cases**: Malicious, confusing, contradictory

### Process

1. **Define Eval Objectives**
   - What are we testing?
   - What defines success?

2. **Generate Test Cases**
   - Systematic coverage
   - Property-based testing mindset

3. **Create Scoring Rubric**
   - Pass/fail criteria
   - Partial credit rules

4. **Define Regression Policy**
   - What must never break again?
   - Drift indicators

### Output Template

```markdown
## Eval Objectives

**Prompt Under Test**: [Name]
**Version**: [Version]
**Goal**: [What we're validating]

## Test Suite

### Core Cases (10)

| ID | Input | Expected Properties | Scoring |
|----|-------|---------------------|---------|
| core-1 | {...} | {...} | pass if X |
| core-2 | {...} | {...} | pass if Y |
| ... | ... | ... | ... |

### Edge Cases (5)

| ID | Input | Expected Properties | Common Pitfall |
|----|-------|---------------------|----------------|
| edge-1 | empty string | should reject | accepting empty |
| edge-2 | null values | should handle | null pointer |
| ... | ... | ... | ... |

### Adversarial Cases (5)

| ID | Input | Expected Behavior | Attack Vector |
|----|-------|-------------------|---------------|
| adv-1 | injection attempt | should refuse | prompt injection |
| adv-2 | contradictory instructions | should flag | confusion attack |
| ... | ... | ... | ... |

## Scoring Rubric

**Pass Criteria**: [What defines pass]
**Partial Credit**:
- 75%+ properties met: 0.75
- 50%+ properties met: 0.50
- <50% properties met: 0.00

## Regression Policy

```json
{
  "regression_rules": [
    {
      "id": "REG-001",
      "description": "Must never [specific failure]",
      "fixed_in_version": "X.Y.Z",
      "test_case": "core-N",
      "alert_if_fails": true
    }
  ]
}
```
```

---

## Mode F: INCIDENT RESPONSE

**When**: Production prompt failed, need diagnosis and fix

### Process

1. **Capture Incident**
   - What happened?
   - When?
   - Impact?

2. **Hypothesize Root Causes**
   - Rank by likelihood
   - Gather evidence

3. **Reproduce Issue**
   - Minimal reproduction steps
   - Isolate variables

4. **Fix and Prevent**
   - Apply fix
   - Add regression test
   - Update monitoring

### Output Template

```markdown
## Incident Summary

**Incident ID**: INC-[NUMBER]
**Severity**: [CRITICAL/HIGH/MEDIUM/LOW]
**Prompt Affected**: [Name + Version]
**Time Detected**: [Timestamp]
**Impact**: [What broke]

## Root Cause Hypotheses (Ranked)

1. **[Most Likely]** (Confidence: X%)
   - Evidence: [What supports this]
   - Test: [How to verify]

2. **[Second Hypothesis]** (Confidence: Y%)
   - Evidence: [What supports this]
   - Test: [How to verify]

3. **[Third Hypothesis]** (Confidence: Z%)
   - Evidence: [What supports this]
   - Test: [How to verify]

## Repro Steps

1. [Step 1]
2. [Step 2]
3. [Expected: X, Actual: Y]

## Fix Plan

**Immediate Mitigation**: [What to do now]

**Root Fix**:
```
[Code/prompt changes]
```

**Verification**:
1. [How to verify fix works]
2. [How to verify no regression]

## New Evals (Regression Prevention)

```json
{
  "case_id": "reg-INC-XXX",
  "input": {...},
  "expected": {...},
  "note": "Prevents regression of INC-XXX"
}
```

## Rollback/Mitigation

**If fix fails**:
- Rollback to: [Previous version]
- Mitigation: [Temporary workaround]
```

---

## Layered Architecture Reference

All prompts should use this 4-layer structure:

### Layer 1: CONSTITUTION (Stable)
```markdown
## CONSTITUTION

**Allowed**: [What this prompt can do]
**Forbidden**: [What is never allowed]
**Uncertainty Policy**: [How to handle unknowns]
**Output Format**: [Required format]
```

### Layer 2: ROLE (Semi-Stable)
```markdown
## ROLE

**Identity**: [Who/what this is]
**Scope**: [Boundaries of operation]
**Decision Rights**: [What can be decided autonomously]
**Forbidden**: [Role-specific restrictions]
```

### Layer 3: TASK DIRECTIVE (Per-Request)
```markdown
## TASK

**Objective**: [Specific goal]
**Constraints**: [Task-specific limits]
**Steps**: [Ordered process]
**Acceptance Criteria**: [What defines done]
```

### Layer 4: CONTEXT (Dynamic)
```markdown
## CONTEXT

**Project**: [Current project info]
**Environment**: [Runtime details]
**Data**: [Input data, examples]
**References**: [Relevant files, docs]
```

---

## Meta-Authority Hierarchy

When instructions conflict, defer in this order:

1. Platform/system-level safety policies
2. Tool/runtime constraints
3. Product/project constitutions (PRD, domain.json)
4. **Prompt Governance framework** (this pattern)
5. User requests and style preferences

When deferring to higher authority:
```
DEFERRAL: Higher-priority instruction overrides toolkit rule: {description}
```

---

## Escape Hatches (Required in All Prompts)

Every prompt must include these responses:

### Unknown Information
```json
{
  "status": "insufficient_data",
  "missing": ["fact1", "fact2"],
  "question": "..."
}
```

### Disallowed Request
```json
{
  "status": "refused",
  "reason": "Forbidden: {action} violates {rule}",
  "alternative": "..."
}
```

### Contradictions
```json
{
  "status": "contradiction",
  "conflicts": ["rule1 vs rule2"],
  "clarification_needed": true
}
```

---

## SemVer for Prompts

### Version Rules

| Change Type | Version Bump | Examples |
|-------------|--------------|----------|
| MAJOR | Breaking changes | Schema changes, behavior changes |
| MINOR | Additive changes | New optional fields, new modes |
| PATCH | Fixes | Clarifications, bug fixes |

### Required Metadata
```yaml
---
name: [prompt-name]
version: X.Y.Z
scope: [what this does]
changelog:
  - X.Y.Z: [Change description]
migration_notes: |
  [How to upgrade from previous version]
deprecates: [previous-version-name]
---
```

---

## Integration with APE Optimizer

Prompt-Gov validates APE-generated variations:

```
APE Process:
1. Generate 5 prompt variations
2. FOR EACH variation:
   → Run Prompt-Gov Mode B (Reviewer)
   → Check: schema valid, evals exist, escape hatches present
   → Score: validation_score
3. Composite score = performance_score × validation_score
4. Deploy best validated variation
```

**Validation Criteria**:
- Schema: Valid structured output
- Evals: 10 core + 5 edge + 5 adversarial
- Escape hatches: Present and correct
- Versioning: SemVer compliant
- Regression: Policy defined

---

## Quick Reference

**Start Mode A (Builder)**: "Create a new prompt for [purpose]"
**Start Mode B (Reviewer)**: "Review this prompt: [prompt text]"
**Start Mode C (Surgeon)**: "Fix only this issue: [issue description]"
**Start Mode D (Factory)**: "Design a pipeline for [workflow]"
**Start Mode E (Eval Designer)**: "Create evals for [prompt name]"
**Start Mode F (Incident)**: "Diagnose failure: [incident description]"

---

## Example: Review /build-feature

**Mode B Execution**:

```markdown
## Summary Verdict

NEEDS WORK - Missing schema enforcement and escape hatches

## Critical Issues (Ranked)

1. **No structured output schema** (CRITICAL)
   - Problem: Output format undefined
   - Impact: Inconsistent results, unparseable responses
   - Fix: Add JSON schema with validation

2. **Missing uncertainty policy** (HIGH)
   - Problem: No guidance for ambiguous cases
   - Impact: Hallucination risk
   - Fix: Add escape hatches section

3. **No self-check loop** (MEDIUM)
   - Problem: No verification step
   - Impact: May produce invalid output
   - Fix: Add validation before output

## Revised Prompt

[Schema-enforced version with all fixes]

## Eval Additions

[20 test cases covering gaps]

## Risk Register

1. Existing code modification without regression suite
2. Feature complexity may exceed PR scope
3. Domain compliance validation incomplete
```

---

**Select your mode and provide the prompt or request to begin.**
