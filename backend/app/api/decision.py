"""
Decision Dashboard — 5-Agent Agentic Chain
==========================================
Implements the LangChain SequentialChain pattern with five focused agents:

  Agent 1 — Profile Agent    : Identifies top-3 matching universities from DB.
  Agent 2 — Visa Agent       : Returns factual visa assessment for each country.
  Agent 3 — Finance Agent    : Calculates total cost, ROI and break-even year.
  Agent 4 — Jobs Agent       : Scores part-time / graduate job availability.
  Agent 5 — Synthesis Agent  : Combines all four outputs and produces a ranked
                               top-3 recommendation with plain-English rationale.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.university import University
from app.services.recommendation import calculate_score, _get_budget_usd, GRAD_SALARY_USD as _REC_GRAD_SALARY, JOB_SCORE as _REC_JOB_SCORE
from app.core.config import settings

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

router = APIRouter()

INR_TO_USD = 1 / 83.0

# ── Real post-study work visa data (factual, not LLM-generated) ──────────────

VISA_INFO: dict[str, dict] = {
    "United Kingdom": {
        "name": "Graduate Route",
        "duration": "2 years (3 for PhD)",
        "work_rights": "Full-time any employer",
        "difficulty": "Easy",
        "note": "Apply within 2 years of graduating. No job offer needed.",
    },
    "United States": {
        "name": "OPT (Optional Practical Training)",
        "duration": "12 months (+24 month STEM extension = 36 months total)",
        "work_rights": "Must be in field of study",
        "difficulty": "Moderate",
        "note": "Apply through your university DSO. STEM OPT extension requires E-Verify employer.",
    },
    "Canada": {
        "name": "PGWP (Post-Graduation Work Permit)",
        "duration": "1–3 years (matches program length)",
        "work_rights": "Full-time, any employer",
        "difficulty": "Easy",
        "note": "Apply within 180 days of graduation. Most flexible in the world for Indian students.",
    },
    "Australia": {
        "name": "Graduate Temporary Visa (Subclass 485)",
        "duration": "2 years (4 years in regional areas)",
        "work_rights": "Unrestricted full-time",
        "difficulty": "Easy",
        "note": "Must apply within 6 months of graduation. Regional study gets extra 2 years.",
    },
    "Germany": {
        "name": "Job Seeker Visa",
        "duration": "18 months job search, then work permit",
        "work_rights": "Full-time once employed",
        "difficulty": "Moderate",
        "note": "No work rights during job search. Requires B1 German or offer in English-taught field.",
    },
    "Netherlands": {
        "name": "Orientation Year (Zoekjaar)",
        "duration": "12 months",
        "work_rights": "Unrestricted during orientation year",
        "difficulty": "Easy",
        "note": "Available within 3 years of graduation from a recognised Dutch or top-200 global university.",
    },
    "Ireland": {
        "name": "Stay Back Option (Third Level Graduate Programme)",
        "duration": "1 year (Bachelors/PG Diploma), 2 years (Masters+)",
        "work_rights": "Full-time any employer",
        "difficulty": "Easy",
        "note": "Apply before your student permission expires. No job offer needed.",
    },
    "Singapore": {
        "name": "Employment Pass / S Pass",
        "duration": "No automatic post-study permit — job offer required",
        "work_rights": "Tied to employer",
        "difficulty": "Hard",
        "note": "Must secure job offer from an employer before applying. High salary threshold (~SGD 5,000/month).",
    },
    "Sweden": {
        "name": "Job Search Permit",
        "duration": "6 months",
        "work_rights": "Can work during job search",
        "difficulty": "Moderate",
        "note": "Apply after finishing your degree. English jobs plentiful in tech but Swedish helps.",
    },
    "Norway": {
        "name": "Job Seeker Permit",
        "duration": "Up to 1 year",
        "work_rights": "Part-time during job search",
        "difficulty": "Moderate",
        "note": "Nordic countries have strong social benefits but high cost of living.",
    },
    "Denmark": {
        "name": "Job Seeker Visa",
        "duration": "6 months",
        "work_rights": "Part-time",
        "difficulty": "Moderate",
        "note": "Must apply within 6 months of graduation. Danish language a major advantage.",
    },
    "Finland": {
        "name": "Job Search Residence Permit",
        "duration": "1 year",
        "work_rights": "Part-time",
        "difficulty": "Moderate",
        "note": "Apply online through Enter Finland. Finnish or Swedish language often required.",
    },
    "New Zealand": {
        "name": "Post Study Work Visa",
        "duration": "1–3 years (based on study duration and location)",
        "work_rights": "Unrestricted",
        "difficulty": "Easy",
        "note": "Study 2+ years → 3 years post-study visa. Regional study gets extra time.",
    },
    "UAE": {
        "name": "No automatic post-study visa",
        "duration": "Job offer required",
        "work_rights": "Tied to employer (sponsored)",
        "difficulty": "Moderate",
        "note": "UAE has no post-study work route. Must secure employment before visa expires. Tax-free salaries.",
    },
    "France": {
        "name": "Temporary Residence Permit (APS)",
        "duration": "12 months",
        "work_rights": "Up to 60% of legal working hours",
        "difficulty": "Moderate",
        "note": "For Masters/PhD graduates. French language significantly improves job prospects.",
    },
    "Switzerland": {
        "name": "No automatic post-study permit",
        "duration": "Job offer required",
        "work_rights": "Employer-sponsored",
        "difficulty": "Hard",
        "note": "Very high salaries but strict immigration. Best prospects in finance, pharma, engineering.",
    },
    "Spain": {
        "name": "Job Search Visa (Búsqueda de Empleo)",
        "duration": "12 months",
        "work_rights": "Limited during search, full once employed",
        "difficulty": "Moderate",
        "note": "Spanish language almost always required. IT sector is an exception.",
    },
    "Portugal": {
        "name": "Job Seeker Visa",
        "duration": "6 months (renewable once)",
        "work_rights": "Part-time during search",
        "difficulty": "Easy",
        "note": "Increasingly popular due to lower cost of living and improving tech scene.",
    },
    "Japan": {
        "name": "Specified Activities Visa",
        "duration": "1 year (renewable if job search active)",
        "work_rights": "Up to 28 hours/week during search",
        "difficulty": "Hard",
        "note": "Japanese language (JLPT N2+) virtually essential for most roles.",
    },
    "South Korea": {
        "name": "D-10 Job Seeker Visa",
        "duration": "6 months (extendable)",
        "work_rights": "Part-time only",
        "difficulty": "Hard",
        "note": "Korean language proficiency highly recommended. TOPIK Level 4+ for most roles.",
    },
}

DEFAULT_VISA_INFO = {
    "name": "Student Visa",
    "duration": "Varies — check official immigration website",
    "work_rights": "Typically limited during study",
    "difficulty": "Moderate",
    "note": "Indian nationals should check the destination country's official immigration portal for current requirements.",
}


def _visa_blurb(country: str) -> str:
    """Return a factual one-line visa summary for display on cards."""
    info = VISA_INFO.get(country, DEFAULT_VISA_INFO)
    return (
        f"{info['name']} · {info['duration']} · {info['difficulty']} process. "
        f"{info['note']}"
    )


# ── Response Schemas ──────────────────────────────────────────────────────────

class UniversityOption(BaseModel):
    name: str
    country: str
    ranking: Optional[int]
    match_score: float           # 0–1
    tuition_usd: Optional[float]
    living_cost_usd: Optional[float]
    total_cost_usd: Optional[float]
    roi_5yr_pct: Optional[float]
    break_even_years: Optional[float]
    job_availability_score: float
    visa_assessment: str
    # Confidence scores per agent (0–1)
    confidence_profile: float = 0.0
    confidence_finance: float = 0.0
    confidence_jobs: float = 0.0
    confidence_visa: float = 0.0
    confidence_overall: float = 0.0


class AgentSteps(BaseModel):
    profile_analysis: str
    visa_assessment: str
    finance_analysis: str
    jobs_analysis: str
    final_synthesis: str


class DecisionResponse(BaseModel):
    top_universities: List[UniversityOption]
    synthesis: str
    agent_steps: AgentSteps
    confidence_score: float = 0.0


# Legacy
class SimpleDecisionResponse(BaseModel):
    best_option: str
    explanation: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=settings.GOOGLE_API_KEY or None,
    )


def _run_agent(llm, system: str, human: str, **kwargs) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", human),
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(kwargs)


# Use the canonical salary/job tables from recommendation.py — single source of truth
_GRAD_SALARY_USD = _REC_GRAD_SALARY
_JOB_SCORE       = _REC_JOB_SCORE


def _calculate_roi(tuition_inr: float, living_inr: float, country: str, duration_years: int = 2) -> dict:
    """
    ROI model using real grad salary data and actual program duration.
    Inputs are INR; converted to USD for calculation.
    duration_years: total program length (1-4 yrs, from university.course_duration)
    """
    annual_usd   = (tuition_inr + living_inr) * INR_TO_USD
    total_usd    = annual_usd * duration_years   # total investment over the whole program
    salary_usd   = _GRAD_SALARY_USD.get(country, 55000)
    net_salary   = salary_usd * 0.75              # ~25% effective tax
    annual_repay = net_salary * 0.30              # 30% of net allocated to loan repayment
    break_even   = total_usd / annual_repay if annual_repay > 0 else 99
    roi_5yr      = ((net_salary * 5) - total_usd) / total_usd * 100 if total_usd > 0 else 0
    return {
        "total_cost_usd":   round(total_usd, 0),
        "annual_cost_usd":  round(annual_usd, 0),
        "roi_5yr_pct":      round(roi_5yr, 1),
        "break_even_years": round(break_even, 1),
    }


# ── Candidate selection ───────────────────────────────────────────────────────

def _get_candidates(db: Session, user: User) -> List[University]:
    """
    Return a broad, profile-appropriate candidate pool (up to 150 unis).

    Filtering rules:
      1. CGPA gap ≤ 2.0 (or no req listed)
      2. Total cost ≤ 2.5× annual budget (or no cost listed)
      3. Prefer target countries (but include others too)
      4. Include unis across the full ranking spectrum
    """
    cgpa       = getattr(user, "cgpa", None)
    budget_usd = _get_budget_usd(user)
    target     = list(getattr(user, "target_countries", None) or [])

    q = db.query(University)

    # CGPA filter: include unis where gap ≤ 2.0 or no req listed
    if cgpa:
        q = q.filter(
            or_(
                University.requirements_cgpa.is_(None),
                University.requirements_cgpa <= cgpa + 2.0,
            )
        )

    # Budget filter: exclude obvious mismatches (>3× budget) — let scoring do fine-grained work
    if budget_usd:
        max_cost_inr = budget_usd * 83 * 3.0
        q = q.filter(
            or_(
                University.tuition.is_(None),
                University.tuition <= max_cost_inr,
            )
        )

    # If user has target countries, ONLY use those — only add others if target pool < 5
    if target:
        target_unis = (
            q.filter(University.country.in_(target))
            .order_by(University.ranking.asc().nulls_last())
            .limit(150)
            .all()
        )
        if len(target_unis) >= 5:
            # Enough options in target countries — don't mix in others
            return target_unis

        # Too few target country options; widen to include non-target
        other_unis = (
            q.filter(University.country.notin_(target))
            .order_by(University.ranking.asc().nulls_last())
            .limit(100)
            .all()
        )
        candidates = target_unis + other_unis
    else:
        candidates = (
            q.order_by(University.ranking.asc().nulls_last())
            .limit(150)
            .all()
        )

    # Final fallback: if still < 5, drop all filters
    if len(candidates) < 5:
        candidates = db.query(University).order_by(University.ranking.asc().nulls_last()).limit(100).all()

    return candidates


# ── Agent Functions ───────────────────────────────────────────────────────────

def agent_profile(user: User, universities: List[University]) -> tuple[List[University], str]:
    """Agent 1 — scores candidates and returns top 3."""
    scored = [(calculate_score(user, uni), uni) for uni in universities]
    scored.sort(key=lambda x: x[0], reverse=True)
    top3_scored = scored[:3]   # [(score, uni), ...]
    top3        = [uni for _, uni in top3_scored]

    cgpa_str   = f"{user.cgpa}" if user.cgpa else "N/A"
    budget_usd = _get_budget_usd(user)
    budget_str = f"${budget_usd:,.0f}" if budget_usd else "N/A"

    summary = (
        f"Profile: CGPA {cgpa_str}, budget {budget_str}/yr, "
        f"field: {getattr(user,'field_of_study','N/A')}. "
        "Top 3 matched universities: "
        + " | ".join(
            f"{u.name} ({u.country}, score {s:.0f}/100)"
            for s, u in top3_scored
        )
    )
    return top3, summary


def agent_visa(top3: List[University]) -> str:
    """Agent 2 — returns factual visa data for each country."""
    lines = []
    seen  = set()
    for u in top3:
        if u.country in seen:
            continue
        seen.add(u.country)
        info = VISA_INFO.get(u.country, DEFAULT_VISA_INFO)
        lines.append(
            f"{u.country}: {info['name']} | Duration: {info['duration']} | "
            f"Work rights: {info['work_rights']} | Difficulty: {info['difficulty']} | "
            f"Note: {info['note']}"
        )
    return "\n".join(lines)


def agent_finance(top3: List[University]) -> tuple[List[dict], str]:
    """Agent 3 — calculates ROI for each option (INR → USD, duration-aware)."""
    results, lines = [], []
    for u in top3:
        t        = u.tuition     or 1_660_000   # ₹20k USD fallback in INR
        lc       = u.living_cost or 996_000     # ₹12k USD fallback in INR
        duration = max(1, min(4, u.course_duration or 2))  # clamp 1–4 yrs
        roi      = _calculate_roi(t, lc, u.country, duration)
        results.append({**roi, "university": u.name, "country": u.country})
        annual_lakhs = round((t + lc) / 100000)
        total_lakhs  = round((t + lc) * duration / 100000)
        lines.append(
            f"{u.name} ({duration}-yr programme): ₹{annual_lakhs}L/yr, ₹{total_lakhs}L total "
            f"(${roi['total_cost_usd']:,.0f} USD) | "
            f"Grad salary ~${_GRAD_SALARY_USD.get(u.country, 55000):,}/yr | "
            f"5yr ROI: {roi['roi_5yr_pct']:.1f}% | Break-even: {roi['break_even_years']:.1f} yrs"
        )
    return results, "\n".join(lines)


def agent_jobs(top3: List[University]) -> tuple[List[float], str]:
    """Agent 4 — job availability scores by country."""
    scores = [_JOB_SCORE.get(u.country, 7.0) for u in top3]
    lines  = [
        f"{u.name} ({u.country}): {scores[i]:.1f}/10 — "
        f"avg grad salary ${_GRAD_SALARY_USD.get(u.country, 55000):,}/yr"
        for i, u in enumerate(top3)
    ]
    return scores, "\n".join(lines)


def agent_synthesis(
    llm,
    user: User,
    top3: List[University],
    profile_summary: str,
    visa_summary: str,
    finance_lines: str,
    jobs_lines: str,
) -> str:
    """Agent 5 — synthesis with student-facing recommendation."""
    budget_usd = _get_budget_usd(user)
    budget_str = f"${budget_usd:,.0f}/yr" if budget_usd else "not set"
    degree     = getattr(user, "preferred_degree", "Masters") or "Masters"
    field      = getattr(user, "field_of_study", "N/A") or "N/A"
    career     = getattr(user, "career_goal", "N/A") or "N/A"

    system = (
        "You are a concise, data-driven Study Abroad Counsellor for Indian students. "
        "Write a brief, practical recommendation — no marketing fluff. Use bullet points. "
        "Base every point on the data provided. Mention specific figures (costs, ROI, visa duration). "
        "Keep total under 180 words."
    )
    human = (
        "Student: {degree} in {field}, CGPA {cgpa}, budget {budget}, career goal: {career}.\n\n"
        "Profile match:\n{profile}\n\n"
        "Visa facts:\n{visa}\n\n"
        "Finance:\n{finance}\n\n"
        "Jobs:\n{jobs}\n\n"
        "Give: (1) top pick with 1 key reason, (2) 2nd and 3rd options in 1 line each, "
        "(3) one financial watch-out, (4) one action item for the student."
    )
    return _run_agent(
        llm, system, human,
        degree=degree,
        field=field,
        cgpa=user.cgpa or "N/A",
        budget=budget_str,
        career=career,
        profile=profile_summary,
        visa=visa_summary,
        finance=finance_lines,
        jobs=jobs_lines,
    )


# ── API Endpoints ─────────────────────────────────────────────────────────────

@router.get("/", response_model=DecisionResponse)
def get_decision(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Run the 5-agent Decision Dashboard pipeline."""
    llm = _make_llm(temperature=0.3)

    # Get profile-filtered candidates
    candidates = _get_candidates(db, current_user)

    if not candidates:
        return DecisionResponse(
            top_universities=[],
            synthesis="No universities found matching your profile. Please update your target countries or CGPA.",
            agent_steps=AgentSteps(
                profile_analysis="No matching universities found.",
                visa_assessment="N/A",
                finance_analysis="N/A",
                jobs_analysis="N/A",
                final_synthesis="N/A",
            ),
        )

    # ── Agent 1: Profile ──────────────────────────────────────────────────
    top3, profile_summary = agent_profile(current_user, candidates)

    # ── Agent 2: Visa (factual data, no LLM call needed) ──────────────────
    visa_summary = agent_visa(top3)

    # ── Agent 3: Finance ──────────────────────────────────────────────────
    finance_data, finance_lines = agent_finance(top3)

    # ── Agent 4: Jobs ─────────────────────────────────────────────────────
    job_scores, jobs_lines = agent_jobs(top3)

    # ── Agent 5: Synthesis ────────────────────────────────────────────────
    synthesis = agent_synthesis(
        llm, current_user, top3,
        profile_summary, visa_summary, finance_lines, jobs_lines,
    )

    # ── Build structured response ─────────────────────────────────────────
    uni_options: List[UniversityOption] = []
    for i, u in enumerate(top3):
        fd  = finance_data[i]
        ms  = calculate_score(current_user, u)   # 0–100

        # Normalise all scores to 0–1
        conf_profile = round(ms / 100, 3)

        roi = fd["roi_5yr_pct"]
        be  = fd["break_even_years"]
        if roi >= 150:
            conf_finance = 0.95
        elif roi >= 100:
            conf_finance = 0.80
        elif roi >= 50:
            conf_finance = 0.65
        elif roi >= 0:
            conf_finance = 0.45
        else:
            conf_finance = 0.20
        if be > 8:
            conf_finance = max(0.10, conf_finance - 0.20)
        conf_finance = round(conf_finance, 3)

        conf_jobs = round(job_scores[i] / 10.0, 3)

        # Visa confidence from factual difficulty rating
        visa_difficulty = VISA_INFO.get(u.country, DEFAULT_VISA_INFO).get("difficulty", "Moderate")
        conf_visa = {"Easy": 0.90, "Moderate": 0.70, "Hard": 0.50}.get(visa_difficulty, 0.68)
        conf_visa = round(conf_visa, 3)

        conf_overall = round(
            conf_profile * 0.35 + conf_finance * 0.30 +
            conf_jobs    * 0.20 + conf_visa    * 0.15,
            3,
        )

        tuition_usd     = (u.tuition or 0)     * INR_TO_USD
        living_cost_usd = (u.living_cost or 0) * INR_TO_USD

        uni_options.append(UniversityOption(
            name=u.name,
            country=u.country,
            ranking=u.ranking,
            match_score=round(ms / 100, 3),   # ← normalised 0–1
            tuition_usd=round(tuition_usd, 0),
            living_cost_usd=round(living_cost_usd, 0),
            total_cost_usd=fd["annual_cost_usd"],  # annual cost for display
            roi_5yr_pct=fd["roi_5yr_pct"],
            break_even_years=fd["break_even_years"],
            job_availability_score=job_scores[i],
            visa_assessment=_visa_blurb(u.country),
            confidence_profile=conf_profile,
            confidence_finance=conf_finance,
            confidence_jobs=conf_jobs,
            confidence_visa=conf_visa,
            confidence_overall=conf_overall,
        ))

    pipeline_conf = uni_options[0].confidence_overall if uni_options else 0.0

    return DecisionResponse(
        top_universities=uni_options,
        synthesis=synthesis,
        confidence_score=pipeline_conf,
        agent_steps=AgentSteps(
            profile_analysis=profile_summary,
            visa_assessment=visa_summary,
            finance_analysis=finance_lines,
            jobs_analysis=jobs_lines,
            final_synthesis=synthesis,
        ),
    )


