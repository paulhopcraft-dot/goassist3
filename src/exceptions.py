"""GoAssist Exception Hierarchy.

Provides structured exception classes for better error handling.

Reference: TODO-IMPROVEMENTS.md Phase 1

Hierarchy:
    GoAssistError (base)
    ├── SessionError
    │   ├── SessionNotFoundError
    │   ├── SessionLimitError
    │   └── SessionStateError
    ├── ConfigurationError
    │   ├── MissingConfigError
    │   └── InvalidConfigError
    ├── ASRError
    │   ├── ASRConnectionError
    │   └── ASRProcessingError
    ├── TTSError
    │   ├── TTSConnectionError
    │   ├── TTSInitializationError
    │   └── TTSSynthesisError
    ├── AnimationError
    │   ├── AnimationConnectionError
    │   ├── AnimationInitializationError
    │   └── BlendshapeError
    └── LLMError
        ├── LLMConnectionError
        ├── LLMGenerationError
        └── ContextOverflowError
"""

from typing import Any


class GoAssistError(Exception):
    """Base exception for all GoAssist errors.

    Attributes:
        message: Human-readable error description
        details: Additional context about the error
        recoverable: Whether the error can be recovered from
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        recoverable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


# =============================================================================
# Session Errors
# =============================================================================


class SessionError(GoAssistError):
    """Base exception for session-related errors."""

    def __init__(
        self,
        message: str,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
        recoverable: bool = False,
    ) -> None:
        details = details or {}
        if session_id:
            details["session_id"] = session_id
        super().__init__(message, details, recoverable)
        self.session_id = session_id


class SessionNotFoundError(SessionError):
    """Raised when a session cannot be found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            message=f"Session not found: {session_id}",
            session_id=session_id,
            recoverable=False,
        )


class SessionLimitError(SessionError):
    """Raised when session limit is reached."""

    def __init__(self, max_sessions: int, current_sessions: int) -> None:
        super().__init__(
            message=f"Session limit reached: {current_sessions}/{max_sessions}",
            details={
                "max_sessions": max_sessions,
                "current_sessions": current_sessions,
            },
            recoverable=True,  # Can retry when a session ends
        )


class SessionStateError(SessionError):
    """Raised for invalid session state transitions."""

    def __init__(
        self,
        message: str,
        session_id: str | None = None,
        current_state: str | None = None,
        target_state: str | None = None,
    ) -> None:
        details = {}
        if current_state:
            details["current_state"] = current_state
        if target_state:
            details["target_state"] = target_state
        super().__init__(message, session_id, details, recoverable=False)


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(GoAssistError):
    """Base exception for configuration-related errors."""

    pass


class MissingConfigError(ConfigurationError):
    """Raised when a required configuration is missing."""

    def __init__(self, config_key: str, description: str | None = None) -> None:
        message = f"Missing required configuration: {config_key}"
        if description:
            message += f" - {description}"
        super().__init__(
            message=message,
            details={"config_key": config_key},
            recoverable=False,
        )


class InvalidConfigError(ConfigurationError):
    """Raised when a configuration value is invalid."""

    def __init__(
        self,
        config_key: str,
        value: Any,
        reason: str,
    ) -> None:
        super().__init__(
            message=f"Invalid configuration for {config_key}: {reason}",
            details={
                "config_key": config_key,
                "value": str(value),
                "reason": reason,
            },
            recoverable=False,
        )


# =============================================================================
# ASR Errors
# =============================================================================


class ASRError(GoAssistError):
    """Base exception for ASR-related errors."""

    pass


class ASRConnectionError(ASRError):
    """Raised when ASR service connection fails."""

    def __init__(self, service: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to connect to ASR service {service}: {reason}",
            details={"service": service, "reason": reason},
            recoverable=True,  # Connection can be retried
        )


class ASRProcessingError(ASRError):
    """Raised when ASR processing fails."""

    def __init__(self, reason: str, audio_duration_ms: float | None = None) -> None:
        details: dict[str, Any] = {"reason": reason}
        if audio_duration_ms is not None:
            details["audio_duration_ms"] = audio_duration_ms
        super().__init__(
            message=f"ASR processing failed: {reason}",
            details=details,
            recoverable=False,
        )


# =============================================================================
# TTS Errors
# =============================================================================


