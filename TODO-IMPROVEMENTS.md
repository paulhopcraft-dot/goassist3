# goassist3 Improvement Plan

## Phase 1: Security & Reliability

- [ ] **Add rate limiting** - Implement slowapi or custom middleware on session creation
- [ ] **Create exception hierarchy**:
  - [ ] SessionError (base)
  - [ ] ConfigurationError
  - [ ] ASRError
  - [ ] TTSError
  - [ ] AnimationError
- [ ] **Add async timeouts** - LLM streaming (30s), animation callbacks (5s), context rollover
- [ ] **Refactor health endpoint registry** - Extract from hardcoded list in auth.py
- [ ] **Add CSRF protection** - For state-changing operations
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
- Current test count: 1073 tests
- Current coverage: 85.04%
- Target: ✅ 85%+ coverage achieved, <100ms p95 TTFA
