#!/usr/bin/env python3
"""Admin user routes."""

from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime
from app.schemas.user import UserOut, AdminMeOut, AdminMeUpdate, AdminUserEmailUpdate
from app.core.security import require_admin, get_current_user
import app.services.user_services as user_services
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()

# Admin User Listing and Lookup
@router.get("/admin/users", response_model=list[UserOut])
async def list_all_users(user=Depends(require_admin)):
    """
    List all users.
    """
    return await user_services.list_all_users_service()

@router.get("/admin/users/me", response_model=AdminMeOut)
async def get_current_admin(user=Depends(get_current_user)):
    """
    Get the current authenticated admin's details.
    """
    return user

@router.patch("/admin/users/me", response_model=AdminMeOut)
async def update_current_admin(user_data: AdminMeUpdate, user=Depends(get_current_user)):
    """
    Update the current authenticated admin's details.
    """
    data = user_data.model_dump()
    return await user_services.update_user_info_service(user.id, data)

@router.patch("/admin/users/update-user-email/", response_model=UserOut)
async def update_user_email(user_data: AdminUserEmailUpdate, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Update a user's email address.
    """
    res = await user_services.update_user_info_service(user_data.user_id, {"email": user_data.new_email})

    if res is not None:
        # Log the email update action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="update_user_email",
            target_type="user",
            target_id=user_data.user_id,
            details={"new_email": user_data.new_email}
    )

    return res

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
async def delete_user(user_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):  # user=Depends(require_admin)
    """
    Delete a user by their ID.
    """
    
    res = await user_services.delete_user_service(user_id)

    if res is not None:
        # Log the user deletion action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="delete_user",
            target_type="user",
            target_id=user_id,
            details={"deleted_user_id": user_id}
        )

    return res

@router.patch("/admin/users/{user_id}/activate", response_model=UserOut)
async def activate_user(user_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Activate a user account.
    """
    res = await user_services.reactivate_account_service(user_id)

    if res is not None:
        # Log the user activation action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="activate_user",
            target_type="user",
            target_id=user_id,
            details={"activated_user_id": user_id}
        )

    return res

@router.patch("/admin/users/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(user_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Deactivate a user account.
    """
    res = await user_services.deactivate_user_service(user_id)

    if res is not None:
        # Log the user deactivation action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="deactivate_user",
            target_type="user",
            target_id=user_id,
            details={"deactivated_user_id": user_id}
        )

    return res

@router.patch("/admin/users/{user_id}/verify", response_model=UserOut)
async def verify_user_email(user_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Verify a user's email.
    """
    res = await user_services.verify_user_email_service(user_id)

    if res is not None:
        # Log the user verification action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="verify_user_email",
            target_type="user",
            target_id=user_id,
            details={"verified_user_id": user_id}
        )

    return res

@router.patch("/admin/users/{user_id}/unverify", response_model=UserOut)
async def unverify_user_email(user_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Unverify a user's email.
    """
    res = await user_services.unverify_user_email_service(user_id)

    if res is not None:
        # Log the user unverification action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="unverify_user_email",
            target_type="user",
            target_id=user_id,
            details={"unverified_user_id": user_id}
        )

    return res

@router.post("/admin/users/{user_id}/resend-verification", response_model=dict)
async def resend_verification_email(user_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)): # Add background task for email sending
    """
    Resend a user's verification email.
    """
    res = await user_services.resend_verification_email_service(user_id)

    # TODO: Add background task to send email asynchronously

    if res:
        # Log the user resend verification email action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="resend_verification_email",
            target_type="user",
            target_id=user_id,
            details={"resend_verification_user_id": user_id}
        )

    return res

# Admin Role Management
@router.patch("/admin/users/{user_id}/update-role/{role}", response_model=UserOut)
async def update_user_role(user_id: int, role: str, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Update a user's role.
    """
    res = await user_services.update_user_role_service(user_id, role)

    if res is not None:
        # Log the user role update action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="update_user_role",
            target_type="user",
            target_id=user_id,
            details={"role": role}
        )

    return res

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