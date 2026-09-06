from typing import List, Optional
from pydantic import BaseModel


class OperatorCreate(BaseModel):
    business_name: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    license_number: Optional[str] = None


class OperatorRead(BaseModel):
    id: str
    user_id: str
    business_name: str
    description: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    website_url: Optional[str]
    license_number: Optional[str]
    is_verified: bool

    model_config = {"from_attributes": True}


class ListingCreate(BaseModel):
    destination_id: str
    title: str
    description: Optional[str] = None
    listing_type: str  # hotel | tour | activity | restaurant | transport
    price_per_unit: float
    currency: str = "USD"
    max_capacity: Optional[int] = None
    image_urls: List[str] = []
    tags: List[str] = []


class ListingRead(BaseModel):
    id: str
    operator_id: str
    destination_id: str
    title: str
    description: Optional[str]
    listing_type: str
    price_per_unit: float
    currency: str
    max_capacity: Optional[int]
    image_urls: List[str]
    tags: List[str]
    is_active: bool

    model_config = {"from_attributes": True}


class BookingCreate(BaseModel):
    listing_id: str
    check_in_date: str
    check_out_date: str
    num_guests: int = 1
    special_requests: Optional[str] = None


class BookingRead(BaseModel):
    id: str
    user_id: str
    listing_id: str
    check_in_date: str
    check_out_date: str
    num_guests: int
    status: str
    total_price: Optional[float]
    special_requests: Optional[str]

    model_config = {"from_attributes": True}


class BookingStatusUpdate(BaseModel):
    status: str  # pending | confirmed | cancelled | completed


class ReviewCreate(BaseModel):
    destination_id: Optional[str] = None
    listing_id: Optional[str] = None
    rating: int  # 1-5
    title: Optional[str] = None
    body: Optional[str] = None


class ReviewRead(BaseModel):
    id: str
    user_id: str
    destination_id: Optional[str]
    listing_id: Optional[str]
    rating: int
    title: Optional[str]
    body: Optional[str]

    model_config = {"from_attributes": True}
