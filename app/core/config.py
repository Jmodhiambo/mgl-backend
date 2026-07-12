#!/usr/bin/env python3
"""Configuration settings for MGLTickets."""

import os

from starlette.config import Config
from pydantic import SecretStr

# Determine the ENV file
env_file = ".env.development"  # Default to development

# Set ENVIRONMENT variable to "production" in production environments to load .env.production.
# Linux: export ENVIRONMENT=production
if os.getenv("ENVIRONMENT", "development") == "production":
    env_file = ".env.production"

config = Config(env_file)

# ── App settings ──────────────────────────────────────────────────────────── #
APP_NAME: str = config("APP_NAME", default="MGLTickets API")
APP_VERSION: str = config("APP_VERSION", default="1.0.0")
DEBUG: bool = config("DEBUG", cast=bool, default=False)

# ── Database ──────────────────────────────────────────────────────────────── #
DB_USER: str = config("DB_USER")
DB_PASSWORD: SecretStr = config("DB_PASSWORD", cast=SecretStr)
DB_HOST: str = config("DB_HOST", default="localhost")
DB_PORT: int = config("DB_PORT", cast=int, default=5432)
DB_NAME: str = config("DB_NAME")

DATABASE_URL: str = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD.get_secret_value()}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

ALEMBIC_DATABASE_URL: str = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD.get_secret_value()}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

SQLALCHEMY_ECHO: bool = config("SQLALCHEMY_ECHO", cast=bool, default=False)

# ── Environment & cookies ─────────────────────────────────────────────────── #
ENVIRONMENT: str = config("ENVIRONMENT", default="development")
COOKIE_DOMAIN: str = config("COOKIE_DOMAIN", default=".mgltickets.com")

# ── Secrets ───────────────────────────────────────────────────────────────── #
TICKET_QR_SECRET: str = config("TICKET_QR_SECRET")
SECRET_KEY: str = config("SECRET_KEY", cast=SecretStr)
ALGORITHM: str = config("ALGORITHM", default="HS256")

# ── URLs ──────────────────────────────────────────────────────────────────── #
FRONTEND_URL: str = config("FRONTEND_URL", default="https://mgltickets.com")
API_URL: str = config("API_URL", default="https://api.mgltickets.com")

# ── CORS ──────────────────────────────────────────────────────────────────── #
ALLOWED_ORIGINS: list[str] = config(
    "ALLOWED_ORIGINS",
    default="http://mgltickets.local:3000,http://organizer.mgltickets.local:3001,http://admin.mgltickets.local:3002",
).split(",")

# ── File uploads ──────────────────────────────────────────────────────────── #
UPLOADS_EVENTS_DIR: str = config("UPLOADS_EVENTS_DIR", default="app/uploads/events")
UPLOADS_EVENTS_URL_PATH: str = config("UPLOADS_EVENTS_URL_PATH", default="uploads/events")
UPLOADS_PROFILES_DIR: str = config("UPLOADS_PROFILES_DIR", default="app/uploads/profiles")
UPLOADS_PROFILES_URL_PATH: str = config("UPLOADS_PROFILES_URL_PATH", default="uploads/profiles")

# ── M-Pesa / Daraja ──────────────────────────────────────────────────────── #
MPESA_CONSUMER_KEY: str = config("MPESA_CONSUMER_KEY", default="")
MPESA_CONSUMER_SECRET: str = config("MPESA_CONSUMER_SECRET", default="")
MPESA_SHORTCODE: str = config("MPESA_SHORTCODE", default="")
MPESA_PASSKEY: str = config("MPESA_PASSKEY", default="")
MPESA_CALLBACK_URL: str = config("MPESA_CALLBACK_URL", default="")
MPESA_ENV: str = config("MPESA_ENV", default="sandbox")

# ── Email (provider-agnostic) ─────────────────────────────────────────────── #
EMAIL_API_KEY: str = config("EMAIL_API_KEY")
EMAIL_FROM_NO_REPLY: str = config("EMAIL_FROM_NO_REPLY")
EMAIL_FROM_SUPPORT: str = config("EMAIL_FROM_SUPPORT")
EMAIL_FROM_BILLING: str = config("EMAIL_FROM_BILLING")
EMAIL_FROM_PRESS: str = config("EMAIL_FROM_PRESS")
EMAIL_FROM_PARTNERSHIP: str = config("EMAIL_FROM_PARTNERSHIP")
EMAIL_FROM_NAME: str = config("EMAIL_FROM_NAME", default="MGLTickets")

# When True, emails are logged but never sent — safe for local development.
# Set EMAIL_DEV_MODE=false in .env.production.
EMAIL_DEV_MODE: bool = config("EMAIL_DEV_MODE", cast=bool, default=True)

# ── Google reCAPTCHA ──────────────────────────────────────────────────────── #
RECAPTCHA_SECRET_KEY: str = config("RECAPTCHA_SECRET_KEY")
RECAPTCHA_VERIFY_URL: str = config(
    "RECAPTCHA_VERIFY_URL",
    default="https://www.google.com/recaptcha/api/siteverify",
)
MIN_RECAPTCHA_SCORE: float = config("MIN_RECAPTCHA_SCORE", cast=float, default=0.5)