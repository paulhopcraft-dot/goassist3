# GoAssist Product Requirements Document (PRD) v3.0

**Status:** Product Definition (Subordinate to TMF v3.0)  
**Version:** 3.0  
**Date:** December 22, 2025  
**Applies to:** GoAssist Speech-to-Speech Agent with optional digital human avatar.

---

## 0. What this PRD is (and is not)

This PRD defines:
- the user experience
- the supported product modes
- functional requirements
- non-functional requirements (latency, reliability, safety)
- success metrics and acceptance criteria

This PRD does **not** define:
- model choices
- GPU choices
- vendors or hosting providers
- internal architecture diagrams

Those are defined by **TMF v3.0** and engineering implementation docs.

---

## 1. Product Summary

GoAssist is a real-time **speech-to-speech** conversational agent. It ships in two user-visible modes:

1) **Voice Mode (default):** fast, natural, interruptible conversation by voice  
2) **Avatar Mode (optional):** Voice Mode plus a real-time, human-like face that speaks in sync

The defining trait is not “intelligence,” it’s **interaction quality**:
- the agent responds quickly
- the agent can be interrupted naturally
- the system remains stable over long runtimes
- visuals never delay voice

---

## 2. Target Users and Use Cases

### 2.1 Primary users
- Customer support and service teams (receptionist, triage, FAQ, appointment setting)
- Sales / demo teams (product explanations, qualification, scripted flows with natural interruption)
- Training / onboarding (interactive instructor)
- Internal operations (voice-first assistant with knowledge base)

### 2.2 Primary environments
- Browser and mobile voice sessions
- Kiosks / in-store displays
- Streaming / demo booths
- Internal call-center style setups (headset + screen)

### 2.3 Core use cases
- Real-time Q&A with organizational knowledge
- Guided flows (qualification, troubleshooting, onboarding)
- Live “presenter” avatar for demos (Avatar Mode)

---

## 3. Product Modes

### 3.1 Voice Mode (default)
- Two-way voice conversation
- Barge-in (user interrupts naturally)
- Optional text transcript for accessibility/debugging (not required for UX)

### 3.2 Avatar Mode (optional)
Everything in Voice Mode, plus:
- Real-time facial animation aligned to the agent’s spoken audio
- Graceful degradation under lag (face relaxes; voice continues)

**Important:** Avatar Mode must never reduce Voice Mode quality. If resources are constrained, Avatar Mode degrades or disables.

---

## 4. UX Principles (Non-negotiable)

1. **Audio is the master clock.** Voice output must not wait on visuals.  
2. **Interrupts must feel human.** The agent stops speaking quickly when the user speaks.  
3. **Start talking fast.** The agent begins responding quickly, even if it continues thinking.  
4. **Stability beats cleverness.** The system must survive long runtimes without needing babysitting.  
5. **Degrade gracefully.** Under load: drop visuals, shorten responses, reduce polish—never “freeze voice.”

---

## 5. Core Interaction Model

### 5.1 State machine (user-facing)
- **Idle:** agent is ready
- **Listening:** user is speaking / agent is capturing speech
- **Thinking:** user finished; agent prepares response (brief)
- **Speaking:** agent outputs voice (and avatar if enabled)
- **Interrupted:** user begins speaking; agent stops output and returns to Listening

### 5.2 Turn-taking rules
- The system must support natural short pauses without cutting the user off.
- The system must support “backchannels” (small acknowledgements) where appropriate.
- User speech during agent speech triggers interruption behavior.

### 5.3 Barge-in
- If the user starts speaking while the agent is speaking:
  - agent audio stops quickly
  - partial thought is discarded unless safe to continue
  - agent returns to Listening immediately

---

## 6. Functional Requirements

### 6.1 Conversation & control
- Two-way speech conversation with streaming responses
- Support for clarifying questions and confirmations
- Support for “cancel / stop / hold on” patterns (voice commands)

### 6.2 Knowledge support (RAG)
- Ability to ground answers in a tenant knowledge base
- Ability to cite sources internally (for audits / QA)
- Ability to refuse or defer when knowledge is missing (no confident fabrication)

### 6.3 Tool use (optional)
- The agent may call tools (APIs) to complete tasks (e.g., lookup, ticket creation)
- Tool execution must not block voice response unnecessarily (speak while waiting when safe)

### 6.4 Admin controls (required)
- Create/edit agent profiles (role, tone, boundaries)
- Configure allowed tools and knowledge sources
- View session metrics (latency, interruptions, errors)
- Export diagnostics for incident review

### 6.5 Safety behaviors (required)
- Refuse disallowed requests
- Avoid impersonation and identity mimicry
- Maintain tenant boundaries (no cross-tenant leakage)

---

## 7. Non-Functional Requirements (Acceptance Criteria)

### 7.1 Latency & responsiveness
- **TTFA (time to first audible response):** ≤ 250ms (target; measured p50 under normal load)
- **Barge-in cancel:** ≤ 150ms (audible stop at client)
- The agent must start speaking before full response completion (streaming)

### 7.2 Reliability
- Continuous runtime target: **24 hours** without manual intervention
- Automatic recovery from transient failures (network jitter, dropped animation frames)
- If Avatar Mode fails, Voice Mode must continue.

### 7.3 Multi-session capability
- The platform must support multiple concurrent sessions per deployment.
- Capacity must scale horizontally without changing user experience semantics.

### 7.4 Privacy & data handling (baseline)
- Clear policy for audio storage (off by default unless enabled)
- Tenant data isolation
- Ability to redact or disable transcript logging

---

## 8. Observability Requirements (Product-facing)

The product must expose:
- session-level latency metrics (TTFA, barge-in)
- error and degradation events (e.g., “avatar degraded”)
- ASR quality indicators (confidence / endpoint timing)
- user interruption count and outcomes
- stability indicators (memory growth, restarts)

---

## 9. Out of Scope (v3.0)

- Training on customer identity (voice, face, personality)
- “Emotional state modeling” or persuasion tuning
- Guaranteed photorealistic rendering under all conditions
- Hard promises of a fixed concurrency number without measured load testing

---

## 10. Success Metrics

### 10.1 Experience metrics
- TTFA p50 and p95
- Interruption success rate (user speaks → agent stops correctly)
- ASR endpoint accuracy (no frequent cut-offs)
- User-rated “responsiveness” score

### 10.2 Operational metrics
- 24h soak pass rate
- Mean time between restarts
- Degradation frequency (Avatar Mode drop/relax) under normal conditions

### 10.3 Quality metrics
- Answer groundedness score (when knowledge base exists)
- Hallucination rate (QA sampling)
- Tool success rate

---

## 11. Release Definition (v3.0)

### v3.0 must ship:
- Voice Mode production-ready
- Avatar Mode (optional) with graceful degradation
- Admin controls for config + diagnostics
- Basic knowledge grounding (RAG)
- 24h soak operational readiness

### v3.x (post v3.0) candidates:
- More agent personas / templates
- Improved turn detection
- Expanded tool catalog
- Better client-side rendering options

---

## 12. Dependencies

- TMF v3.0 (architecture truth)
- Implementation v3.0 (build plan)
- Ops/Runbook v3.0 (deployment + monitoring)

---

## 13. Open Questions (tracked, not blocking)
- Which client platforms are in-scope for Avatar Mode first (web vs native)?
- What is the minimum acceptable quality bar for Avatar Mode in degraded mode?
- What is the initial tenant data retention policy?

