"""Toolkit v3.0 Autonomy Module - Self-directed work capabilities.

Enables autonomous operation:
- Auto-continue: Automatically proceed to next task
- Auto-verify: Run verification after each change
- Auto-commit: Commit when tests pass
- Feedback loops: Learn from outcomes
- Parallel agents: Run multiple agents simultaneously

Usage:
    from toolkit.autonomy import AutonomyController

    controller = AutonomyController()
    controller.enable_auto_continue()

    # Work loop runs autonomously
    while controller.should_continue():
        task = controller.get_next_task()
        result = execute_task(task)
        controller.record_outcome(task, result)
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

# Import learning module if available
try:
    from .learning import get_learner, record
    HAS_LEARNING = True
except ImportError:
    HAS_LEARNING = False


class AutonomyLevel(Enum):
    """Levels of autonomous operation."""

    MANUAL = 0  # Ask before every action
    GUIDED = 1  # Ask for major decisions only
    AUTONOMOUS = 2  # Proceed automatically, report results
    FULL_AUTO = 3  # Complete autonomy with learning


@dataclass
class TaskResult:
    """Result of a task execution."""

    task_id: str
    success: bool
    duration_ms: int = 0
    output: str = ""
    errors: list[str] = field(default_factory=list)
    next_tasks: list[str] = field(default_factory=list)


@dataclass
class AutonomyConfig:
    """Configuration for autonomous operation."""

    level: AutonomyLevel = AutonomyLevel.AUTONOMOUS
    auto_continue: bool = True
    auto_verify: bool = True
    auto_commit: bool = False  # Requires explicit enable
    max_consecutive_errors: int = 3
    pause_on_p0_issues: bool = True
    learn_from_outcomes: bool = True
    parallel_agents: bool = True


class TaskQueue:
    """Priority queue of tasks to execute."""

    def __init__(self) -> None:
        self._tasks: list[dict] = []
        self._completed: list[str] = []
        self._failed: list[str] = []

    def add(self, task_id: str, priority: int = 0, context: dict | None = None) -> None:
        """Add task to queue."""
        self._tasks.append({
            "id": task_id,
            "priority": priority,
            "context": context or {},
            "added_at": datetime.now().isoformat(),
        })
        self._tasks.sort(key=lambda x: x["priority"], reverse=True)

    def get_next(self) -> dict | None:
        """Get next task from queue."""
        if not self._tasks:
            return None
        return self._tasks.pop(0)

    def mark_complete(self, task_id: str) -> None:
        """Mark task as completed."""
        self._completed.append(task_id)

    def mark_failed(self, task_id: str) -> None:
        """Mark task as failed."""
        self._failed.append(task_id)

    @property
    def pending_count(self) -> int:
        """Number of pending tasks."""
        return len(self._tasks)

    @property
    def completed_count(self) -> int:
        """Number of completed tasks."""
        return len(self._completed)

    def to_dict(self) -> dict:
        """Serialize queue state."""
        return {
            "pending": self._tasks,
            "completed": self._completed,
            "failed": self._failed,
        }


class FeedbackLoop:
    """Feedback loop for learning from outcomes."""

    def __init__(self) -> None:
        self._outcomes: list[dict] = []
        self._patterns: dict[str, float] = {}

    def record(
        self,
        action: str,
        context: dict,
        result: TaskResult,
    ) -> None:
        """Record outcome for learning."""
        outcome = {
            "action": action,
            "context": context,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "timestamp": datetime.now().isoformat(),
        }
        self._outcomes.append(outcome)

        # Update success patterns
        key = f"{action}:{context.get('task_type', 'unknown')}"
        if key not in self._patterns:
            self._patterns[key] = 0.5  # Start at 50%

        # Exponential moving average
        alpha = 0.3
        self._patterns[key] = (
            alpha * (1.0 if result.success else 0.0)
            + (1 - alpha) * self._patterns[key]
        )

        # Also record to XGBoost learner if available
        if HAS_LEARNING:
            record(
                command=action,
                context=context,
                outcome="success" if result.success else "failure",
                duration_ms=result.duration_ms,
            )

    def get_success_probability(self, action: str, context: dict) -> float:
        """Get predicted success probability."""
        key = f"{action}:{context.get('task_type', 'unknown')}"
        return self._patterns.get(key, 0.5)

    def get_stats(self) -> dict:
        """Get feedback loop statistics."""
        if not self._outcomes:
            return {"total": 0, "success_rate": 0.0}

        total = len(self._outcomes)
        successes = sum(1 for o in self._outcomes if o["success"])
        return {
            "total": total,
            "success_rate": successes / total,
            "patterns": self._patterns,
        }


class AutonomyController:
    """Controller for autonomous operation.

    Manages the autonomous work loop with:
    - Task queue management
    - Automatic verification
    - Feedback loop learning
    - Error recovery

    Usage:
        controller = AutonomyController()
        controller.enable_auto_continue()

        # Main work loop
        while controller.should_continue():
            task = controller.get_next_task()
            if task:
                result = execute_task(task)
                controller.record_outcome(task, result)
    """

    def __init__(self, config: AutonomyConfig | None = None) -> None:
        self.config = config or AutonomyConfig()
        self._queue = TaskQueue()
        self._feedback = FeedbackLoop()
        self._running = False
        self._consecutive_errors = 0
        self._session_start = datetime.now()

        # Load state if exists
        self._load_state()

    def enable_auto_continue(self) -> None:
        """Enable automatic task continuation."""
        self.config.auto_continue = True
        self.config.level = AutonomyLevel.AUTONOMOUS

    def enable_full_autonomy(self) -> None:
        """Enable full autonomy with auto-commit."""
        self.config.auto_continue = True
        self.config.auto_verify = True
        self.config.auto_commit = True
        self.config.level = AutonomyLevel.FULL_AUTO

    def should_continue(self) -> bool:
        """Check if autonomous loop should continue."""
        if not self.config.auto_continue:
            return False

        if self._consecutive_errors >= self.config.max_consecutive_errors:
            return False

        return self._queue.pending_count > 0

    def get_next_task(self) -> dict | None:
        """Get next task from queue."""
        return self._queue.get_next()

    def add_task(
        self,
        task_id: str,
        priority: int = 0,
        context: dict | None = None,
    ) -> None:
        """Add task to queue."""
        self._queue.add(task_id, priority, context)

    def record_outcome(
        self,
        task: dict,
        result: TaskResult,
    ) -> None:
        """Record task outcome and update state."""
        if result.success:
            self._queue.mark_complete(task["id"])
            self._consecutive_errors = 0

            # Add follow-up tasks
            for next_task in result.next_tasks:
                self.add_task(next_task, priority=0)

        else:
            self._queue.mark_failed(task["id"])
            self._consecutive_errors += 1

        # Record to feedback loop
        if self.config.learn_from_outcomes:
            self._feedback.record(
                action=task.get("action", task["id"]),
                context=task.get("context", {}),
                result=result,
            )

        # Save state
        self._save_state()

    def get_recommendation(self, context: dict) -> dict:
        """Get recommended action based on learning."""
        if HAS_LEARNING:
            from .learning import suggest
            suggestions = suggest(context)
            if suggestions:
                return suggestions[0]

        # Fallback: use feedback loop
        best_action = None
        best_prob = 0.0

        for action in ["continue", "verify", "review", "commit"]:
            prob = self._feedback.get_success_probability(action, context)
            if prob > best_prob:
                best_prob = prob
                best_action = action

        return {"command": best_action or "continue", "confidence": best_prob}

    def get_status(self) -> dict:
        """Get current autonomy status."""
        return {
            "level": self.config.level.name,
            "auto_continue": self.config.auto_continue,
            "auto_verify": self.config.auto_verify,
            "auto_commit": self.config.auto_commit,
            "queue": self._queue.to_dict(),
            "feedback": self._feedback.get_stats(),
            "consecutive_errors": self._consecutive_errors,
            "session_duration_s": (datetime.now() - self._session_start).total_seconds(),
        }

    def _load_state(self) -> None:
        """Load state from disk."""
        state_file = Path(".claude/toolkit/autonomy_state.json")
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                    # Restore queue
                    for task in state.get("queue", {}).get("pending", []):
                        self._queue.add(task["id"], task.get("priority", 0), task.get("context"))
            except Exception:
                pass

    def _save_state(self) -> None:
        """Save state to disk."""
        state_file = Path(".claude/toolkit/autonomy_state.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(state_file, "w") as f:
                json.dump(self.get_status(), f, indent=2)
        except Exception:
            pass


# Global controller
_controller: AutonomyController | None = None


def get_controller() -> AutonomyController:
    """Get global autonomy controller."""
    global _controller
    if _controller is None:
        _controller = AutonomyController()
    return _controller


def enable_autonomy(level: str = "autonomous") -> AutonomyController:
    """Enable autonomous operation.

    Args:
        level: "guided", "autonomous", or "full_auto"

    Returns:
        Configured AutonomyController
    """
    controller = get_controller()

    if level == "guided":
        controller.config.level = AutonomyLevel.GUIDED
        controller.config.auto_continue = True
        controller.config.auto_verify = True
    elif level == "autonomous":
        controller.enable_auto_continue()
    elif level == "full_auto":
        controller.enable_full_autonomy()

    return controller
