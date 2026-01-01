"""GoAssist v3.0 - Speech-to-speech conversational agent."""

__version__ = "3.0.0"

# Export exception hierarchy for easy importing
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

__all__ = [
    "__version__",
    # Base
    "GoAssistError",
    # Session
    "SessionError",
    "SessionNotFoundError",
    "SessionLimitError",
    "SessionStateError",
    # Configuration
    "ConfigurationError",
    "MissingConfigError",
    "InvalidConfigError",
    # ASR
    "ASRError",
    "ASRConnectionError",
    "ASRProcessingError",
    # TTS
    "TTSError",
    "TTSConnectionError",
    "TTSInitializationError",
    "TTSSynthesisError",
    # Animation
    "AnimationError",
    "AnimationConnectionError",
    "AnimationInitializationError",
    "BlendshapeError",
    # LLM
    "LLMError",
    "LLMConnectionError",
    "LLMGenerationError",
    "ContextOverflowError",
    # Transport
    "TransportError",
    "WebRTCError",
    "DataChannelError",
]
