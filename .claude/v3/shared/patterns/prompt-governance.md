# Prompt Governance Pattern

**Version**: 2.1.0 (from Immortal Toolkit Prompt)
**Pattern Type**: Production Prompt Engineering Framework
**Source**: Prompt Governance Kernel v2.1

---

## Overview

Prompt Governance treats **prompts as production artifacts** - constrained, testable, versioned, and resilient to model swaps. Not creative writing, but **control systems** with measurable reliability.

**Key Insight**: Prompts control downstream models/agents. Poor prompts = unreliable systems. Production-grade prompts need the same rigor as production code.

---

## Core Principles

### Prompts Are Control Systems

**Good Prompt Checklist**:
- ✅ Specifies role + ownership + boundaries
- ✅ Enforces validated output schema
- ✅ Defines failure modes + uncertainty policy
- ✅ Includes self-check + repair loop
- ✅ Ships with evals (core + edge + adversarial)
- ✅ Avoids bloat via modular layering

**Bad Prompt**:
```
"You are a helpful assistant. Build the feature carefully and make sure it works well."
```
→ Vague, untestable, no schema, no failure handling

**Good Prompt**:
```
Role: Feature implementation specialist
Scope: TypeScript features in /src
Forbidden: Modifying config files without approval

Output Schema:
{
  "files_created": ["path1", "path2"],
  "tests_passing": boolean,
  "coverage_pct": number
}

Failure Policy:
- If build fails, emit {"status": "build_failed", "error": "..."}
- If tests fail, emit {"status": "tests_failed", "failures": [...]}

Self-Check:
1. Run tests
2. Validate coverage >= 85%
3. If invalid, retry once
4. If still invalid, emit structured failure
```
→ Testable, bounded, fails gracefully

---

## Meta-Authority Hierarchy

**Priority Order** (highest to lowest):
1. Platform/system-level safety policies
2. Tool/runtime constraints (required formats)
3. Product/project constitutions (PRD, domain.json)
4. **Prompt Governance framework** (this pattern)
5. User requests and style preferences

**Deferral Rule**:
When higher authority overrides governance rule, must state explicitly:
```
DEFERRAL: Higher-priority instruction overrides toolkit rule: {description}
```

Never fabricate tool results, citations, or access.

---

## Layered Architecture

**All prompts must be layered**, not monolithic blobs:

### Layer 1: CONSTITUTION (Stable)
- Governance rules
- Safety boundaries
- Refusal policies
- Uncertainty handling
- Format requirements
- Tool permissions
- Escalation rules

**Example**:
```markdown
## CONSTITUTION

**Allowed**:
- Read/write TypeScript files in /src
- Run npm test, npm build
- Update features.json

**Forbidden**:
- Modify package.json without approval
- Delete existing tests
- Commit failing code

**Uncertainty Policy**:
- Missing requirement → Ask user
- Ambiguous spec → Proceed with labeled assumption
- Complex dependency → Request clarification

**Output Format**: JSON only, schema-validated
```

### Layer 2: ROLE (Semi-Stable)
- Identity and ownership
- Scope boundaries
- Decision rights
- Forbidden actions

**Example**:
```markdown
## ROLE

**Identity**: Feature implementation specialist for revenue domain
**Scope**: TypeScript features implementing PRD requirements
**Decision Rights**:
- Choose implementation approach (within SOLID principles)
- Select test framework
- Refactor existing code for feature integration

**Forbidden**:
- Change domain.json compliance rules
- Skip PRD validation
- Deploy without tests
```

### Layer 3: TASK DIRECTIVE (Per-Request)
- Specific objective
- Constraints
- Steps
- Acceptance criteria

**Example**:
```markdown
## TASK

**Objective**: Implement OQE scoring algorithm per PRD section 2.3

**Constraints**:
- Use existing DimensionScores interface
- Maintain weights: labor 30%, software 20%, replaceability 25%, moat 15%, reachability 10%
- Return decision: "go" (>=75), "hold" (50-74), "kill" (<50)

**Steps**:
1. Read PRD section 2.3
2. Write tests for scoring logic
3. Implement calculateOQEScore function
4. Verify tests pass + coverage >= 85%

**Acceptance**:
- All tests passing
- Coverage >= 85%
- PRD section 2.3 requirements met
```

