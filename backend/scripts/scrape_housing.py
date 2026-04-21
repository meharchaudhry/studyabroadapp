import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import sys
import random
import time

# --- Setup ---
# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load environment variables
dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# --- Constants ---
REALTOR_API_KEY = os.getenv("REALTOR_API_KEY")
API_HOST = "realtor-com.p.rapidapi.com"

# Define cities of interest for the countries you support
CITIES_OF_INTEREST = {
    "USA": ["New York, NY", "Boston, MA", "Los Angeles, CA", "Chicago, IL"],
    "UK": ["London", "Manchester", "Edinburgh"],
    "Germany": ["Berlin", "Munich", "Hamburg"],
    "France": ["Paris"],
    "Netherlands": ["Amsterdam"],
    "Australia": ["Sydney", "Melbourne"],
    "Singapore": ["Singapore"],
    "Hong Kong": ["Hong Kong"],
    "Spain": ["Madrid", "Barcelona"],
    "Switzerland": ["Zurich", "Geneva"],
    "Finland": ["Helsinki"],
    "India": ["Bangalore", "Mumbai", "Delhi"],
}

def get_project_root() -> Path:
    """Gets the absolute path to the project root directory."""
    return Path(__file__).parent.parent

def fetch_realtor_listings(city: str, country: str) -> list[dict]:
    """Fetches rental listings for a given city from the Realtor.com API."""
    if not REALTOR_API_KEY:
        print("❌ Realtor API key is missing. Please add REALTOR_API_KEY to your .env file.")
        return []

    url = "https://realtor-com.p.rapidapi.com/properties/v3/list"
    payload = {
        "city": city.split(',')[0],
        "state_code": city.split(', ')[1] if ',' in city else None,
        "limit": 50,
        "offset": 0,
        "prop_status": "for_rent",
        "sort": {
            "direction": "desc",
            "field": "list_date"
        }
    }
    # Remove None values from payload
    payload = {k: v for k, v in payload.items() if v is not None}

    headers = {
        "x-rapidapi-key": REALTOR_API_KEY,
        "x-rapidapi-host": API_HOST
    }

    print(f"  Fetching rental listings for {city}, {country}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("home_search", {}).get("results", [])
    except requests.RequestException as e:
        print(f"  ❌ API request failed for {city}: {e}")
        if e.response:
            print(f"  Response: {e.response.text}")
    except Exception as e:
        print(f"  ❌ An unexpected error occurred for {city}: {e}")
    return []

def transform_listing(listing: dict, country: str) -> dict:
    """Transforms a raw API listing into the desired format."""
    # Basic details
    prop_id = listing.get("property_id")
    details = listing.get("description")
    location = listing.get("location", {})
    address = location.get("address", {})
    
    # Price - find the first available price
    price = listing.get("list_price")

    # Photos
    photos = listing.get("photos", [])
    image_url = photos[0].get("href") if photos else "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&q=80"

    # Amenities
    tags = listing.get("tags", [])
    amenities = [tag for tag in tags if "days_on_market" not in tag and "for_rent" not in tag]

    return {
        "id": f"realtor_{prop_id}",
        "title": f"{details.get('beds', 'Studio')} Bed in {address.get('city', 'Unknown City')}",
        "country": country,
        "price_inr": int(price * 83) if price else random.randint(50000, 150000), # Convert USD to INR approx
        "distance_km": round(random.uniform(1.0, 10.0), 1), # Placeholder
        "amenities": amenities,
        "image_url": image_url,
        "available_from": "Immediate", # Placeholder
        "student_friendly": True, # Assume student friendly
        "source": "Realtor.com",
        "url": f"https://www.realtor.com/realestateandhomes-detail/{listing.get('permalink')}"
    }

def scrape_and_save_housing_data():
    """Main function to scrape and save housing data."""
    root = get_project_root()
    output_path = root / "data" / "housing_data.json"
    all_listings = []
    total_listings_count = 0

    print("🚀 Starting housing data scrape from Realtor.com...")

    for country, cities in CITIES_OF_INTEREST.items():
        print(f"\nProcessing country: {country}")
        country_listings_count = 0
        for city in cities:
            raw_listings = fetch_realtor_listings(city, country)
            if raw_listings:
                print(f"    -> Found {len(raw_listings)} raw listings for {city}.")
                transformed_count = 0
                for listing in raw_listings:
                    # Basic filter for apartments/rentals
                    if listing.get("description") and listing.get("description").get("type") in ["apartment", "condo", "townhome", "single_family"]:
                        transformed = transform_listing(listing, country)
                        all_listings.append(transformed)
                        transformed_count += 1
                country_listings_count += transformed_count
                print(f"    -> Transformed and added {transformed_count} listings for {city}.")
            else:
                print(f"    -> No listings found for {city}.")
            
            print("    ...waiting 1 second to respect API rate limit...")
            time.sleep(1) # IMPORTANT: Wait for 1 second between requests

        print(f"  Found {country_listings_count} total listings for {country}.")
        total_listings_count += country_listings_count

    # Save the data
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_listings, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Scraping complete! Saved {total_listings_count} total listings to {output_path.relative_to(root.parent)}")

if __name__ == "__main__":
    scrape_and_save_housing_data()
