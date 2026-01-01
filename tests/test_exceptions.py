"""Tests for Exception Hierarchy.

Tests cover:
- GoAssistError base class
- Session exceptions
- Configuration exceptions
- ASR exceptions
- TTS exceptions
- Animation exceptions
- LLM exceptions
- Transport exceptions
"""

import pytest

from src.exceptions import (
    GoAssistError,
    SessionError,
    SessionNotFoundError,
    SessionLimitError,
    SessionStateError,
    ConfigurationError,
    MissingConfigError,
    InvalidConfigError,
    ASRError,
    ASRConnectionError,
    ASRProcessingError,
    TTSError,
    TTSConnectionError,
    TTSInitializationError,
    TTSSynthesisError,
    AnimationError,
    AnimationConnectionError,
    AnimationInitializationError,
    BlendshapeError,
    LLMError,
    LLMConnectionError,
    LLMGenerationError,
    ContextOverflowError,
    TransportError,
    WebRTCError,
    DataChannelError,
)


class TestGoAssistError:
    """Tests for GoAssistError base class."""

    def test_basic_creation(self):
        """Create basic error with message."""
        error = GoAssistError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details == {}
        assert error.recoverable is False

    def test_with_details(self):
        """Create error with details."""
        error = GoAssistError(
            "Operation failed",
            details={"operation": "test", "code": 42},
        )
        assert error.details == {"operation": "test", "code": 42}
        assert "operation" in str(error)

    def test_recoverable_flag(self):
        """Test recoverable flag."""
        error = GoAssistError("Temporary failure", recoverable=True)
        assert error.recoverable is True

    def test_to_dict(self):
        """Convert error to dictionary."""
        error = GoAssistError(
            "Test error",
            details={"key": "value"},
            recoverable=True,
        )
        result = error.to_dict()

        assert result["type"] == "GoAssistError"
        assert result["message"] == "Test error"
        assert result["details"] == {"key": "value"}
        assert result["recoverable"] is True

    def test_inheritance(self):
        """All exceptions inherit from GoAssistError."""
        assert issubclass(SessionError, GoAssistError)
        assert issubclass(ConfigurationError, GoAssistError)
        assert issubclass(ASRError, GoAssistError)
        assert issubclass(TTSError, GoAssistError)
        assert issubclass(AnimationError, GoAssistError)
        assert issubclass(LLMError, GoAssistError)
        assert issubclass(TransportError, GoAssistError)


class TestSessionErrors:
    """Tests for session-related exceptions."""

    def test_session_error_with_session_id(self):
        """SessionError includes session_id."""
        error = SessionError("Session failed", session_id="sess-123")
        assert error.session_id == "sess-123"
        assert error.details["session_id"] == "sess-123"

    def test_session_not_found_error(self):
        """SessionNotFoundError creation."""
        error = SessionNotFoundError("sess-456")
        assert "sess-456" in str(error)
        assert error.session_id == "sess-456"
        assert error.recoverable is False

    def test_session_limit_error(self):
        """SessionLimitError creation."""
        error = SessionLimitError(max_sessions=10, current_sessions=10)
        assert "10/10" in str(error)
        assert error.details["max_sessions"] == 10
        assert error.details["current_sessions"] == 10
        assert error.recoverable is True  # Can retry when session ends

    def test_session_state_error(self):
        """SessionStateError creation."""
        error = SessionStateError(
            "Invalid transition",
            session_id="sess-789",
            current_state="IDLE",
            target_state="SPEAKING",
        )
        assert error.details["current_state"] == "IDLE"
        assert error.details["target_state"] == "SPEAKING"


class TestConfigurationErrors:
    """Tests for configuration-related exceptions."""

    def test_missing_config_error(self):
        """MissingConfigError creation."""
        error = MissingConfigError("API_KEY")
        assert "API_KEY" in str(error)
        assert error.details["config_key"] == "API_KEY"

    def test_missing_config_with_description(self):
        """MissingConfigError with description."""
        error = MissingConfigError("API_KEY", "Required for authentication")
        assert "Required for authentication" in str(error)

    def test_invalid_config_error(self):
        """InvalidConfigError creation."""
        error = InvalidConfigError(
            config_key="max_sessions",
            value=-1,
            reason="Must be positive",
        )
        assert "max_sessions" in str(error)
        assert error.details["value"] == "-1"
        assert error.details["reason"] == "Must be positive"


class TestASRErrors:
    """Tests for ASR-related exceptions."""

    def test_asr_connection_error(self):
        """ASRConnectionError creation."""
        error = ASRConnectionError("Deepgram", "Connection refused")
        assert "Deepgram" in str(error)
        assert error.details["service"] == "Deepgram"
        assert error.recoverable is True

    def test_asr_processing_error(self):
        """ASRProcessingError creation."""
        error = ASRProcessingError("Invalid audio format", audio_duration_ms=5000)
        assert error.details["audio_duration_ms"] == 5000
        assert error.recoverable is False


class TestTTSErrors:
    """Tests for TTS-related exceptions."""

    def test_tts_connection_error(self):
        """TTSConnectionError creation."""
        error = TTSConnectionError("XTTS", "Server unavailable")
        assert "XTTS" in str(error)
        assert error.recoverable is True

    def test_tts_initialization_error(self):
        """TTSInitializationError creation."""
        error = TTSInitializationError("Kyutai", "Model not found")
        assert error.details["backend"] == "Kyutai"
        assert error.recoverable is False

    def test_tts_synthesis_error(self):
        """TTSSynthesisError creation."""
        error = TTSSynthesisError(
            "Synthesis timeout",
            text_length=500,
            backend="XTTS",
        )
        assert error.details["text_length"] == 500
        assert error.details["backend"] == "XTTS"


