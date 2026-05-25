#!/usr/bin/env python3
"""
app/db/seed.py
──────────────────────────────────────────────────────────────────────────────
Database seeder for MGLTickets.

PURPOSE
───────
This module handles initial data seeding — inserting the first rows that the
application needs to function but that are not schema (Alembic handles schema).

The key distinction:
  - Alembic migrations  →  CREATE TABLE, ALTER TABLE, ADD COLUMN, etc.
  - This seed file      →  INSERT the first rows of data those tables need.

Keeping these two concerns separate means:
  1. Migrations stay clean — no data mixed into schema history.
  2. The seed is environment-aware — you can change default values here for
     dev, staging, or production without touching migration files.
  3. The seed is idempotent — safe to call on every single app startup with
     zero risk of duplicate rows or errors (it checks before inserting).

WHAT IS SEEDED
──────────────
  PlatformSettings (singleton — always exactly one row, id=1)
  ────────────────────────────────────────────────────────────
  Stores the platform-wide configuration that the admin Settings page reads
  and writes.  Examples: platform name, support email, fee percentage,
  maintenance mode toggle, session timeout duration.

  This row MUST exist before any admin opens the Settings page, otherwise
  GET /admin/settings returns HTTP 503.  The seed guarantees it is there.

  Why a singleton?
    All platform config lives in one place, one GET fetches everything, one
    PUT updates everything.  Simple and sufficient for a single-tenant app
    like MGLTickets.  If multi-tenancy is ever needed, this can be migrated
    to a key-value table (see architecture notes below).

  AdminNotificationPrefs (one row per admin user)
  ────────────────────────────────────────────────
  NOT seeded here — these rows are created on first save via an upsert in
  settings_repo.py.  Until an admin saves their preferences, the service
  layer returns all-True defaults without touching the database.

HOW IT IS CALLED
────────────────
  seed.py is called from app/main.py inside the FastAPI lifespan function,
  which runs once when the server starts:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await seed_platform_settings()   # ← here
        yield

  This means the seeder runs on every startup, but the idempotency check
  (if existing is not None: return) makes it a no-op after the first run.

STARTUP ORDER
─────────────
  The correct startup sequence is always:

    1. alembic upgrade head          ← creates / updates tables (schema)
    2. uvicorn app.main:app ...      ← starts app, lifespan calls seed (data)

  If you reverse this order and the app starts before Alembic has created the
  tables, the seed will raise a "relation does not exist" error.

  In a single command (production / CI):
    alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000

ADDING NEW SEEDS IN THE FUTURE
───────────────────────────────
  1. Add a new async function following the same pattern:
       - Query to check if the row(s) already exist.
       - Return early if they do (idempotency).
       - Insert with safe defaults if they don't.
       - Commit and log.
  2. Call the new function from run_all_seeds() at the bottom of this file.
  3. Do NOT use this file to seed large datasets (fixtures, test data, etc).
     Large seeds belong in a separate management command or a dedicated
     fixtures loader, not in a startup hook.

RESETTING SEEDS IN DEVELOPMENT
───────────────────────────────
  If you need to re-seed from scratch during development:
    1. Drop and recreate the database (or just the relevant table rows).
    2. Run:  alembic upgrade head && uvicorn app.main:app ...
  The seed will detect the missing row and insert it again.

  Alternatively, to reset just the settings row without dropping the DB:
    DELETE FROM platform_settings WHERE id = 1;
  Then restart the app — the seed will re-insert the defaults.

ARCHITECTURE NOTES
──────────────────
  The singleton pattern used here is appropriate for a single-tenant
  application.  If MGLTickets ever becomes multi-tenant or if settings
  need to be changed without an admin UI (e.g. via feature flags), consider
  migrating to one of these patterns:

    Key-value table:
      id | key                    | value  | updated_at
       1 | platform_fee_percent   | 5.0    | ...
       2 | maintenance_mode       | false  | ...
      Advantage: add new settings without schema migrations.

    Environment variables (via pydantic-settings):
      For static config that should not change at runtime (platform name,
      email provider credentials, session secret keys).
      Advantage: no database dependency for reading config.
"""

from sqlalchemy import select
from app.db.session import get_async_session
from app.db.models.platform_settings import PlatformSettings
from app.core.logging_config import logger


async def seed_platform_settings() -> None:
    """
    Insert the singleton PlatformSettings row (id=1) if it does not exist.

    This function is idempotent — it checks for the existing row before
    inserting and returns immediately if the row is already present.
    Safe to call on every application startup.

    Default values
    ──────────────
    These are the production-safe defaults for MGLTickets.
    Change them here (not in the migration file) if the defaults need
    to differ between environments.

    Raises
    ──────
    Any SQLAlchemy async exception if the database is unreachable or the
    platform_settings table does not exist (i.e. Alembic has not been run).
    The exception is intentionally not caught here so the app fails fast
    at startup rather than silently running without valid settings.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(PlatformSettings).where(PlatformSettings.id == 1)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            logger.info("Platform settings already seeded — skipping.")
            return

        logger.info("Seeding platform settings for the first time...")

        session.add(PlatformSettings(
            id=1,

            # ── General / Identity ────────────────────────────────────────────
            platform_name="MGLTickets",
            platform_email="admin@mgltickets.com",
            support_email="support@mgltickets.com",

            # ── Locale ───────────────────────────────────────────────────────
            default_currency="KES",
            timezone="Africa/Nairobi",

            # ── Platform / Business rules ─────────────────────────────────────
            platform_fee_percent=7.0,
            require_event_approval=True,
            allow_user_registration=True,
            allow_organizer_signup=True,
            enable_refunds=True,
            max_tickets_per_booking=10,

            # ── Security ──────────────────────────────────────────────────────
            session_timeout_hours=24,

            # ── Maintenance ───────────────────────────────────────────────────
            maintenance_mode=False,
        ))

        await session.commit()
        logger.info("Platform settings seeded successfully.")


async def run_all_seeds() -> None:
    """
    Entry point called by the FastAPI lifespan function.

    Add any future seed functions here in the order they should run.
    If a seed depends on another (e.g. requires a user row to exist first),
    call the dependency first.

    Usage in app/main.py:
        from app.db.seed import run_all_seeds

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await run_all_seeds()
            yield
    """
    await seed_platform_settings()
    # await seed_something_else()   # ← add future seeds here