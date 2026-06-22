#!/usr/bin/env python3
"""
Analytics route for the Organizer dashboard.
"""

from fastapi import (
    APIRouter, Depends, UploadFile, File, Form,
    HTTPException, status, BackgroundTasks,
)
from datetime import datetime
from typing import Optional

from app.schemas.user import UserOut
from app.schemas.event import (
    OrganizerEventOut,
    EventCreateWithFlyer,
    EventDetails,
    TopEvent,
    EventUpdate,
)
from app.schemas.organizer import DashboardStats, OrganizerOrderOut
import app.services.event_services as event_services
import app.services.organizer_analytics_services as oa_services
from app.services.notification_services import notify_event_submitted
from app.core.security import require_organizer
from app.utils.generate_image_url import save_flyer_and_get_url
from app.utils.generate_slug import generate_unique_slug


router = APIRouter()

# The route currently exists in events_organizer.py and is duplicated here. I'm not sure where to keep it at the moment.
# Need to add this route to the registry in case the route is removed from events_organizer.py and becomes live here.

# @router.get(
#     "/organizers/me/stats",
#     response_model=DashboardStats,
#     status_code=status.HTTP_200_OK,
# )
# async def get_organizer_dashboard_stats(organizer: UserOut = Depends(require_organizer)):
#     """
#     KPI cards for the organizer dashboard.
#     Returns event counts, booking totals, and the full revenue split
#     (gross / platform_cut / organizer_net) across all confirmed bookings.
#     """
#     return await oa_services.get_dashboard_stats_service(organizer.id)