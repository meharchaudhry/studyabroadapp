import json
import os
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.university import University
from app.models.user import User
from app.services.recommendation import calculate_score
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


@dataclass
class RankedUniversity:
    id: int
    name: str
    country: str
    subject: Optional[str]
    tuition: float
    living_cost: float
    ranking: Optional[int]
    score: float
    reason: str


def _normalize_country(country: str) -> str:
    mapping = {
        "us": "USA",
        "united states": "USA",
        "uk": "UK",
        "united kingdom": "UK",
        "hong kong": "HongKong",
    }
    key = (country or "").strip().lower()
    return mapping.get(key, country)


def _extract_profile(user: User) -> Dict[str, Any]:
    degree_cgpas = [d.cgpa for d in (user.degrees or []) if d.cgpa is not None]
    cgpa = max(degree_cgpas) if degree_cgpas else None

    tests: Dict[str, float] = {}
    for t in user.tests or []:
        if t.test_name and t.score is not None:
            tests[t.test_name.upper()] = t.score

    return {
        "cgpa": cgpa,
        "budget": user.budget,
        "target_countries": [
            _normalize_country(c) for c in (user.target_countries or []) if c
        ],
        "tests": tests,
        "career_goal": user.career_goal,
        "study_priority": user.study_priority,
    }


def _build_reason(uni: University, score: float, profile: Dict[str, Any]) -> str:
    parts: List[str] = []
    if profile.get("cgpa") and uni.requirements_cgpa:
        if profile["cgpa"] >= uni.requirements_cgpa:
            parts.append("your CGPA meets the admission threshold")
        else:
            parts.append("admission is possible but your CGPA is slightly below the usual threshold")

    total_cost = (uni.tuition or 0) + (uni.living_cost or 0)
    budget = profile.get("budget") or 0
    if budget and total_cost:
        if total_cost <= budget:
            parts.append("total yearly cost fits your stated budget")
        else:
            parts.append("this is a stretch option on budget, but still high value academically")

    if uni.ranking and uni.ranking <= 200:
        parts.append("it has a strong global ranking")

    if uni.subject:
        parts.append(f"it aligns with your interest in {uni.subject}")

    if not parts:
        parts.append("it is one of your strongest overall profile matches")

    return f"Match score {round(score * 100)}% because " + ", ".join(parts) + "."


def profile_agent(db: Session, user: User) -> List[RankedUniversity]:
    profile = _extract_profile(user)
    query = db.query(University)

    if profile["target_countries"]:
        query = query.filter(University.country.in_(profile["target_countries"]))

    universities = query.all()
    if not universities:
        universities = db.query(University).order_by(University.ranking).limit(60).all()

    scoring_user = SimpleNamespace(
        cgpa=profile.get("cgpa"),
        budget=profile.get("budget"),
        target_countries=profile.get("target_countries"),
    )

    ranked: List[RankedUniversity] = []
    for uni in universities:
        s = calculate_score(scoring_user, uni)
        ranked.append(
            RankedUniversity(
                id=uni.id,
                name=uni.name,
                country=uni.country,
                subject=uni.subject,
                tuition=float(uni.tuition or 0),
                living_cost=float(uni.living_cost or 0),
                ranking=uni.ranking,
                score=s,
                reason=_build_reason(uni, s, profile),
            )
        )

    ranked.sort(key=lambda u: u.score, reverse=True)
    return ranked[:3]


def _load_visa_data() -> Dict[str, Any]:
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "visa_data.json",
    )
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def visa_agent(recommendations: List[RankedUniversity]) -> Dict[str, Dict[str, Any]]:
    countries = {r.country for r in recommendations}
    visa_data = _load_visa_data().get("countries", {})
    out: Dict[str, Dict[str, Any]] = {}

    for country in countries:
        key = _normalize_country(country)
        item = visa_data.get(key)
        if not item:
            out[country] = {
                "difficulty": "Unknown",
                "score": 0.55,
                "note": "No visa metadata found in local dataset.",
            }
            continue

        fee = int(item.get("visa_fee_inr", 0) or 0)
        proc = str(item.get("processing_time", ""))

        score = 0.7
        if fee > 50000:
            score -= 0.1
        if "8" in proc or "12" in proc:
            score -= 0.1

        score = max(0.35, min(0.9, score))
        difficulty = "Low" if score >= 0.75 else "Medium" if score >= 0.6 else "High"

        out[country] = {
            "difficulty": difficulty,
            "score": round(score, 3),
            "note": f"Processing: {proc}; fee approx INR {fee:,}.",
        }

    return out


def _estimate_starting_salary(subject: Optional[str]) -> int:
    s = (subject or "").lower()
    if "data" in s or "computer" in s or "engineering" in s:
        return 5200000
    if "business" in s or "economics" in s:
        return 4600000
    if "medicine" in s:
        return 5800000
    return 4000000


