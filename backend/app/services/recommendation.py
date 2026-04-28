"""
Recommendation Engine v5 — Personalised University Matching
============================================================
Every student gets a unique ranked list. Two students with different
profiles will see completely different universities at the top.

Scoring is out of 100 points across 13 factors:

  1. Subject / field match          28 pts  ← biggest differentiator
  2. Budget eligibility             18 pts  ← hard cutoff at 2× budget
  3. Academic eligibility (CGPA)    12 pts  ← hard cutoff for large gaps
  4. Ranking preference alignment    8 pts  ← respects user's own preference
  5. Country preference              8 pts  ← target countries get full score
  6. English language eligibility    5 pts
  7. Career outcome alignment        8 pts  ← career_goal × country job market
  8. Study environment / priority    5 pts  ← study_priority × uni type
  9. Safety / match / reach tier     3 pts  ← CGPA buffer above requirement
 10. Profile-specific bonus        up to 3 pts  (MBA work-exp, PhD research, GRE/GMAT)
 11. Scholarship / post-work bonus up to 2 pts
 12. Intake preference bonus       up to 2 pts  ← intake_months match
 13. Living preference bonus       up to 2 pts  ← urban / suburban / rural fit

Hard exclusion rules (score clamped to ≤ 8):
  • Total cost > 2× user's annual budget
  • CGPA more than 2.0 points below the requirement
  • Ranking requirement is "Top 50" but uni is ranked > 200

Degree-type routing:
  • MBA  → business schools scored higher; GMAT counts; work-exp important
  • PhD  → research output (top ranking) weighted more; tuition less
  • MS/Masters → balanced STEM/subject focus
  • Bachelors → more permissive eligibility

Optional fields: all optional profile fields are used when present and
gracefully skipped when absent — the score is normalised accordingly.
"""

import json
import logging
from functools import lru_cache
from typing import Optional

from app.models.user import User
from app.models.university import University

logger = logging.getLogger(__name__)


# ── In-memory LLM score cache (keyed by profile_hash + uni_id) ────────────────
_LLM_SCORE_CACHE: dict[str, dict] = {}


# Country-level graduate salary and job-market priors shared by APIs.
GRAD_SALARY_USD: dict[str, int] = {
    # Primary study-abroad destinations
    "United States": 85000,
    "United Kingdom": 62000,
    "Canada": 68000,
    "Australia": 70000,
    "Germany": 65000,
    "France": 58000,
    "Netherlands": 64000,
    "Ireland": 66000,
    "Singapore": 76000,
    "Japan": 60000,
    "Sweden": 61000,
    "Norway": 67000,
    "Denmark": 68000,
    "Finland": 60000,
    "New Zealand": 59000,
    "UAE": 72000,
    "United Arab Emirates": 72000,
    "Portugal": 48000,
    "Italy": 50000,
    "Spain": 51000,
    "South Korea": 62000,
    "Switzerland": 95000,
    # Secondary destinations
    "Belgium": 57000,
    "Austria": 58000,
    "Hong Kong": 70000,
    "Hong Kong SAR": 70000,
    "Macao": 55000,
    "Macau SAR": 55000,
    "China": 35000,
    "China (Mainland)": 35000,
    "Taiwan": 40000,
    "Malaysia": 28000,
    "Thailand": 22000,
    "Indonesia": 18000,
    "Philippines": 16000,
    "Vietnam": 15000,
    "India": 14000,
    "Pakistan": 8000,
    "Bangladesh": 7000,
    "Sri Lanka": 9000,
    "Nepal": 6000,
    "Turkey": 20000,
    "Russia": 18000,
    "Russian Federation": 18000,
    "Ukraine": 10000,
    "Poland": 30000,
    "Czechia": 32000,
    "Czech Republic": 32000,
    "Hungary": 25000,
    "Romania": 22000,
    "Bulgaria": 19000,
    "Serbia": 18000,
    "Croatia": 22000,
    "Slovenia": 30000,
    "Slovakia": 24000,
    "Greece": 24000,
    "Estonia": 28000,
    "Latvia": 25000,
    "Lithuania": 27000,
    "Luxembourg": 78000,
    "Malta": 38000,
    "Iceland": 70000,
    "Cyprus": 30000,
    "Northern Cyprus": 20000,
    "Brazil": 20000,
    "Colombia": 15000,
    "Chile": 22000,
    "Argentina": 14000,
    "Peru": 14000,
    "Mexico": 18000,
    "Venezuela": 8000,
    "Uruguay": 16000,
    "Ecuador": 12000,
    "Bolivia": 10000,
    "Paraguay": 10000,
    "Costa Rica": 18000,
    "Panama": 18000,
    "Dominican Republic": 14000,
    "Jamaica": 12000,
    "Guatemala": 10000,
    "Honduras": 8000,
    "Cuba": 8000,
    "Puerto Rico": 38000,
    "South Africa": 18000,
    "Egypt": 10000,
    "Nigeria": 8000,
    "Ghana": 8000,
    "Kenya": 10000,
    "Ethiopia": 6000,
    "Tanzania": 6000,
    "Uganda": 6000,
    "Rwanda": 7000,
    "Zambia": 7000,
    "Zimbabwe": 5000,
    "Botswana": 10000,
    "Namibia": 9000,
    "Mozambique": 5000,
    "Senegal": 7000,
    "Morocco": 12000,
    "Tunisia": 11000,
    "Algeria": 10000,
    "Libya": 10000,
    "Sudan": 6000,
    "Saudi Arabia": 50000,
    "Qatar": 55000,
    "Kuwait": 48000,
    "Bahrain": 40000,
    "Oman": 35000,
    "Jordan": 18000,
    "Lebanon": 15000,
    "Israel": 58000,
    "Iran": 8000,
    "Iran, Islamic Republic of": 8000,
    "Iraq": 10000,
    "Syria": 6000,
    "Syrian Arab Republic": 6000,
    "Yemen": 5000,
    "Palestinian Territory, Occupied": 8000,
    "Palestine": 8000,
    "Kazakhstan": 18000,
    "Uzbekistan": 10000,
    "Kyrgyzstan": 8000,
    "Azerbaijan": 14000,
    "Georgia": 14000,
    "Armenia": 12000,
    "Belarus": 10000,
    "Mongolia": 10000,
    "Brunei": 30000,
    "Brunei Darussalam": 30000,
    "Fiji": 14000,
}

