#!/usr/bin/env python3
"""Admin user routes."""

from fastapi import APIRouter, Depends
from datetime import datetime
from app.schemas.user import UserOut
from app.core.security import require_admin
import app.services.user_services as user_services

router = APIRouter()

# Admin User Listing and Lookup
@router.get("/admin/users", response_model=list[UserOut])
async def list_all_users(): # user=Depends(require_admin)
    """
    List all users.
    """
    return await user_services.list_all_users_service()

@router.get("/admin/users/active", response_model=list[UserOut])
async def list_active_users(user=Depends(require_admin)):
    """
    List all active users.
    """
    return await user_services.list_active_users_service()

@router.get("/admin/users/verified", response_model=list[UserOut])
async def list_verified_users(user=Depends(require_admin)):
    """
    List all verified users.
    """
    return await user_services.list_verified_users_service()

@router.get("/admin/users/unverified", response_model=list[UserOut])
async def list_unverified_users(user=Depends(require_admin)):
    """
    List all unverified users.
    """
    return await user_services.list_unverified_users_service()

@router.get("/admin/users/search", response_model=list[UserOut])
async def search_users_by_name(name: str, user=Depends(require_admin)):
    """
    Search for users by name.
    """
    return await user_services.search_users_by_name_service(name)

@router.get("/admin/users/{user_id}", response_model=UserOut)
async def get_user_by_id(user_id: int, user=Depends(require_admin)):
    """
    Get a user by their ID.
    """
    return await user_services.get_user_by_id_service(user_id)

# Admin Level User Actions
@router.delete("/admin/users/{user_id}", response_model=bool)
async def delete_user(user_id: int):  # user=Depends(require_admin)
    """
    Delete a user by their ID.
    """
    return await user_services.delete_user_service(user_id)

@router.patch("/admin/users/{user_id}/activate", response_model=UserOut)
async def activate_user(user_id: int, user=Depends(require_admin)):
    """
    Activate a user account.
    """
    return await user_services.activate_user_service(user_id)

@router.patch("/admin/users/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(user_id: int, user=Depends(require_admin)):
    """
    Deactivate a user account.
    """
    return await user_services.deactivate_user_service(user_id)

@router.patch("/admin/users/{user_id}/verify", response_model=UserOut)
async def verify_user_email(user_id: int, user=Depends(require_admin)):
    """
    Verify a user's email.
    """
    return await user_services.verify_user_email_service(user_id)

@router.patch("/admin/users/{user_id}/unverify", response_model=UserOut)
async def unverify_user_email(user_id: int, user=Depends(require_admin)):
    """
    Unverify a user's email.
    """
    return await user_services.unverify_user_email_service(user_id)

# Admin Role Management
@router.patch("/admin/users/{user_id}/role/user-to-admin", response_model=UserOut)
async def promote_user_to_admin(user_id: int, user=Depends(require_admin)):
    """
    Promote a user to admin role.
    """
    return await user_services.promote_user_to_admin_service(user_id)

@router.patch("/admin/users/{user_id}/role/admin-to-user", response_model=UserOut)
async def demote_user_from_admin(user_id: int, user=Depends(require_admin)):
    """
    Demote a user from admin role.
    """
    return await user_services.demote_user_from_admin_service(user_id)

@router.patch("/admin/users/{user_id}/role/user-to-organizer", response_model=UserOut)
async def promote_user_to_organizer(user_id: int, user=Depends(require_admin)):
    """
    Promote a user to organizer role.
    """
    return await user_services.promote_user_to_organizer_service(user_id)

@router.patch("/admin/users/{user_id}/role/organizer-to-user", response_model=UserOut)
async def demote_user_from_organizer(user_id: int, user=Depends(require_admin)):
    """
    Demote a user from organizer role.
    """
    return await user_services.demote_user_from_organizer_service(user_id)

@router.patch("/admin/users/{user_id}/role/organizer-to-admin", response_model=UserOut)
async def promote_organizer_to_admin(user_id: int, user=Depends(require_admin)):
    """
    Promote an organizer to admin role.
    """
    return await user_services.promote_organizer_to_admin_service(user_id)

@router.patch("/admin/users/{user_id}/role/admin-to-organizer", response_model=UserOut)
async def demote_admin_to_organizer(user_id: int, user=Depends(require_admin)):
    """
    Demote an admin to organizer role.
    """
    return await user_services.demote_admin_to_organizer_service(user_id)

# Admin Analytics
@router.get("/admin/analytics/count", response_model=int)
async def get_total_users(user=Depends(require_admin)):
    """
    Get the total number of users.
    """
    return await user_services.count_users_by_role_service()

@router.get("/admin/analytics/count/{role}", response_model=int)
async def count_users_by_role(role: str, user=Depends(require_admin)):
    """
    Count users by their role.
    """
    return await user_services.count_users_by_role_service(role)

@router.get("/admin/analytics/count/active", response_model=int)
async def count_active_users(user=Depends(require_admin)):
    """
    Count active users.
    """
    return await user_services.count_active_users_service()

@router.get("/admin/analytics/count/verified", response_model=int)
async def count_verified_users(user=Depends(require_admin)):
    """
    Count verified users.
    """
    return await user_services.count_verified_users_service()

@router.get("/admin/analytics/count/unverified", response_model=int)
async def count_unverified_users(user=Depends(require_admin)):
    """
    Count unverified users.
    """
    return await user_services.count_unverified_users_service()

@router.get("/admin/analytics/users/created-after/{date}", response_model=list[dict])
async def list_users_created_after(date: datetime, user=Depends(require_admin)):
    """
    List users created after a specific date.
    """
    return await user_services.list_users_created_after_service(date)

@router.get("/admin/analytics/users/created-before/{date}", response_model=list[dict])
async def list_users_created_before(date: datetime, user=Depends(require_admin)):
    """
    List users created before a specific date.
    """
    return await user_services.list_users_created_before_service(date)

@router.get("/admin/analytics/users/updated-after/{date}", response_model=list[dict])
async def list_users_updated_after(date: datetime, user=Depends(require_admin)):
    """
    List users updated after a specific date.
    """
    return await user_services.list_users_updated_after_service(date)

@router.get("/admin/analytics/users/updated-before/{date}", response_model=list[dict])
async def list_users_updated_before(date: datetime, user=Depends(require_admin)):
    """
    List users updated before a specific date.
    """
    return await user_services.list_users_updated_before_service(date)

@router.get("/admin/analytics/users/count/created-between/{start_date}/{end_date}", response_model=int)
async def count_users_created_between(start_date: datetime, end_date: datetime, user=Depends(require_admin)):
    """
    Count users created between two specific dates.
    """
    return await user_services.count_users_created_between_service(start_date, end_date)

@router.get("/admin/analytics/users/count/updated-between/{start_date}/{end_date}", response_model=int)
async def count_users_updated_between(start_date: datetime, end_date: datetime, user=Depends(require_admin)):
    """
    Count users updated between two specific dates.
    """
    return await user_services.count_users_updated_between_service(start_date, end_date)