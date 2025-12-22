# GoAssist Implementation Specification v3.0

**Status:** Engineering build plan (Derived from TMF v3.0; subordinate to TMF and PRD)  
**Version:** 3.0  
**Date:** December 22, 2025

---

## 0. Purpose

This document explains **how to build** GoAssist in a way that conforms to:
- TMF v3.0 (architecture truth)
- PRD v3.0 (product truth)

It is intentionally conservative:
- keep proven operational patterns from v2.x
- remove forbidden scope (emotion modeling, identity training, vendor fantasies)
- make multi-session scale a first-class implementation concern

---

## 1. Reference Architecture (Implementation View)

### 1.1 Services (recommended split)

1) **Gateway Service**
- WebRTC ingest/egress (audio)
- Session lifecycle (create/close)
- Optional transcripts (debug / accessibility)
- Emits metrics for TTFA, barge-in

2) **Orchestrator (Turn Manager)**
- Per-session state machine (Listening / Thinking / Speaking / Interrupted)
- Turn detection + endpointing policy
- Context rollover policy enforcement
- Tool calling coordinator
- Cancellation propagation (barge-in)

3) **ASR Service (Streaming)**
- Streaming transcription
- Partial hypotheses + timestamps
- Endpoint events to orchestrator

4) **LLM Service (Shared Model)**
- Shared weights across sessions
- Streaming token output
- Prefix caching enabled
- Fast abort on cancel

5) **TTS Service (Streaming + Interruptible)**
- Converts streamed text to streamed audio packets
- Enforces 20ms packets + 5ms overlap contract
- Hard cancel support

6) **Facial Animation Service**
- Default engine: Audio2Face (approved option)
- Fallback engine: LAM-Audio2Expression (or equivalent)
- Produces ARKit-52 blendshapes with heartbeat + slow-freeze

7) **Render / Avatar Runtime (optional)**
- Unreal + avatar ingest (UDP/Live Link)
- May run separately from inference services
- Must degrade gracefully and never block audio

### 1.2 Single-node GPU allocation (reference)
- **GPU0:** LLM serving (shared across sessions)
- **GPU1:** facial animation (Audio2Face/LAM) and/or Unreal rendering depending on deployment

> If Unreal rendering is server-side video, GPU1 will be render-dominated and concurrency will be low. For scale, prefer client-side avatar rendering driven by blendshape streams.

---

## 2. Repository Structure (v3.0)

This is an updated version of the v2.1 layout, with scope corrections.

```
goassist/
  docs/
    TMF-v3.0.md
    TMF-v3.0-Addendum-A.md
    PRD-v3.0.md
    Implementation-v3.0.md
    Parallel-Dev-v3.0.md
    Ops-Runbook-v3.0.md
    Document-Authority-Map-v3.0.md

  src/
    api/
      http_server.py
      webrtc_gateway.py
      session_router.py

    orchestrator/
      state_machine.py
      turn_detector.py
      cancellation.py
      context_rollover.py
      tool_executor.py

    audio/
      vad/
        vad_engine.py
      asr/
        streaming_asr.py
      tts/
        streaming_tts.py
      transport/
        packetizer.py
        overlap_crossfade.py

    llm/
      server.py
      client.py
      prompt/
        system_prompt.txt
        safety_rules.txt
      cache/
        prefix_cache.py
      policies/
        verbosity.py
        backpressure.py

    animation/
      engine_audio2face.py        # default engine adapter
      engine_lam.py               # fallback engine adapter
      arkit_mapping.py
      heartbeat.py
      udp_bridge.py

    rag/
      ingest.py
      retriever.py
      validator.py
      eval_harness.py

    admin/
      ui_server.py
      auth.py
      tenants.py
      feature_flags.py

    observability/
      metrics.py
      tracing.py
      logging.py
      health.py

    config/
      dev.yaml
      prod.yaml
      rate_limits.yaml
      feature_flags.yaml

  deploy/
    docker/
      Dockerfile.gateway
      Dockerfile.llm
      Dockerfile.tts
      Dockerfile.animation
    compose/
      docker-compose.dev.yml
      docker-compose.prod.yml

  unreal/
    # UE project, Live Link mappings, ingest scripts, example Blueprints

  scripts/
    download_models.sh
    smoke_test.sh
    soak_test.sh
    chaos_test.sh
```

