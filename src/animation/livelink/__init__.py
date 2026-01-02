"""Live Link integration for Unreal Engine MetaHuman.

Provides UDP streaming of ARKit-52 blendshapes to Unreal Engine
via the Live Link Face protocol.

Reference: TMF v3.0 §3.6

Components:
- LiveLinkSender: UDP packet sender
- LiveLinkBridge: Animation engine to Live Link adapter
- LiveLinkConfig: Configuration dataclass

Usage:
    from src.animation.livelink import create_livelink_sender

    sender = create_livelink_sender(
        host="127.0.0.1",
        port=11111,
        subject_name="GoAssist",
    )

    await sender.start()
    await sender.send_frame(blendshapes, timestamp_ms)
    await sender.stop()
"""

from __future__ import annotations

from src.animation.livelink.sender import (
    LiveLinkBridge,
    LiveLinkConfig,
    LiveLinkSender,
    create_livelink_sender,
)

__all__ = [
    "LiveLinkBridge",
    "LiveLinkConfig",
    "LiveLinkSender",
    "create_livelink_sender",
]
