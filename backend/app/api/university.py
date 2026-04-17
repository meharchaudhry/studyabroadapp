from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.university import University
from app.services.recommendation import calculate_score, build_match_explanation

router = APIRouter()

class UniDetail(BaseModel):
    id: int
    name: str
    country: str
    ranking: Optional[int] = None
    qs_subject_ranking: Optional[int] = None
    subject: Optional[str] = None
    tuition: Optional[float] = None
    living_cost: Optional[float] = None
    image_url: Optional[str] = None
    website: Optional[str] = None
    requirements_cgpa: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    gre_required: Optional[bool] = None
    scholarships: Optional[str] = None
    course_duration: Optional[int] = None
    match_score: Optional[float] = None
    match_explanation: Optional[str] = None

    class Config:
        from_attributes = True

class UniListResponse(BaseModel):
    total: int
    universities: List[UniDetail]

class RecommendationResponse(BaseModel):
    recommendations: List[UniDetail]


@router.get("/countries")
def get_university_countries(db: Session = Depends(get_db)):
    rows = (
        db.query(University.country)
        .filter(University.country.isnot(None))
        .distinct()
        .all()
    )
    countries = sorted([r[0] for r in rows if r and r[0]])
    return {"countries": countries}

@router.get("", response_model=UniListResponse)
def list_universities(
    country: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    max_tuition: Optional[float] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(University)
    if country:
        query = query.filter(University.country.ilike(f"%{country}%"))
    if subject:
        query = query.filter(University.subject.ilike(f"%{subject}%"))
    if max_tuition is not None:
        query = query.filter(University.tuition <= max_tuition)

    total = query.count()
    universities = query.order_by(University.ranking).offset(offset).limit(limit).all()

    return {"total": total, "universities": [UniDetail.model_validate(u) for u in universities]}

@router.get("/{uni_id}", response_model=UniDetail)
def get_university(uni_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    uni = db.query(University).filter(University.id == uni_id).first()
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
    return UniDetail.model_validate(uni)

@router.post("/recommendations", response_model=RecommendationResponse)
def recommend_universities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(University)
    if current_user.target_countries:
        query = query.filter(University.country.in_(current_user.target_countries))
    universities = query.all()
    if not universities:
        universities = db.query(University).order_by(University.ranking).limit(40).all()

    results = []
    for uni in universities:
        score = calculate_score(current_user, uni)
        d = UniDetail.model_validate(uni)
        d.match_score = score
        d.match_explanation = build_match_explanation(current_user, uni, score)
        results.append(d)

    results.sort(key=lambda x: x.match_score or 0, reverse=True)
    return {"recommendations": results[:15]}
