# Technical Master File (TMF) v3.0 — GoAssist Speech-to-Speech Digital Human

**Status:** Canonical Architecture (Production-Stable)  
**Version:** 3.0  
**Date:** December 22, 2025  
**Scope:** Speech-to-speech conversational agent with optional real-time avatar (face).  
**Primary objective:** Predictable, low-latency speech interaction where **audio is the master clock**.

---

## 0. Executive Summary

TMF v3.0 defines the **architecture truth** for GoAssist. It is intentionally conservative:
- **Speech-first:** voice output is never blocked by rendering, animation, or UI.
- **Low-latency contracts:** TTFA ≤ **250ms**, barge-in cancel ≤ **150ms**.
- **24-hour survivability:** explicit failure behaviors and soak assumptions are defined.
- **Commercial reality:** only components with commercially viable licensing are permitted.

This TMF is written to be engineer-trustworthy. No fictional SDKs. No hand-wavy performance claims.

---

## 1. Hard Constraints (Non-Negotiable)

### 1.1 Speech-first invariants
- **Audio is authoritative.** All other modalities follow audio timestamps.
- **Visuals must never block audio.** Under contention, visuals degrade first.
- **Barge-in is a first-class feature.** User speech cancels agent speech fast and deterministically.

### 1.2 Latency contracts
- **Audio chunk size:** ≤ 20ms per packet
- **Audio overlap:** 5ms sliding overlap (for decoder cross-fade)
- **TTFA (time-to-first-audio):** ≤ 250ms p95 (steady-state operational target, not "demo mode"). p50 and p95 should both be tracked; the contract is satisfied when p95 ≤ 250ms under normal load.
- **Barge-in cancel:** ≤ 150ms from user speech detection to halted agent playback
- **Animation latency target:** < 25ms (best-effort; may be dropped under load)
- **Animation yield rule:** if animation lag > 120ms, animation yields (drops/relaxes), audio continues.

### 1.3 Single-node reference hardware
- **Reference node:** 2× RTX 4090 (24GB each)
- **Per-GPU hard working cap:** 20GB VRAM (leave headroom for fragmentation, drivers, spikes)

> Note: This TMF is not locked to a single GPU SKU forever. It defines *contracts*. The reference hardware is the current baseline for a predictable production build.

---

## 2. System Architecture (v3.0)

### 2.1 High-level pipeline

**User audio in** → VAD/turn detection → streaming ASR → dialogue state → LLM streaming text → streaming TTS → **agent audio out**  
In parallel: **agent audio out** → facial animation engine → ARKit-52 blendshapes → UE ingest → render / playout

### 2.2 Authority & timing
- The **audio output timeline** is the master.
- Every emitted audio packet carries:
  - monotonic timestamp (audio clock)
  - sequence number
  - duration (20ms)
- Animation frames must reference (or be derived from) the same audio clock.

---

## 3. Core Components (Reference Build)

This section describes the reference build configuration. Implementations may substitute components **only if** they preserve the contracts in Section 1.

### 3.1 LLM (shared across sessions)
- **Reference model:** Mistral 7B (open-weights, commercial-friendly)
- **Serving:** vLLM (streaming)
- **Quantization:** 4-bit (AWQ/GPTQ class)
- **Context limit:** 8192 tokens (hard cap)
- **Optimization:** prefix caching + context rollover policy (see 3.2)

> Rationale: Mistral 7B is the best “tokens/sec per VRAM” class model for multi-session speech-first serving. It supports high concurrency and predictable latency under batching.

### 3.2 Context rollover + prefix caching (required)
Problem: fixed context windows create latency spikes when history is rebuilt.

**Policy:**
- Maintain a **Pinned Prefix** (never evicted):
  - system prompt + safety rules
  - canonical persona/role definition
  - the minimal “session grounding” turns
- Maintain a **Rolling Window** for active turns.
- When context reaches 7500 tokens (93.75% of the 8192 hard cap), the orchestrator triggers summarization:
  - summarize older turns into a compact **Session State Block**
  - keep pinned prefix intact
  - continue without full context rebuild spikes
  - If summarization fails or exceeds 5 seconds, reject the new turn with an error indicating context limit reached
