import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.listing import Listing


class Operator(BaseModel):
    __tablename__ = "operators"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[str] = mapped_column(String(50), default="agency", index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="operator",
    )
    listings: Mapped[List["Listing"]] = relationship(
        "Listing",
        back_populates="operator",
        cascade="all, delete-orphan",
    )
