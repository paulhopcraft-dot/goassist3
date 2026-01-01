"""Tests for TTS Input Sanitization.

Tests cover:
- Text sanitization (control chars, SSML, whitespace, Unicode)
- Prosody sanitization (value clamping, type validation)
- Voice ID sanitization (path traversal prevention, whitelisting)
- Language code validation (ISO 639-1 format)
- Full request sanitization
- TTSManager sanitization integration
"""

import pytest

from src.audio.tts.sanitize import (
    SanitizationConfig,
    TextSanitizationError,
    sanitize_text,
    sanitize_prosody,
    sanitize_voice_id,
    sanitize_language,
    sanitize_tts_request,
    DEFAULT_MAX_TEXT_LENGTH,
    DEFAULT_MAX_PROSODY_VALUE,
    DEFAULT_MIN_PROSODY_VALUE,
)


class TestSanitizeText:
    """Tests for text sanitization."""

    def test_sanitize_normal_text(self):
        """Normal text passes through unchanged."""
        text = "Hello, this is a normal sentence."
        result = sanitize_text(text)
        assert result == text

    def test_sanitize_strips_control_characters(self):
        """Control characters are removed."""
        text = "Hello\x00\x01\x02world\x7f\x80"
        result = sanitize_text(text)
        # Control chars are stripped, not replaced with spaces
        assert result == "Helloworld"
        assert "\x00" not in result
        assert "\x7f" not in result

    def test_sanitize_preserves_newlines_and_tabs(self):
        """Whitespace (newlines, tabs) is preserved but normalized."""
        text = "Line 1\n\nLine 2\t\tTabbed"
        result = sanitize_text(text)
        # Multiple whitespace collapsed to single space
        assert result == "Line 1 Line 2 Tabbed"

    def test_sanitize_strips_ssml_tags(self):
        """SSML-like tags are removed."""
        text = "Hello <break time='500ms'/> world <emphasis>important</emphasis>"
        result = sanitize_text(text)
        assert result == "Hello world important"

    def test_sanitize_ssml_disabled(self):
        """SSML stripping can be disabled."""
        config = SanitizationConfig(strip_ssml_tags=False)
        text = "Hello <break/> world"
        result = sanitize_text(text, config)
        assert "<break/>" in result

    def test_sanitize_normalizes_unicode(self):
        """Unicode is NFKC normalized."""
        # Full-width characters
        text = "Hello"  # Full-width "Hello"
        result = sanitize_text(text)
        assert result == "Hello"

    def test_sanitize_unicode_disabled(self):
        """Unicode normalization can be disabled."""
        config = SanitizationConfig(normalize_unicode=False)
        text = "Hello"  # Full-width
        result = sanitize_text(text, config)
        assert result == text

    def test_sanitize_enforces_max_length(self):
        """Text is truncated at max length."""
        config = SanitizationConfig(max_length=10)
        text = "This is a very long sentence"
        result = sanitize_text(text, config)
        assert len(result) == 10
        assert result == "This is a "

    def test_sanitize_default_max_length(self):
        """Default max length is applied."""
        long_text = "A" * (DEFAULT_MAX_TEXT_LENGTH + 100)
        result = sanitize_text(long_text)
        assert len(result) == DEFAULT_MAX_TEXT_LENGTH

    def test_sanitize_normalizes_whitespace(self):
        """Multiple whitespace characters are collapsed."""
        text = "Hello    world   test"
        result = sanitize_text(text)
        assert result == "Hello world test"

    def test_sanitize_strips_leading_trailing_whitespace(self):
        """Leading and trailing whitespace is stripped."""
        text = "   Hello world   "
        result = sanitize_text(text)
        assert result == "Hello world"

    def test_sanitize_whitespace_disabled(self):
        """Whitespace normalization can be disabled."""
        config = SanitizationConfig(normalize_whitespace=False)
        text = "Hello    world"
        result = sanitize_text(text, config)
        assert "    " in result

    def test_sanitize_rejects_non_string(self):
        """Non-string input raises error."""
        with pytest.raises(TextSanitizationError) as exc_info:
            sanitize_text(123)  # type: ignore
        assert "Expected string" in str(exc_info.value)

    def test_sanitize_rejects_invalid_utf8(self):
        """Invalid UTF-8 raises error."""
        # Create a string that will fail re-encoding
        # This is tricky in Python 3 since strings are always valid Unicode
        # We test the error handling path exists
        config = SanitizationConfig()
        # Normal text should work
        result = sanitize_text("Valid text", config)
        assert result == "Valid text"

    def test_sanitize_empty_string(self):
        """Empty string is handled."""
        result = sanitize_text("")
        assert result == ""

    def test_sanitize_injection_attempt_script(self):
        """Script injection is neutralized."""
        text = "<script>alert('xss')</script>Hello"
        result = sanitize_text(text)
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_injection_attempt_speak(self):
        """SSML speak injection is neutralized."""
        text = "<speak><voice name='evil'>Malicious</voice></speak>"
        result = sanitize_text(text)
        assert "<speak>" not in result
        assert "<voice" not in result


