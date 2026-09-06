import uuid
from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    Uuid,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.destination import Destination
    from app.models.listing import Listing
    from app.models.booking import Booking


class Itinerary(BaseModel):
    __tablename__ = "itineraries"
    pass

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    destination_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("destinations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    budget_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_prompt_context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True, nullable=False)
    # AI Generator fields
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    travel_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    budget_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    day_plans: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    total_estimated_cost_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="itineraries",
    )
    destination: Mapped[Optional["Destination"]] = relationship(
        "Destination",
        back_populates="itineraries",
    )
    items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryItem.order_index",
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="itinerary",
    )


class ItineraryItem(BaseModel):
    __tablename__ = "itinerary_items"
    __table_args__ = (
        CheckConstraint("day_number >= 1", name="ck_itinerary_items_day_number"),
        CheckConstraint("order_index >= 0", name="ck_itinerary_items_order_index"),
    )

    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("listings.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    day_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    itinerary: Mapped["Itinerary"] = relationship(
        "Itinerary",
        back_populates="items",
    )
    listing: Mapped[Optional["Listing"]] = relationship(
        "Listing",
        back_populates="itinerary_items",
    )
