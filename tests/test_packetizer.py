"""Tests for Audio Packetizer.

Tests cover:
- AudioPacket dataclass
- Serialization (to_dict, from_dict, to_bytes, from_bytes)
- Packetizer chunking behavior
- Overlap handling
- Flush behavior
- Packet count calculation
"""

from unittest.mock import MagicMock, patch

import pytest

from src.audio.transport.packetizer import (
    AudioPacket,
    Packetizer,
    calculate_packet_count,
)
from src.config.constants import TMF


class TestAudioPacket:
    """Tests for AudioPacket dataclass."""

    def test_create_packet(self):
        """Create an audio packet."""
        packet = AudioPacket(
            session_id="test-session",
            seq=1,
            t_audio_ms=1000,
            payload=b"\x00" * 640,
        )
        assert packet.session_id == "test-session"
        assert packet.seq == 1
        assert packet.t_audio_ms == 1000
        assert packet.duration_ms == TMF.AUDIO_PACKET_DURATION_MS
        assert packet.overlap_ms == TMF.AUDIO_OVERLAP_MS
        assert packet.codec == "pcm16le"
        assert len(packet.payload) == 640

    def test_custom_duration_and_overlap(self):
        """Custom duration and overlap values."""
        packet = AudioPacket(
            session_id="test-session",
            seq=0,
            t_audio_ms=0,
            duration_ms=30,
            overlap_ms=10,
            payload=b"",
        )
        assert packet.duration_ms == 30
        assert packet.overlap_ms == 10


class TestAudioPacketSerialization:
    """Tests for packet serialization."""

    def test_to_dict(self):
        """Convert packet to dictionary."""
        packet = AudioPacket(
            session_id="test-session",
            seq=5,
            t_audio_ms=100,
            duration_ms=20,
            overlap_ms=5,
            codec="pcm16le",
            payload=b"\x01\x02\x03\x04",
        )
        d = packet.to_dict()

        assert d["session_id"] == "test-session"
        assert d["seq"] == 5
        assert d["t_audio_ms"] == 100
        assert d["duration_ms"] == 20
        assert d["overlap_ms"] == 5
        assert d["codec"] == "pcm16le"
        assert d["payload"] == "01020304"  # Hex encoded

    def test_from_dict(self):
        """Create packet from dictionary."""
        d = {
            "session_id": "from-dict-session",
            "seq": 10,
            "t_audio_ms": 500,
            "duration_ms": 20,
            "overlap_ms": 5,
            "codec": "pcm16le",
            "payload": "aabbccdd",
        }
        packet = AudioPacket.from_dict(d)

        assert packet.session_id == "from-dict-session"
        assert packet.seq == 10
        assert packet.t_audio_ms == 500
        assert packet.payload == b"\xaa\xbb\xcc\xdd"

    def test_roundtrip_dict(self):
        """Round-trip through dict serialization."""
        original = AudioPacket(
            session_id="roundtrip-session",
            seq=42,
            t_audio_ms=1234,
            payload=b"hello world",
        )
        d = original.to_dict()
        restored = AudioPacket.from_dict(d)

        assert restored.session_id == original.session_id
        assert restored.seq == original.seq
        assert restored.t_audio_ms == original.t_audio_ms
        assert restored.payload == original.payload

    def test_to_bytes(self):
        """Convert packet to bytes."""
        packet = AudioPacket(
            session_id="bytes-session",
            seq=1,
            t_audio_ms=100,
            payload=b"\x00" * 10,
        )
        data = packet.to_bytes()

        # Header: 36 + 4 + 4 + 2 + 2 + 8 + 4 = 60 bytes
        # Plus payload: 10 bytes
        assert len(data) == 60 + 10

    def test_from_bytes(self):
        """Create packet from bytes."""
        original = AudioPacket(
            session_id="bytes-test",
            seq=99,
            t_audio_ms=5000,
            duration_ms=20,
            overlap_ms=5,
            codec="pcm16le",
            payload=b"test payload data",
        )
        data = original.to_bytes()
        restored = AudioPacket.from_bytes(data)

        assert restored.session_id == original.session_id
        assert restored.seq == original.seq
        assert restored.t_audio_ms == original.t_audio_ms
        assert restored.duration_ms == original.duration_ms
        assert restored.overlap_ms == original.overlap_ms
        assert restored.codec == original.codec
        assert restored.payload == original.payload

    def test_roundtrip_bytes(self):
        """Round-trip through bytes serialization."""
        original = AudioPacket(
            session_id="a" * 36,  # Max length session ID
            seq=0xFFFFFFFF,  # Max uint32
            t_audio_ms=0xFFFFFFFF,
            payload=b"\xff" * 1000,
        )
        data = original.to_bytes()
        restored = AudioPacket.from_bytes(data)

        assert restored.session_id == original.session_id
        assert restored.seq == original.seq
        assert restored.payload == original.payload