JOB_SCORE: dict[str, float] = {
    # Primary destinations
    "United States": 9.4,
    "United Kingdom": 8.8,
    "Canada": 8.9,
    "Australia": 8.7,
    "Germany": 8.8,
    "France": 8.1,
    "Netherlands": 8.5,
    "Ireland": 8.6,
    "Singapore": 9.1,
    "Japan": 8.0,
    "Sweden": 8.2,
    "Norway": 8.3,
    "Denmark": 8.4,
    "Finland": 8.0,
    "New Zealand": 7.9,
    "UAE": 8.4,
    "United Arab Emirates": 8.4,
    "Portugal": 7.5,
    "Italy": 7.4,
    "Spain": 7.6,
    "South Korea": 8.1,
    "Switzerland": 9.2,
    # Secondary destinations
    "Belgium": 8.0,
    "Austria": 7.9,
    "Hong Kong": 8.5,
    "Hong Kong SAR": 8.5,
    "Macao": 7.2,
    "Macau SAR": 7.2,
    "China": 7.2,
    "China (Mainland)": 7.2,
    "Taiwan": 7.5,
    "Malaysia": 7.0,
    "Thailand": 6.8,
    "Indonesia": 6.5,
    "Philippines": 6.3,
    "Vietnam": 6.5,
    "India": 6.8,
    "Turkey": 6.5,
    "Russia": 6.0,
    "Russian Federation": 6.0,
    "Poland": 7.2,
    "Czechia": 7.3,
    "Czech Republic": 7.3,
    "Hungary": 6.8,
    "Romania": 6.5,
    "Bulgaria": 6.3,
    "Greece": 6.5,
    "Estonia": 7.0,
    "Latvia": 6.7,
    "Lithuania": 6.8,
    "Luxembourg": 8.3,
    "Iceland": 8.0,
    "Israel": 8.0,
    "Saudi Arabia": 7.5,
    "Qatar": 7.5,
    "Kuwait": 7.0,
    "Bahrain": 7.0,
    "Oman": 6.8,
    "Brazil": 6.5,
    "Mexico": 6.5,
    "Chile": 6.8,
    "Colombia": 6.2,
    "Argentina": 6.0,
    "South Africa": 6.3,
    "Egypt": 5.8,
    "Nigeria": 5.5,
    "Morocco": 6.0,
    "Brunei": 6.8,
    "Brunei Darussalam": 6.8,
}

POST_STUDY_WORK: dict[str, float] = {
    # Primary destinations
    "United States": 0.80,
    "United Kingdom": 0.92,
    "Canada": 0.95,
    "Australia": 0.90,
    "Germany": 0.88,
    "France": 0.80,
    "Netherlands": 0.84,
    "Ireland": 0.89,
    "Singapore": 0.72,
    "Japan": 0.68,
    "Sweden": 0.78,
    "Norway": 0.74,
    "Denmark": 0.77,
    "Finland": 0.76,
    "New Zealand": 0.86,
    "UAE": 0.65,
    "United Arab Emirates": 0.65,
    "Portugal": 0.73,
    "Italy": 0.70,
    "Spain": 0.71,
    "South Korea": 0.67,
    "Switzerland": 0.81,
    # Secondary destinations
    "Belgium": 0.75,
    "Austria": 0.74,
    "Hong Kong": 0.62,
    "Hong Kong SAR": 0.62,
    "Luxembourg": 0.80,
    "Iceland": 0.78,
    "Israel": 0.65,
    "Malaysia": 0.58,
    "China": 0.45,
    "China (Mainland)": 0.45,
    "Taiwan": 0.52,
    "Thailand": 0.40,
    "Indonesia": 0.38,
    "India": 0.35,
    "Turkey": 0.42,
    "Russia": 0.35,
    "Russian Federation": 0.35,
    "Poland": 0.65,
    "Czechia": 0.67,
    "Czech Republic": 0.67,
    "Hungary": 0.60,
    "Brazil": 0.42,
    "Mexico": 0.40,
    "Chile": 0.45,
    "Argentina": 0.38,
    "South Africa": 0.40,
    "Saudi Arabia": 0.50,
    "Qatar": 0.52,
    "Kuwait": 0.45,
    "Oman": 0.42,
    "Bahrain": 0.45,
    "Egypt": 0.32,
    "Nigeria": 0.30,
    "Morocco": 0.35,
    "Brunei": 0.55,
    "Brunei Darussalam": 0.55,
}

CAREER_COUNTRIES: dict[str, list[str]] = {
    "tech industry": ["united states", "canada", "united kingdom", "germany", "singapore", "netherlands"],
    "finance": ["united states", "united kingdom", "singapore", "switzerland", "canada"],
    "academia": ["united states", "united kingdom", "germany", "switzerland", "netherlands"],
    "entrepreneurship": ["united states", "united kingdom", "singapore", "canada", "germany"],
    "healthcare": ["united states", "united kingdom", "canada", "australia", "germany"],
    "government": ["united kingdom", "canada", "germany", "netherlands", "france"],
    "consulting": ["united states", "united kingdom", "germany", "switzerland", "singapore"],
    "data science": ["united states", "canada", "united kingdom", "germany", "singapore"],
    "research": ["united states", "united kingdom", "germany", "switzerland", "netherlands"],
    "product management": ["united states", "canada", "united kingdom", "germany", "singapore"],
    "design": ["united states", "united kingdom", "germany", "netherlands", "singapore"],
    "marketing": ["united states", "united kingdom", "canada", "australia", "singapore"],
}

# Aliases students commonly type → canonical CAREER_COUNTRIES key
CAREER_GOAL_ALIASES: dict[str, str] = {
    # Tech
    "software engineering":  "tech industry",
    "software developer":    "tech industry",
    "software development":  "tech industry",
    "software engineer":     "tech industry",
    "it industry":           "tech industry",
    "technology":            "tech industry",
    "tech":                  "tech industry",
    "ai":                    "tech industry",
    "ml":                    "tech industry",
    "machine learning":      "tech industry",
    "artificial intelligence": "tech industry",
    "cybersecurity":         "tech industry",
    "cloud computing":       "tech industry",
    # Data
    "data analyst":          "data science",
    "data engineer":         "data science",
    "analytics":             "data science",
    "data":                  "data science",
    # Finance
    "investment banking":    "finance",
    "banking":               "finance",
    "financial services":    "finance",
    "investment":            "finance",
    "asset management":      "finance",
    "economics":             "finance",
    # Consulting
    "management consulting": "consulting",
    "strategy consulting":   "consulting",
    "business consulting":   "consulting",
    # Research / Academia
    "academic research":     "research",
    "phd research":          "research",
    "university professor":  "academia",
    "lecturer":              "academia",
    "researcher":            "research",
    # Healthcare
    "medicine":              "healthcare",
    "medical":               "healthcare",
    "public health":         "healthcare",
    "pharma":                "healthcare",
    "pharmacy":              "healthcare",
    "biotech":               "healthcare",
    # Entrepreneurship
    "startup":               "entrepreneurship",
    "entrepreneur":          "entrepreneurship",
    "founder":               "entrepreneurship",
    "startups":              "entrepreneurship",
    # Product
    "product":               "product management",
    "pm":                    "product management",
    # Marketing
    "digital marketing":     "marketing",
    "brand management":      "marketing",
    "advertising":           "marketing",
}

