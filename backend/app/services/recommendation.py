from typing import Any, Dict, List, Optional


def _get_user_cgpa(user: Any) -> Optional[float]:
    # Backward compatible: if user has direct cgpa attribute, use it.
    if hasattr(user, "cgpa") and getattr(user, "cgpa") is not None:
        return float(getattr(user, "cgpa"))

    # Current schema stores CGPA in user degrees.
    degrees = getattr(user, "degrees", None) or []
    values = [d.cgpa for d in degrees if getattr(d, "cgpa", None) is not None]
    if not values:
        return None
    return float(max(values))


def _country_match(user: Any, uni_country: str) -> bool:
    targets = getattr(user, "target_countries", None) or []
    return bool(targets and uni_country in targets)


def _get_user_tests(user: Any) -> Dict[str, float]:
    tests = getattr(user, "tests", None) or []
    out: Dict[str, float] = {}
    for t in tests:
        test_name = str(getattr(t, "test_name", "") or "").upper().strip()
        score = getattr(t, "score", None)
        if test_name and score is not None:
            out[test_name] = float(score)
    return out


def _get_user_specializations(user: Any) -> List[str]:
    degrees = getattr(user, "degrees", None) or []
    specs = []
    for d in degrees:
        s = str(getattr(d, "specialization", "") or "").strip().lower()
        if s:
            specs.append(s)
    return specs


def _study_priority_weights(user: Any) -> Dict[str, float]:
    priority = str(getattr(user, "study_priority", "") or "").lower()
    if priority == "ranking":
        return {"academic": 0.25, "budget": 0.15, "rank": 0.40, "country": 0.10, "tests": 0.10}
    if priority == "budget":
        return {"academic": 0.20, "budget": 0.40, "rank": 0.15, "country": 0.10, "tests": 0.15}
    if priority == "work":
        return {"academic": 0.20, "budget": 0.20, "rank": 0.20, "country": 0.25, "tests": 0.15}
    return {"academic": 0.30, "budget": 0.30, "rank": 0.25, "country": 0.10, "tests": 0.05}


def _career_goal_subject_bonus(user: Any, uni: Any) -> float:
    goal = str(getattr(user, "career_goal", "") or "").lower()
    subject = str(getattr(uni, "subject", "") or "").lower()
    if not subject:
        return 0.0

    if goal == "industry" and any(k in subject for k in ["computer", "data", "engineering", "business"]):
        return 0.04
    if goal == "research" and any(k in subject for k in ["science", "engineering", "medicine", "law", "psychology"]):
        return 0.04
    if goal == "entrepreneur" and any(k in subject for k in ["business", "economics", "management"]):
        return 0.04
    if goal == "pivot":
        return 0.02
    return 0.0


def _specialization_bonus(user: Any, uni: Any) -> float:
    specs = _get_user_specializations(user)
    subject = str(getattr(uni, "subject", "") or "").lower()
    if not specs or not subject:
        return 0.0

    for spec in specs:
        for token in spec.split():
            token = token.strip()
            if len(token) >= 4 and token in subject:
                return 0.05
    return 0.0


def _test_fit_score(user: Any, uni: Any) -> float:
    tests = _get_user_tests(user)
    s = 0.0

    ielts_req = getattr(uni, "ielts", None)
    toefl_req = getattr(uni, "toefl", None)
    gre_req = getattr(uni, "gre_required", None)

    ielts_user = tests.get("IELTS")
    toefl_user = tests.get("TOEFL")
    pte_user = tests.get("PTE")
    gre_user = tests.get("GRE")
    gmat_user = tests.get("GMAT")

    if ielts_req is not None:
        if ielts_user is not None and ielts_user >= float(ielts_req):
            s += 0.06
        elif pte_user is not None and pte_user >= 58:
            s += 0.04
    elif ielts_user is not None or toefl_user is not None or pte_user is not None:
        s += 0.03

    if toefl_req is not None and toefl_user is not None and toefl_user >= float(toefl_req):
        s += 0.06

    if gre_req:
        if gre_user is not None or gmat_user is not None:
            s += 0.05
        else:
            s -= 0.03

    return s


def _work_experience_bonus(user: Any, uni: Any) -> float:
    exp = getattr(user, "work_experience_years", None)
    subject = str(getattr(uni, "subject", "") or "").lower()
    if exp is None:
        return 0.0
    if exp >= 2 and any(k in subject for k in ["business", "management", "economics"]):
        return 0.03
    if exp == 0 and any(k in subject for k in ["data", "computer", "engineering"]):
        return 0.02
    return 0.0


