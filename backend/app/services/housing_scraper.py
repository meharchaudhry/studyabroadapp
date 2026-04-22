"""
Real housing listings scraped from live property sites.

UK:      SpareRoom.co.uk  — 2-page fetch, up to 50 listings
Germany: WG-Gesucht.de   — 2-page fetch, up to 50 listings (Germany only)

All other countries return platform_guides — 5-7 curated student-friendly
housing websites per country, including Canada, USA, Spain, Netherlands,
France, Singapore, Australia, Ireland, Japan, Sweden, Denmark, UAE,
New Zealand, South Korea.

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
    "GBP": 107, "EUR": 90,  "CAD": 62, "USD": 83,  "AUD": 55,
    "JPY": 0.56, "SGD": 62, "AED": 22, "NZD": 50,  "KRW": 0.062,
    "SEK": 8,   "DKK": 12,
}

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

# ─────────────────────────────────────────────────────────────────────────────
# PLATFORM GUIDES — curated, exhaustive list per country
# ─────────────────────────────────────────────────────────────────────────────
PLATFORM_GUIDES: dict = {
    # ── United Kingdom ────────────────────────────────────────────────────────
    "United Kingdom": [
        {"name": "SpareRoom", "url": "https://www.spareroom.co.uk/flatshare/london", "logo_domain": "spareroom.co.uk", "desc": "UK's #1 flatshare site — largest selection of student rooms nationwide", "student_friendly": True, "type": "rooms", "logo_color": "#E05A00"},
        {"name": "Rightmove", "url": "https://www.rightmove.co.uk/property-to-rent/search.html?searchType=RENT&includeLetAgreed=false", "logo_domain": "rightmove.co.uk", "desc": "UK's largest property portal — filter by price and property type", "student_friendly": False, "type": "apartments", "logo_color": "#00C853"},
        {"name": "Zoopla", "url": "https://www.zoopla.co.uk/to-rent/property/", "logo_domain": "zoopla.co.uk", "desc": "Property search with price history and Zed-Index data", "student_friendly": False, "type": "apartments", "logo_color": "#8E1575"},
        {"name": "Student.com", "url": "https://www.student.com/uk/london", "logo_domain": "student.com", "desc": "Purpose-built student accommodation (PBSA) across UK cities", "student_friendly": True, "type": "student", "logo_color": "#FF5252"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/London--United-Kingdom/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms from India — no viewing needed", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Uniplaces", "url": "https://www.uniplaces.com/en/accommodation/london", "logo_domain": "uniplaces.com", "desc": "Student-only verified listings near major UK universities", "student_friendly": True, "type": "student", "logo_color": "#1A237E"},
        {"name": "Accommodation for Students", "url": "https://www.accommodationforstudents.com/", "logo_domain": "accommodationforstudents.com", "desc": "Free UK student accommodation listings from private landlords", "student_friendly": True, "type": "rooms", "logo_color": "#0097A7"},
    ],
    # ── Germany ───────────────────────────────────────────────────────────────
    "Germany": [
        {"name": "WG-Gesucht", "url": "https://www.wg-gesucht.de/wg-zimmer-in-Munich.90.0.1.0.html", "logo_domain": "wg-gesucht.de", "desc": "Germany's largest flat-share site — essential for student WG rooms", "student_friendly": True, "type": "rooms", "logo_color": "#00796B"},
        {"name": "ImmoScout24", "url": "https://www.immobilienscout24.de/Suche/de/wohnung-mieten", "logo_domain": "immobilienscout24.de", "desc": "Germany's biggest property portal for apartments and rooms", "student_friendly": False, "type": "apartments", "logo_color": "#E53935"},
        {"name": "Immowelt", "url": "https://www.immowelt.de/suche/wohnungen/mieten", "logo_domain": "immowelt.de", "desc": "Large German rental portal with strong student listings", "student_friendly": False, "type": "apartments", "logo_color": "#1565C0"},
        {"name": "Studenten-WG", "url": "https://www.studenten-wg.de/", "logo_domain": "studenten-wg.de", "desc": "Student-only WG rooms across German university cities", "student_friendly": True, "type": "student", "logo_color": "#7B1FA2"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Munich--Germany/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms before arriving — English support", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Wohnungsbörse", "url": "https://www.wohnungsboerse.net/", "logo_domain": "wohnungsboerse.net", "desc": "Free German rental listings — good for smaller university cities", "student_friendly": False, "type": "apartments", "logo_color": "#FF8F00"},
        {"name": "Nestpick", "url": "https://www.nestpick.com/rooms/berlin/", "logo_domain": "nestpick.com", "desc": "Furnished rooms aggregated from multiple German platforms", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    # ── Canada ────────────────────────────────────────────────────────────────
    "Canada": [
        {"name": "Kijiji Rooms", "url": "https://www.kijiji.ca/b-for-rent/city-of-toronto/room/k0c800l1700273", "logo_domain": "kijiji.ca", "desc": "Canada's top classifieds — far more reliable than Craigslist for rooms", "student_friendly": True, "type": "rooms", "logo_color": "#373278"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Toronto--Canada/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms in Toronto, Vancouver & Montreal before arrival", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Padmapper", "url": "https://www.padmapper.com/apartments/toronto-on", "logo_domain": "padmapper.com", "desc": "Map-based rental search aggregating multiple Canadian sites", "student_friendly": True, "type": "rooms", "logo_color": "#E53935"},
        {"name": "Realtor.ca Rentals", "url": "https://www.realtor.ca/map#LatLng=43.70011,-79.4163&Sort=6-D&TransactionTypeId=3", "logo_domain": "realtor.ca", "desc": "Official MLS rental listings — verified and agent-managed", "student_friendly": False, "type": "apartments", "logo_color": "#CC0000"},
        {"name": "RentSeeker", "url": "https://www.rentseeker.ca/", "logo_domain": "rentseeker.ca", "desc": "Canadian apartment search with student-friendly filter", "student_friendly": True, "type": "apartments", "logo_color": "#1565C0"},
        {"name": "Facebook Marketplace", "url": "https://www.facebook.com/marketplace/category/rentals", "logo_domain": "facebook.com", "desc": "Private rooms via Facebook — join your university housing group", "student_friendly": True, "type": "rooms", "logo_color": "#1877F2"},
        {"name": "Nestpick", "url": "https://www.nestpick.com/rooms/toronto/", "logo_domain": "nestpick.com", "desc": "Furnished rooms in Toronto and Vancouver with flexible leases", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    # ── United States ─────────────────────────────────────────────────────────
    "United States": [
        {"name": "Zillow Rentals", "url": "https://www.zillow.com/homes/for_rent/", "logo_domain": "zillow.com", "desc": "USA's largest rental platform — filter by studio for student budget", "student_friendly": False, "type": "apartments", "logo_color": "#006AFF"},
        {"name": "Apartments.com", "url": "https://www.apartments.com/rooms/", "logo_domain": "apartments.com", "desc": "Dedicated rooms & roommates section with verified listings", "student_friendly": True, "type": "rooms", "logo_color": "#E53935"},
        {"name": "Padmapper", "url": "https://www.padmapper.com/", "logo_domain": "padmapper.com", "desc": "Map-based apartment & room search across all major US cities", "student_friendly": True, "type": "rooms", "logo_color": "#D32F2F"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/United-States/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near US universities — book online from India", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Roomies.com", "url": "https://www.roomies.com/", "logo_domain": "roomies.com", "desc": "Student and young-professional roommate matching platform", "student_friendly": True, "type": "rooms", "logo_color": "#9C27B0"},
        {"name": "Facebook Marketplace", "url": "https://www.facebook.com/marketplace/category/rentals", "logo_domain": "facebook.com", "desc": "Private room listings — check your university's Facebook housing group", "student_friendly": True, "type": "rooms", "logo_color": "#1877F2"},
        {"name": "Student.com USA", "url": "https://www.student.com/us/new-york", "logo_domain": "student.com", "desc": "Purpose-built student accommodation near top US universities", "student_friendly": True, "type": "student", "logo_color": "#FF5252"},
    ],
    # ── Netherlands ───────────────────────────────────────────────────────────
    "Netherlands": [
        {"name": "Kamernet", "url": "https://kamernet.nl/en/for-rent/rooms-amsterdam", "logo_domain": "kamernet.nl", "desc": "Largest Dutch student room marketplace with verified listings", "student_friendly": True, "type": "rooms", "logo_color": "#4CAF50"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Amsterdam--Netherlands/rooms", "logo_domain": "housinganywhere.com", "desc": "International platform popular with TU Delft & UvA students", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Pararius", "url": "https://www.pararius.com/rooms/amsterdam", "logo_domain": "pararius.com", "desc": "Dutch rental platform — free for tenants, English support", "student_friendly": False, "type": "apartments", "logo_color": "#0066CC"},
        {"name": "Funda", "url": "https://www.funda.nl/huur/amsterdam/kamer/", "logo_domain": "funda.nl", "desc": "Netherlands' largest property portal for rooms and apartments", "student_friendly": False, "type": "apartments", "logo_color": "#E84E10"},
        {"name": "Nestpick", "url": "https://www.nestpick.com/rooms/amsterdam/", "logo_domain": "nestpick.com", "desc": "Aggregates furnished rooms from multiple Dutch platforms", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
        {"name": "Student.com NL", "url": "https://www.student.com/nl/amsterdam", "logo_domain": "student.com", "desc": "Purpose-built student accommodation near Dutch universities", "student_friendly": True, "type": "student", "logo_color": "#FF5252"},
    ],
    # ── France ────────────────────────────────────────────────────────────────
    "France": [
        {"name": "Immojeune", "url": "https://www.immojeune.com/location-etudiant/paris-75.html", "logo_domain": "immojeune.com", "desc": "Student housing specialist in France — rooms, studios & colocs", "student_friendly": True, "type": "student", "logo_color": "#E91E63"},
        {"name": "La Carte des Colocs", "url": "https://www.lacartedescolocs.fr/colocations/paris", "logo_domain": "lacartedescolocs.fr", "desc": "French flatshare platform — most popular among international students", "student_friendly": True, "type": "rooms", "logo_color": "#FF5722"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Paris--France/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms from India before you arrive", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Studapart", "url": "https://www.studapart.com/en/p/paris", "logo_domain": "studapart.com", "desc": "100% student-focused, accepts international tenants easily", "student_friendly": True, "type": "student", "logo_color": "#673AB7"},
        {"name": "SeLoger", "url": "https://www.seloger.com/list.htm?types=3,1&idtypebien=8,7&projects=1", "logo_domain": "seloger.com", "desc": "Major French real estate portal with thousands of listings", "student_friendly": False, "type": "apartments", "logo_color": "#0051A5"},
        {"name": "PAP.fr", "url": "https://www.pap.fr/annonce/locations-chambre-etudiant-studio-paris-75-g439", "logo_domain": "pap.fr", "desc": "Owner-direct listings — no agency fees, good for students", "student_friendly": True, "type": "rooms", "logo_color": "#E53935"},
    ],
    # ── Singapore ─────────────────────────────────────────────────────────────
    "Singapore": [
        {"name": "PropertyGuru", "url": "https://www.propertyguru.com.sg/property-for-rent/rooms-for-rent-in-singapore", "logo_domain": "propertyguru.com.sg", "desc": "Singapore's top property portal with hundreds of room listings", "student_friendly": False, "type": "rooms", "logo_color": "#00AA55"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Singapore/rooms", "logo_domain": "housinganywhere.com", "desc": "Trusted by NUS & NTU international students", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Roomgo Singapore", "url": "https://sg.roomgo.net/rooms-for-rent/", "logo_domain": "roomgo.net", "desc": "Room rentals popular with expats and international students", "student_friendly": True, "type": "rooms", "logo_color": "#9C27B0"},
        {"name": "SRX Property", "url": "https://www.srx.com.sg/rent/rooms", "logo_domain": "srx.com.sg", "desc": "Singapore rental marketplace with verified listings", "student_friendly": False, "type": "apartments", "logo_color": "#FF3D00"},
        {"name": "Nestpick", "url": "https://www.nestpick.com/rooms/singapore/", "logo_domain": "nestpick.com", "desc": "Furnished rooms with flexible tenancy for international students", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
        {"name": "99.co", "url": "https://www.99.co/singapore/rent/rooms", "logo_domain": "99.co", "desc": "Singapore property portal with strong room & HDB listings", "student_friendly": False, "type": "rooms", "logo_color": "#FF6600"},
    ],
    # ── Australia ─────────────────────────────────────────────────────────────
    "Australia": [
        {"name": "Flatmates.com.au", "url": "https://flatmates.com.au/rooms", "logo_domain": "flatmates.com.au", "desc": "Australia's #1 flatmate finder — 170k+ listings nationwide", "student_friendly": True, "type": "rooms", "logo_color": "#00BCD4"},
        {"name": "Student.com AU", "url": "https://www.student.com/au/sydney", "logo_domain": "student.com", "desc": "Purpose-built student accommodation with on-campus feel", "student_friendly": True, "type": "student", "logo_color": "#FF5252"},
        {"name": "Domain", "url": "https://www.domain.com.au/rent/sydney-region-nsw/", "logo_domain": "domain.com.au", "desc": "Major Australian real estate portal with student-friendly filters", "student_friendly": False, "type": "apartments", "logo_color": "#00897B"},
        {"name": "Gumtree Rooms", "url": "https://www.gumtree.com.au/s-flatshare-houseshare/sydney/k0c18663l3003690", "logo_domain": "gumtree.com.au", "desc": "Classifieds with affordable student room listings", "student_friendly": True, "type": "rooms", "logo_color": "#72BB2F"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Sydney--Australia/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished accommodation from India before arriving", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "UniLodge", "url": "https://www.unilodge.com.au/", "logo_domain": "unilodge.com.au", "desc": "Official student accommodation near Australian universities", "student_friendly": True, "type": "student", "logo_color": "#1565C0"},
        {"name": "Realestate.com.au", "url": "https://www.realestate.com.au/rent/", "logo_domain": "realestate.com.au", "desc": "Australia's largest real estate platform for all rental types", "student_friendly": False, "type": "apartments", "logo_color": "#E53935"},
    ],
    # ── Ireland ───────────────────────────────────────────────────────────────
    "Ireland": [
        {"name": "Daft.ie", "url": "https://www.daft.ie/dublin/rooms-to-rent", "logo_domain": "daft.ie", "desc": "Ireland's largest property portal — essential for Dublin rooms", "student_friendly": True, "type": "rooms", "logo_color": "#00AA66"},
        {"name": "Rent.ie", "url": "https://www.rent.ie/rooms-to-rent/dublin/", "logo_domain": "rent.ie", "desc": "Irish rental site with rooms popular among students", "student_friendly": True, "type": "rooms", "logo_color": "#1565C0"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Dublin--Ireland/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms for Trinity, UCD & DCU in advance", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "UniAcco", "url": "https://uniacco.com/ireland", "logo_domain": "uniacco.com", "desc": "Purpose-built student accommodation across Irish university cities", "student_friendly": True, "type": "student", "logo_color": "#7B1FA2"},
        {"name": "MyHome.ie", "url": "https://www.myhome.ie/residential/search?tenure=3", "logo_domain": "myhome.ie", "desc": "Irish property portal with rooms & sharing options nationwide", "student_friendly": False, "type": "apartments", "logo_color": "#E53935"},
        {"name": "Spotahome Ireland", "url": "https://www.spotahome.com/en/rent/dublin/rooms", "logo_domain": "spotahome.com", "desc": "Video-verified listings — book remotely from India safely", "student_friendly": True, "type": "rooms", "logo_color": "#00C4A7"},
    ],
    # ── Japan ─────────────────────────────────────────────────────────────────
    "Japan": [
        {"name": "Sakura House", "url": "https://www.sakura-house.com/en/type/share-house", "logo_domain": "sakura-house.com", "desc": "Share houses for foreigners — no guarantor needed, English OK", "student_friendly": True, "type": "rooms", "logo_color": "#E91E63"},
        {"name": "GaijinPot Housing", "url": "https://housing.gaijinpot.com/en/rent/", "logo_domain": "gaijinpot.com", "desc": "English-language listings for foreigners in Tokyo & Osaka", "student_friendly": True, "type": "apartments", "logo_color": "#FF5722"},
        {"name": "Leopalace21", "url": "https://www.leopalace21.com/english/", "logo_domain": "leopalace21.com", "desc": "Short-term furnished apartments popular with international students", "student_friendly": True, "type": "apartments", "logo_color": "#3F51B5"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Tokyo--Japan/rooms", "logo_domain": "housinganywhere.com", "desc": "Book from India before visa approval — English support", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Borderless House", "url": "https://www.borderless-house.com/en/japan/", "logo_domain": "borderless-house.com", "desc": "International share houses in Tokyo & Osaka — community focused", "student_friendly": True, "type": "rooms", "logo_color": "#009688"},
        {"name": "Suumo (英語)", "url": "https://suumo.jp/chintai/", "logo_domain": "suumo.jp", "desc": "Japan's largest property site — use with Google Translate", "student_friendly": False, "type": "apartments", "logo_color": "#0D47A1"},
    ],
    # ── Sweden ────────────────────────────────────────────────────────────────
    "Sweden": [
        {"name": "Blocket Bostad", "url": "https://bostad.blocket.se/en/stockholms-lan/hyra/lagenhet", "logo_domain": "blocket.se", "desc": "Sweden's largest online marketplace — rooms and apartments", "student_friendly": False, "type": "apartments", "logo_color": "#FF3D00"},
        {"name": "Samtrygg", "url": "https://www.samtrygg.se/en", "logo_domain": "samtrygg.se", "desc": "Safe subletting platform popular with students in Stockholm", "student_friendly": True, "type": "rooms", "logo_color": "#00BCD4"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Stockholm--Sweden/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near KTH, Chalmers & Stockholm University", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "AF Bostäder", "url": "https://www.afbostader.se/en/", "logo_domain": "afbostader.se", "desc": "Student union housing in Lund — apply on day 1 of admission", "student_friendly": True, "type": "student", "logo_color": "#3F51B5"},
        {"name": "SSSB", "url": "https://www.sssb.se/en/", "logo_domain": "sssb.se", "desc": "Official Stockholm student housing — register immediately on admission", "student_friendly": True, "type": "student", "logo_color": "#4CAF50"},
        {"name": "Hyresrätter", "url": "https://www.hyresratter.se/", "logo_domain": "hyresratter.se", "desc": "Swedish rental listings aggregator with English options", "student_friendly": False, "type": "apartments", "logo_color": "#FF8F00"},
    ],
    # ── Denmark ───────────────────────────────────────────────────────────────
    "Denmark": [
        {"name": "BoligPortal", "url": "https://www.boligportal.dk/en/rentals/", "logo_domain": "boligportal.dk", "desc": "Denmark's most popular rental portal — rooms and apartments", "student_friendly": False, "type": "apartments", "logo_color": "#E53935"},
        {"name": "Findroommate.dk", "url": "https://www.findroommate.dk/", "logo_domain": "findroommate.dk", "desc": "Flatshare and room rentals in Copenhagen — student crowd", "student_friendly": True, "type": "rooms", "logo_color": "#1E88E5"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Copenhagen--Denmark/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near DTU & Copenhagen Business School", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Lejebolig.dk", "url": "https://www.lejebolig.dk/en/", "logo_domain": "lejebolig.dk", "desc": "Danish rental site with English interface for internationals", "student_friendly": False, "type": "apartments", "logo_color": "#00897B"},
        {"name": "Ungdomsboliger", "url": "https://www.ungdomsboliger.dk/", "logo_domain": "ungdomsboliger.dk", "desc": "Official Danish youth & student housing — subsidised options", "student_friendly": True, "type": "student", "logo_color": "#7B1FA2"},
        {"name": "Nestpick CPH", "url": "https://www.nestpick.com/rooms/copenhagen/", "logo_domain": "nestpick.com", "desc": "Furnished Copenhagen rooms with flexible short-term leases", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    # ── UAE ───────────────────────────────────────────────────────────────────
    "United Arab Emirates": [
        {"name": "Dubizzle", "url": "https://dubai.dubizzle.com/property-for-rent/rooms/", "logo_domain": "dubizzle.com", "desc": "UAE's largest classifieds with many room & shared flat listings", "student_friendly": True, "type": "rooms", "logo_color": "#FF6F00"},
        {"name": "Property Finder", "url": "https://www.propertyfinder.ae/en/search?category=1&price_max=3000", "logo_domain": "propertyfinder.ae", "desc": "Major UAE property portal — filter for studio/room types", "student_friendly": False, "type": "apartments", "logo_color": "#D32F2F"},
        {"name": "Bayut", "url": "https://www.bayut.com/to-rent/residential/dubai/rooms/", "logo_domain": "bayut.com", "desc": "Leading Dubai real estate site with verified listings", "student_friendly": False, "type": "apartments", "logo_color": "#1565C0"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Dubai--United-Arab-Emirates/rooms", "logo_domain": "housinganywhere.com", "desc": "International furnished rooms near UAEU & HBMeU campuses", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Nestpick Dubai", "url": "https://www.nestpick.com/rooms/dubai/", "logo_domain": "nestpick.com", "desc": "Furnished rooms with flexible leases for international students", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    # ── New Zealand ───────────────────────────────────────────────────────────
    "New Zealand": [
        {"name": "TradeMe Property", "url": "https://www.trademe.co.nz/property/flatmates-wanted/", "logo_domain": "trademe.co.nz", "desc": "New Zealand's biggest marketplace — best for flatmate ads", "student_friendly": True, "type": "rooms", "logo_color": "#FF6600"},
        {"name": "Flatmates NZ", "url": "https://www.flatmates.co.nz/rooms-for-rent/auckland", "logo_domain": "flatmates.co.nz", "desc": "NZ-specific flatshare site popular with international students", "student_friendly": True, "type": "rooms", "logo_color": "#00BCD4"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Auckland--New-Zealand/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near University of Auckland & AUT", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Realestate.co.nz", "url": "https://www.realestate.co.nz/rental/search?district=auckland-city", "logo_domain": "realestate.co.nz", "desc": "Major NZ real estate portal for apartments and rooms", "student_friendly": False, "type": "apartments", "logo_color": "#2E7D32"},
        {"name": "OneRoof", "url": "https://www.oneroof.co.nz/find-property/rent", "logo_domain": "oneroof.co.nz", "desc": "NZ property portal with suburb-level pricing data", "student_friendly": False, "type": "apartments", "logo_color": "#0D47A1"},
    ],
    # ── South Korea ───────────────────────────────────────────────────────────
    "South Korea": [
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Seoul--South-Korea/rooms", "logo_domain": "housinganywhere.com", "desc": "English-language furnished rooms near Seoul universities", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "GaijinPot Housing", "url": "https://housing.gaijinpot.com/en/rent/korea/", "logo_domain": "gaijinpot.com", "desc": "English listings for foreigners in Korea including goshiwons", "student_friendly": True, "type": "rooms", "logo_color": "#FF5722"},
        {"name": "Zigbang", "url": "https://www.zigbang.com/", "logo_domain": "zigbang.com", "desc": "Major Korean real estate app — use with Google Translate", "student_friendly": False, "type": "apartments", "logo_color": "#5C6BC0"},
        {"name": "Dabang", "url": "https://www.dabangapp.com/", "logo_domain": "dabangapp.com", "desc": "Korean room finder app — popular for officetel & studio search", "student_friendly": False, "type": "apartments", "logo_color": "#FF4081"},
        {"name": "Nestpick Seoul", "url": "https://www.nestpick.com/rooms/seoul/", "logo_domain": "nestpick.com", "desc": "Furnished rooms near Yonsei, SNU & KAIST with English support", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    # ── Spain ─────────────────────────────────────────────────────────────────
    "Spain": [
        {"name": "Idealista", "url": "https://www.idealista.com/en/alquiler-habitaciones-particulares/", "logo_domain": "idealista.com", "desc": "Spain's largest real estate portal — rooms, studios, flatshares", "student_friendly": False, "type": "rooms", "logo_color": "#0066FF"},
        {"name": "Badi", "url": "https://badi.com/en/rooms-for-rent/madrid/", "logo_domain": "badi.com", "desc": "Tech-first room rental platform popular with students & young people", "student_friendly": True, "type": "rooms", "logo_color": "#FF4C6A"},
        {"name": "Spotahome", "url": "https://www.spotahome.com/es/alquiler/madrid/habitaciones", "logo_domain": "spotahome.com", "desc": "Video-verified listings — great for booking from India remotely", "student_friendly": True, "type": "rooms", "logo_color": "#00C4A7"},
        {"name": "Erasmusu", "url": "https://erasmusu.com/en/erasmus-madrid/student-housing", "logo_domain": "erasmusu.com", "desc": "Student housing designed for Erasmus & international students", "student_friendly": True, "type": "student", "logo_color": "#FF6B35"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Madrid--Spain/rooms", "logo_domain": "housinganywhere.com", "desc": "Book furnished rooms before arriving — popular near IE & Carlos III", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Fotocasa", "url": "https://www.fotocasa.es/es/alquiler/habitaciones/madrid/todas-las-zonas/l", "logo_domain": "fotocasa.es", "desc": "Major Spanish property site with room & apartment listings", "student_friendly": False, "type": "rooms", "logo_color": "#E91E63"},
        {"name": "Pisos.com", "url": "https://www.pisos.com/alquiler/habitaciones-madrid/", "logo_domain": "pisos.com", "desc": "Spanish rental portal with strong room listings in university cities", "student_friendly": False, "type": "rooms", "logo_color": "#FF5722"},
    ],
    # ── Norway ────────────────────────────────────────────────────────────────
    "Norway": [
        {"name": "Finn.no Bolig", "url": "https://www.finn.no/realestate/lettings/search.html?property_type=3", "logo_domain": "finn.no", "desc": "Norway's biggest classifieds — most Oslo rooms advertised here", "student_friendly": False, "type": "rooms", "logo_color": "#E53935"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Oslo--Norway/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms near UiO & BI Norwegian Business School", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "SiO Bolig", "url": "https://www.sio.no/en/housing", "logo_domain": "sio.no", "desc": "Official Oslo student housing — subsidised, apply immediately on admission", "student_friendly": True, "type": "student", "logo_color": "#1565C0"},
        {"name": "Hybel.no", "url": "https://www.hybel.no/", "logo_domain": "hybel.no", "desc": "Norway's largest room rental platform for students and young people", "student_friendly": True, "type": "rooms", "logo_color": "#00897B"},
        {"name": "Nestpick Oslo", "url": "https://www.nestpick.com/rooms/oslo/", "logo_domain": "nestpick.com", "desc": "Furnished rooms in Oslo with flexible lease options", "student_friendly": True, "type": "rooms", "logo_color": "#2196F3"},
    ],
    # ── Italy ─────────────────────────────────────────────────────────────────
    "Italy": [
        {"name": "Immobiliare.it", "url": "https://www.immobiliare.it/affitto-case/roma/?idContratto=1&idCategoria=1", "logo_domain": "immobiliare.it", "desc": "Italy's largest property portal with rooms and apartments in all cities", "student_friendly": False, "type": "apartments", "logo_color": "#E53935"},
        {"name": "Erasmusu Italy", "url": "https://erasmusu.com/en/erasmus-rome/student-housing", "logo_domain": "erasmusu.com", "desc": "Student housing designed for Erasmus & international students in Italy", "student_friendly": True, "type": "student", "logo_color": "#FF6B35"},
        {"name": "HousingAnywhere", "url": "https://housinganywhere.com/Rome--Italy/rooms", "logo_domain": "housinganywhere.com", "desc": "Furnished rooms in Rome, Milan & Bologna — book from India", "student_friendly": True, "type": "rooms", "logo_color": "#FF6B35"},
        {"name": "Spotahome Italy", "url": "https://www.spotahome.com/en/rent/milan/rooms", "logo_domain": "spotahome.com", "desc": "Video-verified rooms — ideal for booking without viewing in person", "student_friendly": True, "type": "rooms", "logo_color": "#00C4A7"},
        {"name": "Subito.it", "url": "https://www.subito.it/annunci-italia/affitto/camere-posti-letto/", "logo_domain": "subito.it", "desc": "Italian classifieds — affordable private-landlord rooms nationwide", "student_friendly": True, "type": "rooms", "logo_color": "#FF6600"},
        {"name": "Uniplaces Italy", "url": "https://www.uniplaces.com/en/accommodation/milan", "logo_domain": "uniplaces.com", "desc": "Verified student listings in Milan, Rome, Turin & Bologna", "student_friendly": True, "type": "student", "logo_color": "#1A237E"},
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
# SPAREROOM UK  —  2-page fetch, up to 50 listings
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
    bills = bool(re.search(r"inc\w*\s*bills|bills\s*inc\w*|bills\s*included", description, re.IGNORECASE))
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
        max_gbp  = int(max_budget_inr / FX["GBP"])
        params  += f"&max_rent={max_gbp}&per=pcm"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # Fetch pages 1 and 2 concurrently to get ~50 listings
        p1_html, p2_html = await asyncio.gather(
            _fetch(client, base_url + params),
            _fetch(client, base_url + params + "&page=2"),
        )
        seen:   set  = set()
        unique: list = []
        for html in (p1_html, p2_html):
            for h in re.findall(r'href="(/flatshare/[a-z_/]+/\d+)"', html):
                if h not in seen:
                    seen.add(h)
                    unique.append(h)

        if not unique:
            return []

        tasks   = [_spareroom_detail(client, "https://www.spareroom.co.uk" + h) for h in unique[:50]]
        results = await asyncio.gather(*tasks)

    listings = []
    for i, item in enumerate(results):
        if item:
            item["id"] = f"sr_{unique[i].split('/')[-1]}"
            listings.append(item)
    return listings


# ═══════════════════════════════════════════════════════════════════════════════
# WG-GESUCHT  —  Germany only, 2-page fetch, up to 50 listings
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
    base_url  = f"https://www.wg-gesucht.de/wg-zimmer-in-{city_name}.{city_id}.0.1"
    max_local = int(max_budget_inr / FX[currency]) if max_budget_inr else None

    async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
        # WG-Gesucht page index: .0.html = page 1, .1.html = page 2
        p1_html, p2_html = await asyncio.gather(
            _fetch(client, base_url + ".0.html"),
            _fetch(client, base_url + ".1.html"),
        )

    # Extract + deduplicate by listing URL
    seen_urls: set  = set()
    raw_items: list = []
    for html in (p1_html, p2_html):
        for block in _extract_wg_items(html):
            url_m = re.search(r'"url":\s*"(https://www\.wg-gesucht\.de/wg-zimmer-in-[^"]+)"', block)
            key   = url_m.group(1) if url_m else None
            if key and key in seen_urls:
                continue
            if key:
                seen_urls.add(key)
            raw_items.append(block)

    listings = []
    for i, block in enumerate(raw_items[:50]):
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
            "listing_url": url_m.group(1) if url_m else base_url + ".0.html",
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
# DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════

COUNTRY_SCRAPERS = {
    "United Kingdom": "spareroom_uk",
    "Germany":        "wggesucht",
}

COUNTRY_DEFAULT_CITY = {
    "United Kingdom": "London",
    "Germany":        "Munich",
}


async def get_real_listings(
    country: str,
    city: Optional[str] = None,
    max_budget_inr: Optional[int] = None,
) -> dict:
    """
    Returns:
      {
        "listings":        [...],   # live scraping results (UK / Germany only)
        "platform_guides": [...],   # curated platform links for every country
        "source":          str,
        "scraped":         bool,
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
            else:
                listings = []

            result["listings"] = listings
            result["scraped"]  = len(listings) > 0

        except Exception as exc:
            result["error"] = str(exc)

    _CACHE[cache_key] = (time.time(), result)
    return result
