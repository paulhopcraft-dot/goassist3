---
description: Build feature with PRD enforcement
---

<instructions>
Implement features with strict adherence to Product Requirements Document. For regulated systems requiring requirements traceability.
</instructions>

<arguments>$ARGUMENTS</arguments>

<prerequisite>
**MANDATORY: Read PRD First**

**PRD Location:** /docs/PRD/*.md

Read the FULL PRD before proceeding. Treat it as authoritative product contract.
</prerequisite>

<scope_validation>
**PRD Section Required:** You must specify which PRD section this implements.

Format: `/build-prd [PRD_SECTION] [FEATURE_DESCRIPTION]`

Example: `/build-prd 3.2.1 Claims submission endpoint with evidence attachment`
</scope_validation>

<implementation_rules>
**DO:**
- Only implement behavior explicitly supported by PRD
- Quote PRD section in code comments for non-obvious decisions
- Add PRD section reference to commit message
- Update features.json with PRD traceability

**DO NOT:**
- Introduce features not in PRD
- Make assumptions about unstated requirements
- Implement "nice to have" features without PRD support
- Proceed if PRD section is unclear
</implementation_rules>

<pre_flight_checklist>
Before writing code, verify:
- [ ] Read relevant PRD section(s)
- [ ] Confirmed change is in scope
- [ ] No out-of-scope violations
- [ ] Compliance touchpoints identified
- [ ] Acceptance criteria from PRD documented
</pre_flight_checklist>

<unclear_prd_protocol>
**If PRD is Unclear:**

**STOP and:**
1. Document the ambiguity
2. Flag in docs/PRD-GAPS.md
3. Ask user for clarification
4. Do NOT proceed with assumptions
</unclear_prd_protocol>

<implementation>
After PRD validation passes:

<steps>
1. Implement per PRD requirements
2. Write tests based on PRD acceptance criteria
3. Add comments citing PRD sections for key decisions
4. Update features.json:
   ```json
   {
     "id": "F00X",
     "prd_section": "3.2.1",
     "prd_requirement": "Claims submission with evidence",
     "acceptance_criteria": ["from PRD section 3.2.1"]
   }
   ```
</steps>
</implementation>

<commit_format>
```
feat(prd-3.2.1): implement claims submission endpoint

Implements PRD section 3.2.1: Claims Submission
- Evidence attachment support
- Validation per regulatory requirements
- Audit trail integration

PRD-REF: 3.2.1
```
</commit_format>

<warning>
**If you cannot find PRD support for this work:**
- Say so explicitly
- Do not invent requirements
- Ask if PRD needs updating
- Suggest `/prd-check` to verify scope
</warning>