class TestPacketizer:
    """Tests for Packetizer class."""

    @pytest.fixture
    def packetizer(self):
        """Create packetizer with mocked clock."""
        with patch("src.audio.transport.packetizer.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 0
            packetizer = Packetizer(session_id="test-session")
            yield packetizer

    def test_init(self, packetizer):
        """Test packetizer initialization."""
        assert packetizer.session_id == "test-session"
        assert packetizer.sample_rate == TMF.AUDIO_SAMPLE_RATE
        assert packetizer.channels == TMF.AUDIO_CHANNELS
        assert packetizer.packet_duration_ms == TMF.AUDIO_PACKET_DURATION_MS

    def test_bytes_per_sample(self, packetizer):
        """Bytes per sample calculation."""
        # 16-bit mono = 2 bytes per sample
        assert packetizer.bytes_per_sample == 2

    def test_samples_per_packet(self, packetizer):
        """Samples per packet calculation."""
        # 16kHz * 20ms = 320 samples
        expected = int(16000 * 20 / 1000)
        assert packetizer.samples_per_packet == expected

    def test_bytes_per_packet(self, packetizer):
        """Bytes per packet calculation."""
        # 320 samples * 2 bytes = 640 bytes
        assert packetizer.bytes_per_packet == 640

    def test_samples_per_overlap(self, packetizer):
        """Samples per overlap calculation."""
        # 16kHz * 5ms = 80 samples
        expected = int(16000 * 5 / 1000)
        assert packetizer.samples_per_overlap == expected

    def test_bytes_per_overlap(self, packetizer):
        """Bytes per overlap calculation."""
        # 80 samples * 2 bytes = 160 bytes
        assert packetizer.bytes_per_overlap == 160


class TestPacketizerProcessing:
    """Tests for packetizer audio processing."""

    @pytest.fixture
    def packetizer(self):
        """Create packetizer with mocked clock."""
        with patch("src.audio.transport.packetizer.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 100
            packetizer = Packetizer(session_id="process-session")
            yield packetizer

    def test_process_exact_packet(self, packetizer):
        """Process exactly one packet worth of audio."""
        audio = b"\x00" * 640  # Exactly one packet
        packets = list(packetizer.process(audio))

        assert len(packets) == 1
        assert packets[0].seq == 0
        assert packets[0].session_id == "process-session"
        assert packets[0].t_audio_ms == 100

    def test_process_multiple_packets(self, packetizer):
        """Process multiple packets worth of audio."""
        audio = b"\x00" * (640 * 3)  # Three packets
        packets = list(packetizer.process(audio))

        assert len(packets) == 3
        assert packets[0].seq == 0
        assert packets[1].seq == 1
        assert packets[2].seq == 2

    def test_process_incomplete_packet_buffered(self, packetizer):
        """Incomplete packet is buffered."""
        audio = b"\x00" * 500  # Less than one packet
        packets = list(packetizer.process(audio))

        assert len(packets) == 0

        # Add more audio to complete the packet
        audio2 = b"\x00" * 200  # Total: 700 bytes, enough for 1 packet
        packets2 = list(packetizer.process(audio2))

        assert len(packets2) == 1

    def test_process_with_remainder(self, packetizer):
        """Process leaves remainder in buffer."""
        audio = b"\x00" * 1000  # 640 + 360 remainder
        packets = list(packetizer.process(audio))

        assert len(packets) == 1

    def test_first_packet_no_overlap(self, packetizer):
        """First packet has no overlap."""
        audio = b"\x00" * 640
        packets = list(packetizer.process(audio))

        assert packets[0].overlap_ms == 0

    def test_subsequent_packets_have_overlap(self, packetizer):
        """Subsequent packets have overlap."""
        audio = b"\x00" * (640 * 2)
        packets = list(packetizer.process(audio))

        assert packets[0].overlap_ms == 0
        assert packets[1].overlap_ms == TMF.AUDIO_OVERLAP_MS

    def test_overlap_prepended_to_payload(self, packetizer):
        """Overlap audio is prepended to subsequent packets."""
        # First packet with distinct pattern
        audio1 = b"\x01" * 640
        packets1 = list(packetizer.process(audio1))
        assert len(packets1) == 1
        assert len(packets1[0].payload) == 640

        # Second packet should have overlap from first
        audio2 = b"\x02" * 640
        packets2 = list(packetizer.process(audio2))
        assert len(packets2) == 1
        # Payload should be 640 + 160 overlap = 800 bytes
        assert len(packets2[0].payload) == 800
        # First 160 bytes should be from previous packet (overlap)
        assert packets2[0].payload[:160] == b"\x01" * 160


class TestPacketizerFlush:
    """Tests for packetizer flush behavior."""

    @pytest.fixture
    def packetizer(self):
        """Create packetizer with mocked clock."""
        with patch("src.audio.transport.packetizer.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 0
            packetizer = Packetizer(session_id="flush-session")
            yield packetizer

    def test_flush_empty_buffer(self, packetizer):
        """Flush empty buffer yields nothing."""
        packets = list(packetizer.flush())
        assert len(packets) == 0

    def test_flush_partial_buffer(self, packetizer):
        """Flush partial buffer yields padded packet."""
        # Add incomplete audio
        audio = b"\xff" * 300
        list(packetizer.process(audio))  # Buffers the audio

        # Flush should yield one padded packet
        packets = list(packetizer.flush())
        assert len(packets) == 1
        # Payload should be padded to full packet size
        assert len(packets[0].payload) >= 640


class TestPacketizerReset:
    """Tests for packetizer reset."""

    @pytest.fixture
    def packetizer(self):
        """Create packetizer with mocked clock."""
        with patch("src.audio.transport.packetizer.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 0
            packetizer = Packetizer(session_id="reset-session")
            yield packetizer

    def test_reset_clears_state(self, packetizer):
        """Reset clears all internal state."""
        # Process some audio
        audio = b"\x00" * 1000
        list(packetizer.process(audio))

        # Reset
        packetizer.reset()

        # Sequence should restart at 0
        audio2 = b"\x00" * 640
        packets = list(packetizer.process(audio2))
        assert packets[0].seq == 0
        # No overlap on first packet after reset
        assert packets[0].overlap_ms == 0


class TestCalculatePacketCount:
    """Tests for packet count calculation."""

    def test_exact_multiple(self):
        """Duration is exact multiple of packet duration."""
        count = calculate_packet_count(100, 20)
        assert count == 5

    def test_rounds_up(self):
        """Partial packets are rounded up."""
        count = calculate_packet_count(101, 20)
        assert count == 6

    def test_single_packet(self):
        """Duration less than one packet."""
        count = calculate_packet_count(10, 20)
        assert count == 1

    def test_zero_duration(self):
        """Zero duration returns zero packets."""
        count = calculate_packet_count(0, 20)
        assert count == 0

    def test_default_packet_duration(self):
        """Uses default packet duration."""
        count = calculate_packet_count(100)
        expected = (100 + TMF.AUDIO_PACKET_DURATION_MS - 1) // TMF.AUDIO_PACKET_DURATION_MS
        assert count == expected
