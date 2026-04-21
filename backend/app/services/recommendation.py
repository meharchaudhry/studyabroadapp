"""
Recommendation Engine v2
========================
Multi-factor scoring for university recommendations.

Scoring weights:
  Subject match          30 %   (most important — student's field vs university subjects)
  CGPA eligibility       20 %
  Budget fit             20 %
  QS Ranking quality     15 %
  Country preference     10 %
  IELTS eligibility       5 %

Scores are gracefully degraded when profile data is missing so that
students with incomplete profiles still get sensible recommendations
rather than all zeros.
"""

from typing import Optional
from app.models.user import User
from app.models.university import University

# ── Field → keywords that appear in pipe-separated university subject string ──
FIELD_KEYWORDS: dict[str, list[str]] = {
    "computer science":   ["Computer Science", "Computing", "Software", "Informatics", "CS", "Data Science", "Machine Learning"],
    "engineering":        ["Engineering", "Mechanical", "Electrical", "Civil", "Chemical", "Aerospace"],
    "data science":       ["Data Science", "Data Analytics", "Statistics", "Machine Learning", "AI", "Computer Science"],
    "business":           ["Business", "Management", "MBA", "Commerce", "Administration"],
    "finance":            ["Finance", "Accounting", "Economics", "Banking", "Financial"],
    "medicine":           ["Medicine", "Medical", "Health", "Pharmacy", "Nursing", "Biomedical"],
    "law":                ["Law", "Legal", "Jurisprudence"],
    "arts":               ["Arts", "Humanities", "Liberal Arts", "Design", "Media", "History", "Philosophy"],
    "architecture":       ["Architecture", "Urban", "Built Environment"],
    "psychology":         ["Psychology", "Cognitive", "Neuroscience", "Behavioural"],
    "physics":            ["Physics", "Mathematics", "Maths", "Mathematical", "Applied Mathematics"],
    "mathematics":        ["Mathematics", "Maths", "Applied Mathematics", "Statistics", "Physics"],
    "economics":          ["Economics", "Econometrics", "Political Economy", "Finance", "Business"],
    "environmental":      ["Environmental", "Sustainability", "Climate", "Ecology", "Earth"],
    "public health":      ["Public Health", "Epidemiology", "Global Health", "Medicine"],
    "education":          ["Education", "Teaching"],
    "social science":     ["Social Science", "Sociology", "Anthropology", "Political Science", "International Relations"],
}


def _subject_match_score(field_of_study: str, uni_subject: str) -> float:
    """
    Returns a 0.0–1.0 score indicating how well the student's field
    matches the university's pipe-separated subject list.
    """
    if not field_of_study or not uni_subject:
        return 0.5  # neutral — don't penalise missing data

    fos      = field_of_study.lower().strip()
    subjects = [s.strip() for s in uni_subject.split("|")]
    subj_lo  = [s.lower() for s in subjects]

    # Direct substring match anywhere in subject list
    for s in subj_lo:
        if fos in s or s in fos:
            return 1.0

    # Keyword-based match
    keywords = []
    for canonical, kws in FIELD_KEYWORDS.items():
        if canonical in fos or any(k.lower() in fos for k in kws):
            keywords.extend([k.lower() for k in kws])
            break

    if keywords:
        for s in subj_lo:
            if any(k in s for k in keywords):
                return 1.0
        # Partial — some overlap
        overlap = sum(1 for k in keywords if any(k in s for s in subj_lo))
        if overlap > 0:
            return 0.6

    return 0.2   # no match but keep a small score so uni still appears


# ── Country-level salary + job data ───────────────────────────────────────────

GRAD_SALARY_USD: dict[str, int] = {
    "United States":  78000,
    "United Kingdom": 54000,
    "Canada":         62000,
    "Australia":      64000,
    "Germany":        58000,
    "France":         50000,
    "Netherlands":    55000,
    "Ireland":        62000,
    "New Zealand":    56000,
    "Singapore":      68000,
    "Japan":          46000,
    "Sweden":         54000,
    "Norway":         64000,
    "Denmark":        60000,
    "Finland":        52000,
    "UAE":            68000,
    "Portugal":       40000,
    "Italy":          42000,
    "Spain":          44000,
    "South Korea":    50000,
    "Switzerland":    82000,
    "Belgium":        52000,
    "Poland":         36000,
}

