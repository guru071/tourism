import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.operator import Operator
    from app.models.destination import Destination
    from app.models.itinerary import ItineraryItem
    from app.models.booking import Booking
    from app.models.review import Review


class Listing(BaseModel):
    __tablename__ = "listings"
    __table_args__ = (
        CheckConstraint("base_price >= 0", name="ck_listings_base_price"),
        CheckConstraint(
            "rating_average >= 0 AND rating_average <= 5",
            name="ck_listings_rating_average",
        ),
    )

    operator_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("operators.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    destination_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("destinations.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    availability: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    amenities: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    images: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    rating_average: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"), nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    operator: Mapped["Operator"] = relationship(
        "Operator",
        back_populates="listings",
    )
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="listings",
    )
    itinerary_items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem",
        back_populates="listing",
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="listing",
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="listing",
        cascade="all, delete-orphan",
    )
