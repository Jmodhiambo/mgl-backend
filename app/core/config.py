#!/usr/bin/env python3
"""Configuration settings for MGLTickets."""

from starlette.config import Config
from starlette.datastructures import Secret

# Load environment variables from a .env file
config = Config(".env")

# Database connection settings
DB_USER: str = config("DB_USER")
DB_PASSWORD: Secret = config("DB_PASSWORD", cast=Secret)
DB_HOST: str = config("DB_HOST", default="localhost")
DB_PORT: int = config("DB_PORT", cast=int, default=5432)
DB_NAME: str = config("DB_NAME")

# Construct the SQLAlchemy Database URI
# get_secret_value() is used to retrieve the actual password string from the Secret object
DATABASE_URL: str = (
    f"postgresql+asyncpg://{DB_USER}:{str(DB_PASSWORD)}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

ALEMBIC_DATABASE_URL: str = (
    f"postgresql+psycopg2://{DB_USER}:{str(DB_PASSWORD)}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Optional SQLAlchemy settings
SQLALCHEMY_ECHO: bool = config("SQLALCHEMY_ECHO", cast=bool, default=False)

# Other secrets
SECRET_KEY: str = config("SECRET_KEY", cast=Secret)
ALGORITHM: str = config("ALGORITHM", default="HS256")

# Frontend URL
FRONTEND_URL: str = config("FRONTEND_URL", default="http://localhost:5173")