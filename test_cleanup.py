#!/usr/bin/env python3
"""Test cleanup of expired and revoked sessions."""

import asyncio
from app.services.ref_session_services import cleanup_expired_and_revoked_sessions_service, cleanup_user_sessions_service

async def test_cleanup():
    result = await cleanup_expired_and_revoked_sessions_service(hours=24)
    print(f"Deleted: {result['deleted_count']}")
    print(f"Active: {result['active_sessions']}")

    # result1 = await cleanup_user_sessions_service(user_id=1)
    # print(f"Deleted: {result1['deleted_count']}")

if __name__ == "__main__":
    asyncio.run(test_cleanup())