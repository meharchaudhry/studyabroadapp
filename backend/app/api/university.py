import csv
import os
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.university import University
from app.services.recommendation import calculate_score, explain_match, GRAD_SALARY_USD, JOB_SCORE

router = APIRouter()

# ── Country name normalisation ────────────────────────────────────────────────
# Frontend may send short names; DB always stores full names.
COUNTRY_ALIASES: dict[str, list[str]] = {
    "United Kingdom": ["uk", "united kingdom", "britain", "england", "great britain"],
    "United States":  ["us", "usa", "united states", "united states of america"],
    "UAE":            ["uae", "united arab emirates", "dubai"],
    "South Korea":    ["south korea", "korea"],
    "New Zealand":    ["new zealand", "nz"],
}

def _normalise_country(raw: str) -> str:
    """Map any alias to the canonical full country name stored in the DB."""
    if not raw:
        return raw
    lo = raw.strip().lower()
    for canonical, aliases in COUNTRY_ALIASES.items():
        if lo in aliases or lo == canonical.lower():
            return canonical
    # Title-case the raw value as a fallback
    return raw.strip()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

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
    description: Optional[str] = None
    acceptance_rate: Optional[float] = None
    requirements_cgpa: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    gre_required: Optional[bool] = None
    scholarships: Optional[str] = None
    course_duration: Optional[int] = None
    intake_months: Optional[List[str]] = None
    match_score: Optional[float] = None
    grad_salary_usd: Optional[int] = None
    job_market_score: Optional[float] = None

    class Config:
        from_attributes = True


class UniListResponse(BaseModel):
    total: int
    universities: List[UniDetail]


class RecommendationResponse(BaseModel):
    recommendations: List[UniDetail]


class ExplainResponse(BaseModel):
    match_score: float
    reasons: dict
    financial: dict
    summary: str


def _subject_filter(query, subject: str):
    value = (subject or "").strip()
    if not value:
        return query
    return query.filter(
        or_(
            University.subject.ilike(f"%{value}%"),
            University.subject.ilike(f"%{value.replace(' ', '%')}%"),
        )
    )


def _enrich(uni: University) -> UniDetail:
    return UniDetail(
        id=uni.id,
        name=uni.name,
        country=uni.country,
        ranking=uni.ranking,
        qs_subject_ranking=uni.qs_subject_ranking,
        subject=uni.subject,
        tuition=uni.tuition,
        living_cost=uni.living_cost,
        image_url=uni.image_url,
        website=uni.website,
        description=getattr(uni, "description", None),
        acceptance_rate=getattr(uni, "acceptance_rate", None),
        requirements_cgpa=uni.requirements_cgpa,
        ielts=uni.ielts,
        toefl=uni.toefl,
        gre_required=uni.gre_required,
        scholarships=getattr(uni, "scholarships", None),
        course_duration=getattr(uni, "course_duration", None),
        intake_months=getattr(uni, "intake_months", None),
    )


@router.get("/countries")
def get_university_countries(db: Session = Depends(get_db)):
    try:
        rows = (
            db.query(University.country)
            .filter(University.country.isnot(None))
            .distinct()
            .all()
        )
        countries = sorted([r[0] for r in rows if r and r[0]])
        return {"countries": countries}
    except SQLAlchemyError:
        # Fallback: allow automation workflows to continue from local dataset when DB is down.
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "universities.csv",
        )
        countries = set()
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    c = (row.get("country") or "").strip()
                    if c:
                        countries.add(c)
        except Exception:
            return {"countries": []}

        return {"countries": sorted(countries)}

@router.get("", response_model=UniListResponse)
def list_universities(
    country: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    max_tuition: Optional[float] = Query(None),
    min_ranking: Optional[int] = Query(None),
    max_ranking: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(University)

    if country:
        canon = _normalise_country(country)
        # Match exact normalised name OR partial (handles "United Kingdom" → UK stored differently)
        query = query.filter(
            or_(
                University.country.ilike(canon),
                University.country.ilike(f"%{canon}%"),
            )
        )

    if subject:
        query = _subject_filter(query, subject)

    if max_tuition is not None:
        query = query.filter(University.tuition <= max_tuition)

    if min_ranking is not None:
        query = query.filter(University.ranking >= min_ranking)

    if max_ranking is not None:
        query = query.filter(University.ranking <= max_ranking)

    if search:
        query = query.filter(University.name.ilike(f"%{search}%"))

    total = query.count()
    unis  = query.order_by(University.ranking.nullslast()).offset(offset).limit(limit).all()

    return {"total": total, "universities": [_enrich(u) for u in unis]}


@router.get("/recommendations", response_model=RecommendationResponse)
def recommend_universities(
    limit: int = Query(15, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    # If user has target countries, prioritise those; otherwise use full DB
    if current_user.target_countries:
        normalised = [_normalise_country(c) for c in current_user.target_countries]
        unis = db.query(University).filter(
            or_(*[University.country.ilike(n) for n in normalised])
        ).all()
        # If the target-country filter returns too few, fall back to full DB
        if len(unis) < 20:
            unis = db.query(University).all()
    else:
        unis = db.query(University).all()

    results = []
    for uni in unis:
        score = calculate_score(current_user, uni)
        d = _enrich(uni)
        d.match_score = score
        results.append(d)

    results.sort(key=lambda x: x.match_score or 0, reverse=True)
    return {"recommendations": results[:limit]}


@router.get("/{uni_id}/explain", response_model=ExplainResponse)
def explain_university_match(
    uni_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uni = db.query(University).filter(University.id == uni_id).first()
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
    return explain_match(current_user, uni)


@router.get("/{uni_id}", response_model=UniDetail)
def get_university(
    uni_id: int,
    db: Session = Depends(get_db),
):
    uni = db.query(University).filter(University.id == uni_id).first()
    if not uni:
        raise HTTPException(status_code=404, detail="University not found")
    return _enrich(uni)
