---
description: Design with PRD constraints
---

# PRD-Constrained Design: $ARGUMENTS

## Read PRD: /docs/PRD/*.md

Design decisions MUST align with PRD constraints.

## Design Scope

**PRD Section:** [Which section does this design implement?]

**Requirements from PRD:**
- [List requirements this design must satisfy]

## PRD Constraints

Extract from PRD:

**Functional Requirements:**
- [What it must do per PRD]

**Non-Functional Requirements:**
- Performance: [From PRD]
- Security: [From PRD]
- Compliance: [From PRD]
- Scalability: [From PRD]

**Explicit Exclusions:**
- [What PRD says NOT to build]

## Design Options

For each option, verify PRD alignment:

**Option A:**
- Description: [Design approach]
- PRD support: [Which sections support this]
- PRD violations: [Any conflicts with PRD]
- Compliance: [Satisfies PRD regulatory requirements?]

**Option B:**
- Description: [Design approach]
- PRD support: [Which sections support this]
- PRD violations: [Any conflicts with PRD]
- Compliance: [Satisfies PRD regulatory requirements?]

## Decision Criteria

**From PRD (non-negotiable):**
- [List must-have criteria from PRD]

**From context (optimize for):**
- [Additional criteria not in PRD]

## Recommendation

**Chosen design:** [Which option]

**PRD justification:**
- Satisfies sections: [List]
- No violations: [Confirmed]
- Compliance verified: [Yes/No]

**Document in:**
- docs/DESIGN.md
- Reference PRD sections
- Include requirements traceability matrix
