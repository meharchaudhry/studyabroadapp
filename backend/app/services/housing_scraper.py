"""
Real housing listings scraped from live property sites.

UK:      SpareRoom.co.uk  — OG-tag fetch of individual listing pages
Germany: WG-Gesucht.de   — JSON-LD RealEstateListing extraction (Germany only)
Canada:  Craigslist       — OG-tag fetch of individual posting pages
USA:     Craigslist       — same technique as Canada

All other countries (Netherlands, France, Singapore, Australia, Ireland, Japan,
Sweden, Denmark, UAE, New Zealand, South Korea) return platform_guides — a curated
list of student-friendly housing websites for that country.

Conversion rates (approx):
  GBP → INR : 107
  EUR → INR : 90
  CAD → INR : 62
  USD → INR : 83
  AUD → INR : 55
  JPY → INR : 0.56
  SGD → INR : 62
  AED → INR : 22
  NZD → INR : 50
  KRW → INR : 0.062
  SEK → INR : 8
  DKK → INR : 12
"""

import asyncio
import re
import time
import html as htmllib
from typing import Optional

import httpx

# ── Conversion rates ──────────────────────────────────────────────────────────
FX = {
    "GBP": 107,
    "EUR": 90,
    "CAD": 62,
    "USD": 83,
    "AUD": 55,
    "JPY": 0.56,
    "SGD": 62,
    "AED": 22,
    "NZD": 50,
    "KRW": 0.062,
    "SEK": 8,
    "DKK": 12,
}

# ── In-memory cache ───────────────────────────────────────────────────────────
_CACHE: dict = {}
CACHE_TTL = 1800  # 30 minutes

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
}