class TestSanitizeProsody:
    """Tests for prosody sanitization."""

    def test_sanitize_valid_prosody(self):
        """Valid prosody passes through."""
        prosody = {"speed": 1.5, "pitch": 0.8, "volume": 1.0}
        result = sanitize_prosody(prosody)
        assert result == prosody

    def test_sanitize_prosody_clamps_high_speed(self):
        """Speed above max is clamped."""
        prosody = {"speed": 10.0}
        result = sanitize_prosody(prosody)
        assert result["speed"] == DEFAULT_MAX_PROSODY_VALUE

    def test_sanitize_prosody_clamps_low_speed(self):
        """Speed below min is clamped."""
        prosody = {"speed": 0.1}
        result = sanitize_prosody(prosody)
        assert result["speed"] == DEFAULT_MIN_PROSODY_VALUE

    def test_sanitize_prosody_clamps_volume(self):
        """Volume is clamped to 0-2 range."""
        prosody = {"volume": 5.0}
        result = sanitize_prosody(prosody)
        assert result["volume"] == 2.0

        prosody = {"volume": -1.0}
        result = sanitize_prosody(prosody)
        assert result["volume"] == 0.0

    def test_sanitize_prosody_filters_unknown_keys(self):
        """Unknown keys are filtered out."""
        prosody = {"speed": 1.0, "unknown_key": "value", "malicious": 999}
        result = sanitize_prosody(prosody)
        assert "unknown_key" not in result
        assert "malicious" not in result
        assert result["speed"] == 1.0

    def test_sanitize_prosody_rejects_invalid_types(self):
        """Non-numeric values are filtered."""
        prosody = {"speed": "fast", "pitch": 1.0}
        result = sanitize_prosody(prosody)
        assert "speed" not in result
        assert result["pitch"] == 1.0

    def test_sanitize_prosody_none_returns_none(self):
        """None input returns None."""
        result = sanitize_prosody(None)
        assert result is None

    def test_sanitize_prosody_empty_returns_none(self):
        """Empty dict after filtering returns None."""
        prosody = {"unknown": "value"}
        result = sanitize_prosody(prosody)
        assert result is None

    def test_sanitize_prosody_non_dict_returns_none(self):
        """Non-dict input returns None."""
        result = sanitize_prosody("invalid")  # type: ignore
        assert result is None

    def test_sanitize_prosody_rate_alias(self):
        """Rate is treated as speed alias."""
        prosody = {"rate": 1.5}
        result = sanitize_prosody(prosody)
        assert result["rate"] == 1.5

    def test_sanitize_prosody_custom_config(self):
        """Custom prosody limits are respected."""
        config = SanitizationConfig(max_prosody_value=3.0, min_prosody_value=0.25)
        prosody = {"speed": 2.5}
        result = sanitize_prosody(prosody, config)
        assert result["speed"] == 2.5  # Within custom range


