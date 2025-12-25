"""Audio Packetizer - 20ms packets with 5ms overlap.

TMF v3.0 §3.1: Audio Packet Contract
- Packet duration: 20ms
- Overlap: 5ms for decoder cross-fade
- Overlap must NOT advance the clock

This module handles:
- Chunking raw audio into packets
- Maintaining monotonic sequence numbers
- Computing t_audio_ms from the authoritative clock
- Cross-fade overlap generation (does not advance clock)

Reference: Implementation-v3.0.md §3.1 Audio Packet Schema
"""

import struct
from dataclasses import dataclass, field
from typing import Iterator

from src.audio.transport.audio_clock import AudioClock, get_audio_clock
from src.config.constants import TMF


@dataclass
class AudioPacket:
    """A single audio packet per TMF v3.0 §3.1 schema.

    Attributes:
        session_id: Session identifier
        seq: Monotonically increasing sequence number
        t_audio_ms: Authoritative audio timestamp (session-relative)
        duration_ms: Packet duration (default 20ms)
        overlap_ms: Overlap for cross-fade (default 5ms, does NOT advance clock)
        codec: Audio codec identifier
        payload: Raw audio bytes
    """

    session_id: str
    seq: int
    t_audio_ms: int
    duration_ms: int = TMF.AUDIO_PACKET_DURATION_MS
    overlap_ms: int = TMF.AUDIO_OVERLAP_MS
    codec: str = "pcm16le"
    payload: bytes = b""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "seq": self.seq,
            "t_audio_ms": self.t_audio_ms,
            "duration_ms": self.duration_ms,
            "overlap_ms": self.overlap_ms,
            "codec": self.codec,
            "payload": self.payload.hex(),  # Hex-encode for JSON
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudioPacket":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            seq=data["seq"],
            t_audio_ms=data["t_audio_ms"],
            duration_ms=data.get("duration_ms", TMF.AUDIO_PACKET_DURATION_MS),
            overlap_ms=data.get("overlap_ms", TMF.AUDIO_OVERLAP_MS),
            codec=data.get("codec", "pcm16le"),
            payload=bytes.fromhex(data["payload"]),
        )

    def to_bytes(self) -> bytes:
        """Serialize packet for binary transport.

        Format:
        - 36 bytes: session_id (UUID as string, padded)
        - 4 bytes: seq (uint32)
        - 4 bytes: t_audio_ms (uint32)
        - 2 bytes: duration_ms (uint16)
        - 2 bytes: overlap_ms (uint16)
        - 8 bytes: codec (string, padded)
        - 4 bytes: payload_len (uint32)
        - N bytes: payload
        """
        session_bytes = self.session_id.encode("utf-8")[:36].ljust(36, b"\x00")
        codec_bytes = self.codec.encode("utf-8")[:8].ljust(8, b"\x00")

        header = struct.pack(
            "!36sIIHH8sI",
            session_bytes,
            self.seq,
            self.t_audio_ms,
            self.duration_ms,
            self.overlap_ms,
            codec_bytes,
            len(self.payload),
        )
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "AudioPacket":
        """Deserialize packet from binary transport."""
        header_size = 36 + 4 + 4 + 2 + 2 + 8 + 4  # 60 bytes
        header = data[:header_size]

        (
            session_bytes,
            seq,
            t_audio_ms,
            duration_ms,
            overlap_ms,
            codec_bytes,
            payload_len,
        ) = struct.unpack("!36sIIHH8sI", header)

        return cls(
            session_id=session_bytes.rstrip(b"\x00").decode("utf-8"),
            seq=seq,
            t_audio_ms=t_audio_ms,
            duration_ms=duration_ms,
            overlap_ms=overlap_ms,
            codec=codec_bytes.rstrip(b"\x00").decode("utf-8"),
            payload=data[header_size : header_size + payload_len],
        )


