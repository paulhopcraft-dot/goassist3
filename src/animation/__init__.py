"""Animation package - Audio-driven avatar animation.

Provides:
- Base animation engine interface (ARKit-52 blendshapes)
- Audio2Face integration (NEUTRAL mode per TMF)
- Yield controller for backpressure
- Heartbeat for connection maintenance
- WebRTC data channel emitter

Reference: TMF v3.0 §3.1, §4.3, Addendum A §A3
"""

from src.animation.base import (
    ARKIT_52_BLENDSHAPES,
    AnimationEngine,
    BaseAnimationEngine,
    BlendshapeFrame,
    MockAnimationEngine,
    get_neutral_blendshapes,
)
from src.animation.yield_controller import (
    YieldController,
    YieldState,
    create_yield_controller,
)
from src.animation.heartbeat import (
    HeartbeatEmitter,
    HeartbeatMonitor,
    create_heartbeat_emitter,
)
from src.animation.audio2face_engine import (
    Audio2FaceConfig,
    Audio2FaceEngine,
    create_audio2face_engine,
)
from src.animation.datachannel_emitter import (
    DataChannelEmitter,
    EmitterConfig,
    create_emitter,
)

__all__ = [
    # Base
    "ARKIT_52_BLENDSHAPES",
    "AnimationEngine",
    "BaseAnimationEngine",
    "BlendshapeFrame",
    "MockAnimationEngine",
    "get_neutral_blendshapes",
    # Yield
    "YieldController",
    "YieldState",
    "create_yield_controller",
    # Heartbeat
    "HeartbeatEmitter",
    "HeartbeatMonitor",
    "create_heartbeat_emitter",
    # Audio2Face
    "Audio2FaceConfig",
    "Audio2FaceEngine",
    "create_audio2face_engine",
    # Emitter
    "DataChannelEmitter",
    "EmitterConfig",
    "create_emitter",
]
