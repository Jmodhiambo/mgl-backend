#/usr/bin/env python3
"""Route registery for MGLTickets."""

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as user_router
from app.api.routes.events import router as events_router
from app.api.routes.bookings import router as bookings_router

# Admin routes
from app.api.routes.admin.user_admin import router as admin_user_router
from app.api.routes.admin.event_admin import router as admin_events_router

# Organizer routes
from app.api.routes.organizer.events_organizer import router as events_router

def register_routes(app: FastAPI) -> None:
    """Registers routes for MGLTickets."""
    app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
    app.include_router(user_router, prefix="/api/v1", tags=["Users"])
    app.include_router(events_router, prefix="/api/v1", tags=["Events"])
    app.include_router(bookings_router, prefix="/api/v1", tags=["Bookings"])

    # Organizer routes
    app.include_router(events_router, prefix="/api/v1", tags=["Events-Organizer"])

    # Admin routes
    app.include_router(admin_user_router, prefix="/api/v1", tags=["User-Admin"])
    app.include_router(admin_events_router, prefix="/api/v1", tags=["Event-Admin"])
    app.include_router(bookings_router, prefix="/api/v1", tags=["Bookings"])

