"""Health check endpoints.

Reference: Ops-Runbook-v3.0.md Section 9.2
- /healthz: Liveness probe (is the process alive?)
- /readyz: Readiness probe (is the service ready to accept traffic?)
- /metrics: Prometheus metrics endpoint
"""

from typing import Any

from fastapi import APIRouter, Response, status

router = APIRouter(tags=["health"])


# Health status tracking
_ready: bool = False
_components: dict[str, bool] = {
    "database": False,
    "redis": False,
    "vad": False,
    "asr": False,
    "tts": False,
    "llm": False,
}


def set_ready(ready: bool) -> None:
    """Set overall readiness status."""
    global _ready
    _ready = ready


def set_component_health(component: str, healthy: bool) -> None:
    """Set health status for a specific component."""
    if component in _components:
        _components[component] = healthy


def get_component_health() -> dict[str, bool]:
    """Get health status of all components."""
    return _components.copy()


@router.get("/healthz", response_model=dict[str, str])
async def healthz() -> dict[str, str]:
    """Liveness probe.

    Returns 200 if the process is alive.
    Kubernetes uses this to know when to restart the container.
    """
    return {"status": "alive"}


@router.get("/readyz")
async def readyz(response: Response) -> dict[str, Any]:
    """Readiness probe.

    Returns 200 if the service is ready to accept traffic.
    Returns 503 if any critical component is unhealthy.
    """
    # Check critical components for readiness
    critical_components = ["vad", "asr", "tts", "llm"]
    all_critical_ready = all(_components.get(c, False) for c in critical_components)

    if _ready and all_critical_ready:
        return {
            "status": "ready",
            "components": _components,
        }

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "not_ready",
        "components": _components,
    }


@router.get("/health")
async def health(response: Response) -> dict[str, Any]:
    """Combined health endpoint for backward compatibility.

    Provides both liveness and readiness information.
    """
    critical_components = ["vad", "asr", "tts", "llm"]
    all_critical_ready = all(_components.get(c, False) for c in critical_components)

    status_str = "healthy" if (_ready and all_critical_ready) else "degraded"

    if not _ready or not all_critical_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": status_str,
        "ready": _ready,
        "components": _components,
    }
