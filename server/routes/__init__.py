"""Aggregates API routers."""

from . import artifacts, execute, execute_sync, health, sessions, uploads, vuegraphs, workflows, websocket, batch, tools, observability_sessions, observability_ws

ALL_ROUTERS = [
    health.router,
    vuegraphs.router,
    workflows.router,
    uploads.router,
    artifacts.router,
    sessions.router,
    observability_sessions.router,
    batch.router,
    execute.router,
    execute_sync.router,
    tools.router,
    websocket.router,
    observability_ws.router,
]

__all__ = ["ALL_ROUTERS"]