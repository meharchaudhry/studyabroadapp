"""
Recommendation Engine v4 — Personalised University Matching
============================================================
Every student gets a unique ranked list. Two students with different
profiles will see completely different universities at the top.

Scoring is out of 100 points across 11 factors:

  1. Subject / field match          28 pts  ← biggest differentiator
  2. Budget eligibility             18 pts  ← hard cutoff at 2× budget
  3. Academic eligibility (CGPA)    12 pts  ← hard cutoff for large gaps
  4. Ranking preference alignment    8 pts  ← respects user's own preference
  5. Country preference              8 pts  ← target countries get full score
  6. English language eligibility    5 pts
  7. Career outcome alignment        8 pts  ← NEW: career_goal × country job market
  8. Study environment fit           5 pts  ← NEW: study_priority × uni type
  9. Safety / match / reach tier     3 pts  ← NEW: CGPA buffer above requirement
 10. Profile-specific bonus          up to 3 pts  (MBA work-exp, PhD research, etc.)
 11. Scholarship / post-work bonus   up to 2 pts

Hard exclusion rules (score clamped to ≤ 8):
  • Total cost > 2× user's annual budget
  • CGPA more than 2.0 points below the requirement
  • Ranking requirement is "Top 50" but uni is ranked > 200

Degree-type routing:
  • MBA  → business schools scored higher; GMAT counts
  • PhD  → research output (top ranking) weighted more; tuition less
  • MS/Masters → balanced STEM/subject focus
  • Bachelors → more permissive eligibility
"""

from app.models.user import User
from app.models.university import University

# ── Country metadata ──────────────────────────────────────────────────────────

GRAD_SALARY_USD: dict[str, int] = {
    "United States": 78000, "United Kingdom": 54000, "Canada": 62000,
    "Australia": 64000, "Germany": 58000, "France": 50000,
    "Netherlands": 55000, "Ireland": 62000, "New Zealand": 56000,
    "Singapore": 68000, "Japan": 46000, "Sweden": 54000,
    "Norway": 64000, "Denmark": 60000, "Finland": 52000,
    "UAE": 68000, "Portugal": 40000, "Italy": 42000,
    "Spain": 44000, "South Korea": 50000, "Switzerland": 82000,
    "Belgium": 52000, "Poland": 36000,
    # Legacy aliases
    "UK": 54000, "USA": 78000, "US": 78000,
}

JOB_SCORE: dict[str, float] = {
    "United States": 9.0, "United Kingdom": 8.5, "Canada": 8.5,
    "Australia": 8.0, "Germany": 8.0, "France": 7.0,
    "Netherlands": 7.5, "Ireland": 8.0, "New Zealand": 7.5,
    "Singapore": 8.5, "Japan": 7.0, "Sweden": 7.5,
    "Norway": 7.5, "Denmark": 7.5, "Finland": 7.0,
    "UAE": 8.0, "Portugal": 6.5, "Italy": 6.5, "Spain": 6.5,
    "South Korea": 7.0, "Switzerland": 7.5, "Belgium": 7.0,
    "Poland": 6.5,
    "UK": 8.5, "USA": 9.0, "US": 9.0,
}

# ── Career goal → countries with strong job markets for that goal ─────────────

CAREER_COUNTRIES: dict[str, list[str]] = {
    "tech industry":    ["united states", "canada", "germany", "netherlands", "singapore", "ireland", "uk", "united kingdom", "sweden", "australia"],
    "finance":          ["united kingdom", "uk", "singapore", "united states", "usa", "us", "uae", "switzerland", "ireland"],
    "academia":         ["germany", "netherlands", "sweden", "finland", "norway", "denmark", "united states", "usa", "us", "united kingdom", "uk"],
    "entrepreneurship": ["united states", "usa", "us", "united kingdom", "uk", "germany", "singapore", "netherlands", "ireland", "uae"],
    "healthcare":       ["canada", "australia", "germany", "netherlands", "united kingdom", "uk", "new zealand", "norway"],
    "government":       ["france", "belgium", "netherlands", "germany", "norway", "sweden"],
    "ngo":              ["france", "belgium", "netherlands", "germany", "norway", "sweden", "united kingdom", "uk"],
}

