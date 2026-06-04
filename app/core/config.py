#!/usr/bin/env python3
"""Configuration settings for MGLTickets."""

import os

from starlette.config import Config
from pydantic import SecretStr

# Determine the ENV file
env_file = ".env.development"  # Default to development

# Set ENVIRONMENT variable to "production" in production environments to load .env.production. 
# Linux
# export ENVIRONMENT=production

if os.getenv("ENVIRONMENT", "development") == "production":  # Fall back to "development" if ENVIRONMENT is not set
    env_file = ".env.production"

# Load environment variables from a .env.development file in dev and a .env.production file in production
config = Config(env_file)

# App settings
APP_NAME: str = config("APP_NAME", default="MGLTickets API")
APP_VERSION: str = config("APP_VERSION", default="1.0.0")
DEBUG: bool = config("DEBUG", cast=bool, default=False)

# Database connection settings
DB_USER: str = config("DB_USER")
DB_PASSWORD: SecretStr = config("DB_PASSWORD", cast=SecretStr)
DB_HOST: str = config("DB_HOST", default="localhost")
DB_PORT: int = config("DB_PORT", cast=int, default=5432)
DB_NAME: str = config("DB_NAME")

# Construct the SQLAlchemy Database URI
# get_secret_value() is used to retrieve the actual password string from the Secret object
DATABASE_URL: str = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD.get_secret_value()}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Change to this in alembic/env.py in production
ALEMBIC_DATABASE_URL: str = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD.get_secret_value()}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Optional SQLAlchemy settings
SQLALCHEMY_ECHO: bool = config("SQLALCHEMY_ECHO", cast=bool, default=False)

#Environment and cookie domain
ENVIRONMENT: str = config("ENVIRONMENT", default="development")
COOKIE_DOMAIN: str = config("COOKIE_DOMAIN", default=".mgltickets.com")

# Other secrets
SECRET_KEY: str = config("SECRET_KEY", cast=SecretStr)
ALGORITHM: str = config("ALGORITHM", default="HS256")

# Frontend URL
FRONTEND_URL: str = config("FRONTEND_URL", default="https://mgltickets.com")

# API URL
API_URL: str = config("API_URL", default="https://api.mgltickets.com")

# CORS settings
ALLOWED_ORIGINS: list[str] = config(
    "ALLOWED_ORIGINS",
    default="http://mgltickets.local:3000,http://organizer.mgltickets.local:3001,http://admin.mgltickets.local:3002",
).split(",")

# Upload directories
# config.py — add these two lines near UPLOADS_EVENTS_DIR
UPLOADS_EVENTS_DIR: str = config("UPLOADS_EVENTS_DIR", default="app/uploads/events")
UPLOADS_EVENTS_URL_PATH: str = config("UPLOADS_EVENTS_URL_PATH", default="uploads/events")

UPLOADS_PROFILES_DIR: str = config("UPLOADS_PROFILES_DIR", default="app/uploads/profiles")
UPLOADS_PROFILES_URL_PATH: str = config("UPLOADS_PROFILES_URL_PATH", default="uploads/profiles")

#SendGrid email services
SENDGRID_API_KEY: SecretStr = config("SENDGRID_API_KEY", cast=SecretStr)
SENDGRID_NO_REPLY_EMAIL: str = config("SENDGRID_NO_REPLY_EMAIL")
SENDGRID_SUPPORT_EMAIL: str = config("SENDGRID_SUPPORT_EMAIL")
SENDGRID_BILLING_EMAIL: str = config("SENDGRID_BILLING_EMAIL")
SENDGRID_PRESS_EMAIL: str = config("SENDGRID_PRESS_EMAIL")
SENDGRID_PARTNERSHIP_EMAIL: str = config("SENDGRID_PARTNERSHIP_EMAIL")
SENDGRID_FROM_NAME: str = config("SENDGRID_FROM_NAME")

# Google reCAPTCHA configuration
RECAPTCHA_SECRET_KEY: str = config("RECAPTCHA_SECRET_KEY")
RECAPTCHA_VERIFY_URL: str = config("RECAPTCHA_VERIFY_URL", default="https://www.google.com/recaptcha/api/siteverify")
MIN_RECAPTCHA_SCORE: float = config("MIN_RECAPTCHA_SCORE", cast=float, default=0.5)