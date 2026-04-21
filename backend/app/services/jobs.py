import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.job import Job, Cache
from app.core.config import settings


async def _fetch_all(location: str, keywords: str, job_type: str = "all"):
    """Fetch job listings without a DB session for the live jobs search endpoint."""
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
            results = [
                {
                    "id": f"dummy_{i}",
                    "title": f"Test Job {i}",
                    "company": {"display_name": f"Test Company {i}"},
                    "location": {"display_name": location},
                    "salary_min": 20000,
                    "redirect_url": "https://adzuna.com",
                }
                for i in range(5)
            ]
        else:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json().get("results", [])

        jobs = []
        for r in results:
            title = r.get("title") or ""
            jt = "graduate"
            lowered = title.lower()
            if "intern" in lowered:
                jt = "internship"
            elif "part" in lowered:
                jt = "part-time"

            if job_type not in ("all", "", None) and jt != job_type:
                continue

            jobs.append({
                "id": str(r.get("id")),
                "title": title,
                "company": r.get("company", {}).get("display_name"),
                "location": r.get("location", {}).get("display_name"),
                "salary": str(r.get("salary_min", "Competitive")),
                "job_type": jt,
                "source": "adzuna",
                "apply_link": r.get("redirect_url"),
            })

        return jobs
    except requests.RequestException:
        return []

def fetch_adzuna_jobs(location: str, keywords: str, db: Session):
    cache_key = f"adzuna_{location}_{keywords}"
    
    # Check cache
    cached = db.query(Cache).filter(Cache.key == cache_key).first()
    if cached and cached.expires_at > datetime.utcnow():
        return json.loads(cached.value)
        
    url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
    params = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": keywords,
        "where": location,
        "results_per_page": 20
    }
    
    try:
        # Mocking for development if dummy keys are used
        if settings.ADZUNA_APP_ID == "dummy_id":
            results = [{
                "id": f"dummy_{i}",
                "title": f"Test Job {i}",
                "company": {"display_name": f"Test Company {i}"},
                "location": {"display_name": location},
                "salary_min": 20000,
                "redirect_url": "https://adzuna.com"
            } for i in range(5)]
        else:
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])

        jobs = []
        for r in results:
            jobs.append({
                "id": str(r.get("id")),
                "title": r.get("title"),
                "company": r.get("company", {}).get("display_name"),
                "location": r.get("location", {}).get("display_name"),
                "salary": str(r.get("salary_min", "Competitive")),
                "job_type": "graduate",
                "source": "adzuna",
                "apply_link": r.get("redirect_url")
            })

        # Save to cache table (TTL 6 hours)
        expires = datetime.utcnow() + timedelta(hours=6)
        
        # update or insert
        if cached:
            cached.value = json.dumps(jobs)
            cached.expires_at = expires
        else:
            new_cache = Cache(key=cache_key, value=json.dumps(jobs), expires_at=expires)
            db.add(new_cache)
        db.commit()
        
        return jobs
        
    except requests.RequestException as e:
        print(f"Adzuna API Error: {e}")
        return []
