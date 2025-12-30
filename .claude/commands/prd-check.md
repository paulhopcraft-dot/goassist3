---
description: Verify alignment with PRD before making changes
---

# PRD Alignment Check

**Before proceeding with any work, verify alignment with the Product Requirements Document.**

## Read PRD
View the canonical PRD at: $ARGUMENTS

If no path provided, check these locations in order:
1. /docs/PRD/*.md
2. /docs/REQUIREMENTS.md
3. README.md (PRD section)

## Analysis Required

### 1. Scope Verification
**What PRD sections apply to this work?**
- [List relevant sections with numbers/titles]

**Is this change explicitly in scope?**
- YES: [Quote supporting PRD section]
- NO: [Explain what's missing from PRD]
- UNCLEAR: [What needs clarification]

### 2. Out of Scope Check
**What is explicitly OUT of scope per the PRD?**
- [List excluded items relevant to this work]

**Does this change violate any exclusions?**
- YES: [Which exclusion and why]
- NO: [Confirmed clear]

### 3. Requirements Coverage
**Which specific requirements does this satisfy?**
- Requirement ID: [e.g., REQ-3.2]
- Requirement text: [Quote from PRD]
- How this work addresses it: [Explanation]

### 4. Compliance Impact
**Does this work touch:**
- [ ] Regulated data (PII, PHI, claims data)
- [ ] Evidence chain (audit trail, provenance)
- [ ] AI/ML predictions (lifecycle, versioning)
- [ ] Legal/compliance obligations

**If YES to any, PRD sections that govern this:**
- [List with quotes]

### 5. Verification Questions
**Unanswered questions before proceeding:**
1. [What's unclear in PRD]
2. [What assumptions being made]
3. [What needs stakeholder confirmation]

## Decision

**PROCEED** if:
- Change is explicitly in PRD scope
- No exclusions violated
- All compliance touchpoints documented
- Assumptions are minimal and safe

**STOP** if:
- No PRD support found
- Violates out-of-scope exclusions
- Compliance impact unclear
- Major assumptions required

## Next Steps

If PROCEED:
- Document PRD sections in feature/task description
- Add requirements traceability to commit message
- Update features.json with PRD section references

If STOP:
- Flag for PRD update/clarification
- Document gap in docs/PRD-GAPS.md
- Escalate to product owner
