"""WebSocket endpoint for real-time updates, scoped per organisation."""

from __future__ import annotations

import logging

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{org_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    org_id: str,
    token: str = Query(...),  # noqa: B008
) -> None:
    """
    Authenticate via JWT query param, then keep the connection open for
    real-time event streaming scoped to the organisation.
    """
    # --- Authenticate ---
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001, reason="Token expired")
        return
    except jwt.PyJWTError:
        await websocket.close(code=4003, reason="Invalid token")
        return

    user_id: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")
    if user_id is None or token_type != "access":
        await websocket.close(code=4003, reason="Invalid token")
        return

    # --- Connect ---
    await ws_manager.connect(org_id, websocket)

    try:
        # Keep alive — read messages (client may send pings / heartbeats)
        while True:
            # We don't expect meaningful client messages, but we must read to
            # detect disconnections.  A ping/pong or small JSON is fine.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS error: org=%s user=%s", org_id, user_id)
    finally:
        ws_manager.disconnect(org_id, websocket)