@dataclass
class Packetizer:
    """Audio packetizer for chunking audio streams.

    Handles:
    - Chunking raw PCM audio into 20ms packets
    - Generating overlap audio for cross-fade
    - Maintaining sequence numbers
    - Computing timestamps from authoritative clock

    Usage:
        packetizer = Packetizer(session_id="session-123")

        # Process incoming audio
        for packet in packetizer.process(audio_bytes):
            send_packet(packet)

        # Flush remaining audio at end of stream
        for packet in packetizer.flush():
            send_packet(packet)
    """

    session_id: str
    sample_rate: int = TMF.AUDIO_SAMPLE_RATE
    channels: int = TMF.AUDIO_CHANNELS
    bits_per_sample: int = 16
    packet_duration_ms: int = TMF.AUDIO_PACKET_DURATION_MS
    overlap_ms: int = TMF.AUDIO_OVERLAP_MS
    codec: str = "pcm16le"

    # Internal state
    _buffer: bytes = field(default=b"", init=False)
    _seq: int = field(default=0, init=False)
    _clock: AudioClock = field(default=None, init=False)
    _overlap_buffer: bytes = field(default=b"", init=False)

    def __post_init__(self) -> None:
        """Initialize clock reference."""
        self._clock = get_audio_clock()

    @property
    def bytes_per_sample(self) -> int:
        """Bytes per audio sample."""
        return (self.bits_per_sample * self.channels) // 8

    @property
    def samples_per_packet(self) -> int:
        """Number of samples per packet."""
        return int(self.sample_rate * self.packet_duration_ms / 1000)

    @property
    def bytes_per_packet(self) -> int:
        """Bytes per packet (excluding overlap)."""
        return self.samples_per_packet * self.bytes_per_sample

    @property
    def samples_per_overlap(self) -> int:
        """Number of overlap samples."""
        return int(self.sample_rate * self.overlap_ms / 1000)

    @property
    def bytes_per_overlap(self) -> int:
        """Bytes of overlap audio."""
        return self.samples_per_overlap * self.bytes_per_sample

    def _get_timestamp(self) -> int:
        """Get current audio timestamp from authoritative clock.

        Important: This is session-relative time in milliseconds.
        The clock is the single source of truth for timing.
        """
        return self._clock.get_time_ms(self.session_id)

    def process(self, audio_bytes: bytes) -> Iterator[AudioPacket]:
        """Process incoming audio bytes and yield complete packets.

        Args:
            audio_bytes: Raw PCM audio data

        Yields:
            AudioPacket for each complete 20ms chunk

        Note:
            Incomplete packets are buffered for the next call.
            Overlap audio is prepended but does NOT advance the clock.
        """
        self._buffer += audio_bytes

        while len(self._buffer) >= self.bytes_per_packet:
            # Extract packet payload
            payload = self._buffer[: self.bytes_per_packet]
            self._buffer = self._buffer[self.bytes_per_packet :]

            # Prepend overlap from previous packet (for decoder cross-fade)
            # Important: Overlap does NOT advance the clock
            if self._overlap_buffer:
                full_payload = self._overlap_buffer + payload
            else:
                full_payload = payload

            # Save overlap for next packet
            self._overlap_buffer = payload[-self.bytes_per_overlap :] if self.bytes_per_overlap > 0 else b""

            # Get authoritative timestamp
            t_audio_ms = self._get_timestamp()

            # Create packet
            packet = AudioPacket(
                session_id=self.session_id,
                seq=self._seq,
                t_audio_ms=t_audio_ms,
                duration_ms=self.packet_duration_ms,
                overlap_ms=self.overlap_ms if self._seq > 0 else 0,  # No overlap on first packet
                codec=self.codec,
                payload=full_payload,
            )

            self._seq += 1
            yield packet

    def flush(self) -> Iterator[AudioPacket]:
        """Flush any remaining buffered audio as a final packet.

        Yields:
            AudioPacket if there's remaining audio, padded if necessary
        """
        if not self._buffer:
            return

        # Pad to full packet size
        if len(self._buffer) < self.bytes_per_packet:
            padding = self.bytes_per_packet - len(self._buffer)
            self._buffer += b"\x00" * padding

        yield from self.process(b"")

    def reset(self) -> None:
        """Reset packetizer state for a new stream."""
        self._buffer = b""
        self._seq = 0
        self._overlap_buffer = b""


def calculate_packet_count(audio_duration_ms: int, packet_duration_ms: int = TMF.AUDIO_PACKET_DURATION_MS) -> int:
    """Calculate number of packets for a given audio duration.

    Args:
        audio_duration_ms: Total audio duration in milliseconds
        packet_duration_ms: Packet duration (default 20ms)

    Returns:
        Number of complete packets (rounded up)
    """
    return (audio_duration_ms + packet_duration_ms - 1) // packet_duration_ms