# study_priority → countries / conditions considered strong for it
PRIORITY_HUB_COUNTRIES: dict[str, list[str]] = {
    "internships":       ["united states", "usa", "us", "united kingdom", "uk", "germany", "netherlands", "singapore", "ireland"],
    "startup ecosystem": ["united states", "usa", "us", "united kingdom", "uk", "germany", "netherlands", "singapore", "uae"],
    "networking":        ["united states", "usa", "us", "united kingdom", "uk", "singapore", "uae"],
}

# Post-study work visa quality (for work_abroad_interest scoring)
POST_STUDY_WORK: dict[str, float] = {
    "United Kingdom": 0.9,   # Graduate Route visa — 2 yrs
    "Canada":         1.0,   # PGWP — up to 3 yrs, PR pathway
    "Australia":      0.95,  # Grad visa — 2-6 yrs
    "Ireland":        0.85,  # Stay Back — 2 yrs
    "Germany":        0.80,  # 18 month job-search
    "Netherlands":    0.75,
    "France":         0.70,
    "United States":  0.60,  # OPT 1-3 yrs but limited H1B
    "Singapore":      0.65,
    "New Zealand":    0.80,
    "Sweden":         0.65,
    "Switzerland":    0.50,
    "UAE":            0.55,
}


# ── Field → subject keywords (appears in pipe-sep subject column) ─────────────

FIELD_KEYWORDS: dict[str, list[str]] = {
    "computer science":            ["Computer Science","Computing","Software","Informatics","Data Science","Machine Learning","AI","Cybersecurity"],
    "data science / ai":           ["Data Science","Machine Learning","AI","Statistics","Analytics","Computer Science","Informatics"],
    "data science":                ["Data Science","Machine Learning","AI","Statistics","Analytics","Computer Science"],
    "electrical engineering":      ["Electrical","Electronic","Engineering","Computer Engineering","Telecommunications"],
    "mechanical engineering":      ["Mechanical","Engineering","Aerospace","Manufacturing","Automotive"],
    "civil engineering":           ["Civil","Structural","Environmental Engineering","Construction","Architecture"],
    "chemical engineering":        ["Chemical","Engineering","Process","Materials","Biotechnology"],
    "engineering":                 ["Engineering","Mechanical","Electrical","Civil","Chemical","Aerospace","Biomedical Engineering","Computer Engineering"],
    "business / mba":              ["Business","Management","MBA","Commerce","Administration","Strategy","Entrepreneurship","Finance"],
    "business":                    ["Business","Management","MBA","Commerce","Administration"],
    "finance / economics":         ["Finance","Economics","Accounting","Banking","Financial","Investment","Econometrics"],
    "finance":                     ["Finance","Accounting","Banking","Financial","Economics"],
    "economics":                   ["Economics","Econometrics","Political Economy","Finance","Business"],
    "marketing":                   ["Marketing","Advertising","Business","Commerce","Management","Media"],
    "medicine / public health":    ["Medicine","Medical","Public Health","Pharmacy","Nursing","Biomedical","Health Sciences","Epidemiology"],
    "medicine":                    ["Medicine","Medical","Health Sciences","Pharmacy","Nursing","Biomedical"],
    "law":                         ["Law","Legal","Jurisprudence","International Law","Criminal Justice"],
    "architecture / design":       ["Architecture","Design","Urban Planning","Built Environment","Interior Design"],
    "physics / mathematics":       ["Physics","Mathematics","Maths","Applied Mathematics","Mathematical Physics","Statistics"],
    "mathematics":                 ["Mathematics","Maths","Applied Mathematics","Statistics","Physics","Data Science"],
    "biotechnology":               ["Biotechnology","Bioscience","Biochemistry","Life Sciences","Molecular Biology","Medicine"],
    "psychology":                  ["Psychology","Cognitive","Neuroscience","Behavioural","Social Science","Psychiatry"],
    "social science":              ["Social Science","Sociology","Anthropology","Political Science","International Relations","Geography","History"],
    "environmental":               ["Environmental","Sustainability","Climate","Ecology","Earth Science","Geography"],
    "public health":               ["Public Health","Epidemiology","Global Health","Medicine","Health Policy"],
    "education":                   ["Education","Teaching","Pedagogy","Social Science"],
}


