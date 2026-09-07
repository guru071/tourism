from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, field_validator
import re


class DestinationBase(BaseModel):
    name: str
    country: str
    city: Optional[str] = None
    region: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: str = "UTC"
    image_urls: List[str] = []
    tags: List[str] = []
    is_active: bool = True


class DestinationCreate(DestinationBase):
    slug: Optional[str] = None

    @field_validator("slug", mode="before")
    @classmethod
    def generate_slug(cls, v, info):
        if not v and "name" in info.data:
            base = info.data["name"].lower()
            return re.sub(r"[^a-z0-9]+", "-", base).strip("-")
        return v


class DestinationRead(DestinationBase):
    id: str
    slug: str
    avg_rating: Optional[float] = None
    review_count: int = 0
    recommendation_reason: Optional[str] = None
    match_score: Optional[float] = None

    model_config = {"from_attributes": True}


class DestinationList(BaseModel):
    items: List[DestinationRead]
    total: int
    limit: int
    offset: int
