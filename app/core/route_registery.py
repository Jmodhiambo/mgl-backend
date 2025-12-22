#/usr/bin/env python3
"""Route registery for MGLTickets."""

from fastapi import FastAPI

# Authentication route
from app.api.routers.auth.auth import router as auth_router

# User routes
from app.api.routers.user.users import router as user_router
from app.api.routers.user.events import router as events_router
from app.api.routers.user.bookings import router as bookings_router
from app.api.routers.user.payments import router as payments_router 
from app.api.routers.user.ticket_instances import router as ti_router
from app.api.routers.user.ticket_types import router as tt_router

# Organizer routes
from app.api.routers.organizer.user_organizer import router as organizer_user_router
from app.api.routers.organizer.events_organizer import router as organizer_events_router
from app.api.routers.organizer.bookings_organizer import router as organizer_bookings_router
from app.api.routers.organizer.payments_organizer import router as organizer_payments_router
from app.api.routers.organizer.ticket_instances_organizer import router as organizer_ti_router
from app.api.routers.organizer.ticket_types_organizer import router as organizer_tt_router

# Admin routes
from app.api.routers.admin.user_admin import router as admin_user_router
from app.api.routers.admin.event_admin import router as admin_events_router
from app.api.routers.admin.booking_admin import router as admin_bookings_router
from app.api.routers.admin.payment_admin import router as admin_payments_router
from app.api.routers.admin.ticket_instance_admin import router as admin_ti_router
from app.api.routers.admin.ticket_type_admin import router as admin_tt_router


def register_routes(app: FastAPI) -> None:
    """Registers routes for MGLTickets."""
    # Authentication routes
    app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])

    # User routes
    app.include_router(user_router, prefix="/api/v1", tags=["Users"])
    app.include_router(events_router, prefix="/api/v1", tags=["Events"])
    app.include_router(bookings_router, prefix="/api/v1", tags=["Bookings"])
    app.include_router(payments_router, prefix="/api/v1", tags=["Payments"])
    app.include_router(ti_router, prefix="/api/v1", tags=["Ticket Instances"])
    app.include_router(tt_router, prefix="/api/v1", tags=["Ticket Types"])

    # Organizer routes
    app.include_router(organizer_user_router, prefix="/api/v1", tags=["Users-Organizer"])
    app.include_router(organizer_events_router, prefix="/api/v1", tags=["Events-Organizer"])
    app.include_router(organizer_bookings_router, prefix="/api/v1", tags=["Bookings-Organizer"])
    app.include_router(organizer_payments_router, prefix="/api/v1", tags=["Payments-Organizer"])
    app.include_router(organizer_ti_router, prefix="/api/v1", tags=["Ticket Instances-Organizer"])
    app.include_router(organizer_tt_router, prefix="/api/v1", tags=["Ticket Types-Organizer"])
    
    # Admin routes
    app.include_router(admin_user_router, prefix="/api/v1", tags=["User-Admin"])
    app.include_router(admin_events_router, prefix="/api/v1", tags=["Event-Admin"])
    app.include_router(admin_bookings_router, prefix="/api/v1", tags=["Booking-Admin"])
    app.include_router(admin_payments_router, prefix="/api/v1", tags=["Payment-Admin"])
    app.include_router(admin_ti_router, prefix="/api/v1", tags=["Ticket Instance-Admin"])
    app.include_router(admin_tt_router, prefix="/api/v1", tags=["Ticket Type-Admin"])