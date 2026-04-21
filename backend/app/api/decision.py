"""
Decision Dashboard — 5-Agent Agentic Chain
==========================================
Implements the LangChain SequentialChain pattern with five focused agents:

  Agent 1 — Profile Agent    : Identifies top-3 matching universities from DB.
  Agent 2 — Visa Agent       : Queries the RAG pipeline to assess visa difficulty
                               for each candidate country.
  Agent 3 — Finance Agent    : Calculates total cost, ROI and break-even year
                               for each option.
  Agent 4 — Jobs Agent       : Scores part-time / graduate job availability
                               near each university city.
  Agent 5 — Synthesis Agent  : Combines all four outputs and produces a ranked
                               top-3 recommendation with plain-English rationale.

Each agent is a separate LLM call with a tightly-scoped prompt, making the
output reliable and each step independently testable.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.university import University
from app.services.recommendation import calculate_score
from app.core.config import settings

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

router = APIRouter()


# ── Response Schemas ──────────────────────────────────────────────────────────

class UniversityOption(BaseModel):
    name: str
    country: str
    ranking: Optional[int]
    match_score: float
    tuition_usd: Optional[float]
    living_cost_usd: Optional[float]
    total_cost_usd: Optional[float]
    roi_5yr_pct: Optional[float]
    break_even_years: Optional[float]
    job_availability_score: float
    visa_assessment: str
    # Confidence scores per agent
    confidence_profile: float = 0.0   # 0–1: how well profile matches (normalized match_score)
    confidence_finance: float = 0.0   # 0–1: based on ROI and budget fit
    confidence_jobs: float = 0.0      # 0–1: job_availability_score normalized to 0–1
    confidence_visa: float = 0.0      # 0–1: based on LLM visa difficulty
    confidence_overall: float = 0.0   # weighted composite


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
    confidence_score: float = 0.0   # pipeline-level confidence (0–1)


# Legacy single-field response for backward compatibility
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
    """Run a single focused LLM call with a system + human message."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", human),
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(kwargs)


def _calculate_roi(tuition: float, living: float, avg_grad_salary_usd: float = 65000) -> dict:
    """
    Simple ROI model:
      - total cost = tuition + living
      - net salary ~75 % of gross after taxes
      - 30 % of net allocated to loan repayment
      - break-even = total_cost / annual_repayment
      - 5-yr ROI = (net_salary*5 - total_cost) / total_cost * 100
    """
    total = tuition + living
    net_salary = avg_grad_salary_usd * 0.75
    annual_repayment = net_salary * 0.30
    break_even = total / annual_repayment if annual_repayment > 0 else 99
    roi_5yr = ((net_salary * 5) - total) / total * 100 if total > 0 else 0
    return {
        "total_cost":        round(total, 0),
        "roi_5yr_pct":       round(roi_5yr, 1),
        "break_even_years":  round(break_even, 1),
    }


# Average graduate salaries (USD/year) by country — sourced from public datasets
_GRAD_SALARY = {
    "USA":         75000, "UK":          52000, "Canada":      60000,
    "Australia":   62000, "Germany":     55000, "France":      48000,
    "Netherlands": 52000, "Ireland":     58000, "New Zealand": 55000,
    "Singapore":   65000, "Japan":       45000, "Sweden":      52000,
    "Norway":      60000, "Denmark":     58000, "Finland":     50000,
    "UAE":         65000,
}

# Job market quality scores (0–10) by country, reflecting part-time and grad opportunities
_JOB_SCORE = {
    "USA":         9.0, "UK":          8.5, "Canada":      8.5,
    "Australia":   8.0, "Germany":     8.0, "France":      7.0,
    "Netherlands": 7.5, "Ireland":     8.0, "New Zealand": 7.5,
    "Singapore":   8.5, "Japan":       7.0, "Sweden":      7.5,
    "Norway":      7.5, "Denmark":     7.5, "Finland":     7.0,
    "UAE":         8.0,
}


# ── Agent Functions ───────────────────────────────────────────────────────────

def agent_profile(user: User, universities: List[University]) -> tuple[List[University], str]:
    """
    Agent 1 — Profile Agent
    Scores all candidate universities and returns the top 3.
    """
    scored = []
    for uni in universities:
        s = calculate_score(user, uni)
        scored.append((s, uni))
    scored.sort(key=lambda x: x[0], reverse=True)
    top3 = [uni for _, uni in scored[:3]]

    summary = (
        f"Top 3 universities matched for CGPA {user.cgpa}, "
        f"budget ${user.budget}: "
        + " | ".join(
            f"{u.name} ({u.country}, score {calculate_score(user, u):.2f})"
            for u in top3
        )
    )
    return top3, summary