**What changed vs v2.1:**
- Removed emotion/sentiment modules (SCOS redefined; see §6)
- Removed hybrid “cloud router” assumption
- Added explicit cancellation + context rollover modules
- Added animation heartbeat and audio overlap contract modules

---

## 3. Interface Contracts (must match TMF v3.0)

### 3.1 Audio packet schema (20ms + 5ms overlap)

All agent audio packets must include:

```json
{
  "session_id": "uuid",
  "seq": 12345,
  "t_audio_ms": 987654321,
  "duration_ms": 20,
  "overlap_ms": 5,
  "codec": "pcm16le|opus",
  "payload": "<bytes>"
}
```

Rules:
- `t_audio_ms` is monotonic and authoritative.
- overlap audio is used only for decoder cross-fade.
- overlap must not advance the clock.

### 3.2 Cancellation control (barge-in)
Cancellation must be a first-class control plane message, not a "best effort" flag.

```json
{
  "session_id": "uuid",
  "type": "CANCEL",
  "reason": "USER_BARGE_IN|USER_STOP|SYSTEM_OVERLOAD",
  "t_event_ms": 987654400
}
```

On CANCEL:
- TTS stops emitting immediately
- audio playback halts
- animation emission halts
- orchestrator returns to Listening state

### 3.3 Blendshape frame schema (ARKit-52 + heartbeat)

```json
{
  "session_id": "uuid",
  "seq": 4321,
  "t_audio_ms": 987654321,
  "fps": 30,
  "heartbeat": true,
  "blendshapes": {
    "jawOpen": 0.12,
    "mouthClose": 0.01,
    "...": 0.0
  }
}
```

Rules:
- Frames are time-aligned to `t_audio_ms`.
- If frames are missing, heartbeat + slow-freeze applies:
  - hold last pose, then ease to neutral over 150ms.

---

## 4. Per-Session State Machine (reference implementation)

### 4.1 States
- IDLE
- LISTENING
- THINKING
- SPEAKING
- INTERRUPTED (transient; immediately transitions to LISTENING)

### 4.2 Transition triggers (summary)
- IDLE → LISTENING: session created or user starts speaking
- LISTENING → THINKING: endpoint detected
- THINKING → SPEAKING: first output token available (stream begins)
- SPEAKING → INTERRUPTED: user speech detected OR explicit STOP
- SPEAKING → LISTENING: output complete (or cancelled) and floor returns to user

### 4.3 Barge-in implementation detail
- Barge-in detection must run during SPEAKING (not only while listening).
- The orchestrator emits CANCEL immediately to:
  - LLM generation (abort)
  - TTS synthesis (abort)
  - audio playout (stop)
  - animation pipeline (stop/relax)

---

## 5. LLM Serving (Mistral 7B default)

### 5.1 Serving mode
- Use a shared-model inference server with:
  - streaming tokens
  - continuous batching across sessions
  - fast abort support
  - prefix caching

### 5.2 Context management
Implement **context_rollover.py**:
- pinned prefix (system + safety + canonical persona)
- rolling window turns
- summary state block on rollover
- strict 8192 cap (reject or summarize; never silently overflow)

### 5.3 Backpressure policy (multi-session)
When overloaded:
1) drop avatar frames first (visual degrade)
2) shorten responses (verbosity policy)
3) refuse non-essential tool calls
4) as last resort, queue or reject new sessions

Audio continuity always wins.

---

## 6. SCOS (reframed) — Session Control & Optimization Signals

v2.x used SCOS for sentiment/emotion. That is **forbidden** in TMF v3.0.

