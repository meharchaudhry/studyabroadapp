from app.models.user import User
from app.models.university import University

def calculate_score(user: User, uni: University) -> float:
    score = 0.0
    
    # 1. CGPA fit (35%) — checks eligibility against requirements_cgpa
    if user.cgpa and uni.requirements_cgpa:
        if user.cgpa >= uni.requirements_cgpa:
            # Reward being well above minimum
            excess = user.cgpa - uni.requirements_cgpa
            score += min(0.35, 0.25 + (excess / 10.0) * 0.10)
        else:
            # Below minimum — partial score (might still apply)
            gap = uni.requirements_cgpa - user.cgpa
            score += max(0.0, 0.10 - gap * 0.05)
    elif user.cgpa:
        # No requirement set — use raw CGPA
        score += (user.cgpa / 10.0) * 0.25

    # 2. Budget fit (30%) — tuition + living_cost vs user budget
    total_cost = (uni.tuition or 0) + (uni.living_cost or 0)
    if user.budget and total_cost > 0:
        if total_cost <= user.budget:
            score += 0.30
        elif total_cost <= user.budget * 1.15:
            score += 0.20
        elif total_cost <= user.budget * 1.30:
            score += 0.10

    # 3. QS Subject Ranking bonus (25%)
    rank = uni.qs_subject_ranking or uni.ranking
    if rank:
        if rank <= 10:
            score += 0.25
        elif rank <= 50:
            score += 0.20
        elif rank <= 100:
            score += 0.15
        elif rank <= 200:
            score += 0.10
        else:
            score += 0.05

    # 4. Country preference (10%)
    if user.target_countries and uni.country in user.target_countries:
        score += 0.10

    return round(min(score, 1.0), 3)
