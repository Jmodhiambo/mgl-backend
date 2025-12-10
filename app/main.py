#!/usr/bin/env python3
"""FastAPI entrypoint for MGLTickets."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.logging_config import configure_logging, logger
from app.core.logging_middleware import LoggingMiddleware
from app.core.route_registery import register_routes
from app.db.session import async_engine
from app.db import models

configure_logging() # Initialize logging configuration

# Lifespan (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    logger.info("Starting up MGLTickets...")
    yield
    logger.info("Shutting down MGLTickets...")
    async_engine.dispose()
    logger.info("MGLTickets shut down.")

app = FastAPI(lifespan=lifespan)

# Middlewares
# Enable CORS Middleware
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Mount Static Files
# Static files for serving uploaded event flyers and profile images
app.mount("/uploads/events", StaticFiles(directory="app/uploads/events"), name="event_uploads")
app.mount("/uploads/profiles", StaticFiles(directory="app/uploads/profiles"), name="profile_uploads")


# Register routes from app.core.route_registery
register_routes(app)