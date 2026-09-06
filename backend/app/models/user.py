from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.operator import Operator
    from app.models.itinerary import Itinerary
    from app.models.booking import Booking
    from app.models.review import Review


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="tourist", index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    # Relationships
    operator: Mapped[Optional["Operator"]] = relationship(
        "Operator",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    itineraries: Mapped[List["Itinerary"]] = relationship(
        "Itinerary",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )
