"""Pytest configuration and shared fixtures."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing settings
os.environ.update({
    "MAX_CONCURRENT_SESSIONS": "5",
    "LLM_MODEL_PATH": "/test/models/llm",
    "ASR_MODEL_PATH": "/test/models/asr",
    "TTS_ENGINE": "mock",  # Use mock TTS for testing
    "TTS_MODEL_PATH": "/test/models/tts",
    "ENVIRONMENT": "development",
    "ANIMATION_ENABLED": "false",  # Disable animation for unit tests
    "RATE_LIMIT_ENABLED": "false",  # Disable rate limiting for tests
    "CSRF_ENABLED": "false",  # Disable CSRF for tests (tested separately)
})


@pytest.fixture
def test_settings():
    """Provide test settings instance."""
    from src.config.settings import Settings
    return Settings(
        max_concurrent_sessions=5,
        llm_model_path="/test/models/llm",
        asr_model_path="/test/models/asr",
        tts_engine="mock",  # Use mock TTS for testing
        tts_model_path="/test/models/tts",
        animation_enabled=False,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide FastAPI test client."""
    from src.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def audio_clock():
    """Provide fresh audio clock for testing."""
    from src.audio.transport.audio_clock import AudioClock

    # Create a new instance for testing (bypassing singleton)
    clock = object.__new__(AudioClock)
    clock._init_clock()
    return clock
