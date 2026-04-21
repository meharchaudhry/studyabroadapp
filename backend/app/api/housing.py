import asyncio
from fastapi import APIRouter, Query
from typing import Optional
from app.services.housing_scraper import get_real_listings, COUNTRY_SCRAPERS, SEARCH_LINKS

router = APIRouter()

SUPPORTED_COUNTRIES = list(COUNTRY_SCRAPERS.keys()) + list(SEARCH_LINKS.keys())

# City options per country
COUNTRY_CITIES = {
    "United Kingdom": [
        "London", "Manchester", "Edinburgh", "Birmingham", "Bristol",
        "Leeds", "Glasgow", "Liverpool", "Nottingham", "Sheffield",
    ],
    "Germany": ["Munich", "Berlin", "Hamburg", "Frankfurt", "Cologne", "Heidelberg"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "United States": ["New York", "Boston", "Chicago", "Los Angeles", "San Francisco"],
    "Canada": ["Toronto", "Vancouver", "Montreal", "Ottawa"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Eindhoven"],
    "France": ["Paris", "Lyon", "Marseille", "Bordeaux"],
    "Singapore": ["Singapore"],
    "Japan": ["Tokyo", "Osaka", "Kyoto"],
    "Ireland": ["Dublin", "Cork", "Galway"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmö"],
}


@router.get("/listings")
async def get_housing_listings(
    country: str = Query("United Kingdom", description="Country name"),
    city: Optional[str] = Query(None, description="City within the country"),
    max_budget_inr: Optional[int] = Query(None, description="Max monthly budget in INR"),
    student_friendly: Optional[bool] = Query(None, description="Filter student-friendly only"),
):
    """Fetch real housing listings from live property websites."""

    data = await get_real_listings(
        country=country,
        city=city,
        max_budget_inr=max_budget_inr,
    )

    listings = data.get("listings", [])

    # Apply student_friendly filter
    if student_friendly:
        listings = [l for l in listings if l.get("student_friendly")]

    return {
        "country": country,
        "city": city,
        "source": data.get("source"),
        "scraped": data.get("scraped", False),
        "search_link": data.get("search_link"),
        "total": len(listings),
        "results": listings,
    }


@router.get("/countries")
def get_housing_countries():
    """List all supported countries and their cities."""
    return {
        "countries": [
            {
                "name": c,
                "cities": COUNTRY_CITIES.get(c, []),
                "scraped": c in COUNTRY_SCRAPERS,
            }
            for c in SUPPORTED_COUNTRIES
        ]
    }
