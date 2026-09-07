from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import destinations
from app.api.v1.endpoints import itineraries
from app.api.v1.endpoints import operators
from app.api.v1.endpoints import listings
from app.api.v1.endpoints import bookings
from app.api.v1.endpoints import reviews
from app.api.v1.endpoints import control_tower
from app.api.v1.endpoints import recommendations
from app.api.v1.endpoints import uploads
from app.api.v1.endpoints import payments
from app.api.v1.endpoints import users

api_v1_router = APIRouter()


@api_v1_router.get("", tags=["Root"])
@api_v1_router.get("/", tags=["Root"])
async def api_v1_root() -> dict:
    """API v1 root indicator endpoint."""
    return {
        "message": "Welcome to the AI Tourism API v1",
        "status": "active",
        "modules": ["auth", "destinations", "itineraries", "operators", "listings", "bookings", "reviews", "control-tower"],
    }


# Mount sub-routers
api_v1_router.include_router(health.router, tags=["Monitoring"])
api_v1_router.include_router(auth.router)
api_v1_router.include_router(destinations.router)
api_v1_router.include_router(itineraries.router)
api_v1_router.include_router(operators.router)
api_v1_router.include_router(listings.router)
api_v1_router.include_router(bookings.router)
api_v1_router.include_router(reviews.router)
api_v1_router.include_router(control_tower.router)
api_v1_router.include_router(recommendations.router)
api_v1_router.include_router(uploads.router)
api_v1_router.include_router(payments.router)
api_v1_router.include_router(users.router)

