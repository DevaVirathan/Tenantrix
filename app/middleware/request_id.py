"""X-Request-ID middleware — attach a unique request ID to every request/response."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assign a unique ``X-Request-ID`` to every incoming request.

    Priority:
      1. Use the value from the incoming ``X-Request-ID`` header (if present and a valid UUID).
      2. Otherwise generate a new UUID4.

    The resolved ID is:
      - Stored on ``request.state.request_id`` for use by other middleware/routes/logging.
      - Echoed back in the ``X-Request-ID`` response header.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        raw = request.headers.get("X-Request-ID", "")
        try:
            request_id = str(uuid.UUID(raw))
        except (ValueError, AttributeError):
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