JOB_SCORE: dict[str, float] = {
    "United States":  9.0,
    "United Kingdom": 8.5,
    "Canada":         8.5,
    "Australia":      8.0,
    "Germany":        8.0,
    "France":         7.0,
    "Netherlands":    7.5,
    "Ireland":        8.0,
    "New Zealand":    7.5,
    "Singapore":      8.5,
    "Japan":          7.0,
    "Sweden":         7.5,
    "Norway":         7.5,
    "Denmark":        7.5,
    "Finland":        7.0,
    "UAE":            8.0,
    "Portugal":       6.5,
    "Italy":          6.5,
    "Spain":          6.5,
    "South Korea":    7.0,
    "Switzerland":    7.5,
    "Belgium":        7.0,
    "Poland":         6.5,
}

# Also keep old aliases for backwards compat
for _old, _new in [("UK","United Kingdom"),("USA","United States"),("US","United States")]:
    if _new in GRAD_SALARY_USD:
        GRAD_SALARY_USD.setdefault(_old, GRAD_SALARY_USD[_new])
        JOB_SCORE.setdefault(_old, JOB_SCORE[_new])


# ── Core scoring ───────────────────────────────────────────────────────────────

def calculate_score(user: User, uni: University) -> float:
    score, _ = _score_with_reasons(user, uni)
    return score


def _score_with_reasons(user: User, uni: University) -> tuple[float, dict]:
    score   = 0.0
    reasons = {}

    # ── 1. Subject / Field match (30%) ────────────────────────────────────────
    field   = getattr(user, "field_of_study", None)
    sub_scr = _subject_match_score(field or "", uni.subject or "")
    score  += 0.30 * sub_scr

    if not field:
        reasons["field"] = "Add your field of study for programme-level matching."
    elif sub_scr >= 1.0:
        reasons["field"] = (
            f"Strong match — {uni.name} offers programmes directly aligned with {field}."
        )
    elif sub_scr >= 0.6:
        reasons["field"] = (
            f"Partial match — {uni.name} has some overlap with {field}. Explore their interdisciplinary options."
        )
    else:
        reasons["field"] = (
            f"{uni.name}'s primary subjects don't closely align with {field}. "
            "Check their full programme catalogue for elective options."
        )

    # ── 2. CGPA eligibility (20%) ─────────────────────────────────────────────
    cgpa = getattr(user, "cgpa", None)
    if cgpa and uni.requirements_cgpa:
        if cgpa >= uni.requirements_cgpa:
            excess  = cgpa - uni.requirements_cgpa
            factor  = min(0.20, 0.14 + (excess / 10.0) * 0.06)
            score  += factor
            reasons["cgpa"] = (
                f"Your CGPA {cgpa:.1f} exceeds the minimum {uni.requirements_cgpa:.1f} "
                f"by {excess:.1f} — you're a competitive applicant."
            )
        else:
            gap    = uni.requirements_cgpa - cgpa
            factor = max(0.0, 0.07 - gap * 0.035)
            score += factor
            reasons["cgpa"] = (
                f"Your CGPA {cgpa:.1f} is {gap:.1f} below the minimum {uni.requirements_cgpa:.1f}. "
                "A strong SOP and recommendation letters could compensate."
            )
    elif cgpa:
        score += (cgpa / 10.0) * 0.14
        reasons["cgpa"] = (
            f"No explicit CGPA requirement listed — your {cgpa:.1f} is competitive for most programmes."
        )
    else:
        score += 0.07   # give partial credit so unprofile'd users still get results
        reasons["cgpa"] = "Add your CGPA to your profile for eligibility assessment."

    # ── 3. Budget fit (20%) ───────────────────────────────────────────────────
    total_cost = (uni.tuition or 0) + (uni.living_cost or 0)
    budget     = getattr(user, "budget", None) or getattr(user, "budget_inr", None)

    # Convert INR budget to USD if it looks like INR (> 500,000)
    if budget and budget > 500_000:
        budget = budget / 83  # approx INR→USD

    if budget and total_cost > 0:
        ratio = total_cost / budget
        if ratio <= 1.0:
            score += 0.20
            reasons["budget"] = (
                f"Within budget — total cost ${total_cost:,.0f}/yr vs your "
                f"${budget:,.0f}/yr budget (${budget - total_cost:,.0f} to spare)."
            )
        elif ratio <= 1.20:
            score += 0.12
            reasons["budget"] = (
                f"Slightly over budget by ${total_cost - budget:,.0f}/yr — "
                "a scholarship or part-time work could bridge the gap."
            )
        elif ratio <= 1.40:
            score += 0.05
            reasons["budget"] = (
                f"Cost ${total_cost:,.0f}/yr is 20–40% above your budget. "
                "Consider a student loan or partial scholarship."
            )
        else:
            reasons["budget"] = (
                f"Cost ${total_cost:,.0f}/yr significantly exceeds your budget of ${budget:,.0f}/yr."
            )
    elif not total_cost:
        score += 0.10
        reasons["budget"] = "Cost data unavailable — check the university website."
    else:
        score += 0.08   # give some credit, don't zero-out unprofile'd users
        reasons["budget"] = "Set a budget in your profile for financial fit scoring."

    # ── 4. QS Ranking quality (15%) ───────────────────────────────────────────
    rank = uni.qs_subject_ranking or uni.ranking
    if rank:
        if rank <= 10:
            score += 0.15
            reasons["ranking"] = f"World-class — QS #{rank} globally. Exceptional research and employer recognition."
        elif rank <= 50:
            score += 0.13
            reasons["ranking"] = f"Elite university — QS #{rank}, highly respected by global employers."
        elif rank <= 100:
            score += 0.10
            reasons["ranking"] = f"Top-100 (QS #{rank}) with strong research output and graduate outcomes."
        elif rank <= 200:
            score += 0.07
            reasons["ranking"] = f"Well-ranked at QS #{rank} with good graduate employment rates."
        elif rank <= 500:
            score += 0.04
            reasons["ranking"] = f"Reputable institution ranked QS #{rank} with strong industry ties."
        else:
            score += 0.02
            reasons["ranking"] = f"QS #{rank} — research the specific programme's reputation."
    else:
        score += 0.05
        reasons["ranking"] = "Ranking not available — research programme-specific reputation."

    # ── 5. Country preference (10%) ───────────────────────────────────────────
    target = getattr(user, "target_countries", None) or []
    # Normalise target countries for comparison
    target_lo = [c.lower().strip() for c in target]
    uni_country_lo = (uni.country or "").lower().strip()

    in_target = (
        uni_country_lo in target_lo
        or any(t in uni_country_lo or uni_country_lo in t for t in target_lo)
    )

    if in_target:
        score += 0.10
        reasons["country"] = f"{uni.country} is one of your target destinations — great alignment!"
    elif target:
        reasons["country"] = (
            f"{uni.country} is outside your current shortlist "
            f"({', '.join(target[:3])}), but worth exploring."
        )
    else:
        score += 0.05   # partial credit for unprofile'd users
        reasons["country"] = "Set target countries in your profile for geographic preference scoring."

    # ── 6. IELTS eligibility (5%) ─────────────────────────────────────────────
    ielts = getattr(user, "english_score", None)
    if ielts and uni.ielts:
        if ielts >= uni.ielts:
            score += min(0.05, 0.03 + (ielts - uni.ielts) * 0.01)
            reasons["ielts"] = f"Your IELTS {ielts:.1f} meets the {uni.ielts:.1f} requirement."
        else:
            gap = uni.ielts - ielts
            reasons["ielts"] = (
                f"Your IELTS {ielts:.1f} is {gap:.1f} bands below the required {uni.ielts:.1f}. "
                "Consider retaking the test."
            )
    elif ielts:
        score += 0.03
        reasons["ielts"] = f"No IELTS requirement on file — your {ielts:.1f} should be acceptable."
    else:
        score += 0.02
        reasons["ielts"] = "Add your IELTS/TOEFL score for language eligibility scoring."

    return round(min(score, 1.0), 3), reasons