@router.get("/simple", response_model=SimpleDecisionResponse)
def get_simple_decision(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Legacy single-university recommendation."""
    candidates = _get_candidates(db, current_user)

    best_uni, best_score = None, -1.0
    for uni in candidates:
        s = calculate_score(current_user, uni)
        if s > best_score:
            best_score, best_uni = s, uni

    if not best_uni:
        return SimpleDecisionResponse(
            best_option="General Study Abroad Advice",
            explanation="We need more profile data to recommend a specific university.",
        )

    llm    = _make_llm(temperature=0.3)
    budget_usd = _get_budget_usd(current_user)
    system = "You are a concise, factual study abroad counsellor for Indian students."
    human  = (
        "Student: CGPA {cgpa}, budget ${budget}/yr, field {field}, "
        "target countries {targets}. "
        "Best match: {uni} in {country} "
        "(tuition ~${tuition_usd:,.0f}/yr, living ~${living_usd:,.0f}/yr, match score {score:.0f}/100). "
        "Write 2 paragraphs: why this is their best option, and one practical next step. "
        "Be specific with figures. Keep under 120 words."
    )
    try:
        explanation = _run_agent(
            llm, system, human,
            cgpa=current_user.cgpa or "N/A",
            budget=f"{budget_usd:,.0f}" if budget_usd else "N/A",
            field=getattr(current_user, "field_of_study", "N/A") or "N/A",
            targets=", ".join(current_user.target_countries or []),
            uni=best_uni.name,
            country=best_uni.country,
            tuition_usd=(best_uni.tuition or 0) * INR_TO_USD,
            living_usd=(best_uni.living_cost or 0) * INR_TO_USD,
            score=best_score,
        )
    except Exception as e:
        explanation = f"LLM generation error: {e}"

    return SimpleDecisionResponse(best_option=best_uni.name, explanation=explanation)
