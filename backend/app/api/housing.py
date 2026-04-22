from fastapi import APIRouter, Query
from typing import Optional
from app.services.housing_scraper import (
    get_real_listings,
    COUNTRY_SCRAPERS,
    PLATFORM_GUIDES,
    WGGESUCHT_CITIES,
    SPAREROOM_UK_CITIES,
)

router = APIRouter()

ALL_COUNTRIES = list(COUNTRY_SCRAPERS.keys()) + [
    c for c in PLATFORM_GUIDES if c not in COUNTRY_SCRAPERS
]

COUNTRY_CITIES = {
    "United Kingdom":       list(SPAREROOM_UK_CITIES.keys()),
    "Germany":              list(WGGESUCHT_CITIES.keys()),
    "Australia":            ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "United States":        ["New York", "Boston", "Chicago", "Los Angeles", "San Francisco", "Seattle", "Austin", "Houston", "Atlanta"],
    "Canada":               ["Toronto", "Vancouver", "Montreal", "Ottawa", "Calgary"],
    "Netherlands":          ["Amsterdam", "Rotterdam", "The Hague", "Eindhoven", "Utrecht"],
    "France":               ["Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse"],
    "Singapore":            ["Singapore"],
    "Japan":                ["Tokyo", "Osaka", "Kyoto", "Nagoya", "Fukuoka"],
    "Ireland":              ["Dublin", "Cork", "Galway", "Limerick"],
    "Sweden":               ["Stockholm", "Gothenburg", "Malmö", "Uppsala"],
    "Denmark":              ["Copenhagen", "Aarhus", "Odense"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah"],
    "New Zealand":          ["Auckland", "Wellington", "Christchurch"],
    "South Korea":          ["Seoul", "Busan", "Daejeon", "Incheon"],
    "Spain":                ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"],
    "Norway":               ["Oslo", "Bergen", "Trondheim"],
    "Italy":                ["Rome", "Milan", "Bologna", "Florence", "Turin"],
}


@router.get("/listings")
async def get_housing_listings(
    country: str = Query("United Kingdom"),
    city: Optional[str] = Query(None),
    max_budget_inr: Optional[int] = Query(None),
    student_friendly: Optional[bool] = Query(None),
):
    """
    Live listings (UK via SpareRoom, Germany via WG-Gesucht) + platform guides for all countries.
    """
    data = await get_real_listings(country=country, city=city, max_budget_inr=max_budget_inr)
    listings = data.get("listings", [])
    if student_friendly:
        listings = [l for l in listings if l.get("student_friendly")]

    return {
        "country":         country,
        "city":            city,
        "source":          data.get("source"),
        "scraped":         data.get("scraped", False),
        "total":           len(listings),
        "results":         listings,
        "platform_guides": data.get("platform_guides", []),
        "error":           data.get("error"),
    }


@router.get("/countries")
def get_housing_countries():
    return {
        "countries": [
            {"name": c, "cities": COUNTRY_CITIES.get(c, []), "scraped": c in COUNTRY_SCRAPERS}
            for c in ALL_COUNTRIES
        ]
    }