PRIORITY_HUB_COUNTRIES: dict[str, list[str]] = {
    "internships": ["united states", "united kingdom", "germany", "canada", "singapore", "netherlands"],
    "startup ecosystem": ["united states", "united kingdom", "singapore", "canada", "germany"],
    "networking": ["united states", "united kingdom", "canada", "singapore", "switzerland"],
}

# Intake preference → which months count as matching
INTAKE_SEASON_MAP: dict[str, list[str]] = {
    "fall":    ["august", "september", "october"],
    "spring":  ["january", "february", "march"],
    "winter":  ["january", "december"],
    "summer":  ["may", "june", "july"],
    "january": ["january"],
    "september": ["september"],
}

# Countries strongly associated with urban living environments
URBAN_COUNTRIES: set[str] = {"singapore", "united arab emirates", "uae", "hong kong"}
# Urban keywords in university/city names
URBAN_CITY_KEYWORDS = [
    "london", "new york", "singapore", "dubai", "paris", "berlin",
    "tokyo", "chicago", "boston", "amsterdam", "sydney", "melbourne",
    "toronto", "montreal", "zurich", "vienna", "seoul", "shanghai",
    "munich", "frankfurt", "edinburgh", "manchester", "barcelona", "rome",
]
# Countries with generally quieter / suburban campuses
SUBURBAN_RURAL_COUNTRIES: set[str] = {"new zealand", "norway", "finland", "denmark", "ireland"}


def normalize_country(value: Optional[str]) -> str:
    if not value:
        return ""
    aliases = {
        "uk": "united kingdom",
        "u.k.": "united kingdom",
        "usa": "united states",
        "us": "united states",
        "u.s.": "united states",
    }
    key = value.strip().lower()
    return aliases.get(key, key)


def resolve_budget_usd(user: User) -> Optional[float]:
    """Return user budget in USD from either budget or budget_inr fields."""
    budget_usd = getattr(user, "budget", None)
    if budget_usd:
        return float(budget_usd)

    budget_inr = getattr(user, "budget_inr", None)
    if budget_inr:
        return float(budget_inr) / 83.0

    return None

# ── Field → keywords that appear in pipe-separated university subject string ──
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

def _is_research_oriented(user: User) -> bool:
    study_p = (getattr(user, "study_priority", "") or "").lower()
    career  = (getattr(user, "career_goal", "") or "").lower()
    return "research" in study_p or "research" in career or "academia" in career

def _infer_city_type(uni_name: str, uni_country: str) -> str:
    """Returns 'urban', 'suburban', or 'unknown'."""
    name_lo    = uni_name.lower()
    country_lo = uni_country.lower()

    if country_lo in URBAN_COUNTRIES:
        return "urban"
    if any(city in name_lo for city in URBAN_CITY_KEYWORDS):
        return "urban"
    if country_lo in SUBURBAN_RURAL_COUNTRIES:
        return "suburban"
    # Large English-speaking cities likely to have urban unis
    urban_country_cities = {
        "united kingdom": ["london", "manchester", "birmingham", "edinburgh", "bristol"],
        "united states":  ["new york", "boston", "chicago", "san francisco", "los angeles"],
        "canada":         ["toronto", "montreal", "vancouver"],
        "australia":      ["sydney", "melbourne", "brisbane"],
        "germany":        ["berlin", "munich", "frankfurt", "hamburg"],
        "france":         ["paris", "lyon"],
        "netherlands":    ["amsterdam", "rotterdam"],
    }
    for country, cities in urban_country_cities.items():
        if country in country_lo:
            if any(city in name_lo for city in cities):
                return "urban"
    return "unknown"


# ── Ranking-tier CGPA expectations ────────────────────────────────────────────
# Real-world minimum CGPA expected by universities of each tier.
# Used to override suspiciously low DB values (data quality issue).

def _ranking_tier_min_cgpa(rank: int | None) -> float:
    """Return the realistic minimum CGPA for a university of this QS rank tier."""
    if rank is None:
        return 6.5
    if rank <= 10:
        return 9.0
    if rank <= 25:
        return 8.8
    if rank <= 50:
        return 8.5
    if rank <= 100:
        return 8.2
    if rank <= 200:
        return 7.8
    if rank <= 400:
        return 7.3
    if rank <= 700:
        return 6.8
    return 6.5


# ── Core scoring ───────────────────────────────────────────────────────────────

def calculate_score(user: User, uni: University) -> float:
    score, _ = _score_with_reasons(user, uni)
    return score