class TestAnimationErrors:
    """Tests for animation-related exceptions."""

    def test_animation_connection_error(self):
        """AnimationConnectionError creation."""
        error = AnimationConnectionError("Audio2Face", "gRPC timeout")
        assert "Audio2Face" in str(error)
        assert error.recoverable is True

    def test_animation_initialization_error(self):
        """AnimationInitializationError creation."""
        error = AnimationInitializationError("LAM", "CUDA not available")
        assert error.details["engine"] == "LAM"

    def test_blendshape_error(self):
        """BlendshapeError creation."""
        error = BlendshapeError("Invalid blendshape count", frame_seq=42)
        assert error.details["frame_seq"] == 42


class TestLLMErrors:
    """Tests for LLM-related exceptions."""

    def test_llm_connection_error(self):
        """LLMConnectionError creation."""
        error = LLMConnectionError("vLLM", "Server not responding")
        assert "vLLM" in str(error)
        assert error.recoverable is True

    def test_llm_generation_error(self):
        """LLMGenerationError creation."""
        error = LLMGenerationError(
            "Token limit exceeded",
            model="llama-3",
            prompt_tokens=8192,
        )
        assert error.details["model"] == "llama-3"
        assert error.details["prompt_tokens"] == 8192

    def test_context_overflow_error(self):
        """ContextOverflowError creation."""
        error = ContextOverflowError(current_tokens=9000, max_tokens=8192)
        assert error.details["current_tokens"] == 9000
        assert error.details["max_tokens"] == 8192
        assert error.recoverable is True  # Can trigger rollover


class TestTransportErrors:
    """Tests for transport-related exceptions."""

    def test_webrtc_error(self):
        """WebRTCError creation."""
        error = WebRTCError("ICE connection failed", session_id="sess-123")
        assert error.details["session_id"] == "sess-123"
        assert error.recoverable is True

    def test_data_channel_error(self):
        """DataChannelError creation."""
        error = DataChannelError("Channel closed", channel_label="blendshapes")
        assert error.details["channel_label"] == "blendshapes"


class TestExceptionHierarchy:
    """Tests for exception hierarchy structure."""

    def test_session_errors_inherit_from_session_error(self):
        """Session-specific errors inherit from SessionError."""
        assert issubclass(SessionNotFoundError, SessionError)
        assert issubclass(SessionLimitError, SessionError)
        assert issubclass(SessionStateError, SessionError)

    def test_config_errors_inherit_from_configuration_error(self):
        """Config-specific errors inherit from ConfigurationError."""
        assert issubclass(MissingConfigError, ConfigurationError)
        assert issubclass(InvalidConfigError, ConfigurationError)

    def test_asr_errors_inherit_from_asr_error(self):
        """ASR-specific errors inherit from ASRError."""
        assert issubclass(ASRConnectionError, ASRError)
        assert issubclass(ASRProcessingError, ASRError)

    def test_tts_errors_inherit_from_tts_error(self):
        """TTS-specific errors inherit from TTSError."""
        assert issubclass(TTSConnectionError, TTSError)
        assert issubclass(TTSInitializationError, TTSError)
        assert issubclass(TTSSynthesisError, TTSError)

    def test_animation_errors_inherit_from_animation_error(self):
        """Animation-specific errors inherit from AnimationError."""
        assert issubclass(AnimationConnectionError, AnimationError)
        assert issubclass(AnimationInitializationError, AnimationError)
        assert issubclass(BlendshapeError, AnimationError)

    def test_llm_errors_inherit_from_llm_error(self):
        """LLM-specific errors inherit from LLMError."""
        assert issubclass(LLMConnectionError, LLMError)
        assert issubclass(LLMGenerationError, LLMError)
        assert issubclass(ContextOverflowError, LLMError)

    def test_transport_errors_inherit_from_transport_error(self):
        """Transport-specific errors inherit from TransportError."""
        assert issubclass(WebRTCError, TransportError)
        assert issubclass(DataChannelError, TransportError)


class TestExceptionCatching:
    """Tests for catching exceptions by base type."""

    def test_catch_all_goassist_errors(self):
        """Can catch all errors with GoAssistError."""
        errors = [
            SessionNotFoundError("sess-1"),
            MissingConfigError("KEY"),
            ASRConnectionError("service", "reason"),
            TTSSynthesisError("reason"),
            BlendshapeError("reason"),
            LLMGenerationError("reason"),
            WebRTCError("reason"),
        ]

        for error in errors:
            with pytest.raises(GoAssistError):
                raise error

    def test_catch_session_errors(self):
        """Can catch session errors by SessionError."""
        with pytest.raises(SessionError):
            raise SessionNotFoundError("sess-1")

        with pytest.raises(SessionError):
            raise SessionLimitError(10, 10)

    def test_catch_tts_errors(self):
        """Can catch TTS errors by TTSError."""
        with pytest.raises(TTSError):
            raise TTSConnectionError("backend", "reason")

        with pytest.raises(TTSError):
            raise TTSSynthesisError("reason")


class TestExceptionImports:
    """Tests for exception imports from src package."""

    def test_import_from_src(self):
        """Can import exceptions from src package."""
        from src import (
            GoAssistError,
            SessionError,
            SessionNotFoundError,
            ConfigurationError,
            ASRError,
            TTSError,
            AnimationError,
            LLMError,
            TransportError,
        )

        # Verify they're the same classes
        from src.exceptions import GoAssistError as DirectGoAssistError
        assert GoAssistError is DirectGoAssistError