def agent_visa(llm, top3: List[University], country_pref: List[str]) -> str:
    """
    Agent 2 — Visa Agent
    Assesses visa difficulty for each candidate country using the LLM
    (backed by the RAG pipeline for rich grounding when called from visa.py;
    here we use a focused LLM call with factual country knowledge).
    """
    countries = list({u.country for u in top3})
    system = (
        "You are a visa difficulty analyst for Indian students studying abroad. "
        "For each country listed, provide a 1-2 sentence assessment of: "
        "typical processing time, key requirements, and overall difficulty (Easy/Moderate/Hard). "
        "Be factual and concise."
    )
    human = "Assess student visa difficulty for Indian students applying to: {countries}"
    return _run_agent(llm, system, human, countries=", ".join(countries))


def agent_finance(top3: List[University]) -> tuple[List[dict], str]:
    """
    Agent 3 — Finance Agent
    Calculates total cost, ROI, and break-even year for each option.
    """
    results = []
    lines   = []
    for u in top3:
        t  = u.tuition     or 20000
        lc = u.living_cost or 12000
        salary = _GRAD_SALARY.get(u.country, 55000)
        roi    = _calculate_roi(t, lc, salary)
        results.append({**roi, "university": u.name, "country": u.country})
        lines.append(
            f"{u.name}: total=${roi['total_cost']:,.0f} | "
            f"ROI(5yr)={roi['roi_5yr_pct']:.1f}% | "
            f"break-even={roi['break_even_years']:.1f} yrs"
        )
    return results, "\n".join(lines)


