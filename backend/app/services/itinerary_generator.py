"""AI Itinerary Generation Service - rule-based smart generator."""
from typing import List, Dict, Any


ACTIVITY_LIBRARY: Dict[str, Dict[str, List[Dict]]] = {
    "Relaxed": {
        "morning": [
            {"title": "Leisurely Breakfast at a Local Café", "description": "Start your day at a charming local café, savoring traditional breakfast dishes while watching the city come alive.", "category": "dining", "duration_hours": 1.5, "cost_budget": 8, "cost_midrange": 15, "cost_luxury": 30},
            {"title": "Peaceful Morning Walk", "description": "Stroll through the city's quietest streets, taking in the local architecture and morning atmosphere.", "category": "leisure", "duration_hours": 1.5, "cost_budget": 0, "cost_midrange": 0, "cost_luxury": 0},
            {"title": "Botanical Garden Visit", "description": "Explore the tranquil botanical gardens with their diverse flora and peaceful walking paths.", "category": "sightseeing", "duration_hours": 2.0, "cost_budget": 5, "cost_midrange": 10, "cost_luxury": 10},
        ],
        "afternoon": [
            {"title": "Museum Visit at Your Own Pace", "description": "Explore a local museum, lingering over exhibits that catch your eye without any rush.", "category": "cultural", "duration_hours": 2.5, "cost_budget": 8, "cost_midrange": 15, "cost_luxury": 25},
            {"title": "Lakeside or Riverside Picnic", "description": "Enjoy a relaxing picnic by the water with locally sourced snacks and drinks.", "category": "leisure", "duration_hours": 2.0, "cost_budget": 12, "cost_midrange": 20, "cost_luxury": 50},
            {"title": "Spa and Wellness Session", "description": "Rejuvenate with a traditional massage and wellness treatment at a local spa.", "category": "leisure", "duration_hours": 2.0, "cost_budget": 20, "cost_midrange": 60, "cost_luxury": 150},
        ],
        "evening": [
            {"title": "Sunset Viewing", "description": "Find the perfect vantage point to watch the sunset paint the sky in brilliant colors.", "category": "leisure", "duration_hours": 1.0, "cost_budget": 0, "cost_midrange": 0, "cost_luxury": 0},
            {"title": "Fine Dining Experience", "description": "Enjoy a leisurely dinner at a highly-rated local restaurant, savoring regional specialties.", "category": "dining", "duration_hours": 2.0, "cost_budget": 15, "cost_midrange": 40, "cost_luxury": 120},
        ],
    },
    "Adventure": {
        "morning": [
            {"title": "Sunrise Hike to Viewpoint", "description": "Beat the crowds with an early morning hike to a stunning natural viewpoint.", "category": "adventure", "duration_hours": 3.0, "cost_budget": 5, "cost_midrange": 20, "cost_luxury": 80},
            {"title": "Kayaking or River Rafting", "description": "Tackle the local waterways with an experienced guide for an adrenaline-pumping experience.", "category": "adventure", "duration_hours": 3.0, "cost_budget": 25, "cost_midrange": 60, "cost_luxury": 150},
            {"title": "Rock Climbing Session", "description": "Scale natural rock faces or visit a local climbing park with certified instructors.", "category": "adventure", "duration_hours": 2.5, "cost_budget": 20, "cost_midrange": 50, "cost_luxury": 120},
        ],
        "afternoon": [
            {"title": "Zip-lining through Canopy", "description": "Soar above the treetops on exhilarating zip-lines with breathtaking aerial views.", "category": "adventure", "duration_hours": 2.0, "cost_budget": 30, "cost_midrange": 65, "cost_luxury": 150},
            {"title": "Mountain Biking Trail", "description": "Tackle scenic mountain biking trails ranging from beginner to expert difficulty.", "category": "adventure", "duration_hours": 2.5, "cost_budget": 15, "cost_midrange": 40, "cost_luxury": 100},
            {"title": "Snorkeling or Diving Excursion", "description": "Explore the underwater world with guided snorkeling or scuba diving in crystal clear waters.", "category": "adventure", "duration_hours": 3.0, "cost_budget": 20, "cost_midrange": 70, "cost_luxury": 200},
        ],
        "evening": [
            {"title": "Campfire Dinner Under the Stars", "description": "Enjoy a traditional outdoor dinner around a campfire, sharing stories of the day's adventures.", "category": "dining", "duration_hours": 2.0, "cost_budget": 15, "cost_midrange": 35, "cost_luxury": 80},
            {"title": "Night Safari or Wildlife Walk", "description": "Discover nocturnal wildlife on a guided night safari with expert naturalists.", "category": "adventure", "duration_hours": 2.5, "cost_budget": 25, "cost_midrange": 60, "cost_luxury": 150},
        ],
    },
    "Cultural": {
        "morning": [
            {"title": "Historic Old Town Walking Tour", "description": "Explore centuries of history on a guided walking tour through the UNESCO-listed old town.", "category": "cultural", "duration_hours": 2.5, "cost_budget": 10, "cost_midrange": 25, "cost_luxury": 80},
            {"title": "Local Market & Cooking Class", "description": "Shop for fresh ingredients at the local market then learn to cook traditional dishes with a local chef.", "category": "cultural", "duration_hours": 3.5, "cost_budget": 25, "cost_midrange": 65, "cost_luxury": 150},
            {"title": "Religious Site Visit", "description": "Visit historically significant temples, churches, or mosques with a knowledgeable cultural guide.", "category": "cultural", "duration_hours": 2.0, "cost_budget": 5, "cost_midrange": 15, "cost_luxury": 40},
        ],
        "afternoon": [
            {"title": "Art Gallery and Museum Circuit", "description": "Discover local artistic traditions across multiple galleries and cultural institutions.", "category": "cultural", "duration_hours": 3.0, "cost_budget": 10, "cost_midrange": 25, "cost_luxury": 60},
            {"title": "Traditional Craft Workshop", "description": "Learn a traditional local craft — pottery, weaving, or painting — from a master artisan.", "category": "cultural", "duration_hours": 2.5, "cost_budget": 20, "cost_midrange": 50, "cost_luxury": 120},
            {"title": "Neighborhood Food Walk", "description": "Taste your way through diverse neighborhood eateries sampling authentic local flavors.", "category": "dining", "duration_hours": 2.5, "cost_budget": 15, "cost_midrange": 35, "cost_luxury": 80},
        ],
        "evening": [
            {"title": "Traditional Performance or Theatre", "description": "Attend a traditional music, dance, or theatre performance celebrating local culture.", "category": "cultural", "duration_hours": 2.0, "cost_budget": 15, "cost_midrange": 40, "cost_luxury": 120},
            {"title": "Rooftop Dinner with City Views", "description": "Dine at a rooftop restaurant while enjoying panoramic views of the illuminated city.", "category": "dining", "duration_hours": 2.0, "cost_budget": 20, "cost_midrange": 55, "cost_luxury": 150},
        ],
    },
    "Luxury": {
        "morning": [
            {"title": "Private Helicopter Tour", "description": "Take in breathtaking aerial views of the destination on a private helicopter sightseeing tour.", "category": "adventure", "duration_hours": 1.5, "cost_budget": 200, "cost_midrange": 400, "cost_luxury": 800},
            {"title": "Sunrise Yacht Cruise", "description": "Watch the sunrise from the deck of a private luxury yacht with champagne breakfast.", "category": "leisure", "duration_hours": 3.0, "cost_budget": 100, "cost_midrange": 300, "cost_luxury": 700},
            {"title": "Private Chef Breakfast Experience", "description": "A personal chef prepares a lavish breakfast at your villa or suite using the finest local ingredients.", "category": "dining", "duration_hours": 1.5, "cost_budget": 80, "cost_midrange": 150, "cost_luxury": 350},
        ],
        "afternoon": [
            {"title": "Private Guided Cultural Tour", "description": "Skip the crowds with a private guide who opens exclusive doors to hidden gems and VIP access.", "category": "cultural", "duration_hours": 3.0, "cost_budget": 80, "cost_midrange": 200, "cost_luxury": 500},
            {"title": "Luxury Spa & Wellness Retreat", "description": "A full afternoon of bespoke treatments at the destination's most prestigious spa.", "category": "leisure", "duration_hours": 3.0, "cost_budget": 100, "cost_midrange": 250, "cost_luxury": 600},
            {"title": "Wine Tasting & Vineyard Tour", "description": "Visit a premier winery for an exclusive tasting with the head sommelier.", "category": "dining", "duration_hours": 2.5, "cost_budget": 40, "cost_midrange": 100, "cost_luxury": 300},
        ],
        "evening": [
            {"title": "Michelin-Star Dinner Reservation", "description": "Enjoy a masterfully crafted tasting menu at one of the world's finest restaurants.", "category": "dining", "duration_hours": 2.5, "cost_budget": 80, "cost_midrange": 200, "cost_luxury": 600},
            {"title": "Exclusive Sunset Cocktail Cruise", "description": "Sip premium cocktails aboard a luxury vessel as the sun sets over the horizon.", "category": "leisure", "duration_hours": 2.0, "cost_budget": 60, "cost_midrange": 150, "cost_luxury": 400},
        ],
    },
}

