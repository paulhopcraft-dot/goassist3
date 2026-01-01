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
  - **Behavior** = code-level concerns: error handling, state transitions, API responses, retry logic
  - **Operation** = human/infra concerns: deployment steps, monitoring setup, manual recovery, scaling procedures
  - **Decision rule:** If it requires code changes → Implementation owns it. If it requires operator action → Runbook owns it.
- Any conflict triggers:
  1) create an RFC in `docs/rfcs/` using `TEMPLATE.md`
  2) resolve conflict at the highest relevant authority
  3) update downstream documents

**RFC process details:**
- **Owner assignment:** Discoverer creates RFC, assigns to lowest common authority owner
- **Template:** Use `docs/rfcs/TEMPLATE.md` (created in PAR-03 resolution)
- **Authority determination:** Follow hierarchy in section 2 (TMF → PRD → Implementation → Runbook)
- **Approval timeout:** 3 business days; escalate to engineering lead if no response
- **Dispute escalation:** Engineering lead decides within 2 business days

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

---

## 6. Cross-Reference Format (standard)

When referencing other documents, use this format:

**Standard:** `[Document] v[Version] section [Number].[Number] ([Name])`

**Examples:**
- TMF v3.0 section 7.3 (Extended Soak)
- PRD v3.0 section 4.1 (Voice Mode)
- Implementation v3.0 section 9 (Observability)

This format is robust against section renumbering (includes both number and name) and clearly identifies version.