def _subject_score(field: str, uni_subject: str) -> float:
    """
    Position-weighted subject match: 0.0–1.0.

    The ORDER of subjects in the pipe-separated list reflects what the
    university is primarily known for. A Finance student at a Medicine-primary
    university (Medicine|...|Economics) gets a much lower score than at an
    Economics-primary university (Economics|Finance|Business|...).

    Position multipliers:
      1st subject  → 1.00 (primary specialism)
      2nd          → 0.90
      3rd          → 0.75
      4th          → 0.55
      5th–6th      → 0.35
      7th+         → 0.15 (just peripherally offered)
    """
    if not field:
        return 0.5   # unknown — neutral

    if not uni_subject:
        return 0.3   # no data — slight penalty

    fos      = field.lower().strip()
    subjects = [s.strip() for s in uni_subject.split("|")]

    POSITION_WEIGHTS = [1.00, 0.90, 0.75, 0.55, 0.35, 0.35, 0.15]

    # Resolve keywords for the student's field
    keywords = []
    for canonical, kws in FIELD_KEYWORDS.items():
        if canonical == fos or any(k.lower() in fos for k in kws[:3]):
            keywords = [k.lower() for k in kws]
            break

    if not keywords:
        for canonical, kws in FIELD_KEYWORDS.items():
            if canonical in fos or fos in canonical:
                keywords = [k.lower() for k in kws]
                break

    best_score = 0.0
    for pos, subj in enumerate(subjects):
        subj_lo = subj.lower()
        weight  = POSITION_WEIGHTS[min(pos, len(POSITION_WEIGHTS) - 1)]

        # Direct name match
        if fos in subj_lo or subj_lo in fos:
            best_score = max(best_score, weight)
            continue

        # Keyword match
        if keywords:
            matched = sum(1 for k in keywords if k in subj_lo)
            if matched >= 2:
                best_score = max(best_score, weight)
            elif matched == 1:
                best_score = max(best_score, weight * 0.80)

    return max(best_score, 0.05)   # always a tiny floor


def _get_budget_usd(user: User) -> float | None:
    """Extract and normalise user's budget to USD."""
    budget = getattr(user, "budget", None)
    budget_inr = getattr(user, "budget_inr", None)

    if budget and budget > 0:
        # If stored as USD already (< 500k means USD)
        if budget < 500_000:
            return float(budget)
        # Looks like INR was stored in budget field — convert
        return budget / 83.0

    if budget_inr and budget_inr > 0:
        return budget_inr / 83.0

    return None


def _ranking_preference_max(pref: str | None) -> int | None:
    """Convert ranking preference string to a maximum acceptable rank."""
    mapping = {"Top 50": 50, "Top 100": 100, "Top 200": 200, "Any": None}
    return mapping.get(pref or "Any")


def _is_phd(user: User) -> bool:
    return (getattr(user, "preferred_degree", "") or "").lower() in ("phd", "doctorate")

def _is_mba(user: User) -> bool:
    degree = (getattr(user, "preferred_degree", "") or "").lower()
    field  = (getattr(user, "field_of_study", "") or "").lower()
    return degree == "mba" or "mba" in field or "business" in field

def _is_stem(user: User) -> bool:
    field = (getattr(user, "field_of_study", "") or "").lower()
    stem_kws = ["computer", "engineering", "data", "physics", "mathematics", "electrical",
                "mechanical", "civil", "chemical", "biotech", "science"]
    return any(k in field for k in stem_kws)


# ── Core scoring ───────────────────────────────────────────────────────────────

def calculate_score(user: User, uni: University) -> float:
    score, _ = _score_with_reasons(user, uni)
    return score