In v3.0, SCOS is redefined as a lightweight per-session control system that estimates:
- user speaking duration / cadence
- interruption frequency
- uncertainty indicators (ASR confidence dips)
- conversation friction indicators (repeats, “what?”)
- engagement proxies (turn frequency, long silences)

SCOS outputs are used only to adjust:
- backchannel timing
- verbosity
- clarification strategy
- when to ask confirmation questions

SCOS must not label emotions (“angry”, “sad”, etc.) and must not attempt persuasion.

---

## 7. Facial Animation (Audio2Face default, swappable)

### 7.1 Default: Audio2Face adapter
Implement `engine_audio2face.py` as an adapter that:
- accepts audio frames aligned to the output audio clock
- produces blendshape weights mapped to ARKit-52
- emits heartbeat frames when audio is absent

**Neutral configuration required:**
- no “emotion” or style inference is used as a product feature
- outputs focus on speech articulation + natural micro motion only

### 7.2 Fallback: LAM adapter
Implement `engine_lam.py` so you can:
- A/B test outputs
- run offline validation
- preserve an escape hatch if Audio2Face becomes unavailable

### 7.3 Heartbeat + slow-freeze
Implement `heartbeat.py` to:
- detect missing frames
- hold and ease to neutral over 150ms
- never snap abruptly

---

## 8. RAG (Knowledge Grounding)

Keep the v2.1 “validator” concept, updated:
- retrieval must be auditable (store doc IDs and confidence)
- optionally attach citations to internal logs or UI
- if retrieval confidence is low:
  - the agent must hedge or refuse rather than fabricate

---

## 9. Observability (must be production-grade)

### 9.1 Metrics (minimum)
- TTFA p50/p95
- barge-in latency p50/p95
- audio packet jitter and loss
- animation lag events + yield counts
- session count + queue depth
- GPU VRAM usage + allocation failures
- restart counts / crash loops

### 9.2 Health checks
Each service exposes:
- `/healthz` (liveness)
- `/readyz` (readiness with dependencies)
- `/metrics` (Prometheus)

### 9.3 Logging
- structured JSON logs
- per-session correlation IDs
- explicit event types for:
  - CANCEL
  - rollover
  - avatar degrade
  - ASR endpoint
  - tool calls

---

## 10. Test Plan (v3.0)

### 10.1 Smoke tests
- single session talk/listen loop
- barge-in during first word and mid-utterance
- avatar mode on/off toggles

### 10.2 Load tests
- N concurrent sessions with burst patterns
- measure TTFA and cancel under burst
- enforce backpressure policy

### 10.3 Soak tests (24h)
- run continuous sessions (scripted) + idle periods
- monitor:
  - VRAM creep
  - latency drift
  - heartbeat frequency
  - crash loops

### 10.4 Chaos tests
- simulate packet loss
- kill/restart animation service
- degrade network to force jitter buffer growth
- confirm audio continues

---

## 11. Security & Data

- Tenant isolation: no cross-tenant memory or RAG leakage
- Secrets via env/secret store (never committed)
- Audio recording off by default (policy-defined)
- Access control for admin endpoints

---

## 12. Configuration (examples)

### 12.1 Minimal `prod.yaml` example (conceptual)

```yaml
llm:
  provider: local
  model: mistral-7b
  quantization: awq
  max_context_tokens: 8192
  prefix_caching: true
  vram_cap_gb: 20

audio:
  packet_ms: 20
  overlap_ms: 5
  ttfa_target_ms: 250
  barge_in_cancel_ms: 150

animation:
  enabled: true
  engine: audio2face
  fallback_engine: lam
  heartbeat: true
  slow_freeze_ms: 150
  drop_if_lag_ms: 120

rag:
  enabled: true
  validator: true

observability:
  prometheus: true
  log_level: info
```

---

## 13. Implementation Notes (conservative)

- Keep interfaces simple and explicit; avoid “magic” framework coupling.
- Treat animation and rendering as **consumers**, not dependencies.
- Prefer configuration-driven component selection.
- Preserve the escape hatch (fallback engines) to avoid vendor lock-in debt.