### Layer 4: CONTEXT (Dynamic)
- User data
- Examples
- Environment details
- Runtime information

**Example**:
```markdown
## CONTEXT

**Project**: govertical (revenue domain, SOX/GAAP compliance)
**Environment**: TypeScript 5.9, vitest testing, better-sqlite3 DB
**PRD Location**: docs/PRD_v1.md
**Domain Config**: .claude/domain.json

**Existing Interfaces**:
```typescript
interface DimensionScores {
  labor_intensity: number;
  software_underspend: number;
  // ...
}
```

**Relevant Tests**: src/db/repositories/verticals.test.ts (lines 149-276)
```

---

## Six Operating Modes

### Mode A: PROMPT BUILDER
**When**: Creating new prompts from scratch
**Output**: Complete prompt pack with evals

**Required Sections**:
- Mode declaration
- Assumptions (or "None")
- Prompt (copy/paste ready)
- Usage notes
- Evals (core + edge + adversarial)
- Risk register
- Open questions

### Mode B: PROMPT REVIEWER
**When**: Auditing existing prompts for quality
**Output**: Issues + revised prompt + new evals

**Required Sections**:
- Summary verdict
- Critical issues (ranked)
- Non-critical issues
- Revised prompt
- Eval additions
- Risk register

### Mode C: PROMPT SURGEON
**When**: Minimal fixes only (patch, not rewrite)
**Output**: Targeted fixes with minimal disruption

**Required Sections**:
- Targeted fixes only
- Patched prompt
- Minimal evals (5+ cases)
- Risks introduced

### Mode D: PROMPT FACTORY (Pipeline)
**When**: Complex multi-stage workflows
**Output**: Router → Specialist → Verifier pipeline

**Required Sections**:
- Pipeline overview
- Shared contract (schemas, failure propagation)
- Stage 1: Router prompt
- Stage 2: Specialist prompt(s)
- Stage 3: Verifier prompt
- Pipeline evals (per-stage + end-to-end)

### Mode E: EVAL DESIGNER
**When**: Building test suites for prompts
**Output**: Comprehensive eval pack

**Required Sections**:
- Eval objectives
- Test suite (10 core, 5 edge, 5 adversarial)
- Scoring rubric
- Regression policy

### Mode F: INCIDENT RESPONSE
**When**: Production prompt failed, need diagnosis
**Output**: Root cause + fix + regression prevention

**Required Sections**:
- Incident summary
- Root cause hypotheses (ranked)
- Repro steps
- Fix plan
- New evals to prevent regression
- Rollback/mitigation

---

## Output Control: Schema + Validation

### Enforce Structured Output

**Pattern**:
```
1. Generate output
2. Validate against schema
3. If invalid, repair once
4. If still invalid, emit structured failure
```

**Example Schema Enforcement**:
```json
{
  "status": "success" | "failure",
  "result": {
    "files_created": ["string"],
    "tests_passing": boolean,
    "coverage_pct": number
  },
  "validation": {
    "schema_valid": boolean,
    "constraints_checked": ["constraint1: pass", "constraint2: pass"],
    "risks": ["risk1", "risk2"]
  }
}
```

**Failure Response** (structured, not prose):
```json
{
  "status": "failure",
  "error_type": "schema_validation_failed",
  "details": "coverage_pct must be number, got undefined",
  "retry_count": 1,
  "next_action": "emit_failure"
}
```

---

## Escape Hatches (Mandatory)

Every prompt must instruct downstream model to:
- ✅ Say "I don't know" when facts missing
- ✅ Ask clarifying questions for key dependencies
- ✅ Refuse disallowed requests explicitly
- ✅ Flag contradictions instead of averaging

**No silent hallucination.**

