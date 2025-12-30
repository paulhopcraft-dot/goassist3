---
description: Edit existing code with PRD validation
---

# PRD-Aware Edit: $ARGUMENTS

## Read PRD: /docs/PRD/*.md

Before modifying ANY behavior, verify change against PRD.

## Change Validation

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

## If Bug Fix

**Current behavior:**
- [What it does now]

**PRD-specified behavior:**
- [What PRD section says it should do]

**Evidence of mismatch:**
- [Proof current behavior violates PRD]

## If Enhancement

**PRD section:** [Must be explicit]

**Verification:**
- [ ] Feature is in PRD scope
- [ ] Not excluded in out-of-scope section
- [ ] Acceptance criteria from PRD documented

## If Refactor

**Confirm no behavior change:**
- [ ] All PRD-specified behavior preserved
- [ ] No new features introduced
- [ ] Compliance touchpoints unchanged

## If Out of Scope

**STOP. Do not proceed.**

Options:
1. Update PRD to include this change
2. File as PRD gap for product review
3. Abandon change

## Implementation

After validation:
1. Make minimal change to satisfy PRD
2. Test against PRD acceptance criteria
3. Update relevant PRD section references
4. Commit with PRD reference
