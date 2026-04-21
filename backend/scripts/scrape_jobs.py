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

COUNTRIES = {
    "USA": "us",
    "UK": "gb",
    "Germany": "de",
    "France": "fr",
    "Netherlands": "nl",
    "Australia": "au",
    "Singapore": "sg",
    "Spain": "es",
    "Switzerland": "ch",
    "Finland": "fi",
    "India": "in",
    # Hong Kong is not directly supported by Adzuna's country codes in the same way
}

COUNTRY_LOCATION_HINTS = {
    "USA": "New York",
    "UK": "London",
    "Germany": "Berlin",
    "France": "Paris",
    "Netherlands": "Amsterdam",
    "Australia": "Sydney",
    "Singapore": "Singapore",
    "Hong Kong": "Hong Kong",
    "Spain": "Madrid",
    "Switzerland": "Zurich",
    "Finland": "Helsinki",
    "India": "Bangalore",
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


def _fetch_adzuna(country_code: str, where: str, query: str, results_per_page: int = 50) -> List[Dict]:
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


def _fetch_remotive(query: str) -> List[Dict]:
    url = f"https://remotive.com/api/remote-jobs?search={query}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json().get("jobs", []) or []
    except Exception:
        return []


def _fetch_arbeitnow(query: str) -> List[Dict]:
    url = f"https://arbeitnow.com/api/job-board-api?search={query}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json().get("data", []) or []
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

    # --- Adzuna API ---
    if APP_ID and APP_KEY:
        for job_type, keywords in KEYWORDS_BY_JOB_TYPE.items():
            for keyword in keywords:
                results = _fetch_adzuna(country_code, location_hint, keyword, results_per_page=50)
                for result in results:
                    rows.append(
                        {
                            "id": str(result.get("id")),
                            "title": result.get("title") or f"{job_type.title()} Role",
                            "description": result.get("description", ""),
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

    # --- Remotive API (Remote) ---
    for job_type, keywords in KEYWORDS_BY_JOB_TYPE.items():
        if job_type == "part-time":  # Remotive is more for full-time
            continue
        for keyword in keywords:
            results = _fetch_remotive(keyword)
            for result in results:
                # Filter by country if possible, otherwise accept remote jobs
                candidate_countries = result.get("candidate_required_location", [])
                if candidate_countries and country_name not in candidate_countries and country_code not in candidate_countries:
                    continue

                rows.append(
                    {
                        "id": f"remotive_{result.get('id')}",
                        "title": result.get("title"),
                        "description": result.get("description", ""),
                        "company": result.get("company_name"),
                        "salary": result.get("salary") or "Competitive",
                        "location": result.get("candidate_required_location", ["Remote"]),
                        "job_type": result.get("job_type", job_type),
                        "source": "remotive",
                        "apply_link": result.get("url"),
                        "country": country_name,
                        "country_code": country_code,
                        "collected_at_utc": result.get("publication_date"),
                    }
                )

    # --- Arbeitnow API ---
    for job_type, keywords in KEYWORDS_BY_JOB_TYPE.items():
        for keyword in keywords:
            results = _fetch_arbeitnow(keyword)
            for result in results:
                if country_name.lower() not in result.get("location", "").lower():
                    continue
                rows.append(
                    {
                        "id": f"arbeitnow_{result.get('slug')}",
                        "title": result.get("title"),
                        "description": result.get("description", ""),
                        "company": result.get("company_name"),
                        "salary": "Competitive",
                        "location": result.get("location"),
                        "job_type": job_type,
                        "source": "arbeitnow",
                        "apply_link": result.get("url"),
                        "country": country_name,
                        "country_code": country_code,
                        "collected_at_utc": result.get("created_at"),
                    }
                )

    # --- Fallback for missing credentials ---
    if not rows:
        print(f"⚠️ No job results found for {country_name} via APIs. You may be missing API keys.")

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
        "description",
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
        writer.writerows(jobs_data)

    print(f"✅ Harvested {len(jobs_data)} job listings into {csv_path}")


def scrape_jobs() -> None:
    all_rows: List[Dict] = []
    countries_to_scrape = COUNTRIES

    print("🚀 Starting job scrape from all sources...")
    i = 0
    for country_name, country_code in countries_to_scrape.items():
        i += 1
        if not country_name or not country_code:
            continue

        print(f"[{i}/{len(countries_to_scrape)}] Fetching jobs for: {country_name} ({country_code})")
        group_rows = _build_job_rows_for_country(country_name, country_code)
        all_rows.extend(group_rows)
        print(f"    -> Found {len(group_rows)} new listings for {country_name}.")

    # Special handling for Hong Kong which doesn't have a dedicated Adzuna endpoint
    print(f"[{i+1}/{len(countries_to_scrape)+1}] Fetching jobs for: Hong Kong")
    hk_rows = _build_job_rows_for_country("Hong Kong", "hk") # Use 'hk' as a code, though Adzuna might not use it
    all_rows.extend(hk_rows)
    print(f"    -> Found {len(hk_rows)} new listings for Hong Kong.")


    print("\nDeduplicating job listings...")
    all_rows = _unique_by_id(all_rows)
    print(f"  -> {len(all_rows)} unique jobs found.")
    
    generate_csv(all_rows)


if __name__ == "__main__":
    scrape_jobs()
