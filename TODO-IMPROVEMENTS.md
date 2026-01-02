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
- [x] **Refactor health endpoint registry** - Centralized public_paths.py for auth/CSRF exemptions
- [x] **Add CSRF protection** - Double-submit cookie pattern for POST/PUT/DELETE/PATCH
- [x] **Add input sanitization** - Sanitize TTS text input (control chars, SSML, Unicode normalization)

## Phase 2: Testing & Observability ✅ COMPLETE

- [x] **Add integration test: full session flow** - 12 tests covering E2E conversation
- [x] **Add integration test: WebRTC pipeline** - 20 tests for signaling & media transport
- [x] **Add integration test: barge-in handling** - 18 tests for TMF ≤150ms validation
- [x] **Add load tests** - 100 concurrent sessions (25+ test cases)
- [x] **Add latency regression tests** - TTFA p95 tracking (12+ test cases)
- [x] **Pin dependencies** - requirements-locked.txt with pip freeze
- [x] **Add OpenTelemetry** - src/observability/tracing.py with OTLP export
- [x] **Add request ID propagation** - src/api/middleware/request_id.py

## Code Quality

- [ ] **Add `from __future__ import annotations`** - Consistency with strict mypy
- [ ] **Standardize Protocol vs ABC** - Pick one pattern for interfaces
- [ ] **Refactor global state in sessions.py** - Use FastAPI dependency caching
- [ ] **Document backpressure recovery** - How to go from SESSION_REJECT → NORMAL

## Metrics to Track
- Current test count: 1267 tests
- Current coverage: 85%
- Target: ✅ 85%+ coverage achieved, <100ms p95 TTFA
