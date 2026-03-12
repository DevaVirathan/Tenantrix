"""WebSocket connection manager — singleton instance for broadcasting events."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Tracks active WebSocket connections grouped by org_id."""

    def __init__(self) -> None:
        # org_id (str) -> set of active WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, org_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(org_id, set()).add(websocket)
        logger.info("WS connected: org=%s, total=%d", org_id, len(self._connections[org_id]))

    def disconnect(self, org_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(org_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                del self._connections[org_id]
        logger.info("WS disconnected: org=%s", org_id)

    async def broadcast_to_org(
        self, org_id: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Send a JSON message to all connections in an org. Removes dead connections."""
        conns = self._connections.get(org_id)
        if not conns:
            return

        message = {"event": event_type, "data": payload}
        dead: list[WebSocket] = []

        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            conns.discard(ws)
        if not conns:
            self._connections.pop(org_id, None)

    def broadcast_to_org_nowait(
        self, org_id: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Fire-and-forget broadcast — safe to call from sync endpoints."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running — skip broadcast silently
            return
        loop.create_task(self.broadcast_to_org(org_id, event_type, payload))


# Singleton — import this from anywhere to broadcast
ws_manager = ConnectionManager()
