#!/usr/bin/env python3
"""Logging middleware for MGLTickets."""

from typing import Awaitable, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import logger, user_id_var, role_var


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches contextual user data to each log entry.
    BaseHTTPMiddleware allows us to run code before and after each request.
    """

    def __init__(self, app: ASGIApp):
        """Initializes the middleware with the FastAPI app instance"""
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Runs for every HTTP request, and logs the request and response.
        """
        # Extract user from request
        user = getattr(request.state, "user", None)

        if user:
            user_id_var.set(str(getattr(user, "id", "unknown")))
            role_var.set(str(getattr(user, "role", "unknown")))
        else:
            user_id_var.set("anonymous")
            role_var.set("guest")

        logger.info("Incoming request", extra={"extra": {
            "method": request.method,
            "path": request.url.path,
        }})

        response = await call_next(request)

        logger.info("Outgoing response", extra={"extra": {
            "status": response.status_code,
            "path": request.url.path,
        }})

        return response
