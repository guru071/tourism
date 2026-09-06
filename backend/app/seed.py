"""
Seed script: Populates the database with sample destinations.
Run with: python -m app.seed
(from the backend/ directory with DB running)
"""
import asyncio
from app.core.database import async_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from app.models.destination import Destination

DESTINATIONS = [
    {
        "name": "Bali",
        "slug": "bali-indonesia",
        "country": "Indonesia",
        "city": "Ubud",
        "region": "Southeast Asia",
        "category": "Cultural",
        "description": "The island of the gods — Bali enchants with terraced rice paddies, ancient temples, world-class surf, and a deeply spiritual Hindu culture unlike anywhere else in Indonesia.",
        "latitude": -8.4095,
        "longitude": 115.1889,
        "timezone": "Asia/Makassar",
        "image_urls": [
            "https://picsum.photos/seed/bali-temple/800/500",
            "https://picsum.photos/seed/bali-rice/800/500",
        ],
        "tags": ["temples", "surf", "yoga", "rice-terraces", "nightlife"],
    },
    {
        "name": "Santorini",
        "slug": "santorini-greece",
        "country": "Greece",
        "city": "Oia",
        "region": "Southern Europe",
        "category": "Beach",
        "description": "Perched on volcanic cliffs above the Aegean Sea, Santorini dazzles with its iconic white-washed buildings, blue-domed churches, blood-red sunsets, and world-renowned wines.",
        "latitude": 36.3932,
        "longitude": 25.4615,
        "timezone": "Europe/Athens",
        "image_urls": [
            "https://picsum.photos/seed/santorini-blue/800/500",
            "https://picsum.photos/seed/santorini-sunset/800/500",
        ],
        "tags": ["sunset", "wine", "beaches", "luxury", "romantic"],
    },
    {
        "name": "Kyoto",
        "slug": "kyoto-japan",
        "country": "Japan",
        "city": "Kyoto",
        "region": "East Asia",
        "category": "Cultural",
        "description": "Japan's ancient imperial capital is a city of 1,600 Buddhist temples, 400 Shinto shrines, and exquisite traditional arts. From geisha districts to bamboo groves, Kyoto is a living museum.",
        "latitude": 35.0116,
        "longitude": 135.7681,
        "timezone": "Asia/Tokyo",
        "image_urls": [
            "https://picsum.photos/seed/kyoto-temple/800/500",
            "https://picsum.photos/seed/kyoto-bamboo/800/500",
        ],
        "tags": ["temples", "geisha", "tea-ceremony", "cherry-blossom", "zen"],
    },
    {
        "name": "Patagonia",
        "slug": "patagonia-argentina",
        "country": "Argentina",
        "city": "El Calafate",
        "region": "South America",
        "category": "Adventure",
        "description": "At the end of the world, Patagonia delivers raw, untamed wilderness — glaciers the size of cities, jagged granite spires, turquoise lakes, and condors riding thermal winds above the pampas.",
        "latitude": -50.3374,
        "longitude": -72.2619,
        "timezone": "America/Argentina/Rio_Gallegos",
        "image_urls": [
            "https://picsum.photos/seed/patagonia-glacier/800/500",
            "https://picsum.photos/seed/patagonia-mountain/800/500",
        ],
        "tags": ["glacier", "trekking", "hiking", "wildlife", "extreme"],
    },
    {
        "name": "Marrakech",
        "slug": "marrakech-morocco",
        "country": "Morocco",
        "city": "Marrakech",
        "region": "North Africa",
        "category": "Cultural",
        "description": "Marrakech is a full sensory assault in the best possible way — labyrinthine souks perfumed with spices, the spectacular Djemaa el-Fna square, ornate riads, and the snow-capped Atlas Mountains on the horizon.",
        "latitude": 31.6295,
        "longitude": -7.9811,
        "timezone": "Africa/Casablanca",
        "image_urls": [
            "https://picsum.photos/seed/marrakech-souk/800/500",
            "https://picsum.photos/seed/marrakech-palace/800/500",
        ],
        "tags": ["souk", "spices", "riad", "desert", "hammam"],
    },
    {
        "name": "Queenstown",
        "slug": "queenstown-new-zealand",
        "country": "New Zealand",
        "city": "Queenstown",
        "region": "Oceania",
        "category": "Adventure",
        "description": "The world's adventure capital, Queenstown sits in a glacially carved valley beside Lake Wakatipu, surrounded by the Remarkables mountain range. Bungee jumping was invented here.",
        "latitude": -45.0312,
        "longitude": 168.6626,
        "timezone": "Pacific/Auckland",
        "image_urls": [
            "https://picsum.photos/seed/queenstown-lake/800/500",
            "https://picsum.photos/seed/queenstown-ski/800/500",
        ],
        "tags": ["bungee", "skiing", "hiking", "fjords", "wine"],
    },
    {
        "name": "Maldives",
        "slug": "maldives",
        "country": "Maldives",
        "city": "Malé",
        "region": "South Asia",
        "category": "Beach",
        "description": "A necklace of 1,200 coral islands scattered across the Indian Ocean, the Maldives is the world's lowest-lying nation and home to the most luminous turquoise waters and pristine overwater bungalows on Earth.",
        "latitude": 3.2028,
        "longitude": 73.2207,
        "timezone": "Indian/Maldives",
        "image_urls": [
            "https://picsum.photos/seed/maldives-overwater/800/500",
            "https://picsum.photos/seed/maldives-reef/800/500",
        ],
        "tags": ["overwater-bungalow", "snorkeling", "diving", "luxury", "honeymoon"],
    },
    {
        "name": "Machu Picchu",
        "slug": "machu-picchu-peru",
        "country": "Peru",
        "city": "Aguas Calientes",
        "region": "South America",
        "category": "Cultural",
        "description": "Hidden in the clouds above the Sacred Valley of the Incas, Machu Picchu is one of humanity's greatest architectural achievements. The lost city emerges from morning mist like a dream.",
        "latitude": -13.1631,
        "longitude": -72.5450,
        "timezone": "America/Lima",
        "image_urls": [
            "https://picsum.photos/seed/machu-picchu-ruins/800/500",
            "https://picsum.photos/seed/machu-picchu-trail/800/500",
        ],
        "tags": ["inca", "ruins", "hiking", "inca-trail", "unesco"],
    },
    {
        "name": "Safari Serengeti",
        "slug": "serengeti-tanzania",
        "country": "Tanzania",
        "city": "Arusha",
        "region": "East Africa",
        "category": "Wildlife",
        "description": "The Serengeti hosts the world's most spectacular wildlife event — the Great Migration — where 1.5 million wildebeest, zebras and gazelles thunder across the plains in an endless cycle of life.",
        "latitude": -2.3333,
        "longitude": 34.8333,
        "timezone": "Africa/Dar_es_Salaam",
        "image_urls": [
            "https://picsum.photos/seed/serengeti-lion/800/500",
            "https://picsum.photos/seed/serengeti-migration/800/500",
        ],
        "tags": ["safari", "wildlife", "big-five", "migration", "camping"],
    },
    {
        "name": "Tokyo",
        "slug": "tokyo-japan",
        "country": "Japan",
        "city": "Tokyo",
        "region": "East Asia",
        "category": "City",
        "description": "The world's most populous metropolis seamlessly blends ultramodern neon-lit skyscrapers with serene ancient temples, samurai culture, cutting-edge fashion, and the finest food scene on the planet.",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "timezone": "Asia/Tokyo",
        "image_urls": [
            "https://picsum.photos/seed/tokyo-skyline/800/500",
            "https://picsum.photos/seed/tokyo-shrine/800/500",
        ],
        "tags": ["anime", "sushi", "technology", "fashion", "temples"],
    },
    {
        "name": "Iceland Ring Road",
        "slug": "iceland-ring-road",
        "country": "Iceland",
        "city": "Reykjavik",
        "region": "Northern Europe",
        "category": "Adventure",
        "description": "Drive the legendary Route 1 past waterfalls, geysers, black sand beaches, lava fields, and glacier lagoons. In winter, hunt the Northern Lights; in summer, drive under the midnight sun.",
        "latitude": 64.9631,
        "longitude": -19.0208,
        "timezone": "Atlantic/Reykjavik",
        "image_urls": [
            "https://picsum.photos/seed/iceland-aurora/800/500",
            "https://picsum.photos/seed/iceland-waterfall/800/500",
        ],
        "tags": ["northern-lights", "waterfall", "geyser", "glacier", "road-trip"],
    },
    {
        "name": "Amalfi Coast",
        "slug": "amalfi-coast-italy",
        "country": "Italy",
        "city": "Positano",
        "region": "Southern Europe",
        "category": "Beach",
        "description": "The Amalfi Coast is a 50-kilometre stretch of drama — pastel-coloured villages clinging to vertiginous cliffs above the sparkling Tyrrhenian Sea, with lemon groves, fresh seafood, and dolce vita.",
        "latitude": 40.6340,
        "longitude": 14.6027,
        "timezone": "Europe/Rome",
        "image_urls": [
            "https://picsum.photos/seed/amalfi-coast-cliff/800/500",
            "https://picsum.photos/seed/amalfi-village/800/500",
        ],
        "tags": ["cliff-villages", "seafood", "boat-trips", "limoncello", "romance"],
    },
]


async def seed():
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as session:
        existing = (await session.execute(select(Destination))).scalars().all()
        existing_slugs = {d.slug for d in existing}
        added = 0
        for data in DESTINATIONS:
            if data["slug"] in existing_slugs:
                continue
            dest = Destination(**data)
            session.add(dest)
            added += 1
        await session.commit()
        print(f"✅ Seeded {added} destinations ({len(existing_slugs)} already existed)")


if __name__ == "__main__":
    asyncio.run(seed())
