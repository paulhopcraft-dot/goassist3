---
description: Edit existing code with PRD validation
---

<instructions>
Modify existing code while maintaining PRD compliance. Validates all changes against Product Requirements Document.
</instructions>

<arguments>$ARGUMENTS</arguments>

<prd_location>
**Read PRD:** /docs/PRD/*.md

Before modifying ANY behavior, verify change against PRD.
</prd_location>

<change_validation>
**What are you changing?**
- [Describe modification]

**Which PRD section governs this?**
- Section: [Number/title]
- Requirement: [Quote from PRD]

**Is this change:**
- [ ] Bug fix (behavior should match PRD but doesn't)
- [ ] Enhancement (adding PRD-specified feature)
- [ ] Refactor (no behavior change, PRD still satisfied)
- [ ] OUT OF SCOPE (not in PRD - STOP)
</change_validation>

<bug_fix_analysis>
**If Bug Fix:**

**Current behavior:**
- [What it does now]

**PRD-specified behavior:**
- [What PRD section says it should do]

**Evidence of mismatch:**
- [Proof current behavior violates PRD]
</bug_fix_analysis>

<enhancement_verification>
**If Enhancement:**

**PRD section:** [Must be explicit]

**Verification:**
- [ ] Feature is in PRD scope
- [ ] Not excluded in out-of-scope section
- [ ] Acceptance criteria from PRD documented
</enhancement_verification>

<refactor_validation>
**If Refactor:**

**Confirm no behavior change:**
- [ ] All PRD-specified behavior preserved
- [ ] No new features introduced
- [ ] Compliance touchpoints unchanged
</refactor_validation>

<out_of_scope_protocol>
**If Out of Scope:**

**STOP. Do not proceed.**

Options:
1. Update PRD to include this change
2. File as PRD gap for product review
3. Abandon change
</out_of_scope_protocol>

<implementation>
After validation:

<steps>
1. Make minimal change to satisfy PRD
2. Test against PRD acceptance criteria
3. Update relevant PRD section references
4. Commit with PRD reference
</steps>
</implementation>