def _score_with_reasons(user: User, uni: University) -> tuple[float, dict]:
    reasons  = {}
    total    = 0.0
    capped   = False   # hard exclusion flag

    # ── Extract all user profile fields ───────────────────────────────────────
    field          = getattr(user, "field_of_study", None)
    cgpa           = getattr(user, "cgpa", None)
    ielts          = getattr(user, "english_score", None)
    toefl          = getattr(user, "toefl_score", None)
    gre            = getattr(user, "gre_score", None)
    gmat           = getattr(user, "gmat_score", None)
    work_exp       = getattr(user, "work_experience_years", None) or 0
    pref_deg       = getattr(user, "preferred_degree", None)
    rank_pref      = getattr(user, "ranking_preference", None)
    target         = [c.lower().strip() for c in (getattr(user, "target_countries", None) or [])]
    work_abroad    = getattr(user, "work_abroad_interest", False)
    scholarship    = getattr(user, "scholarship_interest", False)
    career_goal    = (getattr(user, "career_goal", None) or "").lower().strip()
    study_priority = (getattr(user, "study_priority", None) or "").lower().strip()
    pref_env       = (getattr(user, "preferred_environment", None) or "").lower().strip()
    living_pref    = (getattr(user, "living_preference", None) or "").lower().strip()
    intake_pref    = (getattr(user, "intake_preference", None) or "").lower().strip()
    learning_style = (getattr(user, "learning_style", None) or "").lower().strip()

    budget_usd = _get_budget_usd(user)
    resume_text = (getattr(user, "resume_text", None) or "").strip()

    uni_country_lo = (uni.country or "").lower().strip()
    uni_name       = uni.name or ""

    # ── Country hard exclusion (tight filter) ─────────────────────────────────
    # If the user specified 1–4 target countries, universities outside that list
    # are immediately capped. This reflects real behaviour: students who say
    # "I only want UK/Canada" genuinely do NOT want German results.
    if target and len(target) <= 4:
        in_target = (
            uni_country_lo in target
            or any(t in uni_country_lo or uni_country_lo in t for t in target)
        )
        if not in_target:
            capped = True
    rank           = uni.qs_subject_ranking or uni.ranking

    # ── 1. Subject match (28 pts) ──────────────────────────────────────────────
    # ── Resume-based field enrichment ────────────────────────────────────────────
    # If the user has a resume, extract additional subject signals from it.
    # This catches cases where the profile field_of_study is generic (e.g. "Engineering")
    # but the resume reveals a specific specialisation (e.g. "machine learning", "robotics").
    effective_field = field or ""
    if resume_text and not effective_field:
        # No field set — infer from resume keywords
        resume_lo = resume_text.lower()
        for canonical in FIELD_KEYWORDS:
            if canonical in resume_lo or any(kw.lower() in resume_lo for kw in FIELD_KEYWORDS[canonical][:3]):
                effective_field = canonical
                break
    elif resume_text and effective_field:
        # Field is set — boost if resume confirms a sub-specialisation
        resume_lo = resume_text.lower()
        # Check if resume mentions specialised sub-keywords that tighten the match
        for canonical, kws in FIELD_KEYWORDS.items():
            if canonical != effective_field.lower() and canonical in resume_lo:
                # The resume mentions an adjacent/sub-field — apply small boost
                sub_boost = _subject_score(canonical, uni.subject or "")
                if sub_boost > _subject_score(effective_field, uni.subject or ""):
                    effective_field = canonical  # upgrade to closer match
                    break

    sub_pct = _subject_score(effective_field, uni.subject or "")

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

    if not effective_field:
        reasons["field"] = "Add your field of study for subject matching."
    elif sub_pct >= 0.9:
        first_subj = (uni.subject or "").split("|")[0].strip()
        reasons["field"] = f"Excellent match — {uni_name} offers {first_subj} which directly aligns with your {field} background."
    elif sub_pct >= 0.6:
        reasons["field"] = f"Good overlap between your {effective_field} background and this university's programmes."
    else:
        reasons["field"] = f"Limited subject overlap with your {effective_field} focus — check the full programme catalogue."

    # ── 2. Budget fit (18 pts) — hard cutoff at 2× budget ─────────────────────
    # DB stores tuition and living_cost in INR; convert to USD for comparison.
    INR_TO_USD = 1 / 83.0
    total_cost_inr = (uni.tuition or 0) + (uni.living_cost or 0)
    total_cost_usd = total_cost_inr * INR_TO_USD   # USD for budget comparison

    if budget_usd and total_cost_usd > 0:
        ratio = total_cost_usd / budget_usd

        if ratio > 2.0:
            # HARD EXCLUSION — more than double the budget
            capped = True
            reasons["budget"] = (
                f"${int(total_cost_usd):,}/yr total cost is more than double your "
                f"${int(budget_usd):,}/yr budget. Only consider with a full scholarship."
            )
            total += 0
        elif ratio <= 1.0:
            saved = int(budget_usd - total_cost_usd)
            reasons["budget"] = (
                f"Fits budget — ${int(total_cost_usd):,}/yr is within your "
                f"${int(budget_usd):,}/yr. ${saved:,} to spare annually."
            )
            total += 18
        elif ratio <= 1.20:
            over = int(total_cost_usd - budget_usd)
            reasons["budget"] = (
                f"${int(total_cost_usd):,}/yr is ${over:,} over budget — "
                "a part-time job or small scholarship could bridge this gap."
            )
            total += 10
        elif ratio <= 1.50:
            reasons["budget"] = (
                f"${int(total_cost_usd):,}/yr is 20–50% above your "
                f"${int(budget_usd):,}/yr budget. A student loan may be needed."
            )
            total += 5
        else:
            reasons["budget"] = (
                f"${int(total_cost_usd):,}/yr significantly exceeds your "
                f"${int(budget_usd):,}/yr budget."
            )
            total += 1
    elif not total_cost_inr:
        total += 9
        reasons["budget"] = "Cost data unavailable — verify fees on the university website."
    else:
        total += 7
        reasons["budget"] = "Set your annual budget in your profile for financial eligibility scoring."

    # ── 3. Academic eligibility / CGPA (12 pts) ──────────────────────────────────
    # Use the HIGHER of the DB-stored requirement and the realistic tier expectation.
    # This corrects bad DB data (e.g. Yale stored as 6.8 when it really expects 9.0+).
    db_req_cgpa    = uni.requirements_cgpa or 0.0
    tier_min_cgpa  = _ranking_tier_min_cgpa(rank)
    req_cgpa       = max(db_req_cgpa, tier_min_cgpa) if (db_req_cgpa or rank) else db_req_cgpa

    if cgpa and req_cgpa:
        gap = cgpa - req_cgpa   # positive = above requirement

        # Tiered hard exclusion based on ranking prestige
        if rank and rank <= 100:
            hard_cutoff = -1.0   # top-100 are strict
        elif rank and rank <= 300:
            hard_cutoff = -1.5
        else:
            hard_cutoff = -2.0

        if gap <= hard_cutoff:
            # HARD EXCLUSION — very unlikely to get in
            capped = True
            reasons["cgpa"] = (
                f"Your CGPA {cgpa:.1f} is {abs(gap):.1f} pts below the ~{req_cgpa:.1f} expected for "
                f"this ranked institution. Focus on universities that are a better academic fit."
            )
            total += 0
        elif gap >= 1.0:
            total += 12
            reasons["cgpa"] = f"Strong academic fit — your CGPA {cgpa:.1f} is {gap:.1f} above the ~{req_cgpa:.1f} expectation. You're a competitive applicant."
        elif gap >= 0:
            total += 9
            reasons["cgpa"] = f"CGPA {cgpa:.1f} meets the ~{req_cgpa:.1f} expectation. A strong SOP will strengthen your application."
        elif gap >= -0.5:
            total += 5
            reasons["cgpa"] = f"Your CGPA {cgpa:.1f} is slightly below the ~{req_cgpa:.1f} expectation — offset with strong test scores and SOP."
        elif gap >= hard_cutoff:
            total += 1
            reasons["cgpa"] = f"CGPA gap of {abs(gap):.1f} pts is a stretch — this is a reach school. Prioritise stronger matches."
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
        reasons["cgpa"] = f"No minimum CGPA listed — your {cgpa:.1f} positions you for this programme."
    else:
        total += 4
        reasons["cgpa"] = "Add your CGPA for academic eligibility scoring."

    # ── 4. Ranking preference alignment (8 pts) ───────────────────────────────
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
            pts = 8 if rank <= (max_rank * 0.6) else 6
            total += pts
            reasons["ranking"] = f"QS #{rank} — fits your '{rank_pref}' preference perfectly."
        elif rank and max_rank and rank <= max_rank * 1.5:
            # Borderline — just outside preference but not wildly off
            total += 3
            reasons["ranking"] = f"QS #{rank} is slightly outside your '{rank_pref}' preference but still a reputable institution."
        elif not rank:
            total += 2
            reasons["ranking"] = f"No ranking available — may not meet your '{rank_pref}' preference. Research programme reputation."
        else:
            # Outside preference — hard exclusion for stricter tiers
            total += 0
            if capped is False and rank:
                # Apply exclusion when university is far outside the stated preference
                exclusion_thresholds = {
                    "Top 50":  200,   # want top 50 but ranked >200 → exclude
                    "Top 100": 300,   # want top 100 but ranked >300 → exclude
                    "Top 200": 500,   # want top 200 but ranked >500 → exclude
                }
                threshold = exclusion_thresholds.get(rank_pref)
                if threshold and rank > threshold:
                    capped = True
            reasons["ranking"] = f"QS #{rank} does not meet your '{rank_pref}' preference."

    # ── 5. Country preference (8 pts) ─────────────────────────────────────────
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

    eng_pts = 0

    if ielts and req_ielts:
        gap_ielts = ielts - req_ielts
        if gap_ielts >= 0.5:
            eng_pts = 5
            reasons["ielts"] = f"IELTS {ielts:.1f} comfortably meets the {req_ielts:.1f} requirement."
        elif gap_ielts >= 0:
            eng_pts = 4
            reasons["ielts"] = f"IELTS {ielts:.1f} meets the {req_ielts:.1f} minimum."
        elif gap_ielts >= -0.5:
            eng_pts = 2
            reasons["ielts"] = f"IELTS {ielts:.1f} is {abs(gap_ielts):.1f} bands below the {req_ielts:.1f} requirement — consider retaking."
        else:
            reasons["ielts"] = f"IELTS {ielts:.1f} is below the {req_ielts:.1f} minimum — a retest is needed."
    elif toefl and req_toefl:
        gap = toefl - req_toefl
        if gap >= 5:
            eng_pts = 5
            reasons["ielts"] = f"TOEFL {toefl} comfortably meets the {req_toefl} requirement."
        elif gap >= 0:
            eng_pts = 4
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

    # MBA: work experience matters — minimum 2 yrs expected, 5+ strong
    if _is_mba(user):
        if work_exp >= 5:
            bonus += 2
            reasons["bonus"] = f"Strong MBA profile — {work_exp:.0f} years of professional experience."
        elif work_exp >= 2:
            bonus += 1
            reasons["bonus"] = f"{work_exp:.0f} years work experience strengthens your MBA application."
        elif work_exp >= 1:
            bonus += 0.5
            reasons["bonus"] = f"Some work experience helps — most MBA programmes prefer 2+ years."

    # PhD: high-ranking unis score better (research quality)
    if _is_phd(user):
        if rank and rank <= 50:
            bonus += 2
            reasons["bonus"] = "World-class research environment — ideal for PhD studies."
        elif rank and rank <= 100:
            bonus += 1
            reasons["bonus"] = "Strong research output — suitable for doctoral study."
        # Work experience is also positive for PhD
        if work_exp >= 2:
            bonus = min(3.0, bonus + 0.5)

    # Non-MBA work experience: industry-relevant programmes appreciate it
    if not _is_mba(user) and not _is_phd(user) and work_exp >= 2:
        bonus = min(3.0, bonus + 0.5)
        if "bonus" not in reasons:
            reasons["bonus"] = f"{work_exp:.0f} years of work experience adds strength to your Masters application."

    # GRE: if university requires GRE, check if student has it
    gre_req = getattr(uni, "gre_required", False)
    if gre_req and gre and gre >= 310 and _is_stem(user):
        bonus = min(3.0, bonus + 1)
        reasons.setdefault("bonus", f"GRE {gre} meets this university's requirement — strong STEM application.")
    elif gre and gre >= 320 and _is_stem(user):
        bonus = min(3.0, bonus + 1)
        reasons.setdefault("bonus", f"GRE {gre} is excellent — well above average for STEM programmes.")

    # GMAT bonus for MBA
    if gmat and gmat >= 650 and _is_mba(user):
        bonus = min(3.0, bonus + 1)
        reasons.setdefault("bonus", f"GMAT {gmat} is competitive for MBA programmes at this institution.")

    total += min(3.0, bonus)

    # ── 7b. Ranking tiebreaker bonus (up to 5 pts extra) ─────────────────────
    # Only reward ranking prestige if the student can realistically get in.
    # A student with 8.0 CGPA should NOT get a bonus for Yale (needs 9.0+).
    if rank and cgpa:
        tier_min = _ranking_tier_min_cgpa(rank)
        cgpa_fits_tier = cgpa >= (tier_min - 0.3)   # 0.3 tolerance
        if cgpa_fits_tier:
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
        # else: no ranking bonus — the student is below the tier threshold
    elif rank:
        # No CGPA provided — give small ranking credit
        if rank <= 100:
            total += 2.0
        elif rank <= 300:
            total += 1.0

    # Elite-school bonus: only for students who can actually get in
    if cgpa and cgpa >= 8.8 and rank and rank <= 20:
        total += 2.0
        reasons.setdefault("bonus", f"Your CGPA {cgpa:.1f} makes you a strong candidate for this elite institution.")

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
        # Resolve alias first (e.g. "software engineering" → "tech industry")
        resolved_goal = CAREER_GOAL_ALIASES.get(career_goal, career_goal)
        # Try exact match on resolved goal, then original, then partial keyword scan
        preferred_countries = CAREER_COUNTRIES.get(resolved_goal, [])
        if not preferred_countries:
            preferred_countries = CAREER_COUNTRIES.get(career_goal, [])
        if not preferred_countries:
            # Partial keyword match against canonical keys
            for cg_key, cg_countries in CAREER_COUNTRIES.items():
                if cg_key in career_goal or career_goal in cg_key:
                    preferred_countries = cg_countries
                    break
            # Also scan aliases for partial match
            if not preferred_countries:
                for alias, canonical in CAREER_GOAL_ALIASES.items():
                    if alias in career_goal or career_goal in alias:
                        preferred_countries = CAREER_COUNTRIES.get(canonical, [])
                        if preferred_countries:
                            resolved_goal = canonical
                            break

        display_goal = resolved_goal if resolved_goal in CAREER_COUNTRIES else career_goal
        if uni_country_lo in preferred_countries:
            total += 8
            reasons["career"] = (
                f"{uni.country} is a top destination for {display_goal} — strong industry connections "
                "and graduate hiring in this field."
            )
        elif preferred_countries:
            total += 3
            top_picks = [c.title() for c in preferred_countries[:3]]
            reasons["career"] = (
                f"For {display_goal}, you may find stronger opportunities in "
                f"{', '.join(top_picks)}. {uni.country} still has global employers."
            )
        else:
            total += 4
            reasons["career"] = "Set your career goal to refine country-level job market scoring."
    else:
        total += 4
        reasons["career"] = "Add a career goal to see country-level job market alignment."

    # ── 10. Study environment fit (up to 5 pts) ────────────────────────────────
    env_pts = 0

    # Use preferred_environment if set (overrides study_priority for environment scoring)
    effective_env = study_priority or pref_env

    if effective_env == "research" or _is_research_oriented(user):
        if rank and rank <= 50:
            env_pts = 5
            reasons["environment"] = f"QS #{rank} — world-class research environment, ideal for your research focus."
        elif rank and rank <= 100:
            env_pts = 3
            reasons["environment"] = f"Strong research output at QS #{rank} — aligns with your research priority."
        else:
            env_pts = 1
            reasons["environment"] = "Research priority best served at a top-100 university — explore funding options."
    elif effective_env in ("internships", "startup ecosystem"):
        hub_countries = PRIORITY_HUB_COUNTRIES.get(effective_env, [])
        if uni_country_lo in hub_countries:
            env_pts = 5
            reasons["environment"] = (
                f"{uni.country} is a major hub for {effective_env.replace('_', ' ')} — "
                "strong industry networks and career opportunities."
            )
        else:
            env_pts = 2
            reasons["environment"] = (
                f"For {effective_env.replace('_', ' ')}, countries like USA, UK, Germany, and Singapore "
                "have denser ecosystems — but great opportunities exist globally."
            )
    elif effective_env == "networking":
        hub_countries = PRIORITY_HUB_COUNTRIES.get("networking", [])
        if _is_mba(user) and uni_country_lo in hub_countries:
            env_pts = 5
            reasons["environment"] = f"MBA networking in {uni.country} — excellent alumni networks and global recruiting."
        elif uni_country_lo in hub_countries:
            env_pts = 3
            reasons["environment"] = f"{uni.country} offers strong professional networking opportunities."
        else:
            env_pts = 2
    elif effective_env == "coursework":
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
            reasons["tier"] = f"Safety pick — your CGPA is {buffer:.1f} pts above the minimum. High admission confidence."
        elif buffer >= 0.5:
            total += 2
            reasons["tier"] = f"Strong match — your CGPA is {buffer:.1f} pts above the {req_cgpa:.1f} minimum."
        elif buffer >= 0:
            total += 1
            reasons["tier"] = f"Match — CGPA meets the requirement; differentiate with your SOP and test scores."

    # ── 12. Intake preference bonus (up to 2 pts) ─────────────────────────────
    if intake_pref:
        intake_months_raw = getattr(uni, "intake_months", None) or []
        if intake_months_raw:
            pref_months = INTAKE_SEASON_MAP.get(intake_pref, [intake_pref])
            uni_months_lo = [m.lower() for m in intake_months_raw]
            # Check if any preferred month appears in uni's intake list
            match = any(
                any(pm in um for pm in pref_months)
                for um in uni_months_lo
            )
            if match:
                total += 2
                months_str = ", ".join(intake_months_raw[:3])
                reasons["intake"] = f"Intake match — {uni_name} admits in {months_str}, aligning with your {intake_pref.title()} preference."
            else:
                months_str = ", ".join(intake_months_raw[:3])
                reasons["intake"] = f"Intake note: {uni_name} typically admits in {months_str} — may not align with your {intake_pref.title()} preference."
        else:
            # No intake data — give partial point
            total += 1
            reasons["intake"] = f"Intake timing not confirmed — check if {intake_pref.title()} entry is available."

    # ── 13. Living preference bonus (up to 2 pts) ─────────────────────────────
    if living_pref:
        city_type = _infer_city_type(uni_name, uni.country or "")

        if living_pref in ("urban", "city"):
            if city_type == "urban":
                total += 2
                reasons["living"] = f"City campus — matches your preference for an urban, vibrant environment."
            elif city_type == "suburban":
                total += 0.5
                reasons["living"] = f"Quieter campus setting — may not fully match your urban preference."
        elif living_pref in ("suburban", "quiet", "small town"):
            if city_type == "suburban":
                total += 2
                reasons["living"] = f"Campus in a quieter setting — aligns with your preference."
            elif city_type == "urban":
                total += 0.5
                reasons["living"] = f"City-based campus — may be busier than your preferred environment."
            else:
                total += 1
                reasons["living"] = f"Campus environment in {uni.country} — verify specific location before applying."
        elif living_pref in ("rural", "countryside"):
            if city_type == "suburban":
                total += 1.5
                reasons["living"] = f"More relaxed setting — reasonably aligned with your rural preference."
            elif city_type == "urban":
                total += 0
                reasons["living"] = f"City-based campus — likely busier than your preferred rural environment."
            else:
                total += 1
                reasons["living"] = f"Verify campus location for rural/quiet environment preference."

    # ── Apply hard exclusion cap ───────────────────────────────────────────────
    if capped:
        total = min(total, 8.0)   # max 8/100 for excluded unis

    return round(min(total, 100.0), 1), reasons


