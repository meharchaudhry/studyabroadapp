"""
Jobs Service — Multi-source live fetching
==========================================
Sources (all free, no auth required):

  Arbeitnow   arbeitnow.com/api/job-board-api        EU jobs, 100/call
  Remotive    remotive.com/api/remote-jobs            Remote worldwide, searchable
  RemoteOK    remoteok.com/api                        Remote + salary ranges
  The Muse    themuse.com/api/public/jobs             497 k jobs, location-filtered

Routing strategy:
  EU cities       → Arbeitnow (post-filtered) + Remotive + RemoteOK
  US / CA cities  → Muse (location filter) + Remotive + RemoteOK
  APAC / other    → Remotive + RemoteOK + Muse (Flexible/Remote)

All results normalised to a single schema.  In-memory cache (30 min).
"""

import asyncio
import logging
import re
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── In-memory cache ───────────────────────────────────────────────────────────
_CACHE: dict = {}
CACHE_TTL = 1800  # 30 minutes

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html;q=0.9",
}


# ── Location routing tables ───────────────────────────────────────────────────

# Cities that Arbeitnow covers well (EU-only board)
# Value = list of strings to match inside Arbeitnow location field
ARBEITNOW_FILTER: dict = {
    "London":      ["london", "uk", "england", "united kingdom"],
    "Edinburgh":   ["edinburgh", "scotland", "uk", "united kingdom"],
    "Manchester":  ["manchester", "uk", "england", "united kingdom"],
    "Dublin":      ["dublin", "ireland"],
    "Berlin":      ["berlin", "germany", "deutschland"],
    "Munich":      ["munich", "münchen", "germany", "deutschland"],
    "Hamburg":     ["hamburg", "germany", "deutschland"],
    "Frankfurt":   ["frankfurt", "germany", "deutschland"],
    "Cologne":     ["cologne", "köln", "germany", "deutschland"],
    "Amsterdam":   ["amsterdam", "netherlands", "nederland"],
    "Rotterdam":   ["rotterdam", "netherlands"],
    "Paris":       ["paris", "france"],
    "Lyon":        ["lyon", "france"],
    "Zurich":      ["zurich", "zürich", "switzerland", "schweiz"],
    "Vienna":      ["vienna", "wien", "austria"],
}

# The Muse location strings (URL-encoded format used in their API)
MUSE_LOCATIONS: dict = {
    "London":        "London, England, United Kingdom",
    "Edinburgh":     "Edinburgh, Scotland, United Kingdom",
    "Manchester":    "Manchester, England, United Kingdom",
    "Dublin":        "Dublin, Ireland",
    "New York":      "New York City, New York, United States",
    "Boston":        "Boston, Massachusetts, United States",
    "Chicago":       "Chicago, Illinois, United States",
    "Los Angeles":   "Los Angeles, California, United States",
    "San Francisco": "San Francisco, California, United States",
    "Toronto":       "Toronto, Ontario, Canada",
    "Vancouver":     "Vancouver, British Columbia, Canada",
    "Montreal":      "Montreal, Quebec, Canada",
    "Sydney":        "Sydney, New South Wales, Australia",
    "Melbourne":     "Melbourne, Victoria, Australia",
    "Singapore":     "Singapore",
    "Berlin":        "Berlin, Germany",
    "Munich":        "Munich, Bavaria, Germany",
    "Amsterdam":     "Amsterdam, Netherlands",
    "Paris":         "Paris, France",
    "Tokyo":         "Tokyo, Japan",
    "Dubai":         "Dubai, United Arab Emirates",
    "Zurich":        "Zurich, Switzerland",
}

# FX rates for rough INR salary display
FX_TO_INR = {
    "USD": 83, "GBP": 107, "EUR": 90, "CAD": 62,
    "AUD": 55, "SGD": 62, "JPY": 0.56, "AED": 23,
    "CHF": 93, "SEK": 8,
}

# City → currency (for salary estimates)
CITY_CURRENCY: dict = {
    "London": "GBP", "Edinburgh": "GBP", "Manchester": "GBP",
    "Dublin": "EUR", "Berlin": "EUR", "Munich": "EUR", "Hamburg": "EUR",
    "Frankfurt": "EUR", "Cologne": "EUR", "Amsterdam": "EUR",
    "Rotterdam": "EUR", "Paris": "EUR", "Lyon": "EUR",
    "Zurich": "CHF", "Vienna": "EUR",
    "New York": "USD", "Boston": "USD", "Chicago": "USD",
    "Los Angeles": "USD", "San Francisco": "USD",
    "Toronto": "CAD", "Vancouver": "CAD", "Montreal": "CAD",
    "Sydney": "AUD", "Melbourne": "AUD",
    "Singapore": "SGD",
    "Tokyo": "JPY",
    "Dubai": "AED",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _infer_type(title: str, contract: str = "") -> str:
    t = (title + " " + contract).lower()
    if any(w in t for w in ["remote", "fully remote", "work from home", "wfh"]):
        return "remote"
    if any(w in t for w in ["intern", "internship", "placement", "trainee"]):
        return "internship"
    if any(w in t for w in ["part-time", "part time", "parttime"]):
        return "part-time"
    if any(w in t for w in ["graduate", "grad ", "entry level", "entry-level", "junior", "fresh"]):
        return "graduate"
    return "full-time"


def _fmt_salary(min_s, max_s, currency="USD") -> str:
    if not min_s and not max_s:
        return ""
    sym = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "C$",
           "AUD": "A$", "SGD": "S$", "CHF": "CHF "}.get(currency, "$")
    if min_s and max_s:
        return f"{sym}{int(min_s):,}–{sym}{int(max_s):,}/yr"
    if min_s:
        return f"{sym}{int(min_s):,}+/yr"
    if max_s:
        return f"up to {sym}{int(max_s):,}/yr"
    return ""


