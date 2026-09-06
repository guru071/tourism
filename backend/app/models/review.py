import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.listing import Listing
    from app.models.booking import Booking


class Review(BaseModel):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="reviews",
    )
    listing: Mapped["Listing"] = relationship(
        "Listing",
        back_populates="reviews",
    )
    booking: Mapped[Optional["Booking"]] = relationship(
        "Booking",
        back_populates="review",
    )
