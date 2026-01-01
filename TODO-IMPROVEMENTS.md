# goassist3 Improvement Plan

## Phase 1: Security & Reliability

- [x] **Add rate limiting** - Implement slowapi on session creation (5/min), chat (30/min), WebRTC (10/min)
- [x] **Create exception hierarchy**:
  - [x] GoAssistError (base)
  - [x] SessionError (SessionNotFoundError, SessionLimitError, SessionStateError)
  - [x] ConfigurationError (MissingConfigError, InvalidConfigError)
  - [x] ASRError (ASRConnectionError, ASRProcessingError)
  - [x] TTSError (TTSConnectionError, TTSInitializationError, TTSSynthesisError)
  - [x] AnimationError (AnimationConnectionError, AnimationInitializationError, BlendshapeError)
  - [x] LLMError (LLMConnectionError, LLMGenerationError, ContextOverflowError)
  - [x] TransportError (WebRTCError, DataChannelError)
- [x] **Add async timeouts** - LLM streaming (30s), animation callbacks (500ms per frame), context rollover (5s)
- [ ] **Refactor health endpoint registry** - Extract from hardcoded list in auth.py
- [x] **Add CSRF protection** - Double-submit cookie pattern for POST/PUT/DELETE/PATCH
- [ ] **Add input sanitization** - Sanitize TTS text input (bleach or similar)

## Phase 2: Testing & Observability

- [ ] **Add integration test: full session flow** - Audio in → response out
- [ ] **Add integration test: WebRTC pipeline** - Connection establishment
- [ ] **Add integration test: barge-in handling** - Interruption flow
- [ ] **Add load tests** - 100 concurrent sessions
- [ ] **Add latency regression tests** - Track TTFA p95
- [ ] **Pin dependencies** - Create poetry.lock or use pip-tools
- [ ] **Add OpenTelemetry** - Distributed tracing for multi-service calls
- [ ] **Add request ID propagation** - For debugging across components

## Code Quality

- [ ] **Add `from __future__ import annotations`** - Consistency with strict mypy
- [ ] **Standardize Protocol vs ABC** - Pick one pattern for interfaces
- [ ] **Refactor global state in sessions.py** - Use FastAPI dependency caching
- [ ] **Document backpressure recovery** - How to go from SESSION_REJECT → NORMAL

## Metrics to Track
- Current test count: 1170 tests
- Current coverage: 85%
- Target: ✅ 85%+ coverage achieved, <100ms p95 TTFA
