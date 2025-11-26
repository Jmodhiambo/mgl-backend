#/usr/bin/env python3
"""Route registery for MGLTickets."""

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.events import router as events_router


def register_routes(app: FastAPI) -> None:
    """Registers routes for MGLTickets."""
    app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
    app.include_router(events_router, prefix="/api/v1", tags=["Events"])