- Enable prefix caching so pinned prefix reuse is cheap across turns.

### 3.3 ASR (streaming)
- Must support streaming partial results (no “sentence-final only” ASR).
- Must emit word/segment timestamps sufficient for barge-in timing.
- Licensing must permit commercial use.

> ASR model choice is an implementation decision, but streaming behavior is mandatory.

### 3.4 TTS (streaming + interruptible)
- Must support streaming synthesis (audio can start before full text completion).
- Must support hard stop/cancel without long tail buffering.
- Licensing must permit commercial use.

> TTS engine choice is an implementation decision; only behavior is locked here.

### 3.5 Facial animation (audio-driven, pluggable)
- Engine consumes the same audio stream that is emitted to the user (or a time-aligned copy).
- Produces **ARKit-52** compatible blendshapes at a stable cadence (e.g., 30–60Hz).
- Must be low-latency and must degrade gracefully under lag.

**Default engine (implementation):** NVIDIA Audio2Face (approved; see Addendum A).  
**Fallback engine (implementation):** LAM-Audio2Expression (Apache-2.0) or equivalent.

### 3.6 Unreal avatar render + ingest
- Unreal Engine 5.7 + MetaHuman
- Ingest via Live Link / UDP (JSON payloads)
- Sync rules:
  - Audio authoritative
  - Animation drops/relaxes if lag >120ms
  - Playout delay bounded 40–90ms

### 3.7 Transport & streaming
- Audio transport must support low jitter (WebRTC recommended).
- Video streaming (Pixel Streaming / WebRTC) is optional and is subject to GPU encoder limits.
- For scale (many concurrent agents), prefer **client-side rendering** using blendshape streams over a data channel.

---

## 4. Streaming Contracts (v3.0)

### 4.1 Audio packet contract
- Packet duration: 20ms
- Overlap: 5ms (last 5ms repeated in next packet)
- Receiver performs cross-fade using overlap.
- Overlap must **not** advance the audio clock.

### 4.2 Barge-in contract
- Trigger: user speech detection (server-side VAD/turn detector emits barge-in event)
- Action: stop TTS generation + stop audio packet emission + stop animation emission
- Deadline: ≤150ms from server VAD detection event to client audible stop
  - Measured end-to-end: server detection → client audio output halts
  - Budget includes: server processing, network propagation, client buffer drain
  - Testing: log server VAD event timestamp; measure client-side audio output stop

### 4.3 Animation heartbeat + slow-freeze
Animation frames are expected at 30-60Hz (per section 3.1). If animation frames are missing:
1. Hold last valid blendshape frame.
2. If more than 100ms pass without a valid frame (approximately 3 frames at 30fps or 6 frames at 60fps), trigger slow-freeze: ease to neutral over 150ms.
3. Never snap to neutral instantly.

> **Implementation note:** Use a monotonic timer, not frame count, to detect missing frames. This ensures consistent behavior regardless of actual animation cadence.

---

## 5. Multi-Session (Scale Within a Node)

### 5.1 Definition
A “session” is an independent conversational state machine with:
- its own VAD/turn detection
- its own ASR stream
- its own TTS stream
- its own animation stream
- shared LLM weights (single or replicated instances) with scheduler-based batching

### 5.2 Requirements
- Shared model serving must preserve:
  - streaming token output
  - fast cancellation (barge-in)
  - fair scheduling across sessions
- Backpressure must be explicit:
  - if overloaded, degrade visuals first
  - then degrade response length/verbosity (product policy)
  - audio continuity always preserved

### 5.3 Capacity planning note
Exact session counts depend on:
- average turn length
- concurrency burst patterns
- context sizes
- TTS/ASR GPU/CPU placement
This TMF does not claim a single universal number; it defines behavior under load.

---

## 6. End-to-End Latency Budget (Hard Target ≤ 250ms)

