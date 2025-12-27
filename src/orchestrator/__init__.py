"""Orchestrator module - Session and state management.

Provides:
- Session: Voice session container
- SessionManager: Multi-session management
- SessionStateMachine: 5-state FSM
- ConversationPipeline: End-to-end voice+avatar pipeline
"""

from src.orchestrator.session import Session, SessionConfig, SessionManager
from src.orchestrator.state_machine import SessionState, SessionStateMachine
from src.orchestrator.pipeline import ConversationPipeline, PipelineConfig, create_pipeline

__all__ = [
    # Session management
    "Session",
    "SessionConfig",
    "SessionManager",
    # State machine
    "SessionState",
    "SessionStateMachine",
    # Pipeline
    "ConversationPipeline",
    "PipelineConfig",
    "create_pipeline",
]
