# Autonomous Governance Skill

Loaded when entering autonomous mode. Defines safety rails and execution parameters.

---

## Decision Tree

```
Has tests? ─── NO ──→ INTERACTIVE ONLY
    │
   YES
    │
Clear completion criteria? ─── NO ──→ ASK FIRST
    │
   YES
    │
Restricted category? ─── YES ──→ INTERACTIVE ONLY
    │
    NO
    │
Bounded scope (<20 files)? ─── NO ──→ ASK FIRST
    │
   YES
    │
On feature branch? ─── NO ──→ CREATE BRANCH FIRST
    │
   YES
    │
✅ AUTONOMOUS APPROVED
```

---

## Restricted Paths (NEVER autonomous)

```
**/migrations/**     **/auth/**          **/payment/**
**/schema/**         **/secrets/**       **/billing/**
**/*.sql             **/*.pem            **/stripe/**
**/.env*             **/*.key            **/deploy/**
**/config.prod*      **/credentials/**   **/.github/workflows/**
```

**If task touches these: EXIT. Ask first.**

---

## Iteration Limits

| Task Size | Example | Max |
|-----------|---------|-----|
| Tiny | Single function fix | 5 |
| Small | Single file refactor | 8 |
| Medium | Multi-file, same module | 12 |
| Large | Cross-module refactor | 18 |
| XL | Major migration | 25 |

**Absolute max: 25. If needs more, break into sub-tasks.**

---

## Approved Categories

| Category | Max |
|----------|-----|
| Bug fixes with failing tests | 10 |
| Refactors with test coverage | 15 |
| Linting/formatting fixes | 5 |
| Type error resolution | 10 |
| Test coverage expansion | 15 |
| Documentation generation | 10 |

---

## Prohibited Categories (NEVER)

- Production deployments
- Database migrations
- Payment/billing code
- Auth/authorization
- Security-sensitive paths
- API contract changes
- Code without tests
- Multi-repo changes

---

## Pre-Flight Checklist

```
□ On feature branch (not main)
□ Validation command works
□ Git status clean
□ Completion criteria testable
□ Max iterations set
```

---

## Runtime Protocol

**Per iteration, check:**
- Am I making progress?
- Still solving original problem?
- Tests still passing?
- Within original scope?

**STOP immediately if:**
- Same error 3+ times
- Touching files outside scope
- Previously-passing tests fail
- Progress <50% at 70% iterations

---

## Reporting Formats

**Start:**
```
🚀 AUTONOMOUS START
Task: [description]
Scope: [files]
Completion: [criteria]
Max: [N] iterations
```

**Checkpoint (every 5):**
```
📊 Iteration [N]/[max]
Progress: [metrics]
Tests: [status]
```

**Complete:**
```
✅ COMPLETE
Iterations: [N]
Changes: [summary]
Tests: ✓ passing
```

**Stopped:**
```
⚠️ STOPPED at [N]
Reason: [why]
Rollback: git reset --hard [sha]
```

---

## Escalation

| Situation | Action |
|-----------|--------|
| Touches restricted path | STOP, ask |
| Stalled 3+ iterations | STOP, report |
| Test regression | STOP, rollback |
| >20 files needed | Ask first |
| Uncertain | STOP, ask |

**Default: When uncertain, STOP and ask.**
