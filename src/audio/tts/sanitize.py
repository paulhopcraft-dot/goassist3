"""TTS Input Sanitization - Clean and validate text before synthesis.

Provides sanitization for TTS text input to prevent:
- Injection attacks (SSML, control characters)
- Excessive resource usage (length limits)
- Encoding issues (invalid UTF-8)
- Backend-specific exploits

Reference: TODO-IMPROVEMENTS.md Phase 1
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from src.observability.logging import get_logger

logger = get_logger(__name__)

# Default configuration
DEFAULT_MAX_TEXT_LENGTH = 4096  # Characters
DEFAULT_MAX_PROSODY_VALUE = 2.0  # Multiplier for speed/pitch
DEFAULT_MIN_PROSODY_VALUE = 0.5

# Allowed characters: printable ASCII + common Unicode letters/punctuation
# Control characters (0x00-0x1F, 0x7F-0x9F) are stripped except whitespace
CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')

# SSML-like tags that could be interpreted by some TTS backends
SSML_TAG_PATTERN = re.compile(r'<[^>]+>')

# Valid language codes (ISO 639-1 with optional region)
VALID_LANGUAGE_PATTERN = re.compile(r'^[a-z]{2}(-[A-Z]{2})?$')


@dataclass
class SanitizationConfig:
    """Configuration for text sanitization."""

    max_length: int = DEFAULT_MAX_TEXT_LENGTH
    strip_control_chars: bool = True
    strip_ssml_tags: bool = True
    normalize_whitespace: bool = True
    normalize_unicode: bool = True  # NFKC normalization
    max_prosody_value: float = DEFAULT_MAX_PROSODY_VALUE
    min_prosody_value: float = DEFAULT_MIN_PROSODY_VALUE
    validate_language: bool = True
    log_sanitization: bool = True


class TextSanitizationError(Exception):
    """Raised when text cannot be sanitized."""

    def __init__(self, message: str, original_text: str | None = None) -> None:
        super().__init__(message)
        self.original_text = original_text[:100] if original_text else None


def sanitize_text(
    text: str,
    config: SanitizationConfig | None = None,
) -> str:
    """Sanitize text for TTS synthesis.

    Args:
        text: Input text to sanitize
        config: Optional sanitization configuration

    Returns:
        Sanitized text safe for TTS backends

    Raises:
        TextSanitizationError: If text is invalid or cannot be sanitized

    Example:
        >>> sanitize_text("Hello <break/> world!")
        'Hello  world!'
        >>> sanitize_text("Test\\x00\\x01text")
        'Testtext'
    """
    if config is None:
        config = SanitizationConfig()

    if not isinstance(text, str):
        raise TextSanitizationError(
            f"Expected string, got {type(text).__name__}",
            str(text)[:100] if text else None,
        )

    original_length = len(text)
    sanitized = text

    # 1. Validate UTF-8 encoding (re-encode to catch issues)
    try:
        sanitized = sanitized.encode('utf-8').decode('utf-8')
    except UnicodeError as e:
        raise TextSanitizationError(f"Invalid UTF-8 encoding: {e}", text)

    # 2. Unicode normalization (NFKC: compatibility decomposition + canonical composition)
    if config.normalize_unicode:
        sanitized = unicodedata.normalize('NFKC', sanitized)

    # 3. Strip control characters (keep newlines, tabs, spaces)
    if config.strip_control_chars:
        sanitized = CONTROL_CHAR_PATTERN.sub('', sanitized)

    # 4. Strip SSML-like tags
    if config.strip_ssml_tags:
        sanitized = SSML_TAG_PATTERN.sub('', sanitized)

    # 5. Normalize whitespace (collapse multiple spaces, strip leading/trailing)
    if config.normalize_whitespace:
        # Replace multiple whitespace with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = sanitized.strip()

    # 6. Enforce length limit
    if len(sanitized) > config.max_length:
        sanitized = sanitized[:config.max_length]
        if config.log_sanitization:
            logger.warning(
                "tts_text_truncated",
                original_length=original_length,
                truncated_length=config.max_length,
            )

    # 7. Log significant changes
    if config.log_sanitization and len(sanitized) < original_length * 0.9:
        logger.debug(
            "tts_text_sanitized",
            original_length=original_length,
            sanitized_length=len(sanitized),
            reduction_percent=round((1 - len(sanitized) / original_length) * 100, 1),
        )

    return sanitized


def sanitize_prosody(
    prosody: dict[str, Any] | None,
    config: SanitizationConfig | None = None,
) -> dict[str, Any] | None:
    """Sanitize prosody parameters for TTS synthesis.

    Args:
        prosody: Prosody dictionary with speed, pitch, volume, etc.
        config: Optional sanitization configuration

    Returns:
        Sanitized prosody dictionary or None

    Example:
        >>> sanitize_prosody({"speed": 1.5, "pitch": 0.8})
        {'speed': 1.5, 'pitch': 0.8}
        >>> sanitize_prosody({"speed": 10.0})  # Clamped
        {'speed': 2.0}
    """
    if prosody is None:
        return None

    if not isinstance(prosody, dict):
        logger.warning("tts_prosody_invalid_type", type=type(prosody).__name__)
        return None

    if config is None:
        config = SanitizationConfig()

    sanitized = {}

    # Allowed prosody keys with their value constraints
    allowed_keys = {
        'speed': (config.min_prosody_value, config.max_prosody_value),
        'pitch': (config.min_prosody_value, config.max_prosody_value),
        'volume': (0.0, 2.0),  # 0 = mute, 2 = double volume
        'rate': (config.min_prosody_value, config.max_prosody_value),  # Alias for speed
    }

    for key, value in prosody.items():
        if key not in allowed_keys:
            logger.debug("tts_prosody_unknown_key", key=key)
            continue

        if not isinstance(value, (int, float)):
            logger.warning("tts_prosody_invalid_value", key=key, value_type=type(value).__name__)
            continue

        min_val, max_val = allowed_keys[key]
        clamped = max(min_val, min(max_val, float(value)))

        if clamped != value:
            logger.debug(
                "tts_prosody_clamped",
                key=key,
                original=value,
                clamped=clamped,
            )

        sanitized[key] = clamped

    return sanitized if sanitized else None


def sanitize_voice_id(
    voice_id: str | None,
    allowed_voices: list[str] | None = None,
) -> str | None:
    """Sanitize voice ID for TTS synthesis.

    Args:
        voice_id: Voice identifier
        allowed_voices: Optional whitelist of allowed voice IDs

    Returns:
        Sanitized voice ID or None

    Example:
        >>> sanitize_voice_id("en_speaker_1")
        'en_speaker_1'
        >>> sanitize_voice_id("../../../etc/passwd")
        None
    """
    if voice_id is None:
        return None

    if not isinstance(voice_id, str):
        logger.warning("tts_voice_id_invalid_type", type=type(voice_id).__name__)
        return None

    # Basic sanitization: alphanumeric, underscore, hyphen only
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', voice_id)

    if sanitized != voice_id:
        logger.warning(
            "tts_voice_id_sanitized",
            original=voice_id[:50],
            sanitized=sanitized[:50],
        )

    if not sanitized:
        return None

    # Check whitelist if provided
    if allowed_voices and sanitized not in allowed_voices:
        logger.warning(
            "tts_voice_id_not_allowed",
            voice_id=sanitized,
            allowed_count=len(allowed_voices),
        )
        return None

    return sanitized


def sanitize_language(
    language: str | None,
    allowed_languages: list[str] | None = None,
) -> str | None:
    """Sanitize language code for TTS synthesis.

    Args:
        language: Language code (e.g., "en", "en-US")
        allowed_languages: Optional whitelist of allowed language codes

    Returns:
        Sanitized language code or None

    Example:
        >>> sanitize_language("en-US")
        'en-US'
        >>> sanitize_language("english")
        None
    """
    if language is None:
        return None

    if not isinstance(language, str):
        logger.warning("tts_language_invalid_type", type=type(language).__name__)
        return None

    # Strip whitespace
    language = language.strip()

    # Validate format (ISO 639-1 with optional region)
    if not VALID_LANGUAGE_PATTERN.match(language):
        logger.warning("tts_language_invalid_format", language=language)
        return None

    # Check whitelist if provided
    if allowed_languages and language not in allowed_languages:
        logger.warning(
            "tts_language_not_allowed",
            language=language,
            allowed_count=len(allowed_languages),
        )
        return None

    return language


def sanitize_tts_request(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    prosody: dict[str, Any] | None = None,
    config: SanitizationConfig | None = None,
    allowed_voices: list[str] | None = None,
    allowed_languages: list[str] | None = None,
) -> dict[str, Any]:
    """Sanitize all TTS request parameters.

    Convenience function that sanitizes all TTS request fields.

    Args:
        text: Text to synthesize
        voice_id: Voice identifier
        language: Language code
        prosody: Prosody parameters
        config: Sanitization configuration
        allowed_voices: Whitelist of voice IDs
        allowed_languages: Whitelist of language codes

    Returns:
        Dictionary with sanitized values

    Example:
        >>> sanitize_tts_request(
        ...     text="Hello <break/> world!",
        ...     voice_id="speaker_1",
        ...     language="en-US",
        ...     prosody={"speed": 1.2},
        ... )
        {'text': 'Hello  world!', 'voice_id': 'speaker_1', 'language': 'en-US', 'prosody': {'speed': 1.2}}
    """
    return {
        'text': sanitize_text(text, config),
        'voice_id': sanitize_voice_id(voice_id, allowed_voices),
        'language': sanitize_language(language, allowed_languages),
        'prosody': sanitize_prosody(prosody, config),
    }
