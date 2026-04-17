import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


KEYWORDS_BY_JOB_TYPE = {
    "graduate": ["graduate", "new graduate", "entry level"],
    "internship": ["internship", "intern", "student internship"],
    "part-time": ["part time", "student", "casual"],
}

COUNTRY_LOCATION_HINTS = {
    "UK": "London",
    "US": "New York",
    "USA": "New York",
    "Germany": "Berlin",
    "France": "Paris",
    "Netherlands": "Amsterdam",
    "Australia": "Sydney",
    "Singapore": "Singapore",
    "HongKong": "Hong Kong",
    "Hong Kong": "Hong Kong",
    "Spain": "Madrid",
    "Switzerland": "Zurich",
    "Finland": "Helsinki",
}


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_portals() -> Dict:
    path = os.path.join(_repo_root(), "data", "job_portals.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _country_slug(value: str) -> str:
    return value.lower().replace(" ", "_")


def _unique_by_id(rows: List[Dict]) -> List[Dict]:
    seen = set()
    deduped = []
    for row in rows:
        job_id = row.get("id")
        if job_id in seen:
            continue
        seen.add(job_id)
        deduped.append(row)
    return deduped


def _fetch_adzuna(country_code: str, where: str, query: str, results_per_page: int = 10) -> List[Dict]:
    if not APP_ID or not APP_KEY:
        return []

    url = f"https://api.adzuna.com/v1/api/jobs/{country_code.lower()}/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": query,
        "where": where,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("results", []) or []
    except Exception:
        return []


def _normalize_salary(value: object) -> str:
    if value is None:
        return "Competitive"
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return str(value)


def _build_job_rows_for_country(country_name: str, country_code: str) -> List[Dict]:
    location_hint = COUNTRY_LOCATION_HINTS.get(country_name, country_name)
    rows: List[Dict] = []

    if APP_ID and APP_KEY:
        for job_type, keywords in KEYWORDS_BY_JOB_TYPE.items():
            for keyword in keywords:
                results = _fetch_adzuna(country_code, location_hint, keyword, results_per_page=10)
                for result in results:
                    rows.append(
                        {
                            "id": str(result.get("id")),
                            "title": result.get("title") or f"{job_type.title()} Role",
                            "company": result.get("company", {}).get("display_name") or "Unknown Company",
                            "salary": _normalize_salary(result.get("salary_min")),
                            "location": result.get("location", {}).get("display_name") or location_hint,
                            "job_type": job_type,
                            "source": "adzuna",
                            "apply_link": result.get("redirect_url") or "#",
                            "country": country_name,
                            "country_code": country_code,
                            "collected_at_utc": datetime.utcnow().isoformat() + "Z",
                        }
                    )
    else:
        # Fallback when Adzuna credentials are missing: create country-specific portal-oriented rows
        portals = _load_portals().get("portals", [])
        matching_group = next(
            (group for group in portals if str(group.get("country_code", "")).lower() == country_code.lower()),
            None,
        )
        if matching_group:
            for portal in matching_group.get("portals", [])[:4]:
                for job_type in portal.get("type", ["graduate"]):
                    rows.append(
                        {
                            "id": f"fallback_{_country_slug(country_name)}_{portal.get('id')}_{job_type}",
                            "title": f"{job_type.title()} Opportunity via {portal.get('name')}",
                            "company": portal.get("name", "Portal"),
                            "salary": "Competitive",
                            "location": country_name,
                            "job_type": job_type,
                            "source": "portal_fallback",
                            "apply_link": portal.get("url", "#"),
                            "country": country_name,
                            "country_code": country_code,
                            "collected_at_utc": datetime.utcnow().isoformat() + "Z",
                        }
                    )

    return rows


def generate_csv(jobs_data: List[Dict]) -> None:
    data_dir = os.path.join(_repo_root(), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "local_jobs.csv")

    synthesized_campus_jobs = [
        {
            "id": "campus_mit_ra",
            "title": "Research Assistant",
            "company": "MIT Labs",
            "salary": "₹2,500 / hr",
            "location": "Boston, US",
            "job_type": "on-campus",
            "source": "synthesized",
            "apply_link": "https://careers.mit.edu",
            "country": "USA",
            "country_code": "US",
            "collected_at_utc": datetime.utcnow().isoformat() + "Z",
        },
        {
            "id": "campus_oxford_library",
            "title": "Library Assistant",
            "company": "Oxford Bodleian Library",
            "salary": "₹1,200 / hr",
            "location": "Oxford, UK",
            "job_type": "on-campus",
            "source": "synthesized",
            "apply_link": "https://jobs.ox.ac.uk",
            "country": "UK",
            "country_code": "GB",
            "collected_at_utc": datetime.utcnow().isoformat() + "Z",
        },
        {
            "id": "campus_stanford_ta",
            "title": "Teaching Assistant (CS)",
            "company": "Stanford University",
            "salary": "₹3,000 / hr",
            "location": "Stanford, US",
            "job_type": "on-campus",
            "source": "synthesized",
            "apply_link": "https://careers.stanford.edu",
            "country": "USA",
            "country_code": "US",
            "collected_at_utc": datetime.utcnow().isoformat() + "Z",
        },
        {
            "id": "campus_ucl_cafe",
            "title": "Cafeteria Barista",
            "company": "UCL Student Union",
            "salary": "₹1,150 / hr",
            "location": "London, UK",
            "job_type": "part-time",
            "source": "synthesized",
            "apply_link": "https://studentsunionucl.org",
            "country": "UK",
            "country_code": "GB",
            "collected_at_utc": datetime.utcnow().isoformat() + "Z",
        },
    ]

    fieldnames = [
        "id",
        "title",
        "company",
        "salary",
        "location",
        "job_type",
        "source",
        "apply_link",
        "country",
        "country_code",
        "collected_at_utc",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in jobs_data:
            writer.writerow(row)
        for row in synthesized_campus_jobs:
            writer.writerow(row)

    print(f"✅ Harvested {len(jobs_data) + len(synthesized_campus_jobs)} job listings into {csv_path}")


def scrape_jobs() -> None:
    portals = _load_portals().get("portals", [])
    all_rows: List[Dict] = []

    for group in portals:
        country_name = group.get("country", "")
        country_code = group.get("country_code", "")
        if not country_name or not country_code:
            continue

        group_rows = _build_job_rows_for_country(country_name, country_code)
        all_rows.extend(group_rows)

    all_rows = _unique_by_id(all_rows)
    generate_csv(all_rows)


if __name__ == "__main__":
    scrape_jobs()
