"""Audio2Face Protocol Buffer definitions.

Manually defined to avoid protoc dependency.
These match NVIDIA Audio2Face gRPC API.

Reference: NVIDIA Audio2Face Documentation
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AudioRequest:
    """Request message for audio-to-blendshape conversion."""

    audio_data: bytes = b""  # Raw audio bytes (PCM, 16kHz, mono, 16-bit)
    sample_rate: int = 16000
    instance_id: str = ""  # Audio2Face instance identifier


@dataclass
class BlendshapeResponse:
    """Response message with generated blendshapes."""

    blendshapes: dict[str, float] = field(default_factory=dict)  # ARKit-52 format
    timestamp_ms: int = 0
    success: bool = True
    error_message: str = ""


@dataclass
class StreamConfig:
    """Configuration for streaming session."""

    instance_id: str = ""
    style: str = "NEUTRAL"  # Animation style
    sample_rate: int = 16000
    enable_emotion: bool = False


# ARKit-52 blendshape names for reference
ARKIT_52_BLENDSHAPES = [
    "eyeBlinkLeft", "eyeLookDownLeft", "eyeLookInLeft", "eyeLookOutLeft",
    "eyeLookUpLeft", "eyeSquintLeft", "eyeWideLeft", "eyeBlinkRight",
    "eyeLookDownRight", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight",
    "eyeSquintRight", "eyeWideRight", "jawForward", "jawLeft", "jawRight",
    "jawOpen", "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft",
    "mouthRight", "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft",
    "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft",
    "mouthStretchRight", "mouthRollLower", "mouthRollUpper", "mouthShrugLower",
    "mouthShrugUpper", "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft",
    "mouthLowerDownRight", "mouthUpperUpLeft", "mouthUpperUpRight", "browDownLeft",
    "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight", "noseSneerLeft",
    "noseSneerRight", "tongueOut",
]


def get_neutral_blendshapes() -> dict[str, float]:
    """Get neutral ARKit-52 blendshapes (all zeros)."""
    return {name: 0.0 for name in ARKIT_52_BLENDSHAPES}
