import requests
import json
import csv
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.job import Job, Cache
from app.core.config import settings


async def _fetch_all(location: str, keywords: str, job_type: str = "all", source: str | None = None):
    """Fetch job listings from local dataset and optionally live Adzuna fallback."""
    desired_type = (job_type or "all").strip().lower()
    desired_source = (source or "").strip().lower()
    keyword_tokens = [t for t in (keywords or "").lower().split() if t]
    location_token = (location or "").strip().lower()

    jobs = _load_local_jobs(
        location_token=location_token,
        keyword_tokens=keyword_tokens,
        desired_type=desired_type,
        desired_source=desired_source,
    )

    # If local data is too sparse for the query, top up with live results.
    if len(jobs) < 8:
        jobs.extend(_fetch_adzuna_live(location, keywords, desired_type, desired_source))

    dedup = {}
    for job in jobs:
        dedup[str(job.get("id"))] = job
    return list(dedup.values())


def _jobs_csv_path() -> str:
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(backend_dir, "data", "local_jobs.csv")


def _normalize_place(value: str) -> str:
    return " ".join((value or "").lower().replace("/", " ").replace("-", " ").split())


def _extract_city_name(location: str, country: str = "") -> str:
    raw = (location or "").strip()
    if not raw:
        return (country or "").strip()
    first_segment = raw.split(",")[0].strip()
    if first_segment:
        return first_segment
    return (country or "").strip()


def _infer_job_type(text: str, fallback: str = "graduate") -> str:
    lowered = (text or "").lower()
    if "intern" in lowered:
        return "internship"
    if "part" in lowered:
        return "part-time"
    if "remote" in lowered:
        return "remote"
    if "full" in lowered:
        return "full-time"
    return fallback


def _is_remote_job(row: dict) -> bool:
    text = " ".join([
        str(row.get("title", "")),
        str(row.get("description", "")),
        str(row.get("location", "")),
        str(row.get("job_type", "")),
    ]).lower()
    return "remote" in text or "work from home" in text


def _row_matches(
    row: dict,
    location_token: str,
    keyword_tokens: list[str],
    desired_type: str,
    desired_source: str,
) -> bool:
    location_query = _normalize_place(location_token)
    city_name = _normalize_place(_extract_city_name(str(row.get("location", "")), str(row.get("country", ""))))
    country_name = _normalize_place(str(row.get("country", "")))

    haystack = " ".join([
        str(row.get("title", "")),
        str(row.get("description", "")),
        str(row.get("company", "")),
        str(row.get("location", "")),
        str(row.get("country", "")),
    ]).lower()

    if location_query and not (
        location_query in city_name
        or city_name in location_query
        or location_query in country_name
        or country_name in location_query
        or location_query in haystack
    ):
        return False

    if keyword_tokens and not all(tok in haystack for tok in keyword_tokens):
        return False

    if desired_source and desired_source not in {str(row.get("source", "")).strip().lower()}:
        return False

    row_type = _infer_job_type(
        f"{row.get('job_type', '')} {row.get('title', '')}",
        fallback=(row.get("job_type") or "graduate"),
    )
    if desired_type == "remote":
        return _is_remote_job(row)
    if desired_type not in ("all", "", None) and row_type != desired_type:
        return False

    return True


def _load_local_jobs(
    location_token: str,
    keyword_tokens: list[str],
    desired_type: str,
    desired_source: str,
) -> list[dict]:
    path = _jobs_csv_path()
    if not os.path.exists(path):
        return []

    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not _row_matches(row, location_token, keyword_tokens, desired_type, desired_source):
                continue

            jt = _infer_job_type(
                f"{row.get('job_type', '')} {row.get('title', '')}",
                fallback=(row.get("job_type") or "graduate"),
            )
            remote = _is_remote_job(row)
            apply_url = row.get("apply_link") or row.get("apply_url") or ""
            city = _extract_city_name(str(row.get("location", "")), str(row.get("country", "")))

            rows.append({
                "id": str(row.get("id") or ""),
                "title": row.get("title") or "Untitled Role",
                "company": row.get("company") or None,
                "location": city or row.get("location") or row.get("country") or None,
                "salary": row.get("salary") or "Competitive",
                "job_type": jt,
                "source": row.get("source") or "local",
                "apply_url": apply_url,
                "apply_link": apply_url,
                "description": row.get("description") or None,
                "remote": remote,
                "posted": row.get("collected_at_utc") or None,
                "tags": [t.strip() for t in [row.get("country"), row.get("country_code")] if t],
            })

    return rows


def _fetch_adzuna_live(location: str, keywords: str, desired_type: str, desired_source: str = "") -> list[dict]:
    url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
    params = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": keywords,
        "where": location,
        "results_per_page": 20,
    }

    try:
        if settings.ADZUNA_APP_ID == "dummy_id":
            return []

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        results = response.json().get("results", [])

        jobs = []
        for r in results:
            title = r.get("title") or ""
            description = r.get("description") or ""
            jt = _infer_job_type(f"{title} {description}", fallback="graduate")
            remote = "remote" in f"{title} {description}".lower()

            if desired_source and desired_source != "adzuna":
                continue

            if desired_type == "remote" and not remote:
                continue
            if desired_type not in ("all", "", None, "remote") and jt != desired_type:
                continue

            apply_url = r.get("redirect_url")
            jobs.append({
                "id": str(r.get("id")),
                "title": title,
                "company": r.get("company", {}).get("display_name"),
                "location": _extract_city_name(r.get("location", {}).get("display_name", ""), location),
                "salary": str(r.get("salary_min", "Competitive")),
                "job_type": jt,
                "source": "adzuna",
                "apply_url": apply_url,
                "apply_link": apply_url,
                "description": description or None,
                "remote": remote,
                "posted": r.get("created"),
                "tags": [r.get("category", {}).get("label")] if r.get("category", {}).get("label") else [],
            })

        return jobs
    except requests.RequestException:
        return []