def explain_match(user: User, uni: University) -> dict:
    score, reasons = _score_with_reasons(user, uni)
    salary    = GRAD_SALARY_USD.get(uni.country, 55000)
    job_score = JOB_SCORE.get(uni.country, 7.0)

    # DB stores costs in INR — convert to USD for financial calculations
    total_cost_inr = (uni.tuition or 0) + (uni.living_cost or 0)
    total_cost_usd = total_cost_inr / 83.0

    if total_cost_usd > 0:
        net_salary   = salary * 0.75
        annual_repay = net_salary * 0.30
        break_even   = round(total_cost_usd / annual_repay, 1) if annual_repay > 0 else None
        roi_5yr      = round(((net_salary * 5) - total_cost_usd) / total_cost_usd * 100, 1)
    else:
        break_even = roi_5yr = None

    return {
        "match_score": round(score / 100, 3),   # keep 0-1 for frontend compat
        "reasons":     reasons,
        "financial": {
            "total_annual_cost_usd":     round(total_cost_usd) if total_cost_usd else None,
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
            "Strong match", "Intake match", "City campus",
        ])
    ]
    snippet = positives[0] if positives else "Review the factor breakdown above for details."
    return f"{label} ({score:.0f}/100). {snippet}"


# ═══════════════════════════════════════════════════════════════════════════════
# LLM-ENHANCED RECOMMENDATION ENGINE
# Gemini adds semantic reasoning on top of the rule-based score
# ═══════════════════════════════════════════════════════════════════════════════

