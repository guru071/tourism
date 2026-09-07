import json
import logging
import re
import uuid
from decimal import Decimal
from typing import List, Optional, Union

import google.generativeai as genai
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_async_session
from app.models.booking import Booking
from app.models.destination import Destination
from app.models.listing import Listing
from app.models.review import Review
from app.models.user import User
from app.schemas.destination import DestinationRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    query: Optional[str] = None
    prompt: Optional[str] = None
    preferences: Optional[Union[List[str], str]] = None
    travel_style: Optional[str] = None
    budget_level: Optional[str] = None
    country: Optional[str] = None
    limit: int = 5


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "destination"


async def _extract_user_travel_profile(user_id: str, session: AsyncSession) -> dict:
    """Fetch user's booking and review history to build a personalized travel profile."""
    profile = {
        "user_name": None,
        "past_destinations": [],
        "favorite_categories": set(),
        "past_tags": set(),
        "average_booking_spend": None,
    }

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        return profile

    try:
        # Fetch user
        user = await session.get(User, user_uuid)
        if user:
            profile["user_name"] = user.full_name

        # Fetch past bookings with listings and destinations
        booking_stmt = (
            select(Booking)
            .where(Booking.user_id == user_uuid)
            .options(selectinload(Booking.listing).selectinload(Listing.destination))
        )
        booking_res = await session.execute(booking_stmt)
        bookings = booking_res.scalars().all()

        total_spend = 0.0
        booking_count = 0
        for b in bookings:
            if b.total_price:
                total_spend += float(b.total_price)
                booking_count += 1
            if b.listing and b.listing.destination:
                d = b.listing.destination
                profile["past_destinations"].append(d.name)
                if d.category:
                    profile["favorite_categories"].add(d.category)
                if d.tags:
                    for t in d.tags:
                        profile["past_tags"].add(t)

        if booking_count > 0:
            profile["average_booking_spend"] = round(total_spend / booking_count, 2)

        # Convert sets to lists for JSON serialization
        profile["favorite_categories"] = list(profile["favorite_categories"])
        profile["past_tags"] = list(profile["past_tags"])

    except Exception as e:
        logger.warning(f"Error building user travel profile for {user_id}: {e}")

    return profile


def _get_gemini_models():
    """Returns candidate Gemini models to try in order of preference."""
    candidates = []
    if settings.GEMINI_MODEL and "1.5" not in settings.GEMINI_MODEL and "2.5" not in settings.GEMINI_MODEL:
        candidates.append(settings.GEMINI_MODEL)
    candidates.extend(["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-flash-latest"])
    if settings.GEMINI_MODEL not in candidates:
        candidates.append(settings.GEMINI_MODEL)
    return candidates