**Example**:
```markdown
## ESCAPE HATCHES

**Unknown Information**:
If you don't know a fact required for the task, respond:
{"status": "insufficient_data", "missing": ["fact1", "fact2"], "question": "..."}

**Disallowed Request**:
If user requests forbidden action, respond:
{"status": "refused", "reason": "Forbidden: {action} violates {rule}", "alternative": "..."}

**Contradictions**:
If instructions contradict, respond:
{"status": "contradiction", "conflicts": ["rule1 vs rule2"], "clarification_needed": true}
```

---

## Evals: The Moat

### Minimum Eval Pack

**Structure**:
- **10 core cases** - Happy path, standard usage
- **5 edge cases** - Boundaries, nulls, empty, max values
- **5 adversarial cases** - Malicious, confusing, contradictory

**Each Case Includes**:
- Input
- Expected properties (not just "the answer")
- Scoring rubric (pass/fail or partial credit)
- Common pitfalls

**Example Eval**:
```json
{
  "case_id": "core-1",
  "type": "core",
  "input": {
    "feature_request": "Add email validation",
    "prd_section": "3.2"
  },
  "expected_properties": {
    "files_created": ["src/utils/validateEmail.ts", "src/utils/validateEmail.test.ts"],
    "tests_passing": true,
    "coverage_pct": ">= 85",
    "prd_compliant": true
  },
  "scoring": {
    "pass_criteria": "All properties met",
    "partial_credit": {
      "tests_passing_only": 0.5,
      "files_created_only": 0.3
    }
  },
  "common_pitfalls": [
    "Missing edge case tests (empty string, null)",
    "Not validating against PRD requirements"
  ]
}
```

### Regression Policy

**Track**:
- Failures that must never return once fixed
- Drift indicators (format errors, refusals, hallucinations)
- Schema violations

**Example**:
```json
{
  "regression_rules": [
    {
      "id": "REG-001",
      "description": "Must never skip test generation",
      "fixed_in_version": "2.1.0",
      "test_case": "core-3",
      "alert_if_fails": true
    },
    {
      "id": "REG-002",
      "description": "Must never output invalid JSON",
      "fixed_in_version": "1.5.0",
      "validation": "schema_valid === true",
      "alert_if_fails": true
    }
  ]
}
```

---

## Versioning (SemVer for Prompts)

### Version Rules

**MAJOR** (breaking):
- Behavior changes
- Schema changes
- New required fields
- Different refusal/uncertainty behavior

**MINOR** (additive):
- New optional capabilities
- New optional fields
- New modes or sections

**PATCH** (fixes):
- Clarifications
- Bug fixes
- Tightening wording without behavior breakage

### Version Metadata

**Required in every prompt**:
```markdown
---
name: build-feature
version: 2.1.0
scope: TypeScript feature implementation
changelog:
  - 2.1.0: Added SOX/GAAP compliance validation (MINOR)
  - 2.0.0: Changed output schema to JSON (MAJOR)
  - 1.5.1: Fixed edge case in test generation (PATCH)
migration_notes: |
  From v1.x: Output now requires JSON schema.
  Update consumers to parse JSON instead of text.
deprecates: build-feature-v1
---
```

---

## Integration with APE

**Prompt-Gov validates APE variations**:

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

**Example**:
```
APE Variation 3: 88% performance
Prompt-Gov Validation:
  ✓ Schema: valid JSON
  ✓ Evals: 10 core, 5 edge, 5 adversarial
  ✓ Escape hatches: present
  ✓ Versioning: SemVer compliant
  ✗ Missing: regression policy
  → Validation score: 0.9

Composite: 88% × 0.9 = 79.2 (adjusted down for missing regression policy)
```

---

## Debug / Telemetry

**Two Outputs**:
1. **USER_OUTPUT** - Clean, schema-compliant
2. **DEBUG_OUTPUT** - Optional, structured, toggleable

**Debug OFF by default**. When enabled:

