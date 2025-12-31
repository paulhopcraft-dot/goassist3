"""Audio2Face gRPC Client Package.

Provides gRPC client for NVIDIA Audio2Face integration.

To generate Python stubs from proto:
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. audio2face.proto

Reference: TMF v3.0 Addendum A §A3
"""

from src.animation.grpc.client import (
    Audio2FaceClient,
    Audio2FaceClientConfig,
    ConnectionState,
    create_audio2face_client,
)

__all__ = [
    "Audio2FaceClient",
    "Audio2FaceClientConfig",
    "ConnectionState",
    "create_audio2face_client",
]