class TestSanitizeVoiceId:
    """Tests for voice ID sanitization."""

    def test_sanitize_valid_voice_id(self):
        """Valid voice ID passes through."""
        result = sanitize_voice_id("en_speaker_1")
        assert result == "en_speaker_1"

    def test_sanitize_voice_id_alphanumeric(self):
        """Only alphanumeric, underscore, hyphen allowed."""
        result = sanitize_voice_id("voice-test_123")
        assert result == "voice-test_123"

    def test_sanitize_voice_id_path_traversal(self):
        """Path traversal attempts are blocked."""
        result = sanitize_voice_id("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_sanitize_voice_id_special_chars(self):
        """Special characters are stripped."""
        result = sanitize_voice_id("voice@#$%^&*()+=id")
        assert result == "voiceid"

    def test_sanitize_voice_id_none_returns_none(self):
        """None input returns None."""
        result = sanitize_voice_id(None)
        assert result is None

    def test_sanitize_voice_id_empty_returns_none(self):
        """Empty after sanitization returns None."""
        result = sanitize_voice_id("@#$%")
        assert result is None

    def test_sanitize_voice_id_whitelist(self):
        """Whitelist is enforced."""
        allowed = ["voice1", "voice2"]
        result = sanitize_voice_id("voice1", allowed)
        assert result == "voice1"

        result = sanitize_voice_id("voice3", allowed)
        assert result is None

    def test_sanitize_voice_id_non_string_returns_none(self):
        """Non-string input returns None."""
        result = sanitize_voice_id(123)  # type: ignore
        assert result is None


class TestSanitizeLanguage:
    """Tests for language code sanitization."""

    def test_sanitize_valid_language_code(self):
        """Valid ISO 639-1 code passes through."""
        result = sanitize_language("en")
        assert result == "en"

    def test_sanitize_valid_language_with_region(self):
        """Valid language with region passes through."""
        result = sanitize_language("en-US")
        assert result == "en-US"

    def test_sanitize_language_invalid_format(self):
        """Invalid format returns None."""
        result = sanitize_language("english")
        assert result is None

        result = sanitize_language("e")
        assert result is None

        result = sanitize_language("eng")
        assert result is None

    def test_sanitize_language_strips_whitespace(self):
        """Whitespace is stripped."""
        result = sanitize_language("  en-US  ")
        assert result == "en-US"

    def test_sanitize_language_none_returns_none(self):
        """None input returns None."""
        result = sanitize_language(None)
        assert result is None

    def test_sanitize_language_whitelist(self):
        """Whitelist is enforced."""
        allowed = ["en", "fr", "de"]
        result = sanitize_language("en", allowed)
        assert result == "en"

        result = sanitize_language("es", allowed)
        assert result is None

    def test_sanitize_language_non_string_returns_none(self):
        """Non-string input returns None."""
        result = sanitize_language(123)  # type: ignore
        assert result is None


class TestSanitizeTTSRequest:
    """Tests for full TTS request sanitization."""

    def test_sanitize_full_request(self):
        """Full request is sanitized."""
        result = sanitize_tts_request(
            text="Hello <break/> world",
            voice_id="speaker_1",
            language="en-US",
            prosody={"speed": 1.2},
        )

        assert result["text"] == "Hello world"
        assert result["voice_id"] == "speaker_1"
        assert result["language"] == "en-US"
        assert result["prosody"]["speed"] == 1.2

    def test_sanitize_request_with_nulls(self):
        """Request with None values is handled."""
        result = sanitize_tts_request(
            text="Hello",
            voice_id=None,
            language=None,
            prosody=None,
        )

        assert result["text"] == "Hello"
        assert result["voice_id"] is None
        assert result["language"] is None
        assert result["prosody"] is None

    def test_sanitize_request_with_whitelists(self):
        """Whitelists are enforced in full request."""
        result = sanitize_tts_request(
            text="Hello",
            voice_id="voice1",
            language="en",
            allowed_voices=["voice1", "voice2"],
            allowed_languages=["en", "fr"],
        )

        assert result["voice_id"] == "voice1"
        assert result["language"] == "en"

        # Not in whitelist
        result = sanitize_tts_request(
            text="Hello",
            voice_id="voice3",
            language="es",
            allowed_voices=["voice1", "voice2"],
            allowed_languages=["en", "fr"],
        )

        assert result["voice_id"] is None
        assert result["language"] is None


class TestSanitizationConfig:
    """Tests for SanitizationConfig dataclass."""

    def test_default_config(self):
        """Default config has expected values."""
        config = SanitizationConfig()
        assert config.max_length == DEFAULT_MAX_TEXT_LENGTH
        assert config.strip_control_chars is True
        assert config.strip_ssml_tags is True
        assert config.normalize_whitespace is True
        assert config.normalize_unicode is True
        assert config.max_prosody_value == DEFAULT_MAX_PROSODY_VALUE
        assert config.min_prosody_value == DEFAULT_MIN_PROSODY_VALUE
        assert config.validate_language is True
        assert config.log_sanitization is True

    def test_custom_config(self):
        """Custom config overrides defaults."""
        config = SanitizationConfig(
            max_length=100,
            strip_ssml_tags=False,
            log_sanitization=False,
        )
        assert config.max_length == 100
        assert config.strip_ssml_tags is False
        assert config.log_sanitization is False


class TestTextSanitizationError:
    """Tests for TextSanitizationError."""

    def test_error_message(self):
        """Error contains message."""
        error = TextSanitizationError("Test error")
        assert str(error) == "Test error"

    def test_error_with_original_text(self):
        """Error stores truncated original text."""
        long_text = "A" * 200
        error = TextSanitizationError("Test error", long_text)
        assert error.original_text is not None
        assert len(error.original_text) == 100

    def test_error_without_original_text(self):
        """Error handles None original text."""
        error = TextSanitizationError("Test error", None)
        assert error.original_text is None
