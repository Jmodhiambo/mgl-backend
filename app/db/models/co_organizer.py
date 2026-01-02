#!/usr/bin/env python3
"""Database Co-Organizer model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    # Avoid circular imports. User and Event are only imported for type hints, not executed at runtime.
    from app.db.models.user import User
    from app.db.models.event import Event

class CoOrganizer(Base):
    __tablename__ = "co_organizers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"))
    invited_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    create_co_organizer: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User", back_populates="co_organizers")
    event: Mapped["Event"] = relationship("Event", back_populates="co_organizers")

    def __repr__(self):
        return f"CoOrganizer(id={self.id}, user_id={self.user_id}, event_id={self.event_id})"