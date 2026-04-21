from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.job import SavedJob
from app.services.jobs import _fetch_all   # use async directly in FastAPI
import json
import os

router = APIRouter()

class SearchJobsResponse(BaseModel):
    source: str
    total: int
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
) -> Any:
    jobs = await _fetch_all(location, keywords, job_type)
    return {"source": "live", "total": len(jobs), "jobs": jobs}

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