| Stage | Component | Budget (ms) | Cumulative |
|---|---|---:|---:|
| Ingestion | VAD / endpoint detection | 15 | 15 |
| Reasoning | LLM (streaming first token) | 160 | 175 |
| Animation | Audio→blendshapes | 20 | 195 |
| Packaging | Serialization + dispatch | 5 | 200 |
| Network | WebRTC/SFU transit | 40 | 240 |
| Buffer | Client jitter buffer | 10 | **250** |

Notes:
- This budget represents ideal-case (p50) allocation. Actual p95 latency may exceed individual component budgets while still meeting the overall 250ms p95 contract.
- Network budget is an operating target, not guaranteed.
- Under worse network, audio remains continuous; visuals yield first.
- Track both p50 and p95 metrics; section 1.2 defines the p95 contract, this table provides p50 baseline for capacity planning.

### 6.1 Overage behavior
When any component exceeds its budget:
1. **Log degradation event** with component name, actual latency, and budget.
2. **Continue processing** — never fail a turn due to latency overage alone.
3. **Apply degradation order** (per section 1.1): animation yields first, then verbosity, audio never yields.
4. **Emit metrics**: `ttfa_overage_count{component}`, `ttfa_actual_ms{component}`.

**Hard timeout policy:**
- If cumulative latency exceeds 500ms before first audio byte, log a `turn_timeout` event and reset the turn state.
- The client receives a brief acknowledgment tone or silence; no partial response is emitted.

---

## 7. Failure-Mode Matrix (2h / 8h / 24h)

### 7.1 0–2 hours (warm runtime)
**Risks:** buffer growth, logging overhead, minor latency drift  
**Signals:** TTFA creep, jitter buffer expansion  
**Mitigations:** fixed-size ring buffers, bounded logs, periodic metrics snapshots

### 7.2 2–8 hours (sustained runtime)
**Risks:** VRAM allocator churn, memory fragmentation, cache eviction spikes  
**Signals:** occasional TTFA spikes, VRAM sawtooth, more animation yield events  
**Mitigations:** pre-allocation pools, stable shapes, prefix caching + rollover enforcement, heartbeat slow-freeze

### 7.3 8–24 hours (extended soak)

**Definition:** The 24-hour extended soak is 24 hours of mixed-load operation with a 30% active duty cycle:
- **Active periods (30%):** Concurrent voice sessions at expected node capacity, with typical conversation patterns (user turns, agent responses, natural pauses)
- **Idle periods (70%):** System ready and accepting connections, no active sessions
- **Pass criteria:** No manual intervention required, all latency contracts maintained (TTFA p95 ≤ 250ms), no OOM events, no deadlocks

> All documents referencing "24h soak" inherit this definition unless explicitly overridden.

**Risks:** clock drift (audio vs render), rare deadlocks, thermal throttling
**Signals:** increased heartbeat relaxations, more frequent animation yields, sustained GPU clock drop
**Mitigations:** audio-clock authority resync, animation-only state reset allowed, degraded-mode policies

### 7.4 Always-on risks
- **Network jitter/packet loss:** mitigated by 5ms overlap + cross-fade
- **Animation packet loss:** mitigated by heartbeat + slow-freeze
- **GPU throttling:** treat as degraded mode; protect audio first

---

## 8. Explicit Non-Goals (v3.0)

- No identity training or user voice/face cloning from customer data
- No emotional state modeling or persuasion layer
- No proprietary “ACE-style” licensing dependencies as architectural requirements
- No requirement that visuals always be present (visuals are optional and degradable)
- No promises of a specific concurrency number without measured load testing

---

## 9. Change Control

- TMF changes only when constraints change.
- Major architectural changes require a new TMF major version.
- Clarifications that do not change contracts may be issued as addenda.

---

## 10. Related Documents (v3.0)
- PRD v3.0 — Product Requirements (subordinate to TMF)
- Implementation v3.0 — Engineering plan (derived from TMF)
- Parallel Dev v3.0 — Delivery plan (derived from TMF)
- Ops/Runbook v3.0 — Deployment and operations (derived from TMF)
- **Addendum A (Clarifications)** — approved pluggable engines (Audio2Face, etc.)

