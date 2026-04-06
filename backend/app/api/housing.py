from fastapi import APIRouter, Query
from typing import Optional
import json
import os

router = APIRouter()

def load_live_housing():
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "live_housing.json")
    try:
        with open(data_path, "r") as f:
            return json.load(f)
    except Exception:
        return []

@router.get("/listings")
def get_housing_listings(
    country: Optional[str] = Query(None, description="Country name"),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    student_friendly: Optional[bool] = Query(None),
):
    listings = load_live_housing()

    if country and country != "All":
        # Handle cases like "UK" matching "United Kingdom"
        c_map = {"UK": "United Kingdom", "USA": "United States"}
        target_country = c_map.get(country, country).lower()
        listings = [l for l in listings if target_country in l.get("country", "").lower() or target_country == l.get("country_code", "").lower()]
        
    if min_price is not None:
        listings = [l for l in listings if l.get("price_inr", 0) >= min_price]
    if max_price is not None:
        listings = [l for l in listings if l.get("price_inr", 0) <= max_price]
    if student_friendly is not None and student_friendly:
        listings = [l for l in listings if l.get("student_friendly") == True]

    return {"total": len(listings), "results": listings}
