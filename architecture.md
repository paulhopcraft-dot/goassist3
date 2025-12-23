# GoAssist v3.0 Documentation Architecture

## Overview
This is a **documentation clarification project** for GoAssist v3.0, a speech-to-speech conversational agent with optional real-time avatar.

## Purpose
The GoAssist v3.0 documentation set underwent a RED-TEAM clarity review. This project tracks and resolves the 45 identified clarity issues without changing system design or architecture.

## Document Set Structure

### Authority Hierarchy (Highest → Lowest)
1. **TMF v3.0** — Technical Master File (architecture truth, immutable)
2. **TMF v3.0 Addendum A** — Clarifications (extends TMF without changing contracts)
3. **PRD v3.0** — Product Requirements (user experience, features)
4. **Implementation v3.0** — Engineering build plan (how to build)
5. **Parallel Dev v3.0** — Delivery strategy (how teams work in parallel)
6. **Ops Runbook v3.0** — Deployment & operations (how to run)
7. **Document Authority Map v3.0** — Meta-document defining authority rules

## Review Methodology
**Review Role:** RED-TEAM Document Reviewer (clarity auditor, non-design)

**Scope:**
- Ambiguity (unclear wording, multiple interpretations)
- Internal contradictions (conflicts within or between documents)
- Missing operational detail (insufficient specificity to implement/operate)
- Unclear ownership/authority (responsibility gaps)

**Out of Scope:**
- Design changes or alternatives
- New features or capabilities
- Architectural improvements
- Technology choices

## Issue Categories

### By Type
| Type | Count | Description |
|------|-------|-------------|
| Ambiguity | 18 | Terms or statements with multiple interpretations |
| Internal Contradictions | 4 | Conflicts within or between documents |
| Missing Operational Detail | 12 | Insufficient specificity for implementation |
| Unclear Ownership | 6 | Authority or responsibility gaps |
| Cross-Document | 5 | Issues spanning multiple documents |

### By Priority
| Priority | Count | Description |
|----------|-------|-------------|
| P0-BLOCKING | 10 | Blocks operational deployment or implementation |
| P1 | 15 | Important for clarity but not immediately blocking |
| P2 | 10 | Process or minor clarity improvements |

### By Document
| Document | Findings | Blocking |
|----------|----------|----------|
| TMF v3.0 | 11 | 6 |
| PRD v3.0 | 7 | 1 |
| Implementation v3.0 | 5 | 1 |
| Ops Runbook v3.0 | 8 | 2 |
| Parallel Dev v3.0 | 5 | 1 |
| TMF Addendum A | 2 | 0 |
| Authority Map | 2 | 0 |
| Cross-Document | 5 | 1 |

## Top 10 Blocking Issues

1. **TMF-09** — Context rollover threshold undefined
2. **TMF-05** — Barge-in measurement point ambiguous
3. **CD-02** — 24-hour soak definition inconsistent (affects 5+ docs)
4. **OPS-06** — Environment variable requirements unclear
5. **PAR-03** — Ownership boundary approval process undefined
6. **TMF-08** — TTFA percentile missing
7. **OPS-08** — Recovery procedure authority unclear
8. **TMF-10** — Latency budget overage behavior undefined
9. **TMF-11** — Animation heartbeat missing packet count
10. **CD-04** — Model substitution liability unclear

## Resolution Strategy

### Phase 1: Critical Path (P0-BLOCKING)
Resolve top 10 issues that block implementation or operations

### Phase 2: Dependency Resolution
Fix issues that block other issues (e.g., TMF-07 blocks CD-02, ADD-02)

### Phase 3: Clarity Improvements (P1)
Address remaining ambiguities and missing details

### Phase 4: Process & Standards (P2)
Standardize cross-references, process definitions, etc.

## Tracking Mechanism
All findings tracked in `features.json` with:
- Issue ID (e.g., TMF-09, CD-02)
- Priority (P0/P1/P2)
- Category (ambiguity, contradiction, missing detail, ownership)
- Document location (file, line number)
- Current problematic text
- Required change
- Acceptance criteria
- Dependencies (blocks/blocked_by)
- Pass/fail status

## Constraints

### IMMUTABLE
- TMF v3.0 architecture contracts (audio-first, latency budgets, failure modes)
- Document authority hierarchy
- System design decisions

### MUTABLE
- Wording for clarity
- Missing operational thresholds
- Cross-reference formats
- Process definitions
- Ownership assignments within authority bounds

## Success Criteria
Project complete when:
1. All 45 findings resolved (passes: true)
2. No new ambiguities introduced
3. TMF authority hierarchy preserved
4. All cross-references use standard format
5. Documents operational (engineers can implement, operators can deploy)