class TTSError(GoAssistError):
    """Base exception for TTS-related errors."""

    pass


class TTSConnectionError(TTSError):
    """Raised when TTS service connection fails."""

    def __init__(self, backend: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to connect to TTS backend {backend}: {reason}",
            details={"backend": backend, "reason": reason},
            recoverable=True,  # Connection can be retried
        )


class TTSInitializationError(TTSError):
    """Raised when TTS engine fails to initialize."""

    def __init__(self, backend: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to initialize TTS backend {backend}: {reason}",
            details={"backend": backend, "reason": reason},
            recoverable=False,
        )


class TTSSynthesisError(TTSError):
    """Raised when TTS synthesis fails."""

    def __init__(
        self,
        reason: str,
        text_length: int | None = None,
        backend: str | None = None,
    ) -> None:
        details: dict[str, Any] = {"reason": reason}
        if text_length is not None:
            details["text_length"] = text_length
        if backend:
            details["backend"] = backend
        super().__init__(
            message=f"TTS synthesis failed: {reason}",
            details=details,
            recoverable=False,
        )


# =============================================================================
# Animation Errors
# =============================================================================


class AnimationError(GoAssistError):
    """Base exception for animation-related errors."""

    pass


class AnimationConnectionError(AnimationError):
    """Raised when animation service connection fails."""

    def __init__(self, service: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to connect to animation service {service}: {reason}",
            details={"service": service, "reason": reason},
            recoverable=True,  # Connection can be retried
        )


class AnimationInitializationError(AnimationError):
    """Raised when animation engine fails to initialize."""

    def __init__(self, engine: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to initialize animation engine {engine}: {reason}",
            details={"engine": engine, "reason": reason},
            recoverable=False,
        )


class BlendshapeError(AnimationError):
    """Raised when blendshape processing fails."""

    def __init__(self, reason: str, frame_seq: int | None = None) -> None:
        details: dict[str, Any] = {"reason": reason}
        if frame_seq is not None:
            details["frame_seq"] = frame_seq
        super().__init__(
            message=f"Blendshape processing failed: {reason}",
            details=details,
            recoverable=False,
        )


# =============================================================================
# LLM Errors
# =============================================================================


class LLMError(GoAssistError):
    """Base exception for LLM-related errors."""

    pass


class LLMConnectionError(LLMError):
    """Raised when LLM service connection fails."""

    def __init__(self, backend: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to connect to LLM backend {backend}: {reason}",
            details={"backend": backend, "reason": reason},
            recoverable=True,  # Connection can be retried
        )


class LLMGenerationError(LLMError):
    """Raised when LLM generation fails."""

    def __init__(
        self,
        reason: str,
        model: str | None = None,
        prompt_tokens: int | None = None,
    ) -> None:
        details: dict[str, Any] = {"reason": reason}
        if model:
            details["model"] = model
        if prompt_tokens is not None:
            details["prompt_tokens"] = prompt_tokens
        super().__init__(
            message=f"LLM generation failed: {reason}",
            details=details,
            recoverable=False,
        )


class ContextOverflowError(LLMError):
    """Raised when context window is exceeded."""

    def __init__(
        self,
        current_tokens: int,
        max_tokens: int,
    ) -> None:
        super().__init__(
            message=f"Context overflow: {current_tokens} tokens exceeds limit of {max_tokens}",
            details={
                "current_tokens": current_tokens,
                "max_tokens": max_tokens,
            },
            recoverable=True,  # Can trigger rollover
        )


# =============================================================================
# Transport Errors
# =============================================================================


class TransportError(GoAssistError):
    """Base exception for transport-related errors."""

    pass


class WebRTCError(TransportError):
    """Raised for WebRTC-related failures."""

    def __init__(self, reason: str, session_id: str | None = None) -> None:
        details: dict[str, Any] = {"reason": reason}
        if session_id:
            details["session_id"] = session_id
        super().__init__(
            message=f"WebRTC error: {reason}",
            details=details,
            recoverable=True,
        )


class DataChannelError(TransportError):
    """Raised when data channel operations fail."""

    def __init__(self, reason: str, channel_label: str | None = None) -> None:
        details: dict[str, Any] = {"reason": reason}
        if channel_label:
            details["channel_label"] = channel_label
        super().__init__(
            message=f"Data channel error: {reason}",
            details=details,
            recoverable=True,
        )