def _profile_hash(user: User) -> str:
    """Lightweight hash to identify a user's profile state for caching.
    Includes all fields that materially affect recommendations.
    """
    target = sorted(getattr(user, "target_countries", None) or [])
    resume_snippet = (getattr(user, "resume_text", None) or "")[:200]  # first 200 chars as fingerprint
    parts = [
        str(getattr(user, "field_of_study", "")),
        str(getattr(user, "cgpa", "")),
        str(getattr(user, "career_goal", "")),
        str(getattr(user, "preferred_degree", "")),
        str(getattr(user, "budget", "") or getattr(user, "budget_inr", "")),
        str(getattr(user, "study_priority", "")),
        str(getattr(user, "living_preference", "")),
        str(getattr(user, "ranking_preference", "")),
        ",".join(target),
        resume_snippet,
    ]
    return "|".join(parts)


def _build_user_profile_text(user: User) -> str:
    """Render a user's profile as natural language for Gemini."""
    field        = getattr(user, "field_of_study", "") or "unspecified field"
    degree       = getattr(user, "preferred_degree", "") or "Masters"
    cgpa         = getattr(user, "cgpa", None)
    career       = getattr(user, "career_goal", "") or ""
    countries    = getattr(user, "target_countries", []) or []
    budget_usd   = _get_budget_usd(user)
    work_exp     = getattr(user, "work_experience_years", 0) or 0
    study_p      = getattr(user, "study_priority", "") or ""
    ielts        = getattr(user, "english_score", None)
    gre          = getattr(user, "gre_score", None)
    scholarship  = getattr(user, "scholarship_interest", False)
    rank_pref    = getattr(user, "ranking_preference", "") or ""

    resume_text = (getattr(user, "resume_text", None) or "").strip()

    lines = [
        f"Degree sought: {degree} in {field}",
        f"CGPA: {cgpa}/10" if cgpa else "CGPA: not specified",
        f"Work experience: {work_exp} years",
        f"Career goal: {career}" if career else "Career goal: not specified",
        # Hard constraints — labelled explicitly for the LLM
        f"HARD CONSTRAINT — Target countries (only these): {', '.join(countries)}" if countries else "Target countries: open to anywhere",
        f"HARD CONSTRAINT — Ranking preference: {rank_pref} (universities outside this band are a poor fit)" if rank_pref else "",
        f"Annual budget: ${budget_usd:,.0f} USD" if budget_usd else "Budget: flexible",
        f"Study priority: {study_p}" if study_p else "",
        f"IELTS: {ielts}" if ielts else "",
        f"GRE: {gre}" if gre else "",
        f"Scholarship interest: yes" if scholarship else "",
        # Include resume excerpt — first 800 chars gives Gemini enough context
        f"Resume / CV summary (use for skills & specialisations):\n{resume_text[:800]}" if resume_text else "",
    ]
    return "\n".join(l for l in lines if l)


