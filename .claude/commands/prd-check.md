---
description: Verify alignment with PRD before making changes
---

<instructions>
Before proceeding with any work, verify alignment with the Product Requirements Document.
</instructions>

<prd_location>
View the canonical PRD at: $ARGUMENTS

If no path provided, check these locations in order:
1. /docs/PRD/*.md
2. /docs/REQUIREMENTS.md
3. README.md (PRD section)
</prd_location>

<analysis>
<scope_verification>
### 1. Scope Verification
**What PRD sections apply to this work?**
- [List relevant sections with numbers/titles]

**Is this change explicitly in scope?**
- YES: [Quote supporting PRD section]
- NO: [Explain what's missing from PRD]
- UNCLEAR: [What needs clarification]
</scope_verification>

<out_of_scope_check>
### 2. Out of Scope Check
**What is explicitly OUT of scope per the PRD?**
- [List excluded items relevant to this work]

**Does this change violate any exclusions?**
- YES: [Which exclusion and why]
- NO: [Confirmed clear]
</out_of_scope_check>

<requirements_coverage>
### 3. Requirements Coverage
**Which specific requirements does this satisfy?**
- Requirement ID: [e.g., REQ-3.2]
- Requirement text: [Quote from PRD]
- How this work addresses it: [Explanation]
</requirements_coverage>

<compliance_impact>
### 4. Compliance Impact
**Does this work touch:**
- [ ] Regulated data (PII, PHI, claims data)
- [ ] Evidence chain (audit trail, provenance)
- [ ] AI/ML predictions (lifecycle, versioning)
- [ ] Legal/compliance obligations

**If YES to any, PRD sections that govern this:**
- [List with quotes]
</compliance_impact>

<verification_questions>
### 5. Verification Questions
**Unanswered questions before proceeding:**
1. [What's unclear in PRD]
2. [What assumptions being made]
3. [What needs stakeholder confirmation]
</verification_questions>
</analysis>

<decision>
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
</decision>

<next_steps>
If PROCEED:
- Document PRD sections in feature/task description
- Add requirements traceability to commit message
- Update features.json with PRD section references

If STOP:
- Flag for PRD update/clarification
- Document gap in docs/PRD-GAPS.md
- Escalate to product owner
</next_steps>
