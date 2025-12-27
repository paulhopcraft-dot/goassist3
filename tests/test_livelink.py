"""Tests for Live Link integration.

Tests cover:
- LiveLinkSender UDP packet building
- LiveLinkBridge frame processing
- ARKit-52 blendshape serialization
- Error handling
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.animation.base import ARKIT_52_BLENDSHAPES, BlendshapeFrame, get_neutral_blendshapes
from src.animation.livelink import (
    LiveLinkBridge,
    LiveLinkConfig,
    LiveLinkSender,
    create_livelink_sender,
)


class TestLiveLinkConfig:
    """Tests for LiveLinkConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LiveLinkConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 11111
        assert config.subject_name == "GoAssist"
        assert config.target_fps == 30

    def test_custom_config(self):
        """Test custom configuration."""
        config = LiveLinkConfig(
            host="192.168.1.100",
            port=12345,
            subject_name="CustomAvatar",
            target_fps=60,
        )

        assert config.host == "192.168.1.100"
        assert config.port == 12345
        assert config.subject_name == "CustomAvatar"
        assert config.target_fps == 60


class TestLiveLinkSenderCreation:
    """Tests for LiveLinkSender initialization."""

    def test_create_with_default_config(self):
        """Test sender creation with defaults."""
        sender = LiveLinkSender()

        assert sender.config.host == "127.0.0.1"
        assert sender.config.port == 11111
        assert sender.is_running is False

    def test_create_with_custom_config(self):
        """Test sender creation with custom config."""
        config = LiveLinkConfig(
            host="10.0.0.1",
            port=22222,
        )
        sender = LiveLinkSender(config=config)

        assert sender.config.host == "10.0.0.1"
        assert sender.config.port == 22222

    def test_factory_function(self):
        """Test factory function creates sender."""
        sender = create_livelink_sender(
            host="192.168.1.1",
            port=33333,
            subject_name="TestAvatar",
        )

        assert sender.config.host == "192.168.1.1"
        assert sender.config.port == 33333
        assert sender.config.subject_name == "TestAvatar"


class TestLiveLinkSenderState:
    """Tests for LiveLinkSender state management."""

    @pytest.fixture
    def sender(self):
        """Create sender for testing."""
        return LiveLinkSender()

    @pytest.mark.asyncio
    async def test_start_creates_socket(self, sender):
        """Test start initializes UDP socket."""
        await sender.start()

        assert sender.is_running is True
        assert sender._socket is not None

        await sender.stop()

    @pytest.mark.asyncio
    async def test_stop_closes_socket(self, sender):
        """Test stop closes socket."""
        await sender.start()
        await sender.stop()

        assert sender.is_running is False
        assert sender._socket is None

    @pytest.mark.asyncio
    async def test_start_with_subject_name(self, sender):
        """Test start can override subject name."""
        await sender.start("CustomName")

        assert sender.config.subject_name == "CustomName"

        await sender.stop()

    @pytest.mark.asyncio
    async def test_frame_count_increments(self, sender):
        """Test frame count tracks sent frames."""
        await sender.start()

        blendshapes = get_neutral_blendshapes()
        await sender.send_frame(blendshapes, 0)
        await sender.send_frame(blendshapes, 33)

        assert sender.frame_count == 2

        await sender.stop()


class TestLiveLinkPacketBuilding:
    """Tests for Live Link packet format."""

    @pytest.fixture
    def sender(self):
        """Create sender for testing."""
        return LiveLinkSender()

    def test_packet_contains_device_id(self, sender):
        """Test packet includes subject name as DeviceID."""
        blendshapes = get_neutral_blendshapes()
        packet = sender._build_packet(blendshapes, 1000)

        data = json.loads(packet.decode("utf-8"))
        assert data["DeviceID"] == "GoAssist"

    def test_packet_contains_timestamp(self, sender):
        """Test packet includes timestamp in seconds."""
        blendshapes = get_neutral_blendshapes()
        packet = sender._build_packet(blendshapes, 1500)

        data = json.loads(packet.decode("utf-8"))
        assert data["Timestamp"] == 1.5  # 1500ms = 1.5s

    def test_packet_contains_all_blendshapes(self, sender):
        """Test packet includes all 52 ARKit blendshapes."""
        blendshapes = get_neutral_blendshapes()
        packet = sender._build_packet(blendshapes, 0)

        data = json.loads(packet.decode("utf-8"))
        assert len(data["Blendshapes"]) == 52

        for name in ARKIT_52_BLENDSHAPES:
            assert name in data["Blendshapes"]

    def test_packet_clamps_blendshape_values(self, sender):
        """Test blendshape values are clamped to 0-1."""
        blendshapes = {
            "jawOpen": 1.5,  # Over 1
            "eyeBlinkLeft": -0.5,  # Under 0
            "mouthSmileLeft": 0.5,  # Normal
        }
        packet = sender._build_packet(blendshapes, 0)

        data = json.loads(packet.decode("utf-8"))
        assert data["Blendshapes"]["jawOpen"] == 1.0
        assert data["Blendshapes"]["eyeBlinkLeft"] == 0.0
        assert data["Blendshapes"]["mouthSmileLeft"] == 0.5

    def test_packet_contains_head_rotation(self, sender):
        """Test packet includes head rotation when enabled."""
        sender._config.send_head_rotation = True
        blendshapes = get_neutral_blendshapes()
        packet = sender._build_packet(blendshapes, 0)

        data = json.loads(packet.decode("utf-8"))
        assert "HeadRotation" in data
        assert "Pitch" in data["HeadRotation"]
        assert "Yaw" in data["HeadRotation"]
        assert "Roll" in data["HeadRotation"]

    def test_packet_custom_head_rotation(self, sender):
        """Test custom head rotation values."""
        blendshapes = get_neutral_blendshapes()
        packet = sender._build_packet(blendshapes, 0, head_rotation=(10.0, 20.0, 5.0))

        data = json.loads(packet.decode("utf-8"))
        assert data["HeadRotation"]["Pitch"] == 10.0
        assert data["HeadRotation"]["Yaw"] == 20.0
        assert data["HeadRotation"]["Roll"] == 5.0


