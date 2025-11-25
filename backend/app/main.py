#!/usr/bin/env python3
"""FastAPI entrypoint for MGLTickets."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.logging_config import configure_logging, logger
from app.core.logging_middleware import LoggingMiddleware
from app.api.routes import auth, events
from app.db.session import engine
from app.db.models import *

configure_logging() # Initialize logging configuration

app = FastAPI()

# Middlewares
# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Mount Static Files
# Static files for serving uploaded event flyers and profile images
app.mount("/uploads/events", StaticFiles(directory="app/uploads/events"), name="event_uploads")
app.mount("/uploads/profiles", StaticFiles(directory="app/uploads/profiles"), name="profile_uploads")


# Routes
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(events.router, prefix="/api/v1", tags=["Events"])

# Auto-create tables in the database
@app.on_event("startup")
async def startup_event():
    """Automatically create the database tables if they don't exist."""
    logger.info("Starting up MGLTickets...")
    # Removing create_all() since we have alembic to handle schema creation
    # Base.metadata.create_all(bind=engine)
    # logger.info("MGLTickets started.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing database connections...")
    engine.dispose()
    logger.info("Shutting down MGLTickets...")
# Register handlers globally