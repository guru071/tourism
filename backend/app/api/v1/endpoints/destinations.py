from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
import re
import json

from app.core.database import get_async_session
from app.models.destination import Destination
from app.schemas.destination import DestinationCreate, DestinationRead, DestinationList
from app.core.config import settings

router = APIRouter(prefix="/destinations", tags=["Destinations"])


def _make_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.get("", response_model=DestinationList)
async def list_destinations(
    q: Optional[str] = Query(None, description="Search query"),
    query: Optional[str] = Query(None, description="Search query alias"),
    category: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Destination).where(Destination.is_active == True)

    search_term = None
    if isinstance(query, str) and query.strip():
        search_term = query.strip()
    elif isinstance(q, str) and q.strip():
        search_term = q.strip()

    if search_term:
        query = search_term
        ts_vector = func.to_tsvector('english', Destination.name + ' ' + Destination.description)
        stmt = stmt.where(
            func.to_tsvector('english', Destination.name + ' ' + Destination.description).match(query)
        )
        rank = func.ts_rank(ts_vector, func.plainto_tsquery('english', query))
    else:
        query = None

    if isinstance(category, str) and category.strip():
        stmt = stmt.where(Destination.category == category.strip())
    if isinstance(country, str) and country.strip():
        stmt = stmt.where(func.lower(Destination.country) == country.strip().lower())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    if query:
        stmt = stmt.order_by(desc(rank), Destination.name)
    else:
        stmt = stmt.order_by(Destination.name)

    page_limit = limit if isinstance(limit, int) else 20
    page_offset = offset if isinstance(offset, int) else 0

    stmt = stmt.limit(page_limit).offset(page_offset)
    results = (await session.execute(stmt)).scalars().all()

    items = []
    for d in results:
        item = DestinationRead.model_validate(d)
        items.append(item)

    return DestinationList(items=items, total=total, limit=page_limit, offset=page_offset)


@router.post("/search-nl", response_model=list[DestinationRead])
async def search_nl(
    payload: dict,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Natural language search using Gemini AI.
    Example: {"query": "A romantic beach getaway in Asia"}
    """
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=422, detail="Query is required")

    # Fetch all destinations to pass context to the LLM (in production this would be RAG / Embeddings)
    all_dests = (await session.execute(select(Destination).where(Destination.is_active == True))).scalars().all()
    
    if not settings.GEMINI_API_KEY:
        # Fallback if no LLM: simple text match
        terms = query.lower().split()
        matches = []
        for d in all_dests:
            score = 0
            text_corpus = f"{d.name} {d.country} {d.category} {d.description} {' '.join(d.tags)}".lower()
            for t in terms:
                if t in text_corpus:
                    score += 1
            if score > 0:
                matches.append((score, d))
        matches.sort(key=lambda x: x[0], reverse=True)
        return [DestinationRead.model_validate(m[1]) for m in matches[:5]]

    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        dest_context = []
        for d in all_dests:
            dest_context.append({
                "id": str(d.id),
                "name": d.name,
                "country": d.country,
                "category": d.category,
                "tags": d.tags,
                "description": d.description[:100]
            })

        system_prompt = """You are a travel recommender. You are given a list of available destinations.
Based on the user's query, return a JSON array of the best matching destination IDs, ordered by relevance.
Only return IDs that exist in the provided list. Return max 5 IDs.
Format: ["id1", "id2"]"""

        prompt = f"User Query: {query}\n\nAvailable Destinations: {json.dumps(dest_context)}"
        
        response = model.generate_content(
            [system_prompt, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        
        raw = response.text.strip()
        matched_ids = json.loads(raw)
        
        # Hydrate
        result = []
        dest_map = {str(d.id): d for d in all_dests}
        for uid in matched_ids:
            if uid in dest_map:
                result.append(DestinationRead.model_validate(dest_map[uid]))
                
        return result

    except Exception as e:
        print(f"NL Search error: {e}")
        # Return fallback on error
        return [DestinationRead.model_validate(d) for d in all_dests[:5]]


@router.get("/{destination_id}", response_model=DestinationRead)
async def get_destination(
    destination_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Destination).where(Destination.id == destination_id))
    destination = result.scalar_one_or_none()
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return DestinationRead.model_validate(destination)


@router.post("", response_model=DestinationRead, status_code=201)
async def create_destination(
    payload: DestinationCreate,
    session: AsyncSession = Depends(get_async_session),
):
    slug = payload.slug or _make_slug(payload.name)
    # ensure slug uniqueness
    existing = await session.execute(select(Destination).where(Destination.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{len(slug)}"

    destination = Destination(
        name=payload.name,
        slug=slug,
        country=payload.country,
        city=payload.city,
        region=payload.region,
        category=payload.category,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timezone=payload.timezone,
        image_urls=payload.image_urls,
        tags=payload.tags,
        is_active=payload.is_active,
    )
    session.add(destination)
    await session.commit()
    await session.refresh(destination)
    return DestinationRead.model_validate(destination)
