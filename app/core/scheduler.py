from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.ref_session_services import cleanup_expired_and_revoked_sessions_service
from app.core.logging_config import logger

scheduler = AsyncIOScheduler()


async def run_session_cleanup():
    """Background job to clean up expired sessions"""
    try:
        result = await cleanup_expired_and_revoked_sessions_service(hours=24)
        logger.info(
            f"Session cleanup completed: "
            f"{result['deleted_count']} deleted, "
            f"{result['active_sessions']} active"
        )
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")


def start_scheduler():
    """Start the background scheduler"""
    scheduler.add_job(
        run_session_cleanup,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_sessions",
        name="Clean up expired refresh sessions",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Background scheduler started - cleanup runs daily at 3 AM")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    scheduler.shutdown()
    logger.info("Background scheduler stopped")