def _build_uni_text(uni: University) -> str:
    """Render a university's key facts for Gemini.
    Tuition and living_cost are stored in INR in the database — convert to USD for Gemini.
    """
    tuition_usd  = round((uni.tuition or 0) / 83)     if uni.tuition     else None
    living_usd   = round((uni.living_cost or 0) / 83) if uni.living_cost else None
    total_usd    = (tuition_usd or 0) + (living_usd or 0)
    subjects     = (uni.subject or "").split("|")[:4]
    subjects_str = ", ".join(s.strip() for s in subjects)

    lines = [
        f"University: {uni.name} ({uni.country})",
        f"Global rank: #{uni.ranking}" if uni.ranking else "Rank: unranked",
        f"Subject rank: #{uni.qs_subject_ranking}" if uni.qs_subject_ranking else "",
        f"Primary subjects: {subjects_str}",
        f"Annual cost: ~${total_usd:,} USD (tuition ${tuition_usd:,} + living ${living_usd:,})" if total_usd else "Cost: not available",
        f"Min CGPA required: {uni.requirements_cgpa}/10" if uni.requirements_cgpa else "",
        f"IELTS minimum: {uni.ielts}" if uni.ielts else "",
        f"Acceptance rate: {round(uni.acceptance_rate * 100)}%" if uni.acceptance_rate else "",
        f"Scholarships: {uni.scholarships}" if uni.scholarships else "",
        f"Description: {uni.description}" if uni.description else "",
    ]
    return "\n".join(l for l in lines if l)


