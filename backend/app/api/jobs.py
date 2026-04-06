from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.job import SavedJob
from app.services.jobs import fetch_adzuna_jobs
import json
import os

router = APIRouter()

class SearchJobsResponse(BaseModel):
    source: str
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
    country: Optional[str] = Query(None, description="Country name or code"),
    job_type: Optional[str] = Query(None, description="Type: internship, part-time, graduate"),
    student_friendly: Optional[bool] = Query(None),
):
    data = load_portals()
    portals = data.get("portals", [])
    
    if country:
        portals = [p for p in portals if p["country"].lower() == country.lower() or p["country_code"].lower() == country.lower()]
    
    results = []
    for entry in portals:
        filtered = entry["portals"]
        if job_type:
            filtered = [p for p in filtered if job_type in p.get("type", [])]
        if student_friendly is not None:
            filtered = [p for p in filtered if p.get("student_friendly") == student_friendly]
        if filtered:
            results.append({
                "country": entry["country"],
                "country_code": entry["country_code"],
                "portals": filtered
            })
    
    return {"results": results}

@router.get("/countries")
def get_job_countries():
    data = load_portals()
    return {
        "countries": [{"name": p["country"], "code": p["country_code"]} for p in data.get("portals", [])]
    }

@router.get("/search", response_model=SearchJobsResponse)
def search_jobs(
    location: str = Query(...),
    job_type: str = Query("graduate"),
    keywords: str = Query(""),
    db: Session = Depends(get_db)
) -> Any:
    jobs = fetch_adzuna_jobs(location, keywords, db)
    return {"source": "live" if jobs else "cache", "jobs": jobs}

@router.post("/saved", response_model=dict)
def save_job(
    req: SaveJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    saved = db.query(SavedJob).filter(SavedJob.user_id == current_user.id, SavedJob.job_id == req.job_id).first()
    if not saved:
        new_saved = SavedJob(user_id=current_user.id, job_id=req.job_id)
        db.add(new_saved)
        db.commit()
    return {"status": "success", "message": "Job saved to profile"}