def finance_agent(recommendations: List[RankedUniversity]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for rec in recommendations:
        total_cost = rec.tuition + rec.living_cost
        loan_interest = total_cost * 0.2
        true_cost = total_cost + loan_interest

        net_salary = _estimate_starting_salary(rec.subject) * 0.75
        yearly_payoff = net_salary * 0.3
        break_even_years = (true_cost / yearly_payoff) if yearly_payoff else 99
        roi_5y = (((net_salary * 5) - true_cost) / true_cost) * 100 if true_cost else 0

        out[rec.name] = {
            "true_cost": int(true_cost),
            "break_even_years": round(break_even_years, 2),
            "roi_5y": round(roi_5y, 2),
            "score": round(min(max((roi_5y + 50) / 200, 0.2), 0.95), 3),
        }

    return out


def _load_job_portals() -> Dict[str, Any]:
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "job_portals.json",
    )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def jobs_agent(recommendations: List[RankedUniversity]) -> Dict[str, Dict[str, Any]]:
    data = _load_job_portals().get("portals", [])
    out: Dict[str, Dict[str, Any]] = {}

    for rec in recommendations:
        normalized = _normalize_country(rec.country)
        match = next(
            (
                p
                for p in data
                if p.get("country", "").lower() == normalized.lower()
                or p.get("country_code", "").lower() == normalized.lower()
            ),
            None,
        )

        if not match:
            out[rec.name] = {
                "score": 0.5,
                "note": "No country-specific portal metadata found.",
                "portal_count": 0,
            }
            continue

        portals = match.get("portals", [])
        student_friendly = len([p for p in portals if p.get("student_friendly")])
        base = 0.45 + min(len(portals), 8) * 0.05 + min(student_friendly, 4) * 0.04
        score = min(base, 0.92)

        out[rec.name] = {
            "score": round(score, 3),
            "note": f"{len(portals)} portals listed, {student_friendly} marked student-friendly.",
            "portal_count": len(portals),
        }

    return out


def _synthesis_text_with_llm(summary_prompt: str) -> Optional[str]:
    if not settings.GOOGLE_API_KEY:
        return None
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        resp = llm.invoke([HumanMessage(content=summary_prompt)])
        return str(resp.content)
    except Exception:
        return None


def run_decision_chain(db: Session, user: User) -> Dict[str, Any]:
    profile = _extract_profile(user)
    top = profile_agent(db, user)
    visa = visa_agent(top)
    finance = finance_agent(top)
    jobs = jobs_agent(top)

    scored = []
    for rec in top:
        final_score = (
            rec.score * 0.45
            + visa.get(rec.country, {}).get("score", 0.55) * 0.15
            + finance.get(rec.name, {}).get("score", 0.55) * 0.25
            + jobs.get(rec.name, {}).get("score", 0.55) * 0.15
        )
        scored.append((rec, round(final_score, 3)))

    scored.sort(key=lambda x: x[1], reverse=True)

    prompt = (
        "You are a study abroad advisor. Write a concise recommendation (max 180 words) "
        "explaining why the top option is ranked #1 and who should pick #2/#3 instead.\n"
        f"User profile: {profile}\n"
        f"Ranked options: {[{'name': r.name, 'country': r.country, 'score': s} for r, s in scored]}\n"
        f"Visa notes: {visa}\nFinance notes: {finance}\nJobs notes: {jobs}"
    )
    llm_text = _synthesis_text_with_llm(prompt)

    steps = [
        {
            "id": "profile",
            "name": "Profile Agent",
            "result": f"Scored universities using CGPA/budget/country fit. Top candidates: {', '.join([r.name for r, _ in scored])}.",
        },
        {
            "id": "visa",
            "name": "Visa Agent",
            "result": "Evaluated visa complexity from local official checklist metadata by country.",
        },
        {
            "id": "finance",
            "name": "Finance Agent",
            "result": "Estimated true study cost, 5-year ROI, and break-even timeline per option.",
        },
        {
            "id": "jobs",
            "name": "Jobs Agent",
            "result": "Scored job-market readiness using country job portal coverage and student-friendly signals.",
        },
        {
            "id": "synthesis",
            "name": "Synthesis Agent",
            "result": "Combined all agent scores into final ranking and generated recommendation rationale.",
        },
    ]

    recommendations = []
    for rec, final_score in scored:
        recommendations.append(
            {
                "id": rec.id,
                "name": rec.name,
                "country": rec.country,
                "subject": rec.subject,
                "match_score": rec.score,
                "final_score": final_score,
                "reason": rec.reason,
                "visa": visa.get(rec.country, {}),
                "finance": finance.get(rec.name, {}),
                "jobs": jobs.get(rec.name, {}),
            }
        )

    best = recommendations[0] if recommendations else None
    fallback_text = (
        "Top choice balances profile fit, visa practicality, ROI, and jobs. "
        "Compare #2 and #3 if your budget or country preference changes."
    )

    return {
        "best_option": best["name"] if best else "No recommendation",
        "explanation": llm_text or fallback_text,
        "recommendations": recommendations,
        "agent_steps": steps,
    }
