# GoAssist Coding Standards

## Type Annotations

### Future Annotations
**Status**: ✅ **ENFORCED**

All Python modules must include:
```python
from __future__ import annotations
```

**Location**: After module docstring, before other imports

**Benefits**:
- Forward references without string quotes
- Better readability: `def foo() -> Bar:` instead of `def foo() -> "Bar":`
- Deferred evaluation (performance improvement)
- Preparation for Python 3.14+ strict typing

**Example**:
```python
"""Module docstring."""

from __future__ import annotations

import asyncio
from typing import Optional
```

---

## Interface Patterns

### ABC vs Protocol
**Decision**: **Use `ABC` (Abstract Base Classes)**
**Status**: ✅ **ENFORCED**

**Rationale**:
- Explicit inheritance makes interfaces discoverable
- Runtime type checking with `isinstance()`
- Better IDE support and autocomplete
- Clear contract enforcement

**When to use ABC**:
- ✅ Plugin interfaces (TTS, ASR, Animation engines)
- ✅ Component base classes with shared behavior
- ✅ When you need `@abstractmethod` enforcement

**When NOT to use Protocol**:
- ❌ Don't use `typing.Protocol` for structural subtyping
- ❌ Our codebase uses nominal typing (ABC), not structural

**Current Usage**:
- `src/audio/tts/base.py`: `TTSEngine(ABC)`
- `src/audio/asr/base.py`: `ASREngine(ABC)`
- `src/animation/base.py`: `AnimationEngine(ABC)`
- Total: 4 ABC-based interfaces, 0 Protocol-based

**Example**:
```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        """Stream audio chunks for given text."""
        pass

class XTTSBackend(TTSEngine):
    """XTTS implementation."""

    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        # Implementation
        yield b"audio data"
```

---

## Async Patterns

### Context Variables for Request Scoping
Use `contextvars.ContextVar` for request-scoped data:

```python
from contextvars import ContextVar

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)

def get_request_id() -> str | None:
    return _request_id_ctx.get()
```

### Dependency Injection (FastAPI)

#### Singleton Factory Pattern (Current Standard)
**Status**: ✅ **ACCEPTED**

Our API routes use a **lazy singleton factory pattern** for shared resources:

```python
# Singleton factories (in src/api/routes/sessions.py)
_session_manager: SessionManager | None = None

def get_session_manager() -> SessionManager:
    """Get global session manager (lazy singleton)."""
    global _session_manager
    if _session_manager is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _session_manager = SessionManager(max_sessions=settings.max_concurrent_sessions)
    return _session_manager

# Route usage - direct call
@router.post("/sessions")
async def create_session(...):
    manager = get_session_manager()  # Lazy singleton
    session = await manager.create_session(...)
    return response
```

**Why This Pattern**:
- ✅ Thread-safe in async context
- ✅ Lazy initialization (only creates on first use)
- ✅ Testable (can mock `get_session_manager`)
- ✅ Explicit resource sharing (singleton per process)
- ✅ No repeated instantiation overhead

**Alternative**: FastAPI `Depends()`
```python
# Could also use dependency injection:
@router.post("/sessions")
async def create_session(
    manager: SessionManager = Depends(get_session_manager)
):
    session = await manager.create_session(...)
```

Both patterns are acceptable. The direct call is slightly more explicit about singleton behavior.

**When to Use Each**:
- **Singleton Factory** (current): Shared resources (SessionManager, WebRTCGateway, LLMClient)
- **Depends()**: Per-request resources, overridable dependencies, testability

**Anti-Pattern** (Avoid):
```python
# ❌ DON'T: Eager global instantiation
session_manager = SessionManager()  # Created at import time!

@router.post("/sessions")
async def create_session():
    session = await session_manager.create()  # Hard to test/mock
```

---

## Error Handling

### Exception Hierarchy
Use the structured exception hierarchy in `src/exceptions.py`:

```
GoAssistError (base)
├── SessionError
│   ├── SessionNotFoundError
│   ├── SessionLimitError
│   └── SessionStateError
├── ConfigurationError
├── ASRError
├── TTSError
├── AnimationError
├── LLMError
└── TransportError
```

**Example**:
```python
from src.exceptions import SessionNotFoundError

def get_session(session_id: str) -> Session:
    if session_id not in sessions:
        raise SessionNotFoundError(f"Session {session_id} not found")
    return sessions[session_id]
```

---

## Naming Conventions

### Files and Modules
- **Lowercase with underscores**: `audio_clock.py`, `turn_detector.py`
- **Exception**: `TTSManager.py` (legacy, allowed for backwards compatibility)

### Classes
- **PascalCase**: `SessionManager`, `AudioClock`, `TTSEngine`

### Functions and Variables
- **snake_case**: `get_session()`, `session_id`, `is_speaking`

### Constants
- **UPPER_SNAKE_CASE**: `MAX_SESSIONS`, `DEFAULT_TIMEOUT`
- **Dataclass constants**: `TMF.TTFA_P95_MS` (namespaced under class)

### Private Members
- **Single underscore prefix**: `_internal_state`, `_process_audio()`
- Not enforced, but signals "internal use only"

---

## Documentation

### Docstrings
Required for:
- ✅ All public modules
- ✅ All public classes
- ✅ All public functions/methods

**Format**: Google-style or NumPy-style (be consistent within a file)

**Example**:
```python
def calculate_ttfa(start_ms: int, end_ms: int) -> float:
    """Calculate Time-to-First-Audio latency.

    Args:
        start_ms: Request start timestamp in milliseconds
        end_ms: First audio chunk timestamp in milliseconds

    Returns:
        TTFA latency in milliseconds

    Raises:
        ValueError: If end_ms < start_ms
    """
    if end_ms < start_ms:
        raise ValueError("end_ms must be >= start_ms")
    return end_ms - start_ms
```

### Type Hints
**Required**: All function signatures must have type hints

```python
# ✅ GOOD
def process_audio(data: bytes, timestamp_ms: int) -> bool:
    pass

# ❌ BAD
def process_audio(data, timestamp_ms):
    pass
```

---

## Testing

### File Naming
- `test_<module>.py` for unit tests
- `test_integration_<feature>.py` for integration tests
- `test_load_<scenario>.py` for load tests

### Test Organization
```python
class TestFeatureName:
    """Group related tests."""

    def test_success_case(self):
        """Test description."""
        pass

    def test_error_case(self):
        """Test error handling."""
        pass
```

---

## Imports

### Order
1. Future annotations (FIRST)
2. Standard library
3. Third-party packages
4. Local imports

**Example**:
```python
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from fastapi import APIRouter
from pydantic import BaseModel

from src.config.settings import get_settings
from src.exceptions import SessionError
```

### Import Style
- **Absolute imports**: Prefer `from src.module import Class` over relative imports
- **Avoid wildcards**: Never use `from module import *`
- **Group related imports**: Multiple imports from same module on one line is OK

---

## Version
**Document Version**: 1.0
**Last Updated**: 2026-01-02
**Applies to**: GoAssist v3.0+
