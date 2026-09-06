import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.listing import Listing
    from app.models.itinerary import Itinerary
    from app.models.review import Review


class Booking(BaseModel):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_bookings_dates"),
        CheckConstraint("guests_count >= 1", name="ck_bookings_guests"),
        CheckConstraint("total_price >= 0", name="ck_bookings_price"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("listings.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    itinerary_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("itineraries.id", ondelete="SET NULL"),
        nullable=True,
    )
    booking_reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    guests_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(50), default="unpaid", nullable=False)
    payment_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="bookings",
    )
    listing: Mapped["Listing"] = relationship(
        "Listing",
        back_populates="bookings",
    )
    itinerary: Mapped[Optional["Itinerary"]] = relationship(
        "Itinerary",
        back_populates="bookings",
    )
    review: Mapped[Optional["Review"]] = relationship(
        "Review",
        back_populates="booking",
        uselist=False,
    )