def _score_with_reasons(user: User, uni: University) -> tuple[float, dict]:
    reasons  = {}
    total    = 0.0
    capped   = False   # hard exclusion flag

    field    = getattr(user, "field_of_study", None)
    cgpa     = getattr(user, "cgpa", None)
    ielts    = getattr(user, "english_score", None)
    toefl    = getattr(user, "toefl_score", None)
    gre      = getattr(user, "gre_score", None)
    gmat     = getattr(user, "gmat_score", None)
    work_exp = getattr(user, "work_experience_years", None) or 0
    pref_deg = getattr(user, "preferred_degree", None)
    rank_pref = getattr(user, "ranking_preference", None)
    target   = [c.lower().strip() for c in (getattr(user, "target_countries", None) or [])]
    work_abroad = getattr(user, "work_abroad_interest", False)
    scholarship = getattr(user, "scholarship_interest", False)
    career_goal    = (getattr(user, "career_goal", None) or "").lower().strip()
    study_priority = (getattr(user, "study_priority", None) or "").lower().strip()
    pref_env       = (getattr(user, "preferred_environment", None) or "").lower().strip()

    budget_usd = _get_budget_usd(user)

    # ── 1. Subject match (28 pts) ──────────────────────────────────────────────
    sub_pct = _subject_score(field or "", uni.subject or "")

    # Boost for degree type alignment
    if _is_mba(user) and uni.subject:
        s_lo = uni.subject.lower()
        if any(k in s_lo for k in ["business", "management", "mba", "finance", "economics"]):
            sub_pct = min(1.0, sub_pct + 0.15)

    if _is_phd(user):
        # PhD students care most about research quality (ranking) so field match weighted less
        sub_pts = sub_pct * 20   # reduced for PhD
    else:
        sub_pts = sub_pct * 28

    total += sub_pts

    if not field:
        reasons["field"] = "Add your field of study for subject matching."
    elif sub_pct >= 0.9:
        first_subj = (uni.subject or "").split("|")[0].strip()
        reasons["field"] = f"Excellent match — {uni.name} offers {first_subj} which directly aligns with your {field} background."
    elif sub_pct >= 0.6:
        reasons["field"] = f"Good overlap between your {field} background and this university's programmes."
    else:
        reasons["field"] = f"Limited subject overlap with your {field} focus — check the full programme catalogue."

    # ── 2. Budget fit (18 pts) — hard cutoff at 2× budget ─────────────────────
    total_cost = (uni.tuition or 0) + (uni.living_cost or 0)

    if budget_usd and total_cost > 0:
        ratio = total_cost / budget_usd

        if ratio > 2.0:
            # HARD EXCLUSION — more than double the budget
            capped = True
            reasons["budget"] = (
                f"Cost ${total_cost:,.0f}/yr is more than double your budget of ${budget_usd:,.0f}/yr. "
                "Not recommended unless you have external funding."
            )
            total += 0
        elif ratio <= 1.0:
            # Affordable — FLAT score so cheap unis don't beat elite ones
            total += 18
            saved = int(budget_usd - total_cost)
            reasons["budget"] = f"Fits budget — ${total_cost:,.0f}/yr within your ${budget_usd:,.0f}/yr. ${saved:,} to spare."
        elif ratio <= 1.20:
            total += 10
            over = int(total_cost - budget_usd)
            reasons["budget"] = f"${over:,}/yr over budget — a part-time job or scholarship could bridge this."
        elif ratio <= 1.50:
            total += 5
            reasons["budget"] = f"${total_cost:,.0f}/yr is 20-50% above your budget. Consider a student loan."
        else:
            total += 1
            reasons["budget"] = f"${total_cost:,.0f}/yr significantly exceeds your ${budget_usd:,.0f}/yr budget."
    elif not total_cost:
        total += 9
        reasons["budget"] = "Cost data unavailable — verify fees on the university website."
    else:
        total += 7
        reasons["budget"] = "Set your budget in profile for financial eligibility scoring."

    # ── 3. Academic eligibility / CGPA (12 pts) — hard cutoff at -2.0 ─────────
    req_cgpa = uni.requirements_cgpa

    if cgpa and req_cgpa:
        gap = cgpa - req_cgpa   # positive = above requirement

        if gap < -2.0:
            # HARD EXCLUSION — very unlikely to get in
            capped = True
            reasons["cgpa"] = (
                f"Your CGPA {cgpa:.1f} is {abs(gap):.1f} points below the minimum {req_cgpa:.1f}. "
                "This is a significant gap — focus on universities with lower requirements."
            )
            total += 0
        elif gap >= 1.0:
            total += 12
            reasons["cgpa"] = f"Strong fit — your CGPA {cgpa:.1f} is {gap:.1f} above the {req_cgpa:.1f} minimum. You're a competitive applicant."
        elif gap >= 0:
            total += 9
            reasons["cgpa"] = f"CGPA {cgpa:.1f} meets the {req_cgpa:.1f} requirement. A strong SOP will strengthen your application."
        elif gap >= -0.5:
            total += 5
            reasons["cgpa"] = f"Your CGPA {cgpa:.1f} is slightly below the {req_cgpa:.1f} minimum — offset with strong test scores and SOP."
        elif gap >= -1.0:
            total += 2
            reasons["cgpa"] = f"CGPA {cgpa:.1f} is {abs(gap):.1f} below the {req_cgpa:.1f} requirement — a stretch, but not impossible with excellent tests."
        else:
            total += 0
            reasons["cgpa"] = f"CGPA gap is {abs(gap):.1f} points — consider programmes with more flexible admission criteria."
    elif cgpa:
        # No requirement listed — use CGPA quality as a proxy
        if cgpa >= 8.5:
            total += 11
        elif cgpa >= 7.5:
            total += 8
        elif cgpa >= 6.5:
            total += 5
        else:
            total += 2
        reasons["cgpa"] = f"No minimum CGPA listed — your {cgpa:.1f} positions you competitively for this programme."
    else:
        total += 4
        reasons["cgpa"] = "Add your CGPA for academic eligibility scoring."

    # ── 4. Ranking preference alignment (8 pts) ───────────────────────────────
    rank    = uni.qs_subject_ranking or uni.ranking
    max_rank = _ranking_preference_max(rank_pref)

    if rank_pref == "Any" or not rank_pref:
        # No preference — reward any ranked uni slightly
        if rank and rank <= 100:
            total += 7
            reasons["ranking"] = f"Highly ranked at QS #{rank} — excellent research and employer recognition worldwide."
        elif rank and rank <= 300:
            total += 4
            reasons["ranking"] = f"QS #{rank} — solid institution with good graduate outcomes."
        elif rank:
            total += 3
            reasons["ranking"] = f"QS #{rank} — research the specific programme's industry connections."
        else:
            total += 3
            reasons["ranking"] = "No global ranking listed — research programme-specific reputation."
    else:
        if rank and max_rank and rank <= max_rank:
            # Perfect alignment — user wants Top 50 and it is Top 50
            pts = 8 if rank <= (max_rank * 0.6) else 6
            total += pts
            reasons["ranking"] = f"QS #{rank} — fits your '{rank_pref}' preference perfectly."
        elif rank and max_rank and rank <= max_rank * 2:
            # Slightly outside — partial score
            total += 3
            reasons["ranking"] = f"QS #{rank} is slightly outside your '{rank_pref}' preference but still a strong institution."
        elif not rank:
            total += 2
            reasons["ranking"] = f"No ranking available — may not meet your '{rank_pref}' preference. Research programme reputation."
        else:
            total += 0
            if capped is False and rank_pref == "Top 50" and rank and rank > 200:
                capped = True
            reasons["ranking"] = f"QS #{rank} does not meet your '{rank_pref}' preference."

    # ── 5. Country preference (8 pts) ─────────────────────────────────────────
    uni_country_lo = (uni.country or "").lower().strip()
    in_target = (
        uni_country_lo in target
        or any(t in uni_country_lo or uni_country_lo in t for t in target)
    )

    if in_target:
        total += 8
        reasons["country"] = f"{uni.country} is in your target list — great geographic alignment!"
    elif target:
        total += 0
        reasons["country"] = f"{uni.country} is not in your target list ({', '.join([c.title() for c in target[:3]])})."
    else:
        total += 3
        reasons["country"] = "Set target countries to personalise geographic scoring."

    # ── 6. English eligibility (5 pts) ────────────────────────────────────────
    req_ielts = uni.ielts
    req_toefl = uni.toefl

    eng_ok = False
    eng_pts = 0

    if ielts and req_ielts:
        gap_ielts = ielts - req_ielts
        if gap_ielts >= 0.5:
            eng_pts = 5; eng_ok = True
            reasons["ielts"] = f"IELTS {ielts:.1f} comfortably meets the {req_ielts:.1f} requirement."
        elif gap_ielts >= 0:
            eng_pts = 4; eng_ok = True
            reasons["ielts"] = f"IELTS {ielts:.1f} meets the {req_ielts:.1f} minimum."
        elif gap_ielts >= -0.5:
            eng_pts = 2
            reasons["ielts"] = f"IELTS {ielts:.1f} is {abs(gap_ielts):.1f} bands below the {req_ielts:.1f} requirement — consider retaking."
        else:
            reasons["ielts"] = f"IELTS {ielts:.1f} is below the {req_ielts:.1f} minimum — a retest is needed."
    elif toefl and req_toefl:
        gap = toefl - req_toefl
        if gap >= 5:
            eng_pts = 5; eng_ok = True
            reasons["ielts"] = f"TOEFL {toefl} comfortably meets the {req_toefl} requirement."
        elif gap >= 0:
            eng_pts = 4; eng_ok = True
            reasons["ielts"] = f"TOEFL {toefl} meets the {req_toefl} minimum."
        else:
            reasons["ielts"] = f"TOEFL {toefl} is below the {req_toefl} requirement."
    elif ielts:
        eng_pts = 4
        reasons["ielts"] = f"No English requirement listed — your IELTS {ielts:.1f} is competitive."
    elif toefl:
        eng_pts = 4
        reasons["ielts"] = f"No English requirement listed — your TOEFL {toefl} should be accepted."
    else:
        eng_pts = 2
        reasons["ielts"] = "Add your IELTS/TOEFL score for language eligibility scoring."

    total += eng_pts

    # ── 7. Profile-specific bonus (up to 3 pts) ────────────────────────────────
    bonus = 0.0

    # MBA: work experience matters
    if _is_mba(user) and work_exp >= 2:
        if work_exp >= 5:
            bonus += 2
            reasons["bonus"] = f"Strong profile for MBA — {work_exp:.0f} years of professional experience."
        elif work_exp >= 2:
            bonus += 1
            reasons["bonus"] = f"{work_exp:.0f} years work experience is a positive for MBA applications."

    # PhD: high-ranking unis score better (research quality)
    if _is_phd(user):
        if rank and rank <= 50:
            bonus += 2
            reasons["bonus"] = "World-class research environment — ideal for PhD studies."
        elif rank and rank <= 100:
            bonus += 1
            reasons["bonus"] = "Strong research output — suitable for doctoral study."

    # GRE bonus for STEM programmes
    if gre and gre >= 320 and _is_stem(user):
        bonus += 1
        if "bonus" not in reasons:
            reasons["bonus"] = f"GRE {gre} is excellent for STEM admission."

    # GMAT bonus for MBA
    if gmat and gmat >= 650 and _is_mba(user):
        bonus += 1
        if "bonus" not in reasons:
            reasons["bonus"] = f"GMAT {gmat} is competitive for MBA programmes."

    total += min(3.0, bonus)

    # ── 7b. Ranking tiebreaker bonus (up to 5 pts extra) ─────────────────────
    # Within the same profile, better-ranked universities should appear higher.
    # This differentiates e.g. Oxford (rank 3) from Bath (rank 179) for the same student.
    if rank:
        if rank <= 10:
            total += 5.0
        elif rank <= 25:
            total += 4.0
        elif rank <= 50:
            total += 3.0
        elif rank <= 100:
            total += 2.0
        elif rank <= 200:
            total += 1.0
        # 200+ gets 0 tiebreaker

    # Elite-school bonus: only for students who can actually get in
    if cgpa and cgpa >= 8.5 and rank and rank <= 20:
        total += 2.0   # high-CGPA students see truly elite schools at the top
        reasons.setdefault("bonus", "Your CGPA {:.1f} makes you a strong candidate for this elite institution.".format(cgpa))

    # ── 8. Scholarship / post-study work bonus (up to 2 pts) ──────────────────
    ext_bonus = 0.0

    if scholarship and uni.scholarships:
        ext_bonus += 1
        reasons["scholarship"] = f"Scholarships available: {uni.scholarships[:60]}."

    if work_abroad and work_abroad is not False:
        psw = POST_STUDY_WORK.get(uni.country, 0.5)
        if psw >= 0.85:
            ext_bonus += 1
            reasons["work_visa"] = f"{uni.country} has an excellent post-study work visa (Graduate Route / PGWP / Grad Visa)."
        elif psw >= 0.70:
            ext_bonus += 0.5
            reasons["work_visa"] = f"{uni.country} offers a good post-study work visa pathway."

    total += min(2.0, ext_bonus)

    # ── 9. Career outcome alignment (up to 8 pts) ─────────────────────────────
    if career_goal:
        preferred_countries = CAREER_COUNTRIES.get(career_goal, [])
        if uni_country_lo in preferred_countries:
            total += 8
            reasons["career"] = (
                f"{uni.country} is a top destination for {career_goal} — strong industry connections "
                "and graduate hiring in this field."
            )
        elif preferred_countries:
            # Partial if career goal is set but country isn't ideal
            total += 3
            top_picks = [c.title() for c in preferred_countries[:3]]
            reasons["career"] = (
                f"For {career_goal}, you may find stronger opportunities in "
                f"{', '.join(top_picks)}. {uni.country} still has global employers."
            )
        else:
            total += 4
            reasons["career"] = f"Set your career goal to refine country-level job market scoring."
    else:
        total += 4
        reasons["career"] = "Add a career goal to see country-level job market alignment."

    # ── 10. Study environment fit (up to 5 pts) ───────────────────────────────
    env_pts = 0

    if study_priority == "research":
        if rank and rank <= 50:
            env_pts = 5
            reasons["environment"] = f"QS #{rank} — world-class research environment, ideal for your research focus."
        elif rank and rank <= 100:
            env_pts = 3
            reasons["environment"] = f"Strong research output at QS #{rank} — aligns with your research priority."
        else:
            env_pts = 1
            reasons["environment"] = "Research priority best served at a top-100 university — explore funding options."
    elif study_priority in ("internships", "startup ecosystem"):
        hub_countries = PRIORITY_HUB_COUNTRIES.get(study_priority, [])
        if uni_country_lo in hub_countries:
            env_pts = 5
            reasons["environment"] = (
                f"{uni.country} is a major hub for {study_priority.replace('_', ' ')} — "
                "strong industry networks and career opportunities."
            )
        else:
            env_pts = 2
            reasons["environment"] = (
                f"For {study_priority.replace('_', ' ')}, countries like USA, UK, Germany, and Singapore "
                "have denser ecosystems — but great opportunities exist globally."
            )
    elif study_priority == "networking":
        hub_countries = PRIORITY_HUB_COUNTRIES.get("networking", [])
        if _is_mba(user) and uni_country_lo in hub_countries:
            env_pts = 5
            reasons["environment"] = f"MBA networking in {uni.country} — excellent alumni networks and global recruiting."
        elif uni_country_lo in hub_countries:
            env_pts = 3
            reasons["environment"] = f"{uni.country} offers strong professional networking opportunities."
        else:
            env_pts = 2
    elif study_priority == "coursework":
        env_pts = 3
        reasons["environment"] = "Coursework focus — programme structure matters more than country; check the curriculum."
    else:
        env_pts = 2

    total += env_pts

    # ── 11. Safety / match / reach tier (up to 3 pts) ─────────────────────────
    if cgpa and req_cgpa:
        buffer = cgpa - req_cgpa
        if buffer >= 1.5:
            total += 3
            if "environment" not in reasons or env_pts == 0:
                reasons["tier"] = f"Safety school — your CGPA is {buffer:.1f} pts above the minimum. High admission confidence."
            else:
                reasons["tier"] = f"Safety pick — CGPA buffer of {buffer:.1f} pts gives you a strong application."
        elif buffer >= 0.5:
            total += 2
            reasons["tier"] = f"Strong match — your CGPA is {buffer:.1f} pts above the {req_cgpa:.1f} minimum."
        elif buffer >= 0:
            total += 1
            reasons["tier"] = f"Match — CGPA meets the requirement; differentiate with your SOP and test scores."
        # Below requirement: 0 pts (already penalised in factor 3)

    # ── Apply hard exclusion cap ───────────────────────────────────────────────
    if capped:
        total = min(total, 8.0)   # max 8/100 for excluded unis

    return round(min(total, 100.0), 1), reasons


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
        "match_score": round(score / 100, 3),   # keep 0-1 for frontend compat
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
    if score >= 80:
        label = "Excellent match"
    elif score >= 65:
        label = "Strong match"
    elif score >= 45:
        label = "Moderate match"
    elif score >= 20:
        label = "Stretch target"
    else:
        label = "Not recommended"

    positives = [
        v for k, v in reasons.items()
        if any(w in v for w in [
            "comfortably", "well under", "Fits budget", "Strong fit", "Excellent",
            "in your target", "directly aligns", "Great geographic", "excellent post",
            "top destination", "world-class research", "major hub", "Safety pick",
            "Strong match",
        ])
    ]
    snippet = positives[0] if positives else "Review the factor breakdown above for details."
    return f"{label} ({score:.0f}/100). {snippet}"
