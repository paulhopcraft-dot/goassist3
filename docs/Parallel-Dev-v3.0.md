# GoAssist Parallel Development Strategy v3.0

**Status:** Delivery plan (Subordinate to TMF v3.0 and PRD v3.0)  
**Version:** 3.0  
**Date:** December 22, 2025

---

## 1. Purpose

This document defines how multiple engineers/teams can build GoAssist in parallel **without** breaking:
- speech-first invariants
- latency contracts
- document authority boundaries

It is conservative by design: stable interfaces, clear ownership, and early integration gates.

---

## 2. Document Authority (must be understood by all tracks)

1) **TMF v3.0** — architecture truth (audio master clock, latency contracts, failure modes)  
2) **PRD v3.0** — product truth (user experience, features, acceptance criteria)  
3) **Implementation v3.0** — build plan (derived from TMF/PRD)  
4) **Ops/Runbook v3.0** — deployment and on-call reality  
5) This document — delivery strategy and sequencing

If a lower doc conflicts with a higher doc, the lower doc is wrong.

---

## 3. Engineering Tracks

### 3.1 Track overview

| Track | Owner | Scope | Key Deliverable |
|---|---|---|---|
| **T1 Render/Client** | Graphics | Client rendering or server render integration | Avatar mode output path |
| **T2 Animation** | ML/Realtime | Audio→blendshapes engine + heartbeat | ARKit-52 stream |
| **T3 Audio Pipeline** | Realtime | WebRTC audio in/out, packetization, barge-in | Speech-first loop |
| **T4 Control Signals (SCOS)** | Product Eng | Conversation adaptation signals (non-emotional) | Verbosity/backchannel policy |
| **T5 RAG/Tools** | Backend | Retrieval + tool calling | Grounded responses |
| **T6 Infra/Observability** | Infra/SRE | Metrics, logging, soak tooling | 24h survivability |
| **T7 Admin/UI** | Full-stack | Admin config + diagnostics | Operator control plane |

**Hard rule:** No track may introduce emotion modeling, identity training, or “persuasion systems.”

---

## 4. Directory Ownership

### 4.1 Ownership map (recommended)

| Path | Owner Track | Rules |
|---|---|---|
| `src/api/*` | T3 | Gateway interfaces only |
| `src/orchestrator/*` | T3 | State machine + cancellation |
| `src/audio/*` | T3 | Packetization, overlap, transport |
| `src/llm/*` | T3 | Shared serving + context rollover |
| `src/animation/*` | T2 | Engine adapters + heartbeat |
| `src/rag/*` | T5 | Retrieval, validator, eval harness |
| `src/admin/*` | T7 | Admin UI + auth |
| `src/observability/*` | T6 | Metrics/logging/health |
| `unreal/*` | T1 | UE project + ingest tooling |
| `deploy/*` | T6 | Docker/compose templates |

Changes across ownership boundaries require:
- a small RFC in `docs/rfcs/`
- explicit approval from both owners

---

## 5. Git Worktree Strategy (recommended)

Each track works in an isolated worktree:
- reduces merge contention
- allows parallel experimentation
- keeps main branch stable

Example worktree layout:

```
goassist-main/         # main branch
goassist-t2-animation/ # T2 branch
goassist-t3-audio/     # T3 branch
goassist-t6-infra/     # T6 branch
```

---

## 6. Phased Plan (conservative)

### Phase 0 — Foundation (Week 1)
**Goal:** lock interfaces and contracts before building features.

Deliverables:
- agree on audio packet schema, cancel schema, blendshape schema
- skeleton services that compile and expose health endpoints
- basic “echo” pipeline (ASR mocked, LLM mocked, TTS mocked)

### Phase 1 — Track Work in Parallel (Weeks 2–8)
**Goal:** build subsystems behind stable contracts.

- T3: WebRTC gateway, barge-in, packetizer, cancellation fanout
- T2: animation engine adapter + heartbeat + ARKit mapping
- T5: RAG retrieval + validator
- T6: metrics + soak harness
- T7: admin UI skeleton (feature flags, config)
- T1: client-side avatar rendering path (preferred for scale) OR server render integration

### Phase 2 — Integration (Weeks 9–12)
**Goal:** connect real components end-to-end.

- Replace mocks with real ASR/LLM/TTS/animation
- Validate TTFA and barge-in under normal load
- Run first 2h soak and fix drift

### Phase 3 — Hardening (Weeks 13–16)
**Goal:** production survivability.

- 8h soak, then 24h soak
- chaos tests (drop animation service, degrade network)
- confirm graceful degradation rules

---

## 7. Interface Contracts (v3.0 required)

### 7.1 Audio packet schema (T3)
Use the TMF-defined 20ms + 5ms overlap packet contract.

### 7.2 Cancellation schema (T3)
Cancel must propagate to LLM + TTS + audio playout + animation.

### 7.3 Blendshape schema (T2 → T1)
ARKit-52 blendshapes + heartbeat + audio timestamp alignment.

### 7.4 SCOS API (T4)
SCOS emits non-emotional control signals:
- verbosity level suggestion
- backchannel allowed/blocked
- clarification needed confidence

### 7.5 RAG API (T5)
RAG returns:
- retrieved snippets/doc IDs
- confidence scores
- optional internal citations

---

## 8. CI/CD Integration

### 8.1 Automated testing per track
- Unit tests in each module directory
- Contract tests for schemas (JSON schema validation)
- Smoke test script required for every PR

### 8.2 Pre-merge requirements
- all tests pass
- linting pass
- contract test pass
- “no forbidden scope” checklist item completed

### 8.3 Main branch protection
- required reviews from code owners
- required green CI
- required changelog note if public surface changes

---

## 9. Conflict Resolution & Communication

- Interface changes require an RFC and a versioned schema update.
- If latency contracts are threatened, T3 has veto power.
- If deploy stability is threatened, T6 has veto power.

---

## 10. Decision Template (for `docs/rfcs/`)

```
Decision: <title>

Context:
- what problem are we solving?
- what TMF/PRD constraint applies?

Options:
- option A
- option B
- option C

Decision:
- chosen option and why

Consequences:
- trade-offs and risks
- test plan
```