```json
{
  "user_output": {
    "status": "success",
    "files_created": ["src/feature.ts"],
    "tests_passing": true
  },
  "debug_output": {
    "assumptions": ["Test framework is vitest", "Coverage target is 85%"],
    "constraints_checked": [
      {"constraint": "coverage >= 85%", "result": "pass"},
      {"constraint": "tests passing", "result": "pass"}
    ],
    "schema_validation": {"valid": true},
    "refusals": [],
    "risks": [
      "Existing code modified without full regression suite",
      "Feature complexity may require integration tests",
      "SOX compliance not verified (revenue domain)"
    ]
  }
}
```

**Debug must NEVER include**:
- Hidden system instructions
- Private policies
- Secrets or credentials
- Long chain-of-thought narratives

---

## Toolkit Integration

### When to Use Prompt-Gov

**Building Toolkit Commands**:
- Creating new `/command`
- Updating existing commands for reliability
- Designing prompt pipelines

**Quality Gates**:
- Before deploying APE-optimized variations
- After command failures in production
- During command version upgrades

**Eval Development**:
- Building test suites for critical commands
- Regression testing after model upgrades
- A/B testing command variations

### Example: Review `/build-feature`

```
Mode: B (Prompt Reviewer)

Input: Current /build-feature command prompt

Output:
- Summary verdict: "Lacks schema enforcement and escape hatches"
- Critical issues:
  1. No structured output schema (HIGH)
  2. Missing uncertainty policy (HIGH)
  3. No self-check loop (MEDIUM)
- Revised prompt: [schema-enforced version]
- Eval additions: [20 test cases]
- Risk register: [3 identified risks]
```

---

## Examples from Our Toolkit

### Before Prompt-Gov

```markdown
# Build Feature Command

Build the requested feature following these steps:
1. Read PRD
2. Write tests
3. Implement
4. Verify
```

**Problems**:
- No output schema
- No failure handling
- No evals
- Vague steps

### After Prompt-Gov (Mode A: Builder)

```markdown
---
name: build-feature
version: 3.0.0
scope: TypeScript feature implementation with PRD compliance
---

## CONSTITUTION

**Allowed**: Read/write /src, run tests, update features.json
**Forbidden**: Modify package.json, delete tests, skip PRD validation
**Uncertainty**: Ask user if requirement ambiguous
**Output**: JSON schema (validated)

## ROLE

**Identity**: Feature implementation specialist
**Scope**: TypeScript features per PRD
**Decision Rights**: Choose implementation approach within SOLID
**Forbidden**: Skip tests, ignore domain compliance

## TASK TEMPLATE

**Objective**: Implement feature {feature_id} per PRD section {section}

**Steps**:
1. Read PRD section {section}
2. Write tests (RED)
3. Implement (GREEN)
4. Refactor + verify coverage >= 85% (REFACTOR)
5. Self-check output schema
6. Update features.json

**Output Schema**:
```json
{
  "status": "success" | "failure",
  "feature_id": "string",
  "files_created": ["string"],
  "tests_passing": boolean,
  "coverage_pct": number,
  "prd_compliant": boolean,
  "validation": {
    "schema_valid": boolean,
    "constraints_met": ["string"]
  }
}
```

**Escape Hatches**:
- Unknown requirement → {"status": "insufficient_data", "missing": [...]}
- Forbidden action → {"status": "refused", "reason": "..."}
- Test failure → {"status": "tests_failed", "failures": [...]}

## EVALS

[10 core + 5 edge + 5 adversarial test cases with rubrics]

## RISK REGISTER

1. Existing code modification without full regression suite
2. Feature complexity may exceed single PR scope
3. Domain compliance validation may be incomplete
```

**Result**: Testable, bounded, versioned, resilient.

---

## References

- **Source**: Immortal Toolkit Prompt v2.1
- **Our Implementation**: `.claude/skills/prompt-gov/SKILL.md`
- **Related Patterns**: `ape.md`, `meta-prompting.md`
- **Integration**: APE optimizer validation layer

---

**Created**: 2025-12-27
**Pattern Library**: claude-code-toolkit v3.3
**Status**: Foundation for production-grade prompt engineering