async def _get(client: httpx.AsyncClient, url: str, **kwargs) -> dict | list | None:
    try:
        r = await client.get(url, headers=HEADERS, timeout=12,
                             follow_redirects=True, **kwargs)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.debug(f"GET {url} failed: {e}")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE: Arbeitnow
# Primarily DACH + EU tech jobs. Returns 100 results per call; we post-filter
# by location keywords when a European city is requested.
# ═══════════════════════════════════════════════════════════════════════════════

async def _fetch_arbeitnow(
    client: httpx.AsyncClient,
    location: str,
    keywords: str,
) -> list:
    params: dict = {}
    if keywords:
        params["search"] = keywords

    data = await _get(client, "https://arbeitnow.com/api/job-board-api", params=params)
    if not data:
        return []

    raw = data.get("data", [])

    # If we have a known EU city, filter by location keywords
    filter_terms = ARBEITNOW_FILTER.get(location, [])
    if filter_terms:
        raw = [
            j for j in raw
            if any(t in (j.get("location") or "").lower() for t in filter_terms)
            or j.get("remote", False)
        ]
    # For non-EU cities, take remote-only results
    elif location not in ARBEITNOW_FILTER:
        raw = [j for j in raw if j.get("remote", False)]

    results = []
    for j in raw[:20]:
        results.append({
            "id":          j.get("slug", ""),
            "title":       j.get("title", ""),
            "company":     j.get("company_name", ""),
            "location":    j.get("location", "Remote") or "Remote",
            "salary":      "",
            "job_type":    _infer_type(j.get("title", ""), " ".join(j.get("job_types", []))),
            "tags":        j.get("tags", [])[:5],
            "remote":      j.get("remote", False),
            "source":      "Arbeitnow",
            "apply_url":   j.get("url", ""),
            "posted":      str(j.get("created_at", "")),
            "description": _strip_html(j.get("description", ""))[:280],
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE: Remotive
# Free remote jobs API. Searchable by keyword and category. ~20 results/call.
# ═══════════════════════════════════════════════════════════════════════════════

async def _fetch_remotive(
    client: httpx.AsyncClient,
    keywords: str,
) -> list:
    params: dict = {"limit": 20}
    if keywords:
        params["search"] = keywords

    data = await _get(client, "https://remotive.com/api/remote-jobs", params=params)
    if not data:
        return []

    results = []
    for j in data.get("jobs", [])[:20]:
        results.append({
            "id":          str(j.get("id", "")),
            "title":       j.get("title", ""),
            "company":     j.get("company_name", ""),
            "location":    "Remote — " + (j.get("candidate_required_location") or "Worldwide"),
            "salary":      j.get("salary") or "",
            "job_type":    "remote",
            "tags":        (j.get("tags") or [])[:5],
            "remote":      True,
            "source":      "Remotive",
            "apply_url":   j.get("url", ""),
            "posted":      j.get("publication_date", ""),
            "description": _strip_html(j.get("description", ""))[:280],
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE: RemoteOK
# Free remote jobs with salary_min / salary_max. ~96 results.
# ═══════════════════════════════════════════════════════════════════════════════

async def _fetch_remoteok(
    client: httpx.AsyncClient,
    keywords: str,
) -> list:
    data = await _get(client, "https://remoteok.com/api")
    if not data or not isinstance(data, list):
        return []

    raw = [x for x in data if isinstance(x, dict) and x.get("position")]

    # Keyword filter
    if keywords:
        kw = keywords.lower()
        raw = [
            j for j in raw
            if kw in (j.get("position") or "").lower()
            or any(kw in t.lower() for t in (j.get("tags") or []))
            or kw in (j.get("description") or "").lower()[:200]
        ]

    results = []
    for j in raw[:20]:
        sal = _fmt_salary(j.get("salary_min"), j.get("salary_max"), "USD")
        results.append({
            "id":          str(j.get("id", "")),
            "title":       j.get("position", ""),
            "company":     j.get("company", ""),
            "location":    j.get("location") or "Remote",
            "salary":      sal,
            "job_type":    _infer_type(j.get("position", "")),
            "tags":        (j.get("tags") or [])[:5],
            "remote":      True,
            "source":      "RemoteOK",
            "apply_url":   j.get("apply_url") or j.get("url", ""),
            "posted":      j.get("date", ""),
            "description": _strip_html(j.get("description", ""))[:280],
            "logo_url":    j.get("company_logo") or j.get("logo"),
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE: The Muse
# 497 k jobs with location filter. Great for US, UK, Canada.
# ═══════════════════════════════════════════════════════════════════════════════

async def _fetch_muse(
    client: httpx.AsyncClient,
    location: str,
    keywords: str,
    job_type: str,
) -> list:
    muse_loc = MUSE_LOCATIONS.get(location)

    params: dict = {"page": 0}
    if muse_loc:
        params["location"] = muse_loc
    if job_type == "internship":
        params["level"] = "internship"
    elif job_type == "graduate":
        params["level"] = "entry"

    data = await _get(client, "https://www.themuse.com/api/public/jobs", params=params)
    if not data:
        return []

    results = []
    for j in data.get("results", [])[:20]:
        locs = j.get("locations", [])
        loc_str = ", ".join(l.get("name", "") for l in locs) or location
        company = j.get("company", {})
        refs    = j.get("refs", {})
        levels  = j.get("levels", [])
        level_name = levels[0].get("name", "") if levels else ""

        results.append({
            "id":          str(j.get("id", "")),
            "title":       j.get("name", ""),
            "company":     company.get("name", ""),
            "location":    loc_str,
            "salary":      "",
            "job_type":    _infer_type(j.get("name", ""), level_name),
            "tags":        [c.get("name", "") for c in j.get("categories", [])][:5],
            "remote":      "remote" in loc_str.lower() or "flexible" in loc_str.lower(),
            "source":      "The Muse",
            "apply_url":   refs.get("landing_page", ""),
            "posted":      j.get("publication_date", ""),
            "description": _strip_html(j.get("contents", ""))[:280],
            "logo_url":    company.get("refs", {}).get("landing_page"),
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATOR
# ═══════════════════════════════════════════════════════════════════════════════

EU_CITIES = set(ARBEITNOW_FILTER.keys())
US_CA_CITIES = {
    "New York", "Boston", "Chicago", "Los Angeles", "San Francisco",
    "Toronto", "Vancouver", "Montreal", "Ottawa",
}


async def _fetch_all(location: str, keywords: str, job_type: str) -> list:
    """Fetch from all relevant sources in parallel, merge, and cache (30 min)."""
    cache_key = f"{location}|{keywords}|{job_type}".lower().strip()
    if cache_key in _CACHE:
        ts, data = _CACHE[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data

    async with httpx.AsyncClient(timeout=15) as client:
        tasks = []
        kw = keywords.strip() or "software engineer intern graduate"

        # Remotive — always (searchable keyword-filtered remote jobs)
        tasks.append(_fetch_remotive(client, kw))

        # RemoteOK — only when: remote job type requested, OR keywords given
        if job_type == "remote" or keywords.strip():
            tasks.append(_fetch_remoteok(client, keywords))

        # EU city → Arbeitnow (post-filtered by location) + Muse
        if location in EU_CITIES:
            tasks.append(_fetch_arbeitnow(client, location, keywords))
            tasks.append(_fetch_muse(client, location, keywords, job_type))

        # US/CA city or other city in Muse map → Muse only
        elif location in MUSE_LOCATIONS:
            tasks.append(_fetch_muse(client, location, keywords, job_type))

        # Unknown city → Muse without location filter
        else:
            tasks.append(_fetch_muse(client, "", keywords, job_type))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: list = []
    seen: set = set()  # dedupe by (title, company)

    for batch in results:
        if isinstance(batch, Exception):
            logger.warning(f"Source error: {batch}")
            continue
        for job in batch:
            key = (job.get("title", "").lower(), job.get("company", "").lower())
            if key not in seen and job.get("title"):
                seen.add(key)
                all_jobs.append(job)

    # Filter by job_type when explicitly requested
    if job_type and job_type != "all":
        filtered = [j for j in all_jobs if j.get("job_type") == job_type
                    or (job_type == "remote" and j.get("remote"))]
        # Fall back to all jobs if filter was too aggressive
        all_jobs = filtered if filtered else all_jobs

    result = all_jobs[:40]
    _CACHE[cache_key] = (time.time(), result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_jobs(location: str, keywords: str, job_type: str, db=None) -> list:
    """
    Main entry point (sync wrapper).
    db is accepted for backward-compatibility but not used (in-memory cache).
    """
    cache_key = f"{location}|{keywords}|{job_type}".lower()
    if cache_key in _CACHE:
        ts, data = _CACHE[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data

    jobs = asyncio.run(_fetch_all(location, keywords, job_type))
    _CACHE[cache_key] = (time.time(), jobs)
    return jobs


# Backward-compatible alias
def fetch_adzuna_jobs(location: str, keywords: str, db=None) -> list:
    return fetch_jobs(location, keywords, "all", db)
