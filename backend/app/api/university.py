from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
    summary: str
    reasons: dict
    financial: dict


# ── Helpers ───────────────────────────────────────────────────────────────────

def _enrich(u: University) -> UniDetail:
    d = UniDetail.model_validate(u)
    d.grad_salary_usd  = GRAD_SALARY_USD.get(u.country)
    d.job_market_score = JOB_SCORE.get(u.country)
    return d


# ── Subject expansion: map UI label → keywords that appear in pipe-sep subject field
SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "Computer Science": ["Computer Science", "Computing", "Software", "Informatics", "CS"],
    "Engineering":      ["Engineering", "Mechanical", "Electrical", "Civil", "Chemical", "Aerospace", "Biomedical Engineering"],
    "Data Science":     ["Data Science", "Data Analytics", "Machine Learning", "AI", "Statistics", "Big Data"],
    "Business":         ["Business", "Management", "MBA", "Commerce", "Administration", "Strategy"],
    "Finance":          ["Finance", "Accounting", "Banking", "Financial"],
    "Economics":        ["Economics", "Econometrics", "Political Economy", "Economic"],
    "Medicine":         ["Medicine", "Medical", "Health Sciences", "Pharmacy", "Nursing", "Biomedical"],
    "Law":              ["Law", "Legal", "Jurisprudence", "International Law"],
    "Arts":             ["Arts", "Humanities", "Liberal Arts", "Design", "Media", "Journalism", "History", "Philosophy", "Literature"],
    "Architecture":     ["Architecture", "Urban Planning", "Built Environment"],
    "Psychology":       ["Psychology", "Cognitive", "Neuroscience", "Behavioural"],
    "Physics":          ["Physics", "Mathematics", "Applied Mathematics", "Maths", "Mathematical"],
    "Environmental":    ["Environmental", "Sustainability", "Climate", "Ecology", "Earth Science"],
    "Public Health":    ["Public Health", "Epidemiology", "Global Health", "Health Policy"],
    "Education":        ["Education", "Teaching", "Pedagogy"],
    "Social Science":   ["Social Science", "Sociology", "Anthropology", "Political Science", "International Relations", "Geography"],
}


def _subject_filter(query, subject_str: str):
    """Apply ILIKE filters across the pipe-separated subject column."""
    keywords = SUBJECT_KEYWORDS.get(subject_str, [subject_str])
    conditions = [University.subject.ilike(f"%{kw}%") for kw in keywords]
    return query.filter(or_(*conditions))


# ── Endpoints ─────────────────────────────────────────────────────────────────

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
