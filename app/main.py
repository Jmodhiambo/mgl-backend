#!/usr/bin/env python3
"""FastAPI entrypoint for MGLTickets."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import (
    APP_NAME,
    APP_VERSION,
    ALLOWED_ORIGINS,
    UPLOADS_EVENTS_DIR,
    UPLOADS_PROFILES_DIR
)
from app.core.logging_config import configure_logging, logger
from app.core.logging_middleware import LoggingMiddleware
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.core.route_registery import register_routes
from app.db.session import async_engine
from app.db import models

configure_logging() # Initialize logging configuration

# Lifespan (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    logger.info(f"Starting up {APP_NAME} v{APP_VERSION}...")
    start_scheduler()
    yield
    logger.info(f"Shutting down {APP_NAME}...")
    shutdown_scheduler()
    await async_engine.dispose()
    logger.info(f"{APP_NAME} shut down successfully.")

app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

# Enable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Mount Static Files
# Static files for serving uploaded event flyers and profile images
app.mount("/uploads/events", StaticFiles(directory=UPLOADS_EVENTS_DIR), name="event_uploads")
app.mount("/uploads/profiles", StaticFiles(directory=UPLOADS_PROFILES_DIR), name="profile_uploads")


# Register routes from app.core.route_registery
register_routes(app)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "app": "MGLTickets API",
        "version": "1.0.0"
    }
