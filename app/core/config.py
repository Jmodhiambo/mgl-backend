#!/usr/bin/env python3
"""Configuration settings for MGLTickets."""

from starlette.config import Config
from starlette.datastructures import Secret

# Load environment variables from a .env file
config = Config(".env")

# App settings
APP_NAME: str = config("APP_NAME", default="MGLTickets API")
APP_VERSION: str = config("APP_VERSION", default="1.0.0")
DEBUG: bool = config("DEBUG", cast=bool, default=False)

# Database connection settings
DB_USER: str = config("DB_USER")
DB_PASSWORD: Secret = config("DB_PASSWORD", cast=Secret)
DB_HOST: str = config("DB_HOST", default="localhost")
DB_PORT: int = config("DB_PORT", cast=int, default=5432)
DB_NAME: str = config("DB_NAME")

# Construct the SQLAlchemy Database URI
# get_secret_value() is used to retrieve the actual password string from the Secret object
DATABASE_URL: str = config (
    "SQLITE_DATABASE_URL",
    default=(
        f"postgresql+asyncpg://{DB_USER}:{str(DB_PASSWORD)}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    ),
)

# Change to this in alembic/env.py in production
ALEMBIC_DATABASE_URL: str = config (
    "ALEMBIC_DATABASE_URL",
    default=(
        f"postgresql+psycopg2://{DB_USER}:{str(DB_PASSWORD)}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    ),
)

# Optional SQLAlchemy settings
SQLALCHEMY_ECHO: bool = config("SQLALCHEMY_ECHO", cast=bool, default=False)

# Other secrets
SECRET_KEY: str = config("SECRET_KEY", cast=Secret)
ALGORITHM: str = config("ALGORITHM", default="HS256")

# Frontend URL
FRONTEND_URL: str = config("FRONTEND_URL", default="http://localhost:3000")

# CORS settings
ALLOWED_ORIGINS: list[str] = config(
    "ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# Upload directories
UPLOADS_EVENTS_DIR: str = config("UPLOADS_EVENTS_DIR", default="app/uploads/events")
UPLOADS_PROFILES_DIR: str = config("UPLOADS_PROFILES_DIR", default="app/uploads/profiles")

#SendGrid email services
SENDGRID_API_KEY: Secret = config("SENDGRID_API_KEY", cast=Secret)
SENDGRID_NO_REPLY_EMAIL= config("SENDGRID_NO_REPLY_EMAIL")
SENDGRID_SUPPORT_EMAIL= config("SENDGRID_SUPPORT_EMAIL")
SENDGRID_BILLING_EMAIL= config("SENDGRID_BILLING_EMAIL")
SENDGRID_PRESS_EMAIL= config("SENDGRID_PRESS_EMAIL")
SENDGRID_PARTNERSHIP_EMAIL= config("SENDGRID_PARTNERSHIP_EMAIL")
SENDGRID_FROM_NAME= config("SENDGRID_FROM_NAME")