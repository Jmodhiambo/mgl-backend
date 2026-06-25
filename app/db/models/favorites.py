#!/usr/bin/env python3
"""Database Favorite model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    # Avoid circular imports. User and Event are only imported for type hints, not executed at runtime.
    from app.db.models.user import User
    from app.db.models.event import Event


class Favorite(Base):
    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    # CASCADE: a favorite with no event behind it is meaningless. When an
    # event is hard-deleted, its favorites should go with it rather than
    # blocking the delete or being orphaned with a null event_id.
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE")
    )
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

    # cascade="all, delete-orphan" mirrors the DB-level ondelete=CASCADE on the
    # ORM side, so session.delete(event) behaves correctly even before a flush
    # hits the database, and removing a Favorite from event.favorites deletes it.
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    event: Mapped["Event"] = relationship(
        "Event", back_populates="favorites"
    )

    def __repr__(self):
        return f"Favorite(id={self.id}, user_id={self.user_id}, event_id={self.event_id})"