from typing import Any, Dict, List


def _safe_profile(profile: Dict[str, Any] | None) -> Dict[str, Any]:
    return profile or {}


def generate_checklist(country: str, profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    p = _safe_profile(profile)
    degree = p.get("preferred_degree") or p.get("current_degree") or "your chosen program"
    field = p.get("field_of_study") or "your field"

    base_items = [
        "Valid passport (with enough validity)",
        "University offer/admission letter",
        "Academic transcripts and certificates",
        "Proof of funds and bank statements",
        "Statement of Purpose",
        "Language test score report (IELTS/TOEFL/PTE)",
        "Passport-size photographs",
    ]

    return {
        "country": country,
        "program_context": f"{degree} in {field}",
        "checklist": base_items,
        "notes": [
            "Always verify with the official embassy/immigration site before final submission.",
            "Keep both digital and physical copies of all documents.",
        ],
    }


def generate_timeline(intake: str = "Fall", countries: List[str] | None = None, profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    _ = _safe_profile(profile)
    countries = countries or []
    target = ", ".join(countries) if countries else "your shortlisted countries"

    timeline = [
        {"month": "Month 1", "task": "Finalize target universities and eligibility checks."},
        {"month": "Month 2", "task": "Prepare tests, SOP, LOR, and core documents."},
        {"month": "Month 3", "task": "Submit university applications and track deadlines."},
        {"month": "Month 4", "task": "Review admits, compare ROI, and finalize target school."},
        {"month": "Month 5", "task": "Start visa documentation and financial proof preparation."},
        {"month": "Month 6", "task": "File visa, arrange housing, and complete pre-departure tasks."},
    ]

    return {
        "intake": intake,
        "countries": countries,
        "focus": f"Application plan for {target}",
        "timeline": timeline,
    }


def analyze_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    p = _safe_profile(profile)

    strengths: List[str] = []
    gaps: List[str] = []
    actions: List[str] = []

    if p.get("cgpa"):
        strengths.append("CGPA is provided for eligibility screening.")
    else:
        gaps.append("CGPA missing.")
        actions.append("Add CGPA to improve recommendation quality.")

    if p.get("budget") or p.get("budget_inr"):
        strengths.append("Budget information available for ROI filtering.")
    else:
        gaps.append("Budget missing.")
        actions.append("Add budget to avoid unrealistic recommendations.")

    if p.get("target_countries"):
        strengths.append("Target countries are set.")
    else:
        gaps.append("Target countries not set.")
        actions.append("Add 3-5 target countries to narrow university matching.")

    if p.get("english_score") or p.get("toefl_score"):
        strengths.append("Language proficiency score is available.")
    else:
        gaps.append("English test score missing.")
        actions.append("Add IELTS/TOEFL/PTE score or planned test date.")

    return {
        "strengths": strengths,
        "gaps": gaps,
        "recommended_actions": actions,
        "overall": "Profile is strong" if len(gaps) <= 1 else "Profile needs a few improvements",
    }


def ai_coach_chat(message: str, profile: Dict[str, Any] | None = None, history: List[Dict[str, Any]] | None = None) -> str:
    _ = _safe_profile(profile)
    history = history or []
    msg = (message or "").strip()
    if not msg:
        return "Ask me anything about university shortlisting, visa preparation, funding, or job planning."

    if "visa" in msg.lower():
        return "Start with the official checklist for your target country, then prepare funds proof, admission documents, and language scores in parallel."
    if "scholar" in msg.lower():
        return "Shortlist scholarships by country and university first, then align your SOP and achievements with each scholarship rubric."
    if "job" in msg.lower():
        return "Prioritize countries with stronger post-study work rights and begin internship applications 3-4 months before arrival."

    return "Focus on three tracks in parallel: admissions documents, finances, and visa readiness. I can help you break any of these into step-by-step actions."


def generate_sop_outline(profile: Dict[str, Any] | None = None, university: str = "", program: str = "") -> str:
    p = _safe_profile(profile)
    field = p.get("field_of_study") or "your chosen field"
    uni = university or "the target university"
    prog = program or "the selected program"

    return (
        f"SOP Outline for {prog} at {uni}\n\n"
        "1. Introduction and motivation\n"
        f"- Why {field} interests you and your long-term goals.\n\n"
        "2. Academic background\n"
        "- Relevant coursework, projects, and achievements.\n\n"
        "3. Professional exposure\n"
        "- Internships/work experience and key impact.\n\n"
        "4. Why this university and program\n"
        "- Faculty, curriculum fit, labs, and outcomes.\n\n"
        "5. Career plan\n"
        "- Short-term and long-term goals after graduation.\n\n"
        "6. Conclusion\n"
        "- Reinforce fit, readiness, and contribution."
    )