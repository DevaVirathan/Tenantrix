"""Global exception handler — consistent error envelope for all HTTP errors."""

from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("tenantrix.errors")


def _error_response(
    request: Request,
    status_code: int,
    detail: object,
    *,
    request_id: str | None = None,
) -> JSONResponse:
    rid = request_id or getattr(request.state, "request_id", None)
    body = {"error": {"status_code": status_code, "detail": detail}}
    if rid:
        body["error"]["request_id"] = rid  # type: ignore[index]
    return JSONResponse(status_code=status_code, content=body)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    return _error_response(request, exc.status_code, exc.detail)


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
        for e in exc.errors()
    ]
    return _error_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, errors)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return _error_response(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "An unexpected error occurred. Please try again later.",
    )
