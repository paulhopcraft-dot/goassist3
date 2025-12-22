# GoAssist Document Authority Map v3.0

**Version:** 3.0  
**Date:** December 22, 2025

---

## 1. Why this exists

GoAssist previously had “all-in-one” documents (v2.x) that mixed:
- product requirements
- architecture
- implementation detail
- deployment/runbooks

As of v3.0, documentation is split into **clear authorities** so teams do not fight each other or ship contradictions.

---

## 2. Authority Order (highest → lowest)

### A. **TMF v3.0 — Technical Master File**
- **Audience:** architecture, senior engineering, infra
- **Owns:** system invariants, latency contracts, failure modes, non-goals
- **Supersedes:** everything else
- **Change policy:** major changes require new TMF major version

### B. **TMF v3.0 Addendum A — Clarifications**
- **Audience:** engineering + ops
- **Owns:** explicit implementation allowances (e.g., approved pluggable engines)
- **May not:** change TMF contracts; only clarifies

### C. **PRD v3.0 — Product Requirements**
- **Audience:** product, stakeholders, GTM, delivery
- **Owns:** user experience, supported modes, acceptance criteria, success metrics
- **May not:** name models/vendors/GPUs or contradict TMF constraints

### D. **Implementation v3.0**
- **Audience:** engineering
- **Owns:** how we build it (modules, contracts, config, test plan)
- **Must:** conform to TMF + PRD

### E. **Parallel Development v3.0**
- **Audience:** engineering leadership + contributors
- **Owns:** delivery sequencing, ownership, CI rules, integration gates
- **Must:** not introduce architecture or product scope

### F. **Ops/Runbook v3.0**
- **Audience:** infra/SRE/on-call
- **Owns:** deployment, monitoring, recovery, scaling procedures
- **Must:** operationalize TMF; must not redefine product or architecture

---

## 3. “If two docs disagree…”

- TMF beats everything.
- PRD beats implementation details.
- Implementation beats runbook for behavior; runbook beats implementation for how it is operated.
- Any conflict triggers:
  1) create an RFC
  2) resolve conflict at the highest relevant authority
  3) update downstream documents

---

## 4. What v2.1 docs become (archival map)

- v2.1 “Complete Spec” → split into PRD v3.0 + archived reference
- v2.1 “Implementation” → Implementation v3.0 (rebased)
- v2.1 “Parallel Dev” → Parallel Dev v3.0 (rebased)
- v2.1 “RunPod” → Ops/Runbook v3.0 (rebased)

---

## 5. Naming Convention (recommended)

- `TMF-v3.0.md`
- `TMF-v3.0-Addendum-A.md`
- `PRD-v3.0.md`
- `Implementation-v3.0.md`
- `Parallel-Dev-v3.0.md`
- `Ops-Runbook-v3.0.md`
- `Document-Authority-Map-v3.0.md`