def _country_work_rights_bonus(user: Any, uni: Any) -> float:
    priority = str(getattr(user, "study_priority", "") or "").lower()
    if priority != "work":
        return 0.0

    # Simplified signal map for post-study work friendliness.
    map_score = {
        "united kingdom": 0.06,
        "canada": 0.06,
        "australia": 0.05,
        "germany": 0.05,
        "netherlands": 0.04,
        "ireland": 0.05,
        "united states": 0.03,
    }
    country = str(getattr(uni, "country", "") or "").lower()
    return map_score.get(country, 0.02)


def build_match_explanation(user: Any, uni: Any, score: float) -> str:
    cgpa = _get_user_cgpa(user)
    parts = []

    if cgpa is not None and getattr(uni, "requirements_cgpa", None):
        if cgpa >= uni.requirements_cgpa:
            parts.append("your CGPA meets this university's minimum requirement")
        else:
            parts.append("your CGPA is slightly below the listed requirement")

    total_cost = (getattr(uni, "tuition", 0) or 0) + (getattr(uni, "living_cost", 0) or 0)
    budget = getattr(user, "budget", None)
    if budget and total_cost:
        if total_cost <= budget:
            parts.append("the yearly cost is within your budget")
        else:
            parts.append("the yearly cost is above your budget, but may still be a stretch option")

    rank = getattr(uni, "qs_subject_ranking", None) or getattr(uni, "ranking", None)
    if rank:
        parts.append(f"its ranking profile is competitive (rank {rank})")

    if _country_match(user, getattr(uni, "country", "")):
        parts.append("it matches one of your preferred target countries")

    tests = _get_user_tests(user)
    if tests:
        if getattr(uni, "ielts", None) and tests.get("IELTS") is not None:
            parts.append("your IELTS score was considered against this university's requirement")
        elif getattr(uni, "toefl", None) and tests.get("TOEFL") is not None:
            parts.append("your TOEFL score was considered against this university's requirement")

    if _specialization_bonus(user, uni) > 0:
        parts.append("your specialization aligns with this university's subject area")

    if _career_goal_subject_bonus(user, uni) > 0:
        parts.append("your stated career goal aligns with this subject pathway")

    if _work_experience_bonus(user, uni) > 0:
        parts.append("your work experience was included in profile matching")

    if not parts:
        parts.append("it is a strong overall fit against your profile")

    return f"{round(score * 100)}% match: " + "; ".join(parts) + "."


def calculate_score(user: Any, uni: Any) -> float:
    score = 0.0
    cgpa = _get_user_cgpa(user)
    weights = _study_priority_weights(user)
    
    # 1. CGPA fit (35%) — checks eligibility against requirements_cgpa
    if cgpa and uni.requirements_cgpa:
        if cgpa >= uni.requirements_cgpa:
            # Reward being well above minimum
            excess = cgpa - uni.requirements_cgpa
            score += min(weights["academic"], 0.20 + (excess / 10.0) * weights["academic"])
        else:
            # Below minimum — partial score (might still apply)
            gap = uni.requirements_cgpa - cgpa
            score += max(0.0, 0.08 - gap * 0.04)
    elif cgpa:
        # No requirement set — use raw CGPA
        score += (cgpa / 10.0) * (weights["academic"] * 0.75)

    # 2. Budget fit (30%) — tuition + living_cost vs user budget
    total_cost = (uni.tuition or 0) + (uni.living_cost or 0)
    if getattr(user, "budget", None) and total_cost > 0:
        budget = user.budget
        if total_cost <= budget:
            score += weights["budget"]
        elif total_cost <= budget * 1.15:
            score += weights["budget"] * 0.67
        elif total_cost <= budget * 1.30:
            score += weights["budget"] * 0.33

    # 3. QS Subject Ranking bonus (25%)
    rank = uni.qs_subject_ranking or uni.ranking
    if rank:
        if rank <= 10:
            score += weights["rank"]
        elif rank <= 50:
            score += weights["rank"] * 0.8
        elif rank <= 100:
            score += weights["rank"] * 0.6
        elif rank <= 200:
            score += weights["rank"] * 0.4
        else:
            score += weights["rank"] * 0.2

    # 4. Country preference (10%)
    if _country_match(user, uni.country):
        score += weights["country"]

    # 5. Test compatibility and profile enrichment bonuses.
    score += min(max(_test_fit_score(user, uni), -0.05), weights["tests"])
    score += _specialization_bonus(user, uni)
    score += _career_goal_subject_bonus(user, uni)
    score += _work_experience_bonus(user, uni)
    score += _country_work_rights_bonus(user, uni)

    return round(min(score, 1.0), 3)