def explain_match(user: User, uni: University) -> dict:
    score, reasons = _score_with_reasons(user, uni)
    salary    = GRAD_SALARY_USD.get(uni.country, 55000)
    job_score = JOB_SCORE.get(uni.country, 7.0)

    total_cost = (uni.tuition or 0) + (uni.living_cost or 0)
    if total_cost > 0:
        net_salary   = salary * 0.75
        annual_repay = net_salary * 0.30
        break_even   = round(total_cost / annual_repay, 1) if annual_repay > 0 else None
        roi_5yr      = round(((net_salary * 5) - total_cost) / total_cost * 100, 1)
    else:
        break_even = roi_5yr = None

    return {
        "match_score": score,
        "reasons":     reasons,
        "financial": {
            "total_annual_cost_usd":     total_cost or None,
            "estimated_grad_salary_usd": salary,
            "roi_5yr_pct":               roi_5yr,
            "break_even_years":          break_even,
            "job_market_score":          job_score,
        },
        "summary": _build_summary(score, reasons),
    }


def _build_summary(score: float, reasons: dict) -> str:
    pct = round(score * 100)
    if pct >= 80:
        label = "Excellent match"
    elif pct >= 65:
        label = "Good match"
    elif pct >= 50:
        label = "Moderate match"
    else:
        label = "Worth exploring"

    positives = [
        v for k, v in reasons.items()
        if any(w in v for w in ["exceeds", "within", "Strong", "Elite", "World", "target", "meets", "spare", "aligned"])
    ]
    snippet = positives[0] if positives else "Review the factor breakdown for details."
    return f"{label} ({pct}%). {snippet}"
