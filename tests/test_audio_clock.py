"""Tests for AudioClock - TMF v3.0 §2.2 compliance."""

import time

import pytest


class TestAudioClock:
    """Test suite for authoritative audio clock."""

    def test_session_start_returns_absolute_time(self, audio_clock):
        """Session start should return absolute milliseconds."""
        start_ms = audio_clock.start_session("test-session-1")
        assert isinstance(start_ms, int)
        assert start_ms >= 0

    def test_session_time_is_relative(self, audio_clock):
        """Session time should be relative to session start."""
        audio_clock.start_session("test-session-2")

        # First reading should be very small (< 10ms)
        t1 = audio_clock.get_time_ms("test-session-2")
        assert t1 < 10

        # Wait a bit
        time.sleep(0.05)  # 50ms

        # Second reading should be larger
        t2 = audio_clock.get_time_ms("test-session-2")
        assert t2 > t1
        assert t2 >= 50  # At least 50ms elapsed

    def test_duplicate_session_raises(self, audio_clock):
        """Starting a session that already exists should raise."""
        audio_clock.start_session("duplicate-session")

        with pytest.raises(ValueError, match="already started"):
            audio_clock.start_session("duplicate-session")

    def test_unknown_session_raises(self, audio_clock):
        """Getting time for unknown session should raise."""
        with pytest.raises(KeyError, match="not found"):
            audio_clock.get_time_ms("unknown-session")

    def test_session_end_returns_duration(self, audio_clock):
        """Ending a session should return its duration."""
        audio_clock.start_session("duration-session")
        time.sleep(0.02)  # 20ms

        duration_ms = audio_clock.end_session("duration-session")
        assert duration_ms is not None
        assert duration_ms >= 20

    def test_end_unknown_session_returns_none(self, audio_clock):
        """Ending unknown session should return None, not raise."""
        result = audio_clock.end_session("nonexistent")
        assert result is None

    def test_clock_reading_contains_all_fields(self, audio_clock):
        """ClockReading should have raw_ns, ms, and session_id."""
        audio_clock.start_session("reading-session")
        reading = audio_clock.get_reading("reading-session")

        assert reading.raw_ns > 0
        assert reading.ms >= 0
        assert reading.session_id == "reading-session"

    def test_absolute_time_increases_monotonically(self, audio_clock):
        """Absolute time should always increase."""
        readings = [audio_clock.get_absolute_ms() for _ in range(100)]

        for i in range(1, len(readings)):
            assert readings[i] >= readings[i - 1], "Clock went backwards!"

    def test_measure_elapsed_returns_float(self, audio_clock):
        """measure_elapsed_ms should return float for sub-ms precision."""
        audio_clock.start_session("elapsed-session")
        reading = audio_clock.get_reading("elapsed-session")

        elapsed = audio_clock.measure_elapsed_ms(reading.raw_ns)
        assert isinstance(elapsed, float)
        assert elapsed >= 0

    def test_multiple_sessions_independent(self, audio_clock):
        """Multiple sessions should have independent timing."""
        audio_clock.start_session("session-a")
        time.sleep(0.05)  # 50ms

        audio_clock.start_session("session-b")

        # Session A should have ~50ms more elapsed time than B
        t_a = audio_clock.get_time_ms("session-a")
        t_b = audio_clock.get_time_ms("session-b")

        assert t_a > t_b
        assert t_a - t_b >= 40  # Allow some tolerance

    def test_session_exists_check(self, audio_clock):
        """session_exists should correctly report session status."""
        assert not audio_clock.session_exists("new-session")

        audio_clock.start_session("new-session")
        assert audio_clock.session_exists("new-session")

        audio_clock.end_session("new-session")
        assert not audio_clock.session_exists("new-session")

    def test_active_sessions_count(self, audio_clock):
        """active_sessions should track session count."""
        assert audio_clock.active_sessions == 0

        audio_clock.start_session("count-1")
        assert audio_clock.active_sessions == 1

        audio_clock.start_session("count-2")
        assert audio_clock.active_sessions == 2

        audio_clock.end_session("count-1")
        assert audio_clock.active_sessions == 1


class TestAudioClockTMFCompliance:
    """Tests for TMF v3.0 §2.2 monotonic clock requirements."""

    def test_monotonic_never_goes_backwards(self, audio_clock):
        """TMF §2.2: Clock must be monotonically increasing."""
        audio_clock.start_session("monotonic-test")

        prev_reading = audio_clock.get_reading("monotonic-test")
        for _ in range(1000):
            curr_reading = audio_clock.get_reading("monotonic-test")
            assert curr_reading.raw_ns >= prev_reading.raw_ns, \
                "TMF §2.2 violation: clock went backwards"
            assert curr_reading.ms >= prev_reading.ms, \
                "TMF §2.2 violation: t_audio_ms decreased"
            prev_reading = curr_reading

    def test_session_relative_timing_for_packets(self, audio_clock):
        """TMF §2.2: t_audio_ms must be session-relative."""
        audio_clock.start_session("packet-timing")

        # Simulate packet timestamps
        t1 = audio_clock.get_time_ms("packet-timing")
        time.sleep(0.02)  # 20ms packet
        t2 = audio_clock.get_time_ms("packet-timing")

        # Packet interval should be ~20ms
        interval = t2 - t1
        assert 15 <= interval <= 30, \
            f"Packet interval {interval}ms outside expected range"
