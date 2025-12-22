---
description: Build feature with PRD enforcement
---

# PRD-Enforced Build: $ARGUMENTS

## MANDATORY: Read PRD First

**PRD Location:** /docs/PRD/*.md

Read the FULL PRD before proceeding. Treat it as authoritative product contract.

## Scope Validation

**PRD Section Required:** You must specify which PRD section this implements.

Format: `/build-prd [PRD_SECTION] [FEATURE_DESCRIPTION]`

Example: `/build-prd 3.2.1 Claims submission endpoint with evidence attachment`

## Implementation Rules

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

## Pre-Flight Check

Before writing code, verify:
1. [ ] Read relevant PRD section(s)
2. [ ] Confirmed change is in scope
3. [ ] No out-of-scope violations
4. [ ] Compliance touchpoints identified
5. [ ] Acceptance criteria from PRD documented

## If PRD is Unclear

**STOP and:**
1. Document the ambiguity
2. Flag in docs/PRD-GAPS.md
3. Ask user for clarification
4. Do NOT proceed with assumptions

## Implementation

After PRD validation passes:
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

## Commit Format
```
feat(prd-3.2.1): implement claims submission endpoint

Implements PRD section 3.2.1: Claims Submission
- Evidence attachment support
- Validation per regulatory requirements
- Audit trail integration

PRD-REF: 3.2.1
```

## Warning

**If you cannot find PRD support for this work:**
- Say so explicitly
- Do not invent requirements
- Ask if PRD needs updating
- Suggest `/prd-check` to verify scope