def _gemini_semantic_score(user: User, uni: University) -> dict:
    """
    Ask Gemini to semantically assess the student-university fit.
    Returns {"score": 0-10, "insight": "2-sentence insight", "fit_label": "..."}
    Cached per (profile_hash, uni_id).
    """
    cache_key = f"{_profile_hash(user)}::{uni.id}"
    if cache_key in _LLM_SCORE_CACHE:
        return _LLM_SCORE_CACHE[cache_key]

    try:
        from app.core.config import settings
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return {"score": 5.0, "insight": "", "fit_label": ""}

        from google import genai as _genai
        client = _genai.Client(api_key=api_key)

        profile_txt = _build_user_profile_text(user)
        uni_txt     = _build_uni_text(uni)

        prompt = f"""You are a university admissions advisor assessing fit between a student and a university.

STUDENT PROFILE:
{profile_txt}

UNIVERSITY:
{uni_txt}

STRICT SCORING RULES (apply these before anything else):
1. If the university's country is NOT in the student's target countries → score MAX 3/10, no exceptions.
2. If the university ranking falls far outside the student's ranking preference (e.g. student wants Top 50, university is ranked #300+) → score MAX 3/10.
3. If the primary subjects are a poor match for the student's field of study → score MAX 4/10.
4. Only award 7+ when country, ranking, subject, AND academic requirements all align well.
5. The score must reflect real admissions likelihood, not just budget fit or English score.

Respond ONLY with valid JSON (no markdown):
{{
  "score": <number 0-10, where 10 = perfect fit>,
  "insight": "<exactly 2 sentences: sentence 1 = the single biggest reason this IS or ISN'T a good fit, sentence 2 = the most important action item or concern for this specific student>",
  "fit_label": "<one of: Perfect Fit | Strong Fit | Good Fit | Partial Fit | Weak Fit>"
}}

Be brutally honest and specific. Use the student's actual numbers."""

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = resp.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        result = {
            "score":     float(data.get("score", 5.0)),
            "insight":   data.get("insight", ""),
            "fit_label": data.get("fit_label", ""),
        }
        _LLM_SCORE_CACHE[cache_key] = result
        return result

    except Exception as e:
        logger.debug("Gemini semantic score failed for %s: %s", uni.name, e)
        return {"score": 5.0, "insight": "", "fit_label": ""}


def enhanced_score(user: User, uni: University, use_llm: bool = True) -> float:
    """
    Blended score: 65% rule-based + 35% Gemini semantic.
    Falls back to 100% rule-based if Gemini is unavailable.

    Args:
        user:    User SQLAlchemy model
        uni:     University SQLAlchemy model
        use_llm: Set False to skip Gemini (faster, e.g. for bulk pre-filtering)

    Returns float 0–100.
    """
    rule_score, _ = _score_with_reasons(user, uni)

    if not use_llm:
        return rule_score

    # If rule engine applied a hard exclusion (capped to ≤ 8), don't call LLM —
    # hard constraints (wrong country, wrong ranking) cannot be overridden by semantics.
    if rule_score <= 8:
        return rule_score

    llm_data  = _gemini_semantic_score(user, uni)
    llm_score = llm_data.get("score", 5.0) * 10.0    # 0-10 → 0-100

    blended = round(0.65 * rule_score + 0.35 * llm_score, 1)
    return min(blended, 100.0)


def explain_match_enhanced(user: User, uni: University) -> dict:
    """
    Full match explanation with Gemini-powered semantic insight.
    Extends the original explain_match() with an `ai_analysis` field.
    """
    score, reasons = _score_with_reasons(user, uni)
    salary    = GRAD_SALARY_USD.get(uni.country, 55000)
    job_score = JOB_SCORE.get(uni.country, 7.0)

    # DB stores costs in INR — convert to USD for financial calculations
    total_cost_inr = (uni.tuition or 0) + (uni.living_cost or 0)
    total_cost_usd = total_cost_inr / 83.0

    if total_cost_usd > 0:
        net_salary   = salary * 0.75
        annual_repay = net_salary * 0.30
        break_even   = round(total_cost_usd / annual_repay, 1) if annual_repay > 0 else None
        roi_5yr      = round(((net_salary * 5) - total_cost_usd) / total_cost_usd * 100, 1)
    else:
        break_even = roi_5yr = None

    # Hard-excluded universities (wrong country/ranking) — skip LLM entirely.
    # Rule-based hard constraints cannot be overridden by semantic scoring.
    is_hard_excluded = (score <= 8)
    if is_hard_excluded:
        blended   = score
        llm_score = score   # display as same so UI is honest
        llm_data  = {"score": score / 10, "insight": "", "fit_label": "Not Recommended"}
    else:
        llm_data   = _gemini_semantic_score(user, uni)
        llm_score  = llm_data.get("score", 5.0) * 10.0
        blended    = round(0.65 * score + 0.35 * llm_score, 1)

    return {
        "match_score":       round(blended / 100, 3),
        "rule_score":        round(score / 100, 3),
        "llm_score":         round(llm_score / 100, 3),
        "reasons":           reasons,
        "financial": {
            "total_annual_cost_usd":     round(total_cost_usd) if total_cost_usd else None,
            "estimated_grad_salary_usd": salary,
            "roi_5yr_pct":               roi_5yr,
            "break_even_years":          break_even,
            "job_market_score":          job_score,
        },
        "summary":     _build_summary(blended, reasons),
        "ai_analysis": {
            "insight":   llm_data.get("insight", ""),
            "fit_label": llm_data.get("fit_label", ""),
            "powered_by": "Gemini 2.5 Flash semantic analysis",
        },
    }


def rank_universities_enhanced(
    user: User,
    universities: list,
    top_n: int = 20,
) -> list[dict]:
    """
    Full two-pass ranking:
      Pass 1 (fast): rule-based scoring — keeps top `top_n * 3` candidates
      Pass 2 (LLM):  Gemini semantic scoring on the top `top_n` shortlist
      Returns: sorted list of {university, match_data} dicts

    Args:
        user:         User model
        universities: List of University models
        top_n:        How many final results to return (default 20)
    """
    # Pass 1 — fast rule-based pre-filter
    scored_fast = []
    for uni in universities:
        rule_score, _ = _score_with_reasons(user, uni)
        scored_fast.append((rule_score, uni))

    scored_fast.sort(key=lambda x: x[0], reverse=True)
    shortlist = [uni for _, uni in scored_fast[:top_n * 2]]   # keep 2× for LLM pass

    # Pass 2 — LLM semantic scoring (only on shortlist)
    results = []
    for uni in shortlist[:top_n]:
        match_data = explain_match_enhanced(user, uni)
        results.append({
            "university": uni,
            "match_data": match_data,
        })

    # Sort by blended match_score descending
    results.sort(key=lambda x: x["match_data"]["match_score"], reverse=True)
    return results[:top_n]
