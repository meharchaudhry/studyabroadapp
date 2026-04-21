import json
import os
from typing import Any, Dict, List, Optional


COUNTRY_SCRAPERS: Dict[str, str] = {
    "United Kingdom": "https://www.spareroom.co.uk",
    "Germany": "https://www.wg-gesucht.de",
    "France": "https://www.messervices.etudiant.gouv.fr",
    "Netherlands": "https://kamernet.nl",
    "Australia": "https://flatmates.com.au",
    "Singapore": "https://www.propertyguru.com.sg",
    "Hong Kong": "https://www.spacious.hk",
    "United States": "https://offcampuspartners.com",
    "Canada": "https://www.kijiji.ca/b-apartments-condos",
    "Ireland": "https://www.daft.ie",
    "Spain": "https://www.idealista.com",
    "Switzerland": "https://www.homegate.ch",
}

SEARCH_LINKS: Dict[str, str] = {
    "United Kingdom": "https://www.spareroom.co.uk/flatshare/?search_id=",
    "Germany": "https://www.wg-gesucht.de/en/wg-zimmer-in-",
    "France": "https://www.appartager.com",
    "Netherlands": "https://kamernet.nl/en/for-rent/rooms",
    "Australia": "https://flatmates.com.au/rooms",
    "Singapore": "https://www.propertyguru.com.sg/property-for-rent",
    "Hong Kong": "https://www.spacious.hk/en/rent",
    "United States": "https://offcampuspartners.com",
    "Canada": "https://www.kijiji.ca/b-apartments-condos",
    "Ireland": "https://www.daft.ie/property-for-rent",
    "Spain": "https://www.idealista.com/en/alquiler-viviendas",
    "Switzerland": "https://www.homegate.ch/rent",
}


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _data_path() -> str:
    return os.path.join(_repo_root(), "data", "live_housing.json")


def _load_listings() -> List[dict]:
    try:
        with open(_data_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _matches_country(row: dict, country: str) -> bool:
    target = (country or "").strip().lower()
    if not target:
        return True
    row_country = str(row.get("country", "") or "").strip().lower()
    row_code = str(row.get("country_code", "") or "").strip().lower()
    aliases = {
        "uk": "united kingdom",
        "usa": "united states",
        "us": "united states",
        "hongkong": "hong kong",
    }
    target = aliases.get(target, target)
    return target in row_country or target == row_code


def _score_listing(listing: dict, max_budget_inr: Optional[int]) -> bool:
    if max_budget_inr is None:
        return True
    price = listing.get("price_inr")
    return isinstance(price, (int, float)) and price <= max_budget_inr


async def get_real_listings(
    country: str,
    city: Optional[str] = None,
    max_budget_inr: Optional[int] = None,
) -> Dict[str, Any]:
    """Return housing listings from the local generated dataset.

    This keeps the API functional without depending on fragile live scrapers.
    """
    all_listings = _load_listings()
    filtered: List[dict] = []

    city_l = (city or "").strip().lower()
    country_l = (country or "").strip().lower()

    for listing in all_listings:
        if country and not _matches_country(listing, country):
            continue
        if city_l and city_l != "all":
            title = str(listing.get("title", "") or "").lower()
            if city_l not in title:
                continue
        if not _score_listing(listing, max_budget_inr):
            continue
        filtered.append(listing)

    if not filtered and all_listings:
        for listing in all_listings:
            if _matches_country(listing, country):
                filtered.append(listing)
                if len(filtered) >= 30:
                    break

    search_link = SEARCH_LINKS.get(country) or SEARCH_LINKS.get(country.title()) or ""
    source = COUNTRY_SCRAPERS.get(country) or COUNTRY_SCRAPERS.get(country.title()) or "local_dataset"

    return {
        "source": source,
        "scraped": False,
        "search_link": search_link,
        "listings": filtered[:200],
    }