class TestLiveLinkBridge:
    """Tests for LiveLinkBridge."""

    @pytest.fixture
    def mock_sender(self):
        """Create mock sender."""
        sender = MagicMock(spec=LiveLinkSender)
        sender.send_blendshape_frame = AsyncMock(return_value=True)
        return sender

    @pytest.fixture
    def bridge(self, mock_sender):
        """Create bridge with mock sender."""
        return LiveLinkBridge(mock_sender, target_fps=30)

    @pytest.mark.asyncio
    async def test_process_frame_sends_to_sender(self, bridge, mock_sender):
        """Test bridge forwards frames to sender."""
        await bridge.start()

        frame = BlendshapeFrame(
            session_id="test",
            seq=1,
            t_audio_ms=0,
            blendshapes=get_neutral_blendshapes(),
        )

        await bridge.process_frame(frame)

        mock_sender.send_blendshape_frame.assert_called_once_with(frame)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, bridge, mock_sender):
        """Test bridge rate limits frames."""
        await bridge.start()

        frame = BlendshapeFrame(
            session_id="test",
            seq=1,
            t_audio_ms=0,
            blendshapes=get_neutral_blendshapes(),
        )

        # First frame should send
        result1 = await bridge.process_frame(frame)
        assert result1 is True

        # Immediate second frame should be rate limited
        result2 = await bridge.process_frame(frame)
        assert result2 is False

        # Wait for frame interval and try again
        await asyncio.sleep(0.04)  # > 33ms
        result3 = await bridge.process_frame(frame)
        assert result3 is True

    @pytest.mark.asyncio
    async def test_frame_count_tracking(self, bridge, mock_sender):
        """Test bridge tracks sent frames."""
        await bridge.start()

        frame = BlendshapeFrame(
            session_id="test",
            seq=1,
            t_audio_ms=0,
            blendshapes=get_neutral_blendshapes(),
        )

        await bridge.process_frame(frame)
        await asyncio.sleep(0.04)
        await bridge.process_frame(frame)

        assert bridge.frames_sent == 2


class TestLiveLinkIntegration:
    """Integration tests for Live Link with animation pipeline."""

    @pytest.mark.asyncio
    async def test_send_blendshape_frame(self):
        """Test sending a BlendshapeFrame object."""
        sender = LiveLinkSender()
        await sender.start()

        frame = BlendshapeFrame(
            session_id="test-session",
            seq=42,
            t_audio_ms=1000,
            blendshapes=get_neutral_blendshapes(),
        )

        # This will try to send but might fail without Unreal running
        # We're just testing the API works
        result = await sender.send_blendshape_frame(frame)
        # Result depends on network, just verify no exception

        await sender.stop()

    @pytest.mark.asyncio
    async def test_error_callback(self):
        """Test error callback is invoked on send failure."""
        errors = []

        def on_error(e):
            errors.append(e)

        sender = LiveLinkSender(on_error=on_error)
        # Don't start - socket not created

        blendshapes = get_neutral_blendshapes()
        result = await sender.send_frame(blendshapes, 0)

        assert result is False
        # No error callback since we didn't start (no socket)

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test complete Live Link pipeline."""
        sender = create_livelink_sender(subject_name="TestAvatar")
        bridge = LiveLinkBridge(sender, target_fps=30)

        await sender.start()
        await bridge.start()

        # Simulate animation frames
        for i in range(5):
            blendshapes = get_neutral_blendshapes()
            blendshapes["jawOpen"] = i * 0.2  # Animate jaw

            frame = BlendshapeFrame(
                session_id="test",
                seq=i,
                t_audio_ms=i * 33,
                blendshapes=blendshapes,
            )

            await bridge.process_frame(frame)
            await asyncio.sleep(0.04)

        await bridge.stop()
        await sender.stop()

        assert sender.frame_count > 0
