"""
Phase 4: Gemini AI Itinerary Generator
Falls back to rule-based generator if GEMINI_API_KEY is not set or call fails.
"""
import json
import logging
from typing import Optional

from app.core.config import settings
from app.services.itinerary_generator import generate_itinerary as rule_based_generate

logger = logging.getLogger(__name__)

GEMINI_SYSTEM_PROMPT = """You are an expert travel planner. Generate a detailed day-by-day itinerary in valid JSON.
Return ONLY raw JSON matching this exact schema — no markdown, no explanation:
{
  "title": "string",
  "summary": "string (2-3 sentences)",
  "day_plans": [
    {
      "day": 1,
      "theme": "string",
      "tips": "string (local tip)",
      "total_estimated_cost_usd": 0.0,
      "activities": [
        {
          "time_of_day": "morning|afternoon|evening",
          "title": "string",
          "description": "string",
          "location": "string",
          "duration_hours": 2.0,
          "estimated_cost_usd": 0.0,
          "category": "sightseeing|food|adventure|culture|transport|leisure|shopping"
        }
      ]
    }
  ],
  "total_estimated_cost_usd": 0.0
}
"""

TRAVEL_STYLE_PROMPTS = {
    "Relaxed": "slow-paced, relaxing, minimal rushing, emphasis on comfort and rest",
    "Cultural": "museums, temples, historical sites, local traditions, art galleries",
    "Adventure": "outdoor activities, hiking, sports, thrilling experiences",
    "Luxury": "5-star experiences, fine dining, exclusive access, premium services",
}

BUDGET_PROMPTS = {
    "Budget": "budget traveler spending $30-60/day, hostels, street food, free attractions",
    "Mid-range": "comfortable traveler spending $80-150/day, 3-star hotels, local restaurants",
    "Luxury": "luxury traveler spending $300+/day, 5-star hotels, fine dining, private tours",
}


async def generate_itinerary_gemini(
    destination_name: str,
    destination_id: str,
    duration_days: int,
    travel_style: str,
    budget_level: str,
) -> dict:
    """
    Generate itinerary using Google Gemini API.
    Falls back to rule-based generator if Gemini is unavailable.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("No GEMINI_API_KEY set — using rule-based generator")
        return rule_based_generate(destination_name, destination_id, duration_days, travel_style, budget_level)

    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        style_desc = TRAVEL_STYLE_PROMPTS.get(travel_style, travel_style)
        budget_desc = BUDGET_PROMPTS.get(budget_level, budget_level)

        prompt = (
            f"Create a {duration_days}-day itinerary for {destination_name}.\n"
            f"Travel style: {travel_style} — {style_desc}.\n"
            f"Budget level: {budget_level} — {budget_desc}.\n"
            f"Include 3 activities per day (morning, afternoon, evening).\n"
            f"Make it specific to {destination_name}'s real attractions, cuisine, and culture.\n"
            f"Return ONLY valid JSON matching the schema provided."
        )

        response = model.generate_content(
            [GEMINI_SYSTEM_PROMPT, prompt],
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )

        raw = response.text.strip()
        # Strip markdown code fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        # Ensure required top-level keys exist
        if "day_plans" not in data or not data["day_plans"]:
            raise ValueError("Invalid response structure from Gemini")

        # Inject destination_id
        data["destination_id"] = destination_id
        logger.info(f"Gemini generated itinerary for {destination_name} ({duration_days}d {travel_style})")
        return data

    except Exception as e:
        logger.warning(f"Gemini generation failed: {e} — falling back to rule-based")
        if settings.AI_FALLBACK_TO_RULES:
            return rule_based_generate(destination_name, destination_id, duration_days, travel_style, budget_level)
        raise RuntimeError(f"AI generation failed and fallback is disabled: {e}")