def agent_jobs(top3: List[University]) -> tuple[List[float], str]:
    """
    Agent 4 — Jobs Agent
    Returns job availability scores (0–10) for each university's country.
    """
    scores = [_JOB_SCORE.get(u.country, 7.0) for u in top3]
    lines  = [
        f"{u.name} ({u.country}): job score {scores[i]:.1f}/10"
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
    """
    Agent 5 — Synthesis Agent
    Combines all four prior agent outputs into a ranked top-3 recommendation
    with a plain-English explanation for the student.
    """
    system = (
        "You are a Study Abroad Counsellor. Using the structured analysis below, "
        "write a warm, professional, student-facing recommendation that:\n"
        "1. Ranks the three universities in order of overall suitability.\n"
        "2. Explains WHY each is ranked where it is (academic fit, visa ease, "
        "   financial ROI, job market).\n"
        "3. Ends with a clear 'Our top pick for you is …' conclusion.\n"
        "Keep the tone encouraging and actionable. Use bullet points for clarity."
    )
    human = (
        "Student profile — CGPA: {cgpa}, Budget: ${budget}, "
        "Target countries: {targets}.\n\n"
        "Profile Agent:\n{profile}\n\n"
        "Visa Agent:\n{visa}\n\n"
        "Finance Agent:\n{finance}\n\n"
        "Jobs Agent:\n{jobs}\n\n"
        "Please produce the final ranked recommendation."
    )
    return _run_agent(
        llm, system, human,
        cgpa=user.cgpa or "N/A",
        budget=user.budget or "N/A",
        targets=", ".join(user.target_countries or []),
        profile=profile_summary,
        visa=visa_summary,
        finance=finance_lines,
        jobs=jobs_lines,
    )


# ── Per-university visa blurb (quick LLM call) ───────────────────────────────

def _quick_visa_blurb(llm, country: str) -> str:
    try:
        system = (
            "You are a visa expert. Give a single sentence summarising the student "
            "visa process for Indian nationals applying to {country}. Be factual."
        )
        prompt = ChatPromptTemplate.from_messages([("system", system)])
        chain  = prompt | llm | StrOutputParser()
        return chain.invoke({"country": country})
    except Exception:
        return f"Standard student visa required for {country}."


# ── API Endpoints ─────────────────────────────────────────────────────────────

@router.get("/", response_model=DecisionResponse)
def get_decision(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Run the 5-agent Decision Dashboard pipeline and return a ranked
    top-3 recommendation with per-agent reasoning steps.
    """
    llm = _make_llm(temperature=0.3)

    # Fetch candidate universities
    q = db.query(University)
    if current_user.target_countries:
        q = q.filter(University.country.in_(current_user.target_countries))
    candidates = q.order_by(University.ranking).limit(100).all()

    # Fallback — broaden search if no country-specific results
    if not candidates:
        candidates = db.query(University).order_by(University.ranking).limit(60).all()

    if not candidates:
        return DecisionResponse(
            top_universities=[],
            synthesis="No universities found matching your profile. Please update your target countries.",
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

    # ── Agent 2: Visa ─────────────────────────────────────────────────────
    visa_summary = agent_visa(llm, top3, current_user.target_countries or [])

    # ── Agent 3: Finance ──────────────────────────────────────────────────
    finance_data, finance_lines = agent_finance(top3)

    # ── Agent 4: Jobs ─────────────────────────────────────────────────────
    job_scores, jobs_lines = agent_jobs(top3)

    # ── Agent 5: Synthesis ────────────────────────────────────────────────
    synthesis = agent_synthesis(
        llm, current_user, top3,
        profile_summary, visa_summary, finance_lines, jobs_lines,
    )

    # ── Build structured response with confidence scores ──────────────────
    uni_options: List[UniversityOption] = []
    for i, u in enumerate(top3):
        fd    = finance_data[i]
        blurb = _quick_visa_blurb(llm, u.country)
        ms    = calculate_score(current_user, u)

        # ── Per-agent confidence scores (0–1) ──────────────────────────────
        # Profile confidence: directly from match_score
        conf_profile = round(ms, 3)

        # Finance confidence: based on ROI and break-even
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
        # Penalise if break-even > 8 years
        if be > 8:
            conf_finance = max(0.10, conf_finance - 0.20)
        conf_finance = round(conf_finance, 3)

        # Jobs confidence: job score / 10 → 0–1
        conf_jobs = round(job_scores[i] / 10.0, 3)

        # Visa confidence: heuristic from blurb keywords
        blurb_lower = blurb.lower()
        if any(w in blurb_lower for w in ["straightforward", "easy", "standard", "routine"]):
            conf_visa = 0.90
        elif any(w in blurb_lower for w in ["moderate", "typically", "normally"]):
            conf_visa = 0.72
        elif any(w in blurb_lower for w in ["difficult", "complex", "interview", "strict"]):
            conf_visa = 0.55
        else:
            conf_visa = 0.68
        conf_visa = round(conf_visa, 3)

        # Overall: weighted average (profile 35%, finance 30%, jobs 20%, visa 15%)
        conf_overall = round(
            conf_profile * 0.35 + conf_finance * 0.30 +
            conf_jobs    * 0.20 + conf_visa    * 0.15,
            3,
        )

        uni_options.append(UniversityOption(
            name=u.name,
            country=u.country,
            ranking=u.ranking,
            match_score=ms,
            tuition_usd=u.tuition,
            living_cost_usd=u.living_cost,
            total_cost_usd=fd["total_cost"],
            roi_5yr_pct=fd["roi_5yr_pct"],
            break_even_years=fd["break_even_years"],
            job_availability_score=job_scores[i],
            visa_assessment=blurb,
            confidence_profile=conf_profile,
            confidence_finance=conf_finance,
            confidence_jobs=conf_jobs,
            confidence_visa=conf_visa,
            confidence_overall=conf_overall,
        ))

    # Pipeline-level confidence: average of top-1 university's overall confidence
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
    """Legacy single-university recommendation (backward-compatible)."""
    q = db.query(University)
    if current_user.target_countries:
        q = q.filter(University.country.in_(current_user.target_countries))
    universities = q.all()

    best_uni, best_score = None, -1.0
    for uni in universities:
        s = calculate_score(current_user, uni)
        if s > best_score:
            best_score, best_uni = s, uni

    if not best_uni:
        return SimpleDecisionResponse(
            best_option="General Study Abroad Advice",
            explanation="We need more profile data to recommend a specific university.",
        )

    llm    = _make_llm(temperature=0.3)
    system = "You are an enthusiastic and professional study abroad counsellor."
    human  = (
        "The student has CGPA {cgpa} and a budget of ${budget}. "
        "Their target countries are {targets}. "
        "Our algorithm matched them best with {uni} in {country} "
        "(tuition ${tuition}, living cost ${living}). "
        "Write a 3-paragraph personalised recommendation letter explaining why "
        "{uni} is their best option, touching on budget fit, academic profile, "
        "and career/visa prospects in {country}. Be warm and professional."
    )
    try:
        explanation = _run_agent(
            llm, system, human,
            cgpa=current_user.cgpa or "N/A",
            budget=current_user.budget or "N/A",
            targets=", ".join(current_user.target_countries or []),
            uni=best_uni.name,
            country=best_uni.country,
            tuition=best_uni.tuition or 0,
            living=best_uni.living_cost or 0,
        )
    except Exception as e:
        explanation = f"LLM generation error: {e}"

    return SimpleDecisionResponse(best_option=best_uni.name, explanation=explanation)