DAY_THEMES = {
    "Cultural": ["Arrival & First Impressions", "Historical Depths", "Art & Cuisine", "Hidden Gems", "Local Life & Markets", "Sacred Spaces", "Creative Quarter", "Farewell & Last Discoveries"],
    "Relaxed": ["Gentle Beginnings", "Slow Mornings & Discovery", "Rest & Renewal", "Wandering Without a Plan", "Nature & Calm", "Indulgence Day", "Reflection & Leisure", "Peaceful Farewell"],
    "Adventure": ["Base Camp & Orientation", "Summit Day", "Water Adventures", "Into the Wild", "Extreme Sports Day", "Night Adventure", "Challenge Day", "Victory Lap"],
    "Luxury": ["Grand Arrival", "Exclusive Experiences", "Pamper Day", "Private Access Day", "Fine Dining Journey", "Bespoke Adventure", "VIP Cultural Day", "Farewell in Style"],
}

BUDGET_KEY = {"Budget": "cost_budget", "Mid-range": "cost_midrange", "Luxury": "cost_luxury"}


def generate_itinerary(
    destination_name: str,
    destination_id: str,
    duration_days: int,
    travel_style: str,
    budget_level: str,
) -> dict:
    """Generate a realistic day-by-day itinerary based on style and budget."""
    style = travel_style if travel_style in ACTIVITY_LIBRARY else "Cultural"
    budget_key = BUDGET_KEY.get(budget_level, "cost_midrange")
    themes = DAY_THEMES.get(style, DAY_THEMES["Cultural"])

    day_plans = []
    total_cost = 0.0

    for day_num in range(1, duration_days + 1):
        theme = themes[(day_num - 1) % len(themes)]
        library = ACTIVITY_LIBRARY[style]
        activities = []
        day_cost = 0.0

        # Pick activities for each time of day, cycling through options
        for time_slot, slot_activities in library.items():
            activity_data = slot_activities[(day_num - 1) % len(slot_activities)]
            cost = float(activity_data[budget_key])
            activity = {
                "time_of_day": time_slot,
                "title": activity_data["title"],
                "description": activity_data["description"],
                "location": destination_name,
                "duration_hours": activity_data["duration_hours"],
                "estimated_cost_usd": cost,
                "category": activity_data["category"],
            }
            activities.append(activity)
            day_cost += cost

        tips = _get_tip(style, day_num)
        day_plans.append({
            "day": day_num,
            "theme": theme,
            "activities": activities,
            "total_estimated_cost_usd": round(day_cost, 2),
            "tips": tips,
        })
        total_cost += day_cost

    return {
        "destination_id": destination_id,
        "destination_name": destination_name,
        "duration_days": duration_days,
        "travel_style": style,
        "budget_level": budget_level,
        "title": f"{duration_days}-Day {style} Journey through {destination_name}",
        "summary": f"A carefully crafted {duration_days}-day {style.lower()} itinerary for {destination_name}, tailored to a {budget_level.lower()} traveler.",
        "day_plans": day_plans,
        "total_estimated_cost_usd": round(total_cost, 2),
    }


def _get_tip(style: str, day: int) -> str:
    tips = {
        "Cultural": [
            "Book museum tickets in advance online to avoid long queues.",
            "Try asking locals for restaurant recommendations — they know the best spots.",
            "Many cultural sites offer free admission on the first Sunday of the month.",
            "Consider hiring a local guide for a more authentic perspective.",
        ],
        "Relaxed": [
            "There is no rush — let the day unfold naturally.",
            "Pack a light journal to record your impressions.",
            "Avoid peak tourist hours (10am-2pm) at popular sites.",
            "A good pair of comfortable shoes is your best travel companion.",
        ],
        "Adventure": [
            "Always check weather conditions before outdoor activities.",
            "Stay hydrated and carry energy snacks for long excursions.",
            "Ensure your travel insurance covers adventure activities.",
            "Book guides at least 24 hours in advance for popular trails.",
        ],
        "Luxury": [
            "Concierge services can arrange exclusive experiences not listed online.",
            "Tip generously — it opens doors to exceptional personalized service.",
            "Request early check-in or late check-out for maximum relaxation.",
            "Private transfers eliminate wait times and add a seamless touch.",
        ],
    }
    style_tips = tips.get(style, tips["Cultural"])
    return style_tips[(day - 1) % len(style_tips)]
