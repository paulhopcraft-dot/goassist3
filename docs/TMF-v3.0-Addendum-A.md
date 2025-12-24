# TMF v3.0 — Addendum A (Clarifications)

**Applies to:** TMF v3.0 — GoAssist Speech-to-Speech Digital Human  
**Version:** 3.0-A  
**Date:** December 22, 2025  
**Purpose:** Clarify implementation allowances without changing TMF v3.0 contracts.

---

## A1. Pluggable Engine Policy (LLM / ASR / TTS / Animation)

TMF v3.0 defines behavioral contracts. Implementations may substitute engines **only if**:
- latency contracts remain satisfied (TTFA, barge-in, chunking)
- licensing is commercially viable
- audio remains the authoritative clock
- failures degrade safely (audio first, visuals yield)

Substitution must not require changes to:
- the session state machine semantics
- the audio clocking scheme
- the cancellation/barged-in control plane

---

## A2. Reference LLM Clarification

**Reference build LLM:** Mistral 7B (open-weights, commercial-friendly)

This is a *reference selection*, not a constitutional requirement.

Allowed substitutions include other open-weights models **only** if they can be served with:
- streaming token output
- fast cancellation
- bounded VRAM use on reference hardware (or a clearly documented new hardware baseline)

---

## A3. Facial Animation Engine Clarification (Audio2Face)

### A3.1 Approved default
**NVIDIA Audio2Face** is approved as a **default implementation option** for audio-driven facial animation.

### A3.2 Requirements for using Audio2Face
When Audio2Face is used:
- outputs must be mapped to **ARKit-52** compatible blendshapes
- the engine must not introduce upstream coupling (LLM or ASR must not depend on it)
- engine failure must not block or delay audio output
- animation must follow the heartbeat + slow-freeze policy

### A3.3 Explicit prohibitions
Using Audio2Face must **not** introduce:
- emotional inference or “emotion state” tracking
- persuasion or psychological state modeling
- identity training or user voice/face cloning from customer data

If Audio2Face includes expressiveness controls, the default must be **neutral** (speech articulation only).

### A3.4 Swap-out guarantee
The system must support replacing Audio2Face with any other compliant audio→blendshape model without changing:
- the audio transport contract
- the avatar ingest contract (ARKit-52 + timestamps)
- the barge-in/cancellation contract

---

## A4. TTS Clarification

TMF v3.0 intentionally does not lock a TTS engine.

A TTS engine is considered compliant if it supports:
- streaming audio emission (start speaking early)
- hard cancel within the barge-in contract
- commercially viable licensing

---

## A5. Serving Runtime Clarification (vLLM / alternatives)

TMF v3.0 names **vLLM** as the reference serving runtime.

Alternative serving stacks are permitted if they provide:
- equivalent streaming
- equivalent cancel/abort semantics
- stable long-run behavior (24h soak as defined in TMF v3.0 section 7.3)
- no hidden buffering that breaks TTFA or barge-in targets

This addendum does not recommend switching runtimes by default. It only permits it.

