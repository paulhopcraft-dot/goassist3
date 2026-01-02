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

## Phase 3: Code Quality ✅ COMPLETE

- [x] **Add `from __future__ import annotations`** - 56/67 modules updated
- [x] **Standardize Protocol vs ABC** - Documented ABC as standard (4 ABC interfaces, 0 Protocol)
- [x] **Document global state pattern** - Singleton factory pattern explained in CODING-STANDARDS.md
- [x] **Document backpressure recovery** - Comprehensive guide in BACKPRESSURE-RECOVERY.md

**Deliverables:**
- docs/CODING-STANDARDS.md (comprehensive guidelines)
- docs/BACKPRESSURE-RECOVERY.md (operational playbook)
- 56 modules with future annotations
- Helper script: add_future_import.py

## Metrics to Track
- Current test count: **1337 tests** (was 1267, +70 from Phase 2)
- Current coverage: 85%
- Target: ✅ 85%+ coverage achieved
- Phase 2 additions: 50 integration + 25 load + 12 latency tests
