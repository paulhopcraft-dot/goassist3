"""
Avatar Realism & Utility QA Test Suite

12-Point checklist for evaluating talking avatar quality.
Run with: pytest tests/avatar_qa/ -v
"""

from .checklist import AvatarQAChecklist, CheckResult
from .metrics import BlendshapeAnalyzer, LatencyMeasurer, AudioAnalyzer

__all__ = [
    "AvatarQAChecklist",
    "CheckResult",
    "BlendshapeAnalyzer",
    "LatencyMeasurer",
    "AudioAnalyzer",
]