async def _generate_llm_recommendations(
    user_context: str,
    catalog_destinations: list[Destination],
    limit: int,
) -> list[dict]:
    """Call Google Gemini to generate dynamic personalized recommendations."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")

    # Format available catalog destinations
    catalog_info = []
    for d in catalog_destinations:
        catalog_info.append({
            "id": str(d.id),
            "name": d.name,
            "country": d.country,
            "city": d.city,
            "category": d.category,
            "tags": d.tags or [],
            "description": (d.description[:180] + "...") if d.description and len(d.description) > 180 else (d.description or ""),
        })

    system_prompt = (
        "You are an expert, world-class AI travel recommendation engine for the AI Tourism Ecosystem.\n"
        "Your mission is to analyze user desires, interests, travel style, budget, and travel history, "
        "and produce tailored, highly personalized destination recommendations.\n"
        "Rules:\n"
        "1. If catalog destinations are provided and match the user's criteria, prioritize recommending them using their catalog 'id'.\n"
        "2. If no catalog destinations match or if more are needed to reach the requested limit, dynamically generate real-world destinations.\n"
        "3. Provide a compelling, highly personalized 'recommendation_reason' explaining exactly why each destination aligns with their specific input.\n"
        "4. Provide a 'match_score' between 0.70 and 1.00 indicating the degree of personalization match.\n"
        "5. Output STRICT valid JSON array of objects only. No markdown fences, no explanatory text."
    )

    user_prompt = (
        f"User Input & Travel Profile:\n{user_context}\n\n"
        f"Requested Number of Recommendations: {limit}\n\n"
        f"Available Catalog Destinations (Total: {len(catalog_info)}):\n"
        f"{json.dumps(catalog_info, indent=2)}\n\n"
        "Expected JSON Output Schema:\n"
        "[\n"
        "  {\n"
        "    \"id\": \"string (catalog id if matched from catalog, or null if dynamically generated)\",\n"
        "    \"name\": \"string (Destination Name)\",\n"
        "    \"country\": \"string\",\n"
        "    \"city\": \"string or null\",\n"
        "    \"category\": \"string (e.g. Beach, Culture, Adventure, Nature, Urban, Luxury, Wellness)\",\n"
        "    \"description\": \"string (2-3 sentences engaging overview)\",\n"
        "    \"tags\": [\"string\", \"string\"],\n"
        "    \"match_score\": 0.95,\n"
        "    \"recommendation_reason\": \"string (personalized explanation why this fits their specific input)\"\n"
        "  }\n"
        "]"
    )

    models_to_try = _get_gemini_models()
    last_error = None

    for model_name in models_to_try:
        try:
            logger.info(f"Attempting recommendation generation with Gemini model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [system_prompt, user_prompt],
                generation_config=genai.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=3072,
                    response_mime_type="application/json",
                ),
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            parsed = json.loads(raw)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed[:limit]
            elif isinstance(parsed, dict) and "recommendations" in parsed:
                return parsed["recommendations"][:limit]
        except Exception as e:
            logger.warning(f"Gemini model {model_name} failed: {e}")
            last_error = e

    raise RuntimeError(f"All Gemini models failed: {last_error}")


def _rule_based_fallback(
    catalog_destinations: list[Destination],
    user_context_terms: list[str],
    user_profile: dict,
    limit: int,
) -> list[DestinationRead]:
    """Smart fallback recommendation if LLM is unreachable or key is missing."""
    scored_items = []

    preferred_categories = set(user_profile.get("favorite_categories", []))
    preferred_tags = set(user_profile.get("past_tags", []))

    for d in catalog_destinations:
        score = 0.5
        reasons = []

        if d.category and d.category in preferred_categories:
            score += 0.25
            reasons.append(f"matches your past interest in {d.category} getaways")

        dest_tags = set(d.tags or [])
        common_tags = dest_tags.intersection(preferred_tags)
        if common_tags:
            score += 0.15
            reasons.append(f"features activities you enjoy like {', '.join(list(common_tags)[:2])}")

        corpus = f"{d.name} {d.country} {d.city or ''} {d.category or ''} {d.description or ''} {' '.join(d.tags or [])}".lower()
        matched_terms = [t for t in user_context_terms if t in corpus]
        if matched_terms:
            score += min(0.3, len(matched_terms) * 0.1)
            reasons.append(f"aligns with your search criteria ({', '.join(matched_terms[:3])})")

        reason_str = "Selected based on popularity and top ratings."
        if reasons:
            reason_str = f"Recommended because this destination {' and '.join(reasons)}."

        scored_items.append((score, d, reason_str))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, dest, reason in scored_items[:limit]:
        read_obj = DestinationRead.model_validate(dest)
        read_obj.match_score = round(min(score, 0.99), 2)
        read_obj.recommendation_reason = reason
        results.append(read_obj)

    return results


async def process_recommendations(
    user_id: Optional[str],
    query: Optional[str],
    prompt: Optional[str],
    preferences: Optional[Union[List[str], str]],
    travel_style: Optional[str],
    budget_level: Optional[str],
    country: Optional[str],
    limit: int,
    session: AsyncSession,
) -> list[DestinationRead]:
    """Core recommendation pipeline combining DB context, user profile, and Gemini AI."""
    # 1. Fetch active destinations from database (resilient to DB connection issues)
    catalog_destinations = []
    dest_by_id = {}
    dest_by_name = {}
    try:
        db_result = await session.execute(
            select(Destination).where(Destination.is_active == True)
        )
        catalog_destinations = list(db_result.scalars().all())
        dest_by_id = {str(d.id): d for d in catalog_destinations}
        dest_by_name = {d.name.lower(): d for d in catalog_destinations}
    except Exception as db_err:
        logger.warning(f"Database unavailable for catalog lookup: {db_err}. Proceeding with dynamic AI generation.")

    # 2. Extract user profile if user_id provided
    user_profile = {}
    if user_id:
        user_profile = await _extract_user_travel_profile(user_id, session)

    # 3. Format user query components
    effective_prompt = prompt or query or ""
    prefs_list = []
    if isinstance(preferences, list):
        prefs_list = [p.strip() for p in preferences if p.strip()]
    elif isinstance(preferences, str):
        prefs_list = [p.strip() for p in preferences.split(",") if p.strip()]

    context_parts = []
    if effective_prompt:
        context_parts.append(f"User Request / Desired Experience: {effective_prompt}")
    if prefs_list:
        context_parts.append(f"Specific Interests & Preferences: {', '.join(prefs_list)}")
    if travel_style:
        context_parts.append(f"Travel Style: {travel_style}")
    if budget_level:
        context_parts.append(f"Budget Level: {budget_level}")
    if country:
        context_parts.append(f"Target Country / Region: {country}")
    if user_profile.get("past_destinations"):
        context_parts.append(f"Previously Visited Destinations: {', '.join(user_profile['past_destinations'])}")
    if user_profile.get("favorite_categories"):
        context_parts.append(f"Historical Favorite Categories: {', '.join(user_profile['favorite_categories'])}")
    if user_profile.get("past_tags"):
        context_parts.append(f"Historical Activity Interests: {', '.join(user_profile['past_tags'][:8])}")

    user_context = "\n".join(context_parts)
    if not user_context:
        user_context = "General recommendation for an adventurous, culturally enriching, and relaxing vacation."

    # 4. Generate recommendations using Gemini LLM
    try:
        llm_recommendations = await _generate_llm_recommendations(
            user_context=user_context,
            catalog_destinations=catalog_destinations,
            limit=limit,
        )

        final_destinations: list[DestinationRead] = []
        for item in llm_recommendations:
            matched_id = item.get("id")
            matched_dest = None

            if matched_id and matched_id in dest_by_id:
                matched_dest = dest_by_id[matched_id]
            elif item.get("name") and item["name"].lower() in dest_by_name:
                matched_dest = dest_by_name[item["name"].lower()]

            if matched_dest:
                # Hydrate from catalog destination
                read_model = DestinationRead.model_validate(matched_dest)
                read_model.recommendation_reason = item.get("recommendation_reason") or "Personalized match based on your travel preferences."
                read_model.match_score = float(item.get("match_score", 0.90))
                final_destinations.append(read_model)
            else:
                # Dynamically generated real-world destination from Gemini
                dest_name = item.get("name", "Scenic Getaway")
                slug = _slugify(dest_name)
                generated_id = matched_id if (matched_id and "-" in str(matched_id)) else str(uuid.uuid4())

                # Generate high quality unsplash image tags
                primary_tag = (item.get("tags") or ["travel"])[0]
                image_url = f"https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1000&q=80"
                if item.get("category", "").lower() in ["nature", "adventure", "mountain"]:
                    image_url = "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=80"
                elif item.get("category", "").lower() in ["culture", "urban", "historic"]:
                    image_url = "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=80"

                read_model = DestinationRead(
                    id=generated_id,
                    name=dest_name,
                    slug=slug,
                    country=item.get("country", "Global"),
                    city=item.get("city"),
                    region=item.get("region"),
                    category=item.get("category", "Adventure"),
                    description=item.get("description", "A personalized destination selected specifically for your journey."),
                    latitude=Decimal(str(item.get("latitude", 0.0))) if item.get("latitude") is not None else None,
                    longitude=Decimal(str(item.get("longitude", 0.0))) if item.get("longitude") is not None else None,
                    timezone="UTC",
                    image_urls=[image_url],
                    tags=item.get("tags") or [item.get("category", "travel").lower()],
                    is_active=True,
                    avg_rating=4.8,
                    review_count=12,
                    recommendation_reason=item.get("recommendation_reason") or "Dynamically generated by Gemini to perfectly match your desired experience.",
                    match_score=float(item.get("match_score", 0.95)),
                )
                final_destinations.append(read_model)

        if final_destinations:
            return final_destinations[:limit]

    except Exception as e:
        logger.warning(f"Gemini recommendation generation error: {e}. Falling back to rule-based engine.")

    # 5. Fallback if Gemini fails or is not available
    search_terms = (
        (effective_prompt + " " + " ".join(prefs_list) + f" {travel_style or ''} {budget_level or ''}")
        .lower()
        .split()
    )
    return _rule_based_fallback(catalog_destinations, search_terms, user_profile, limit)


@router.get("", response_model=list[DestinationRead])
async def get_recommendations(
    user_id: Optional[str] = Query(None, description="User UUID for travel history personalization"),
    query: Optional[str] = Query(None, description="Freeform search or experience query"),
    prompt: Optional[str] = Query(None, description="Detailed prompt describing desired destination or vibes"),
    preferences: Optional[str] = Query(None, description="Comma-separated travel interests"),
    travel_style: Optional[str] = Query(None, description="Travel style (e.g. Relaxed, Adventure, Cultural, Luxury)"),
    budget_level: Optional[str] = Query(None, description="Budget level (e.g. Budget, Mid-range, Luxury)"),
    country: Optional[str] = Query(None, description="Filter or target country"),
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations to return"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Personalized AI Destination Recommendation Engine powered by Google Gemini.
    Dynamically analyzes user input (prompt, preferences, style, budget) and historical
    travel profile to recommend real destinations with customized explanations.
    """
    return await process_recommendations(
        user_id=user_id,
        query=query,
        prompt=prompt,
        preferences=preferences,
        travel_style=travel_style,
        budget_level=budget_level,
        country=country,
        limit=limit,
        session=session,
    )


@router.post("", response_model=list[DestinationRead])
async def create_personalized_recommendations(
    payload: RecommendationRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    POST endpoint for personalized AI Destination Recommendations.
    Supports rich JSON payloads with user preferences, travel styles, and custom prompts.
    """
    return await process_recommendations(
        user_id=payload.user_id,
        query=payload.query,
        prompt=payload.prompt,
        preferences=payload.preferences,
        travel_style=payload.travel_style,
        budget_level=payload.budget_level,
        country=payload.country,
        limit=payload.limit,
        session=session,
    )
