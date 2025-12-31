"""Application Settings - Environment-based configuration.

Uses Pydantic Settings for validation and type coercion.
Reference: Ops-Runbook-v3.0.md Section 6.1

Required variables fail startup if missing.
Conditional variables are required only when their parent feature is enabled.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.constants import TMF


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API bind host")
    api_port: int = Field(default=8081, ge=1024, le=65535, description="API port")
    log_level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment name"
    )

    # Authentication
    api_key: str | None = Field(
        default=None,
        description="API key for authentication (required in production)",
    )
    api_key_header: str = Field(
        default="X-API-Key",
        description="Header name for API key",
    )
    auth_enabled: bool = Field(
        default=True,
        description="Enable API authentication (auto-disabled in development if no key)",
    )

    # Session Configuration
    max_concurrent_sessions: int = Field(
        default=10, ge=1, le=100, description="Maximum concurrent sessions (GPU-dependent)"
    )
    session_idle_timeout_s: int = Field(
        default=TMF.SESSION_IDLE_TIMEOUT_S,
        ge=60,
        le=3600,
        description="Session idle timeout in seconds",
    )

    # LLM Configuration
    llm_engine: Literal["mock", "vllm"] = Field(
        default="vllm", description="LLM backend (mock for testing, vllm for production)"
    )
    llm_model_path: str = Field(
        default="models/llm", description="Path to LLM model weights"
    )
    llm_max_context_tokens: int = Field(
        default=TMF.LLM_MAX_CONTEXT_TOKENS,
        ge=1024,
        le=8192,
        description="Maximum context tokens (per TMF v3.0)",
    )
    llm_prefix_caching: bool = Field(default=True, description="Enable prefix caching")
    llm_vram_cap_gb: int = Field(
        default=20, ge=8, le=80, description="VRAM cap in GB (leave 4GB headroom)"
    )
    llm_base_url: str = Field(
        default="http://localhost:8000/v1", description="vLLM API base URL"
    )

    # ASR Configuration
    asr_model_path: str = Field(
        default="models/asr", description="Path to ASR model"
    )
    vad_engine: Literal["silero", "webrtc"] = Field(
        default="silero", description="VAD engine selection"
    )

    # Deepgram (optional, for cloud ASR)
    deepgram_api_key: str | None = Field(
        default=None, description="Deepgram API key for cloud ASR"
    )

    # TTS Configuration
    tts_engine: Literal["mock", "xtts-v2", "kyutai"] = Field(
        default="xtts-v2", description="Primary TTS backend (xtts-v2, kyutai, mock)"
    )
    tts_model_path: str = Field(
        default="models/tts", description="Path to TTS model"
    )
    audio_packet_ms: int = Field(
        default=TMF.AUDIO_PACKET_DURATION_MS,
        ge=10,
        le=40,
        description="Audio packet duration (per TMF v3.0)",
    )
    audio_overlap_ms: int = Field(
        default=TMF.AUDIO_OVERLAP_MS,
        ge=0,
        le=20,
        description="Audio overlap for cross-fade",
    )
    tts_fallback_to_mock: bool = Field(
        default=True,
        description="Fallback to mock TTS if primary backend fails",
    )

    # XTTS-v2 Configuration (when tts_engine="xtts-v2")
    xtts_server_url: str = Field(
        default="http://localhost:8020",
        description="XTTS-v2 server HTTP URL",
    )

    # Kyutai TTS Configuration (when tts_engine="kyutai")
    kyutai_enabled: bool = Field(
        default=False,
        description="Enable Kyutai TTS backend (OPTIONAL, disabled by default)",
    )
    kyutai_tts_url: str = Field(
        default="ws://localhost:8080/tts",
        description="Kyutai TTS WebSocket server URL",
    )
    kyutai_voice_id: str = Field(
        default="default",
        description="Voice ID from Kyutai repository",
    )
    kyutai_sample_rate: int = Field(
        default=24000,
        ge=16000,
        le=48000,
        description="Kyutai TTS sample rate (24kHz default)",
    )

    # Animation Configuration
    animation_enabled: bool = Field(default=True, description="Enable avatar animation")
    animation_engine: Literal["audio2face", "lam"] | None = Field(
        default="audio2face", description="Animation engine (required if animation_enabled)"
    )
    animation_fallback: Literal["lam", "none"] = Field(
        default="lam", description="Fallback animation engine"
    )
    animation_drop_if_lag_ms: int = Field(
        default=TMF.ANIMATION_YIELD_LAG_MS,
        ge=50,
        le=200,
        description="Yield animation if lag exceeds (per TMF v3.0)",
    )
    animation_slow_freeze_ms: int = Field(
        default=TMF.ANIMATION_SLOW_FREEZE_MS,
        ge=100,
        le=300,
        description="Slow-freeze ease duration (per TMF v3.0)",
    )

    # Audio2Face Configuration
    audio2face_grpc_host: str = Field(
        default="localhost", description="Audio2Face gRPC host"
    )
    audio2face_grpc_port: int = Field(
        default=50051, description="Audio2Face gRPC port"
    )

    # WebRTC Configuration
    webrtc_stun_server: str = Field(
        default="stun:stun.l.google.com:19302", description="STUN server URI"
    )
    webrtc_turn_server: str | None = Field(
        default=None, description="TURN server URI"
    )
    webrtc_turn_username: str | None = Field(
        default=None, description="TURN username"
    )
    webrtc_turn_password: str | None = Field(
        default=None, description="TURN password"
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/goassist",
        description="PostgreSQL connection URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )

    # Observability
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9464, description="Prometheus metrics port")

    # Alerting Thresholds (from Ops-Runbook-v3.0.md)
    alert_crash_loop_threshold: int = Field(
        default=3, description="Crash count per hour to trigger alert"
    )

    @field_validator("animation_engine", mode="before")
    @classmethod
    def validate_animation_engine(cls, v: str | None, info) -> str | None:
        """Require animation_engine if animation_enabled is True."""
        # Note: This runs before the model is fully populated
        # Full validation happens in model_validator
        return v

    @field_validator("webrtc_turn_username", "webrtc_turn_password", mode="before")
    @classmethod
    def validate_turn_credentials(cls, v: str | None, info) -> str | None:
        """TURN credentials are validated together after model creation."""
        return v

    def model_post_init(self, __context) -> None:
        """Validate conditional requirements after model creation."""
        # Validate animation engine requirement
        if self.animation_enabled and self.animation_engine is None:
            raise ValueError(
                "animation_engine is required when animation_enabled=true"
            )

        # Validate TURN credentials
        if self.webrtc_turn_server:
            if not self.webrtc_turn_username or not self.webrtc_turn_password:
                raise ValueError(
                    "webrtc_turn_username and webrtc_turn_password are required "
                    "when webrtc_turn_server is set"
                )

        # Validate API key in production
        if self.environment == "production" and self.auth_enabled and not self.api_key:
            raise ValueError(
                "api_key is required when auth_enabled=true in production environment"
            )

    # Property aliases for backward compatibility
    @property
    def turn_url(self) -> str | None:
        """Alias for webrtc_turn_server."""
        return self.webrtc_turn_server

    @property
    def turn_username(self) -> str | None:
        """Alias for webrtc_turn_username."""
        return self.webrtc_turn_username

    @property
    def turn_credential(self) -> str | None:
        """Alias for webrtc_turn_password."""
        return self.webrtc_turn_password


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
