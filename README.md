# GoAssist v3.0 Documentation Clarification

**Status:** Active Documentation Review
**Version:** 3.0
**Last Updated:** 2024-12-22

## What This Is

This project tracks and resolves **45 clarity issues** identified in the GoAssist v3.0 documentation set through RED-TEAM document review.

**GoAssist** is a speech-to-speech conversational agent with optional real-time digital human avatar. This repository contains the documentation clarification effort, NOT the implementation code.

## Documentation Set

The v3.0 documentation consists of 7 documents organized by authority:

| Document | Authority | Purpose |
|----------|-----------|---------|
| [TMF v3.0](docs/TMF-v3.0.md) | Highest | Technical architecture truth |
| [TMF Addendum A](docs/TMF-v3.0-Addendum-A.md) | - | TMF clarifications |
| [PRD v3.0](docs/PRD-v3.0.md) | - | Product requirements |
| [Implementation v3.0](docs/Implementation-v3.0.md) | - | Engineering build plan |
| [Parallel Dev v3.0](docs/Parallel-Dev-v3.0.md) | - | Delivery strategy |
| [Ops Runbook v3.0](docs/Ops-Runbook-v3.0.md) | - | Deployment & operations |
| [Document Authority Map](docs/Document-Authority-Map-v3.0.md) | Meta | Authority hierarchy rules |

## Review Findings

**Total Issues:** 45

### By Category
- **Ambiguity:** 18 issues (unclear wording, multiple interpretations)
- **Internal Contradictions:** 4 issues (conflicts within/between docs)
- **Missing Operational Detail:** 12 issues (insufficient specificity)
- **Unclear Ownership:** 6 issues (authority/responsibility gaps)
- **Cross-Document:** 5 issues (spanning multiple docs)

### By Priority
- **P0-BLOCKING:** 10 issues (block deployment/implementation)
- **P1:** 15 issues (important clarity)
- **P2:** 10 issues (process/minor improvements)

## Top 10 Blocking Issues

1. **TMF-09** — Context rollover threshold undefined ("approaching 8192")
2. **TMF-05** — Barge-in measurement point ambiguous (server vs client)
3. **CD-02** — 24-hour soak definition inconsistent across 5+ documents
4. **OPS-06** — Environment variable requirements unclear (required vs optional)
5. **PAR-03** — Ownership boundary approval process undefined
6. **TMF-08** — TTFA percentile missing (p50? p95? p99?)
7. **OPS-08** — Recovery procedure authority unclear (who executes?)
8. **TMF-10** — Latency budget overage behavior undefined
9. **TMF-11** — Animation heartbeat missing packet count threshold
10. **CD-04** — Model substitution liability unclear

See [full review](https://github.com/user/repo/plans/quizzical-nibbling-pixel.md) for details.

## Project Structure

```
goassist3/
├── docs/                          # Official v3.0 documentation
│   ├── TMF-v3.0.md
│   ├── TMF-v3.0-Addendum-A.md
│   ├── PRD-v3.0.md
│   ├── Implementation-v3.0.md
│   ├── Parallel-Dev-v3.0.md
│   ├── Ops-Runbook-v3.0.md
│   └── Document-Authority-Map-v3.0.md
├── features.json                  # All 45 findings tracked
├── architecture.md                # Documentation structure & strategy
├── claude-progress.txt            # Session log
└── README.md                      # This file
```

## Tracking System

All findings tracked in `features.json` with:
- Issue ID (e.g., TMF-09, CD-02)
- Priority, category, document location
- Current problematic text
- Required change
- Acceptance criteria
- Dependencies (blocks/blocked_by)
- Pass/fail status

### Check Status

```bash
# Count resolved vs pending
grep -c '"passes": true' features.json
grep -c '"passes": false' features.json

# List blocking issues
grep -A5 'P0-BLOCKING' features.json | grep '"id"'
```

## Resolution Workflow

### Phase 1: Critical Path (P0-BLOCKING)
Resolve top 10 blocking issues

### Phase 2: Dependency Resolution
Fix issues with blockers (TMF-07 → CD-02 → ADD-02, etc.)

### Phase 3: Clarity Improvements (P1)
Address remaining ambiguities and missing details

### Phase 4: Standards (P2)
Standardize cross-references, process definitions

## Constraints

### IMMUTABLE (Cannot Change)
- TMF v3.0 architecture contracts
- Document authority hierarchy
- System design decisions

### MUTABLE (Clarifications Only)
- Wording for clarity
- Missing operational thresholds
- Cross-reference formats
- Process definitions

## Using Claude Code Toolkit

This project uses Claude Code skills for tracking:

```bash
# Check current status
/status

# Continue working on next item
/continue

# Review current work
/review

# Add new finding (if discovered)
/add-feature
```

## Contributing

When resolving findings:
1. Update the relevant document in `docs/`
2. Mark finding as `"passes": true` in `features.json`
3. Verify acceptance criteria met
4. Check for downstream impacts
5. Commit with message: `fix: [ISSUE-ID] brief description`

## Questions?

- **What is GoAssist?** Speech-to-speech agent with optional avatar (see PRD v3.0)
- **Why document review?** Ensure clarity before implementation begins
- **Who decides resolutions?** Follow document authority: TMF > PRD > Implementation > Ops
- **Can I change TMF?** Only to clarify existing contracts, not change them

## Current Status

- **Completed:** 0/45
- **In Progress:** 0/45
- **Blocked:** 2/45 (ADD-02, IMP-04)
- **Next:** TMF-09 (context rollover threshold)
