"""Toolkit Learning Module - XGBoost-based self-improvement.

Uses XGBoost to learn from usage patterns and improve toolkit recommendations.

Features:
- Track command usage and outcomes
- Learn optimal command selection
- Predict success likelihood for approaches
- Continuously improve based on feedback

Usage:
    from toolkit.learning import ToolkitLearner

    learner = ToolkitLearner()
    learner.record_interaction(command="continue", context={...}, outcome="success")

    # Get recommendations
    recommendations = learner.suggest_commands(context={...})
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import XGBoost, fallback to simple heuristics if not available
try:
    import xgboost as xgb
    import numpy as np
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


@dataclass
class Interaction:
    """Record of a toolkit interaction."""

    timestamp: str
    command: str
    context: dict[str, Any]
    outcome: str  # "success", "failure", "partial"
    duration_ms: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class LearningConfig:
    """Configuration for toolkit learning."""

    data_dir: str = ".claude/toolkit/data"
    model_dir: str = ".claude/toolkit/models"
    min_samples_for_training: int = 50
    retrain_threshold: int = 20  # New samples before retraining
    feature_extraction_enabled: bool = True


# Feature extractors for different context types
CONTEXT_FEATURES = {
    "file_count": lambda ctx: ctx.get("file_count", 0),
    "has_tests": lambda ctx: 1 if ctx.get("has_tests") else 0,
    "complexity_score": lambda ctx: ctx.get("complexity_score", 0),
    "error_count": lambda ctx: ctx.get("error_count", 0),
    "time_of_day": lambda ctx: datetime.now().hour,
    "is_new_feature": lambda ctx: 1 if ctx.get("is_new_feature") else 0,
    "has_dependencies": lambda ctx: 1 if ctx.get("dependencies") else 0,
}

# Command categories for classification
COMMAND_CATEGORIES = {
    "workflow": ["continue", "status", "verify", "review", "handoff"],
    "planning": ["think", "think-parallel", "constraints", "decide", "perspectives"],
    "implementation": ["build-prd", "tdd", "delegate", "expert", "frontend-design"],
    "maintenance": ["reload", "fresh", "context", "recover", "index"],
}


class ToolkitLearner:
    """XGBoost-based learning for toolkit improvement.

    Tracks interactions, learns patterns, and provides smart recommendations.
    """

    def __init__(self, config: LearningConfig | None = None) -> None:
        self.config = config or LearningConfig()
        self.interactions: list[Interaction] = []
        self.models: dict[str, Any] = {}
        self._new_samples = 0

        # Ensure directories exist
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.model_dir).mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load_interactions()
        self._load_models()

    def record_interaction(
        self,
        command: str,
        context: dict[str, Any],
        outcome: str,
        duration_ms: int = 0,
        metadata: dict | None = None,
    ) -> None:
        """Record a toolkit interaction for learning.

        Args:
            command: The slash command used
            context: Context at time of invocation
            outcome: "success", "failure", or "partial"
            duration_ms: Time taken
            metadata: Additional data
        """
        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            command=command,
            context=context,
            outcome=outcome,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        self.interactions.append(interaction)
        self._new_samples += 1

        # Save interaction
        self._save_interaction(interaction)

        # Retrain if threshold reached
        if (
            self._new_samples >= self.config.retrain_threshold
            and len(self.interactions) >= self.config.min_samples_for_training
        ):
            self._retrain_models()
            self._new_samples = 0

    def suggest_commands(
        self,
        context: dict[str, Any],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Get command suggestions based on context.

        Args:
            context: Current context
            top_k: Number of suggestions to return

        Returns:
            List of suggestions with command and confidence
        """
        if not HAS_XGBOOST or "command_predictor" not in self.models:
            return self._heuristic_suggestions(context, top_k)

        # Extract features
        features = self._extract_features(context)

        try:
            model = self.models["command_predictor"]
            dmatrix = xgb.DMatrix(np.array([features]))
            predictions = model.predict(dmatrix)

            # Get top-k commands
            command_list = self._get_command_list()
            scored = list(zip(command_list, predictions[0]))
            scored.sort(key=lambda x: x[1], reverse=True)

            return [
                {"command": cmd, "confidence": float(score)}
                for cmd, score in scored[:top_k]
            ]
        except Exception:
            return self._heuristic_suggestions(context, top_k)

    def predict_success(
        self,
        command: str,
        context: dict[str, Any],
    ) -> float:
        """Predict success likelihood for a command.

        Args:
            command: Command to evaluate
            context: Current context

        Returns:
            Probability of success (0-1)
        """
        if not HAS_XGBOOST or "success_predictor" not in self.models:
            return self._heuristic_success_probability(command, context)

        # Extract features + command encoding
        features = self._extract_features(context)
        command_idx = self._encode_command(command)
        features.append(command_idx)

        try:
            model = self.models["success_predictor"]
            dmatrix = xgb.DMatrix(np.array([features]))
            return float(model.predict(dmatrix)[0])
        except Exception:
            return self._heuristic_success_probability(command, context)

    def get_stats(self) -> dict[str, Any]:
        """Get learning statistics.

        Returns:
            Dict with interaction counts, success rates, etc.
        """
        if not self.interactions:
            return {"total_interactions": 0}

        total = len(self.interactions)
        successes = sum(1 for i in self.interactions if i.outcome == "success")

        # Command usage counts
        command_counts = {}
        for interaction in self.interactions:
            cmd = interaction.command
            command_counts[cmd] = command_counts.get(cmd, 0) + 1

        return {
            "total_interactions": total,
            "success_rate": successes / total if total > 0 else 0,
            "command_usage": command_counts,
            "has_xgboost": HAS_XGBOOST,
            "models_trained": list(self.models.keys()),
            "pending_samples": self._new_samples,
        }

    def _extract_features(self, context: dict[str, Any]) -> list[float]:
        """Extract numerical features from context."""
        features = []
        for name, extractor in CONTEXT_FEATURES.items():
            try:
                features.append(float(extractor(context)))
            except Exception:
                features.append(0.0)
        return features

    def _encode_command(self, command: str) -> int:
        """Encode command as integer."""
        command_list = self._get_command_list()
        try:
            return command_list.index(command)
        except ValueError:
            return len(command_list)  # Unknown command

    def _get_command_list(self) -> list[str]:
        """Get flat list of all commands."""
        commands = []
        for category_commands in COMMAND_CATEGORIES.values():
            commands.extend(category_commands)
        return commands

    def _heuristic_suggestions(
        self,
        context: dict[str, Any],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Fallback heuristic suggestions when XGBoost unavailable."""
        suggestions = []

        # Basic heuristics based on context
        if context.get("has_errors"):
            suggestions.append({"command": "recover", "confidence": 0.8})

        if context.get("is_new_feature"):
            suggestions.append({"command": "constraints", "confidence": 0.7})
            suggestions.append({"command": "think", "confidence": 0.6})

        if context.get("needs_review"):
            suggestions.append({"command": "review", "confidence": 0.7})
            suggestions.append({"command": "verify", "confidence": 0.6})

        # Default: continue is usually good
        suggestions.append({"command": "continue", "confidence": 0.5})
        suggestions.append({"command": "status", "confidence": 0.4})

        return suggestions[:top_k]

    def _heuristic_success_probability(
        self,
        command: str,
        context: dict[str, Any],
    ) -> float:
        """Fallback heuristic success prediction."""
        # Base probabilities by command category
        for category, commands in COMMAND_CATEGORIES.items():
            if command in commands:
                if category == "workflow":
                    return 0.8  # High success for workflow commands
                elif category == "planning":
                    return 0.7
                elif category == "implementation":
                    return 0.6
                else:
                    return 0.5
        return 0.5

    def _load_interactions(self) -> None:
        """Load interactions from disk."""
        data_file = Path(self.config.data_dir) / "interactions.jsonl"
        if data_file.exists():
            with open(data_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        self.interactions.append(Interaction(**data))
                    except Exception:
                        continue

    def _save_interaction(self, interaction: Interaction) -> None:
        """Append interaction to disk."""
        data_file = Path(self.config.data_dir) / "interactions.jsonl"
        with open(data_file, "a") as f:
            f.write(json.dumps({
                "timestamp": interaction.timestamp,
                "command": interaction.command,
                "context": interaction.context,
                "outcome": interaction.outcome,
                "duration_ms": interaction.duration_ms,
                "metadata": interaction.metadata,
            }) + "\n")

    def _load_models(self) -> None:
        """Load trained models from disk."""
        if not HAS_XGBOOST:
            return

        model_dir = Path(self.config.model_dir)
        for model_file in model_dir.glob("*.json"):
            model_name = model_file.stem
            try:
                model = xgb.Booster()
                model.load_model(str(model_file))
                self.models[model_name] = model
            except Exception:
                continue

    def _retrain_models(self) -> None:
        """Retrain XGBoost models with current data."""
        if not HAS_XGBOOST or len(self.interactions) < self.config.min_samples_for_training:
            return

        try:
            # Prepare training data
            X = []
            y_command = []
            y_success = []

            command_list = self._get_command_list()

            for interaction in self.interactions:
                features = self._extract_features(interaction.context)
                X.append(features)

                # Command prediction target
                try:
                    cmd_idx = command_list.index(interaction.command)
                except ValueError:
                    cmd_idx = len(command_list)
                y_command.append(cmd_idx)

                # Success prediction target
                y_success.append(1.0 if interaction.outcome == "success" else 0.0)

            X = np.array(X)
            y_command = np.array(y_command)
            y_success = np.array(y_success)

            # Train command predictor (multi-class)
            dtrain = xgb.DMatrix(X, label=y_command)
            params = {
                "objective": "multi:softprob",
                "num_class": len(command_list) + 1,
                "max_depth": 4,
                "eta": 0.1,
            }
            self.models["command_predictor"] = xgb.train(params, dtrain, num_boost_round=50)

            # Train success predictor (binary)
            dtrain_success = xgb.DMatrix(
                np.column_stack([X, y_command]),
                label=y_success,
            )
            params_success = {
                "objective": "binary:logistic",
                "max_depth": 4,
                "eta": 0.1,
            }
            self.models["success_predictor"] = xgb.train(params_success, dtrain_success, num_boost_round=50)

            # Save models
            model_dir = Path(self.config.model_dir)
            self.models["command_predictor"].save_model(str(model_dir / "command_predictor.json"))
            self.models["success_predictor"].save_model(str(model_dir / "success_predictor.json"))

        except Exception:
            pass  # Silently fail, fall back to heuristics


# Global learner instance
_learner: ToolkitLearner | None = None


def get_learner() -> ToolkitLearner:
    """Get global toolkit learner instance."""
    global _learner
    if _learner is None:
        _learner = ToolkitLearner()
    return _learner


def record(
    command: str,
    context: dict[str, Any],
    outcome: str,
    **kwargs,
) -> None:
    """Convenience function to record an interaction."""
    get_learner().record_interaction(command, context, outcome, **kwargs)


def suggest(context: dict[str, Any], top_k: int = 3) -> list[dict[str, Any]]:
    """Convenience function to get suggestions."""
    return get_learner().suggest_commands(context, top_k)