# ── Platform guides: curated student-friendly sites per country ───────────────
PLATFORM_GUIDES: dict = {
    "Netherlands": [
        {"name": "Kamernet", "url": "https://kamernet.nl/en/for-rent/rooms-amsterdam", "logo_domain": "kamernet.nl", "desc": "Largest Dutch student room marketplace with verified listings", "student_friendly": True, "type": "rooms", "logo_color": "#4CAF50"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Amsterdam--Netherlands/rooms", "logo_domain": "housinganywhere.com", "desc": "International platform popular with TU Delft & UvA students", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Pararius", "url": "https://www.pararius.com/rooms/amsterdam", "logo_domain": "pararius.com", "desc": "Dutch rental platform — free for tenants, good English support", "student_friendly": False, "type": "apartments", "logo_color": "#0066CC"},
        {"name": "Funda", "url": "https://www.funda.nl/huur/amsterdam/kamer/", "logo_domain": "funda.nl", "desc": "Netherlands' largest property portal for rooms and apartments", "student_friendly": False, "type": "apartments", "logo_color": "#E84E10"},
        {"name": "Nestpick", "url": "https://www.nestpick.com/rooms/amsterdam/", "logo_domain": "nestpick.com", "desc": "Aggregates furnished rooms across multiple Dutch platforms", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    "France": [
        {"name": "Immojeune", "url": "https://www.immojeune.com/location-etudiant/paris-75.html", "logo_domain": "immojeune.com", "desc": "Student housing specialist in France — rooms, studios & colocs", "student_friendly": True, "type": "student", "logo_color": "#E91E63"},
        {"name": "La Carte des Colocs", "url": "https://www.lacartedescolocs.fr/colocations/paris", "logo_domain": "lacartedescolocs.fr", "desc": "French flatshare platform popular among international students", "student_friendly": True, "type": "rooms", "logo_color": "#FF5722"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Paris--France/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms from India before you arrive", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Studapart", "url": "https://www.studapart.com/en/p/paris", "logo_domain": "studapart.com", "desc": "100% student-focused, accepts international tenants easily", "student_friendly": True, "type": "student", "logo_color": "#673AB7"},
        {"name": "SeLoger", "url": "https://www.seloger.com/list.htm?types=3,1&idtypebien=8,7&projects=1", "logo_domain": "seloger.com", "desc": "Major French real estate portal with thousands of listings", "student_friendly": False, "type": "apartments", "logo_color": "#0051A5"},
    ],
    "Singapore": [
        {"name": "PropertyGuru", "url": "https://www.propertyguru.com.sg/property-for-rent/rooms-for-rent-in-singapore", "logo_domain": "propertyguru.com.sg", "desc": "Singapore's top property portal with hundreds of room listings", "student_friendly": False, "type": "rooms", "logo_color": "#00AA55"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Singapore/rooms", "logo_domain": "housinganywhere.com", "desc": "Trusted by NUS & NTU international students", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Roomgo Singapore", "url": "https://sg.roomgo.net/rooms-for-rent/", "logo_domain": "roomgo.net", "desc": "Room rentals popular with expats and international students", "student_friendly": True, "type": "rooms", "logo_color": "#9C27B0"},
        {"name": "SRX Property", "url": "https://www.srx.com.sg/rent/rooms", "logo_domain": "srx.com.sg", "desc": "Singapore rental marketplace with verified listings", "student_friendly": False, "type": "apartments", "logo_color": "#FF3D00"},
        {"name": "Nestpick", "url": "https://www.nestpick.com/rooms/singapore/", "logo_domain": "nestpick.com", "desc": "Furnished rooms with flexible tenancy for international students", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    "Australia": [
        {"name": "Flatmates.com.au", "url": "https://flatmates.com.au/rooms", "logo_domain": "flatmates.com.au", "desc": "Australia's #1 flatmate finder — 170k+ listings nationwide", "student_friendly": True, "type": "rooms", "logo_color": "#00BCD4"},
        {"name": "Student.com", "url": "https://www.student.com/au/sydney", "logo_domain": "student.com", "desc": "Purpose-built student accommodation (PBSA) with on-campus feel", "student_friendly": True, "type": "student", "logo_color": "#FF5252"},
        {"name": "Domain", "url": "https://www.domain.com.au/rent/sydney-region-nsw/", "logo_domain": "domain.com.au", "desc": "Major Australian real estate portal with student-friendly filters", "student_friendly": False, "type": "apartments", "logo_color": "#00897B"},
        {"name": "Gumtree Rooms", "url": "https://www.gumtree.com.au/s-flatshare-houseshare/sydney/k0c18663l3003690", "logo_domain": "gumtree.com.au", "desc": "Classifieds with many affordable student room listings", "student_friendly": True, "type": "rooms", "logo_color": "#72BB2F"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Sydney--Australia/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished accommodation before arriving from India", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "UniLodge", "url": "https://www.unilodge.com.au/", "logo_domain": "unilodge.com.au", "desc": "Official student accommodation near Australian universities", "student_friendly": True, "type": "student", "logo_color": "#1565C0"},
    ],
    "Ireland": [
        {"name": "Daft.ie", "url": "https://www.daft.ie/dublin/rooms-to-rent", "logo_domain": "daft.ie", "desc": "Ireland's largest property portal — essential for Dublin rooms", "student_friendly": True, "type": "rooms", "logo_color": "#00AA66"},
        {"name": "Rent.ie", "url": "https://www.rent.ie/rooms-to-rent/dublin/", "logo_domain": "rent.ie", "desc": "Irish rental site with rooms popular among students", "student_friendly": True, "type": "rooms", "logo_color": "#1565C0"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Dublin--Ireland/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms for Trinity, UCD & DCU in advance", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "UniAcco", "url": "https://uniacco.com/ireland", "logo_domain": "uniacco.com", "desc": "Purpose-built student accommodation across Irish university cities", "student_friendly": True, "type": "student", "logo_color": "#7B1FA2"},
        {"name": "MyHome.ie", "url": "https://www.myhome.ie/residential/search?tenure=3", "logo_domain": "myhome.ie", "desc": "Irish property portal with rooms & sharing options nationwide", "student_friendly": False, "type": "apartments", "logo_color": "#E53935"},
    ],
    "Japan": [
        {"name": "Sakura House", "url": "https://www.sakura-house.com/en/type/share-house", "logo_domain": "sakura-house.com", "desc": "Share houses for foreigners — no guarantor needed, English OK", "student_friendly": True, "type": "rooms", "logo_color": "#E91E63"},
        {"name": "GaijinPot Housing", "url": "https://housing.gaijinpot.com/en/rent/", "logo_domain": "gaijinpot.com", "desc": "English-language listings for foreigners in Tokyo & Osaka", "student_friendly": True, "type": "apartments", "logo_color": "#FF5722"},
        {"name": "Leopalace21", "url": "https://www.leopalace21.com/english/", "logo_domain": "leopalace21.com", "desc": "Short-term furnished apartments popular with international students", "student_friendly": True, "type": "apartments", "logo_color": "#3F51B5"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Tokyo--Japan/rooms", "logo_domain": "housinganywhere.com", "desc": "Book from India before visa approval — English support", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Borderless House", "url": "https://www.borderless-house.com/en/japan/", "logo_domain": "borderless-house.com", "desc": "International share houses in Tokyo & Osaka — community focused", "student_friendly": True, "type": "rooms", "logo_color": "#009688"},
    ],
    "Sweden": [
        {"name": "Blocket Bostad", "url": "https://bostad.blocket.se/en/stockholms-lan/hyra/lagenhet", "logo_domain": "blocket.se", "desc": "Sweden's largest online marketplace — rooms and apartments", "student_friendly": False, "type": "apartments", "logo_color": "#FF3D00"},
        {"name": "Samtrygg", "url": "https://www.samtrygg.se/en", "logo_domain": "samtrygg.se", "desc": "Safe subletting platform popular with students in Stockholm", "student_friendly": True, "type": "rooms", "logo_color": "#00BCD4"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Stockholm--Sweden/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near KTH, Chalmers & Stockholm University", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "AF Bostäder", "url": "https://www.afbostader.se/en/", "logo_domain": "afbostader.se", "desc": "Student union housing in Lund — apply as soon as admitted", "student_friendly": True, "type": "student", "logo_color": "#3F51B5"},
        {"name": "SSSB", "url": "https://www.sssb.se/en/", "logo_domain": "sssb.se", "desc": "Official Stockholm student housing — register on day 1 of admission", "student_friendly": True, "type": "student", "logo_color": "#4CAF50"},
    ],
    "Denmark": [
        {"name": "BoligPortal", "url": "https://www.boligportal.dk/en/rentals/", "logo_domain": "boligportal.dk", "desc": "Denmark's most popular rental portal — rooms and apartments", "student_friendly": False, "type": "apartments", "logo_color": "#E53935"},
        {"name": "Findroommate.dk", "url": "https://www.findroommate.dk/", "logo_domain": "findroommate.dk", "desc": "Flatshare and room rentals in Copenhagen — student crowd", "student_friendly": True, "type": "rooms", "logo_color": "#1E88E5"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Copenhagen--Denmark/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near DTU & Copenhagen Business School", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Lejebolig.dk", "url": "https://www.lejebolig.dk/en/", "logo_domain": "lejebolig.dk", "desc": "Danish rental site with English interface for internationals", "student_friendly": False, "type": "apartments", "logo_color": "#00897B"},
        {"name": "Ungdomsboliger", "url": "https://www.ungdomsboliger.dk/", "logo_domain": "ungdomsboliger.dk", "desc": "Official Danish youth & student housing — subsidised options", "student_friendly": True, "type": "student", "logo_color": "#7B1FA2"},
    ],
    "United Arab Emirates": [
        {"name": "Dubizzle", "url": "https://dubai.dubizzle.com/property-for-rent/rooms/", "logo_domain": "dubizzle.com", "desc": "UAE's largest classifieds with many room & shared flat listings", "student_friendly": True, "type": "rooms", "logo_color": "#FF6F00"},
        {"name": "Property Finder", "url": "https://www.propertyfinder.ae/en/search?category=1&price_max=3000", "logo_domain": "propertyfinder.ae", "desc": "Major UAE property portal — filter for studio/room types", "student_friendly": False, "type": "apartments", "logo_color": "#D32F2F"},
        {"name": "Bayut", "url": "https://www.bayut.com/to-rent/residential/dubai/rooms/", "logo_domain": "bayut.com", "desc": "Leading Dubai real estate site with verified listings", "student_friendly": False, "type": "apartments", "logo_color": "#1565C0"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Dubai--United-Arab-Emirates/rooms", "logo_domain": "housinganywhere.com", "desc": "International furnished rooms near UAEU & HBMeU campuses", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
    ],
    "New Zealand": [
        {"name": "TradeMe Property", "url": "https://www.trademe.co.nz/property/flatmates-wanted/", "logo_domain": "trademe.co.nz", "desc": "New Zealand's biggest marketplace — best for flatmate ads", "student_friendly": True, "type": "rooms", "logo_color": "#FF6600"},
        {"name": "Flatmates NZ", "url": "https://www.flatmates.co.nz/rooms-for-rent/auckland", "logo_domain": "flatmates.co.nz", "desc": "NZ-specific flatshare site popular with international students", "student_friendly": True, "type": "rooms", "logo_color": "#00BCD4"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Auckland--New-Zealand/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near University of Auckland & AUT", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Realestate.co.nz", "url": "https://www.realestate.co.nz/rental/search?district=auckland-city", "logo_domain": "realestate.co.nz", "desc": "Major NZ real estate portal for apartments and rooms", "student_friendly": False, "type": "apartments", "logo_color": "#2E7D32"},
    ],
    "South Korea": [
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Seoul--South-Korea/rooms", "logo_domain": "housinganywhere.com", "desc": "English-language furnished rooms near Seoul universities", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "GaijinPot Housing", "url": "https://housing.gaijinpot.com/en/rent/korea/", "logo_domain": "gaijinpot.com", "desc": "English listings for foreigners in Korea including goshiwons", "student_friendly": True, "type": "rooms", "logo_color": "#FF5722"},
        {"name": "Zigbang", "url": "https://www.zigbang.com/", "logo_domain": "zigbang.com", "desc": "Major Korean real estate app — use Google Translate", "student_friendly": False, "type": "apartments", "logo_color": "#5C6BC0"},
        {"name": "Dabang", "url": "https://www.dabangapp.com/", "logo_domain": "dabangapp.com", "desc": "Korean room finder app — popular for officetel & studio search", "student_friendly": False, "type": "apartments", "logo_color": "#FF4081"},
        {"name": "Airbnb Monthly", "url": "https://www.airbnb.com/s/Seoul--South-Korea/homes?min_nights=28", "logo_domain": "airbnb.com", "desc": "Monthly stays — ideal for first month while finding permanent housing", "student_friendly": True, "type": "rooms", "logo_color": "#FF385C"},
    ],
    "United States": [
        {"name": "Craigslist Rooms", "url": "https://www.craigslist.org/about/sites#US", "logo_domain": "craigslist.org", "desc": "Find your city and search 'rooms & shares' for the best deals", "student_friendly": True, "type": "rooms", "logo_color": "#7C4DFF"},
        {"name": "Zillow", "url": "https://www.zillow.com/homes/for_rent/", "logo_domain": "zillow.com", "desc": "USA's largest rental platform — filter by studio for student budget", "student_friendly": False, "type": "apartments", "logo_color": "#006AFF"},
        {"name": "Padmapper", "url": "https://www.padmapper.com/", "logo_domain": "padmapper.com", "desc": "Map-based apartment & room search aggregator across US cities", "student_friendly": True, "type": "rooms", "logo_color": "#E53935"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/United-States/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near US universities with online booking", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Facebook Marketplace", "url": "https://www.facebook.com/marketplace/category/rentals", "logo_domain": "facebook.com", "desc": "Private room listings — often cheaper, check university Facebook groups", "student_friendly": True, "type": "rooms", "logo_color": "#1877F2"},
    ],
}


async def _fetch(client: httpx.AsyncClient, url: str) -> str:
    try:
        r = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
        return r.text if r.status_code == 200 else ""
    except Exception:
        return ""


def _og(html: str, prop: str) -> str:
    """Extract an OpenGraph meta tag value."""
    m = re.search(
        rf'<meta[^>]+property=["\']og:{prop}["\'][^>]+content=["\']([^"\']+)["\']',
        html,
    )
    if not m:
        m = re.search(
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:{prop}["\']',
            html,
        )
    return htmllib.unescape(m.group(1)).strip() if m else ""


# ═══════════════════════════════════════════════════════════════════════════════
# SPAREROOM UK
# ═══════════════════════════════════════════════════════════════════════════════

SPAREROOM_UK_CITIES = {
    "London":       "london",
    "Manchester":   "manchester",
    "Edinburgh":    "edinburgh",
    "Birmingham":   "birmingham",
    "Bristol":      "bristol",
    "Leeds":        "leeds",
    "Glasgow":      "glasgow",
    "Liverpool":    "liverpool",
    "Nottingham":   "nottingham",
    "Sheffield":    "sheffield",
    "Newcastle":    "newcastle_upon_tyne",
    "Coventry":     "coventry",
}


async def _spareroom_detail(client: httpx.AsyncClient, url: str) -> Optional[dict]:
    html = await _fetch(client, url)
    if not html:
        return None

    title       = _og(html, "title")
    description = _og(html, "description")
    image       = _og(html, "image")
    page_url    = _og(html, "url")

    if not description:
        return None

    m_gbp = re.search(r"£([\d,]+)\s*(pw|pcm)?", description, re.IGNORECASE)
    if not m_gbp:
        return None

    price_gbp = int(m_gbp.group(1).replace(",", ""))
    if (m_gbp.group(2) or "").lower() == "pw":
        price_gbp = int(price_gbp * 4.33)

    bills = bool(
        re.search(r"inc\w*\s*bills|bills\s*inc\w*|bills\s*included", description, re.IGNORECASE)
    )
    area_m = re.match(r"^([^:]+)\s*:", description)
    area   = area_m.group(1).strip() if area_m else ""

    return {
        "title":       title or "Room to Rent",
        "area":        area,
        "image_url":   image or None,
        "listing_url": page_url or url,
        "price_inr":   price_gbp * FX["GBP"],
        "currency":    "GBP",
        "price_label": f"£{price_gbp:,}/mo",
        "bills_inc":   bills,
        "source":      "SpareRoom",
        "country":     "United Kingdom",
        "student_friendly": True,
    }


async def scrape_spareroom_uk(city: str = "London", max_budget_inr: Optional[int] = None) -> list:
    slug     = SPAREROOM_UK_CITIES.get(city, city.lower().replace(" ", "_"))
    base_url = f"https://www.spareroom.co.uk/flatshare/{slug}"
    params   = "?flatshare_type=offered"
    if max_budget_inr:
        max_gbp = int(max_budget_inr / FX["GBP"])
        params += f"&max_rent={max_gbp}&per=pcm"

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        search_html = await _fetch(client, base_url + params)
        if not search_html:
            return []

        hrefs = re.findall(r'href="(/flatshare/[a-z_/]+/\d+)"', search_html)
        seen: set = set()
        unique: list = []
        for h in hrefs:
            if h not in seen:
                seen.add(h)
                unique.append(h)

        if not unique:
            return []

        tasks = [
            _spareroom_detail(client, "https://www.spareroom.co.uk" + h)
            for h in unique[:30]
        ]
        results = await asyncio.gather(*tasks)

    listings = []
    for i, item in enumerate(results):
        if item:
            item["id"] = f"sr_{unique[i].split('/')[-1]}"
            listings.append(item)
    return listings


# ═══════════════════════════════════════════════════════════════════════════════
# WG-GESUCHT — Germany only
# ═══════════════════════════════════════════════════════════════════════════════

WGGESUCHT_CITIES: dict = {
    "Munich":     ("Munich",            90,  "EUR", "Germany"),
    "Berlin":     ("Berlin",             8,  "EUR", "Germany"),
    "Hamburg":    ("Hamburg",           55,  "EUR", "Germany"),
    "Frankfurt":  ("Frankfurt-am-Main", 41,  "EUR", "Germany"),
    "Cologne":    ("Cologne",           73,  "EUR", "Germany"),
    "Heidelberg": ("Heidelberg",        61,  "EUR", "Germany"),
    "Stuttgart":  ("Stuttgart",        124,  "EUR", "Germany"),
    "Dusseldorf": ("Duesseldorf",       30,  "EUR", "Germany"),
}


def _extract_wg_items(html: str) -> list:
    items = []
    start = 0
    while True:
        idx = html.find('"RealEstateListing"', start)
        if idx == -1:
            break
        brace_start = html.rfind("{", 0, idx)
        if brace_start == -1:
            start = idx + 1
            continue
        depth = 0
        pos   = brace_start
        while pos < len(html):
            if html[pos] == "{":
                depth += 1
            elif html[pos] == "}":
                depth -= 1
                if depth == 0:
                    items.append(html[brace_start : pos + 1])
                    start = pos + 1
                    break
            pos += 1
        else:
            break
    return items


async def scrape_wggesucht(city: str = "Munich", max_budget_inr: Optional[int] = None) -> list:
    city_data = WGGESUCHT_CITIES.get(city)
    if not city_data:
        return []

    city_name, city_id, currency, country_name = city_data
    url       = f"https://www.wg-gesucht.de/wg-zimmer-in-{city_name}.{city_id}.0.1.0.html"
    max_local = int(max_budget_inr / FX[currency]) if max_budget_inr else None

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        html = await _fetch(client, url)

    if not html:
        return []

    raw_items = _extract_wg_items(html)
    listings  = []

    for i, block in enumerate(raw_items[:30]):
        name_m  = re.search(r'"name":\s*"([^"]+)"', block)
        url_m   = re.search(r'"url":\s*"(https://www\.wg-gesucht\.de/wg-zimmer-in-[^"]+)"', block)
        price_m = re.search(r'"price":\s*"([0-9.]+)"', block)
        img_m   = re.search(r'"image":\s*"(https://img\.wg-gesucht\.de/[^"]+)"', block)

        if not price_m:
            continue

        price = float(price_m.group(1))
        if price < 50 or price > 8000:
            continue
        if max_local and price > max_local:
            continue

        price_int = int(price)
        title     = htmllib.unescape(name_m.group(1)) if name_m else f"WG Room in {city}"

        listings.append({
            "id":          f"wg_{city_id}_{i}",
            "title":       title,
            "area":        city,
            "image_url":   img_m.group(1) if img_m else None,
            "listing_url": url_m.group(1) if url_m else url,
            "price_inr":   int(price * FX[currency]),
            "currency":    currency,
            "price_label": f"€{price_int:,}/mo",
            "bills_inc":   False,
            "source":      "WG-Gesucht",
            "country":     country_name,
            "student_friendly": True,
        })

    return listings


# ═══════════════════════════════════════════════════════════════════════════════
# CRAIGSLIST — Canada & USA
# ═══════════════════════════════════════════════════════════════════════════════

CRAIGSLIST_CA_CITIES = {
    "Toronto":   "toronto",
    "Vancouver": "vancouver",
    "Montreal":  "montreal",
    "Ottawa":    "ottawa",
    "Calgary":   "calgary",
}

CRAIGSLIST_US_CITIES = {
    "New York":      "newyork",
    "Boston":        "boston",
    "Chicago":       "chicago",
    "Los Angeles":   "losangeles",
    "San Francisco": "sfbay",
    "Seattle":       "seattle",
    "Austin":        "austin",
    "Houston":       "houston",
    "Atlanta":       "atlanta",
}


async def _craigslist_posting(
    client: httpx.AsyncClient, url: str, city: str, currency: str = "CAD"
) -> Optional[dict]:
    html = await _fetch(client, url)
    if not html:
        return None

    title   = _og(html, "title")
    desc    = _og(html, "description")
    image   = _og(html, "image")

    price_m = re.search(r"\$([\d,]+)", desc or "")
    if not price_m:
        price_m = re.search(r'<span[^>]*class="[^"]*price[^"]*"[^>]*>\s*\$([\d,]+)', html)
    if not price_m:
        return None

    price_local = int(price_m.group(1).replace(",", ""))
    min_p, max_p = (100, 10000) if currency == "CAD" else (150, 12000)
    if price_local < min_p or price_local > max_p:
        return None

    symbol     = "C$" if currency == "CAD" else "$"
    country    = "Canada" if currency == "CAD" else "United States"
    clean_title = re.sub(r"\s*-\s*rooms?\s*&.*$", "", title, flags=re.IGNORECASE).strip()
    if not clean_title:
        clean_title = f"Room in {city}"

    return {
        "title":       clean_title,
        "area":        city,
        "image_url":   image or None,
        "listing_url": url,
        "price_inr":   int(price_local * FX[currency]),
        "currency":    currency,
        "price_label": f"{symbol}{price_local:,}/mo",
        "bills_inc":   False,
        "source":      "Craigslist",
        "country":     country,
        "student_friendly": True,
    }


async def scrape_craigslist(
    city: str,
    max_budget_inr: Optional[int],
    city_map: dict,
    currency: str,
) -> list:
    subdomain = city_map.get(city, city.lower().replace(" ", ""))
    max_local = int(max_budget_inr / FX[currency]) if max_budget_inr else None
    search_url = f"https://{subdomain}.craigslist.org/search/roo"
    if max_local:
        search_url += f"?max_price={max_local}"

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        html = await _fetch(client, search_url)
        if not html:
            return []

        links = re.findall(
            rf'href="(https://{re.escape(subdomain)}\.craigslist\.org/[^"]+\.html)"',
            html,
        )
        seen: set = set()
        unique: list = []
        for lnk in links:
            if lnk not in seen and "/d/" in lnk:
                seen.add(lnk)
                unique.append(lnk)

        if not unique:
            return []

        tasks = [_craigslist_posting(client, u, city, currency) for u in unique[:30]]
        results = await asyncio.gather(*tasks)

    listings = []
    for i, item in enumerate(results):
        if item:
            if max_local:
                price_local = int(item["price_inr"] / FX[currency])
                if price_local > max_local:
                    continue
            item["id"] = f"cl_{i}"
            listings.append(item)
    return listings


# ═══════════════════════════════════════════════════════════════════════════════
# DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════

COUNTRY_SCRAPERS = {
    "United Kingdom": "spareroom_uk",
    "Germany":        "wggesucht",
    "Canada":         "craigslist_ca",
    "United States":  "craigslist_us",
}

# Countries without direct scrapers but with curated platform guides
SEARCH_LINKS = {
    country: guides[0]["url"] if guides else ""
    for country, guides in PLATFORM_GUIDES.items()
    if country not in COUNTRY_SCRAPERS
}

COUNTRY_DEFAULT_CITY = {
    "United Kingdom": "London",
    "Germany":        "Munich",
    "Canada":         "Toronto",
    "United States":  "New York",
}


async def get_real_listings(
    country: str,
    city: Optional[str] = None,
    max_budget_inr: Optional[int] = None,
) -> dict:
    """
    Returns:
      {
        "listings":       [...],   # live scraping results (may be empty)
        "platform_guides": [...],  # curated platform links (always populated)
        "source":         str,
        "scraped":        bool,
      }
    """
    cache_key = f"{country}|{city}|{max_budget_inr}"
    if cache_key in _CACHE:
        ts, data = _CACHE[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data

    result: dict = {
        "listings":        [],
        "platform_guides": PLATFORM_GUIDES.get(country, []),
        "source":          None,
        "scraped":         False,
    }

    tag = COUNTRY_SCRAPERS.get(country)

    if tag:
        resolved_city = city or COUNTRY_DEFAULT_CITY.get(country, "")
        try:
            if tag == "spareroom_uk":
                listings = await scrape_spareroom_uk(resolved_city, max_budget_inr)
                result["source"] = "SpareRoom"

            elif tag == "wggesucht":
                if resolved_city not in WGGESUCHT_CITIES:
                    resolved_city = "Munich"
                listings = await scrape_wggesucht(resolved_city, max_budget_inr)
                result["source"] = "WG-Gesucht"

            elif tag == "craigslist_ca":
                listings = await scrape_craigslist(
                    resolved_city, max_budget_inr, CRAIGSLIST_CA_CITIES, "CAD"
                )
                result["source"] = "Craigslist"

            elif tag == "craigslist_us":
                listings = await scrape_craigslist(
                    resolved_city, max_budget_inr, CRAIGSLIST_US_CITIES, "USD"
                )
                result["source"] = "Craigslist"

            else:
                listings = []

            result["listings"] = listings
            result["scraped"]  = len(listings) > 0

        except Exception as exc:
            result["error"] = str(exc)

    _CACHE[cache_key] = (time.time(), result)
    return result
