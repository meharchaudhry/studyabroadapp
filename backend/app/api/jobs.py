from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import csv
import math
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.job import SavedJob
from app.services.jobs import _fetch_all   # use async directly in FastAPI
from app.services.jobs import _extract_city_name
import json
import os

router = APIRouter()

class SearchJobsResponse(BaseModel):
    source: str
    total: int
    page: int
    limit: int
    total_pages: int
    jobs: list[dict]

class SaveJobRequest(BaseModel):
    job_id: str

def load_portals():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "job_portals.json"
    )
    with open(path, "r") as f:
        return json.load(f)

@router.get("/portals")
def get_job_portals(
    country: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    student_friendly: Optional[bool] = Query(None),
):
    data = load_portals()
    portals = data.get("portals", [])
    if country:
        portals = [p for p in portals if p["country"].lower() == country.lower() or p.get("country_code", "").lower() == country.lower()]
    results = []
    for entry in portals:
        filtered = entry["portals"]
        if job_type:
            filtered = [p for p in filtered if job_type in p.get("type", [])]
        if student_friendly is not None:
            filtered = [p for p in filtered if p.get("student_friendly") == student_friendly]
        if filtered:
            results.append({"country": entry["country"], "country_code": entry.get("country_code", ""), "portals": filtered})
    return {"results": results}

@router.get("/countries")
def get_job_countries():
    data = load_portals()
    return {"countries": [{"name": p["country"], "code": p.get("country_code", "")} for p in data.get("portals", [])]}

@router.get("/search", response_model=SearchJobsResponse)
async def search_jobs(
    location: str = Query("London", description="City or country"),
    job_type: str = Query("all", description="all | internship | part-time | graduate | remote"),
    keywords: str = Query("", description="Role keywords e.g. 'software engineer'"),
    source: Optional[str] = Query(None, description="Optional source filter"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
) -> Any:
    jobs = await _fetch_all(location, keywords, job_type, source)
    total = len(jobs)
    total_pages = max(1, math.ceil(total / limit)) if total else 0
    page = min(page, total_pages) if total_pages else 1
    start = (page - 1) * limit
    end = start + limit
    return {
        "source": "live",
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "jobs": jobs[start:end],
    }


@router.get("/filters")
def get_job_filters() -> Any:
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "local_jobs.csv"
    )
    locations = set()
    job_types = set()
    sources = set()

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = _extract_city_name(row.get("location", ""), row.get("country", ""))
                if city:
                    locations.add(city.strip())
                if row.get("job_type"):
                    job_types.add(row["job_type"].strip())
                if row.get("source"):
                    sources.add(row["source"].strip())

    return {
        "locations": sorted(locations)[:200],
        "job_types": sorted(job_types),
        "sources": sorted(sources),
    }

@router.post("/saved", response_model=dict)
def save_job(
    req: SaveJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    existing = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == req.job_id
    ).first()
    if not existing:
        db.add(SavedJob(user_id=current_user.id, job_id=req.job_id))
        db.commit()
    return {"status": "saved"}
