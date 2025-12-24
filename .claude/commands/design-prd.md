---
description: Design with PRD constraints
---

<instructions>
Design solutions that respect PRD boundaries. For architectural decisions in regulated systems.
</instructions>

<arguments>$ARGUMENTS</arguments>

<prd_location>
**Read PRD:** /docs/PRD/*.md

Design decisions MUST align with PRD constraints.
</prd_location>

<design_scope>
**PRD Section:** [Which section does this design implement?]

**Requirements from PRD:**
- [List requirements this design must satisfy]
</design_scope>

<prd_constraints>
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
</prd_constraints>

<design_options>
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
</design_options>

<decision_criteria>
**From PRD (non-negotiable):**
- [List must-have criteria from PRD]

**From context (optimize for):**
- [Additional criteria not in PRD]
</decision_criteria>

<recommendation>
**Chosen design:** [Which option]

**PRD justification:**
- Satisfies sections: [List]
- No violations: [Confirmed]
- Compliance verified: [Yes/No]

**Document in:**
- docs/DESIGN.md
- Reference PRD sections
- Include requirements traceability matrix
</recommendation>
