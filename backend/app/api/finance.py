import logging
import io
import csv as _csv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings
from google import genai as _genai

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Career salary multipliers (applied on top of country base salary) ─────────
CAREER_MULTIPLIERS = {
    "software engineer":          1.35,
    "software developer":         1.30,
    "data scientist":             1.40,
    "data analyst":               1.15,
    "machine learning engineer":  1.45,
    "ai engineer":                1.45,
    "product manager":            1.35,
    "product designer":           1.10,
    "ux designer":                1.05,
    "ui designer":                1.00,
    "finance":                    1.20,
    "investment banker":          1.60,
    "financial analyst":          1.20,
    "management consultant":      1.50,
    "consultant":                 1.30,
    "marketing":                  0.90,
    "digital marketing":          0.85,
    "researcher":                 0.85,
    "professor":                  0.80,
    "doctor":                     1.30,
    "engineer":                   1.20,
    "mechanical engineer":        1.15,
    "civil engineer":             1.10,
    "electrical engineer":        1.20,
    "biomedical":                 1.05,
    "lawyer":                     1.25,
    "accountant":                 1.05,
    "business analyst":           1.10,
    "supply chain":               1.00,
    "hr":                         0.85,
    "teacher":                    0.75,
    "nurse":                      0.90,
    "architect":                  1.00,
}

# Average grad salary USD by country (base for a generic role)
GRAD_SALARY_USD = {
    "United States": 85000,
    "United Kingdom": 52000,
    "Canada": 58000,
    "Australia": 62000,
    "Germany": 58000,
    "France": 46000,
    "Netherlands": 55000,
    "Ireland": 56000,
    "Singapore": 64000,
    "Japan": 38000,
    "Sweden": 52000,
    "Norway": 62000,
    "Denmark": 60000,
    "Finland": 50000,
    "New Zealand": 50000,
    "UAE": 65000,
    "Portugal": 30000,
    "Italy": 35000,
    "Spain": 36000,
    "South Korea": 42000,
    "Switzerland": 92000,
    "Belgium": 50000,
    "Austria": 52000,
}

INR_PER_USD = 83


class ROIRequest(BaseModel):
    country: str
    tuition_inr: float          # per year, INR
    living_inr: float           # per year, INR
    loan_inr: float             # total loan, INR
    study_duration: int         # years
    career_goal: str
    scholarship_inr: float = 0  # per year, INR
    budget_inr: float = 0       # annual budget cap, INR (0 = skip)
    salary_inr: Optional[float] = None  # user-overridden expected salary


def _career_multiplier(career: str) -> float:
    career_lower = career.lower()
    for key, mult in CAREER_MULTIPLIERS.items():
        if key in career_lower:
            return mult
    return 1.0


def _expected_salary_inr(country: str, career: str, user_override: Optional[float]) -> float:
    if user_override and user_override > 0:
        return user_override
    base_usd = GRAD_SALARY_USD.get(country, 55000)
    mult = _career_multiplier(career)
    return round(base_usd * mult * INR_PER_USD)


@router.post("/roi")
def get_roi_analysis(
    request: ROIRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Deterministic ROI calculations + AI qualitative advice.
    All monetary values in and out are INR.
    """
    try:
        # ── 1. Core cost calculations ─────────────────────────────────────────
        annual_net_cost = request.tuition_inr + request.living_inr - request.scholarship_inr
        total_study_cost = annual_net_cost * request.study_duration

        # Education loan: 8.5% p.a. simple interest during study
        loan_interest_study = request.loan_inr * 0.085 * request.study_duration
        total_investment = total_study_cost + loan_interest_study

        # Loan EMI post-graduation: 7-year repayment at 8.5%
        r_monthly = 0.085 / 12
        n_months = 84  # 7 years
        if request.loan_inr > 0 and r_monthly > 0:
            emi_monthly = request.loan_inr * r_monthly / (1 - (1 + r_monthly) ** (-n_months))
        else:
            emi_monthly = 0
        emi_annual = emi_monthly * 12

        # ── 2. Salary & year-by-year projections ─────────────────────────────
        salary_growth_pct = 0.08  # 8% year-on-year
        year1_salary = _expected_salary_inr(request.country, request.career_goal, request.salary_inr)

        projections = []
        cumulative_earnings = 0.0
        break_even_year = None

        for yr in range(1, 13):
            salary = round(year1_salary * ((1 + salary_growth_pct) ** (yr - 1)))
            emi = round(emi_annual) if yr <= 7 else 0
            net_annual = salary - emi
            cumulative_earnings += net_annual

            net_position = cumulative_earnings - total_investment
            if break_even_year is None and cumulative_earnings >= total_investment:
                break_even_year = yr

            projections.append({
                "year": yr,
                "salary_inr": salary,
                "emi_inr": emi,
                "net_annual_inr": net_annual,
                "cumulative_earnings_inr": round(cumulative_earnings),
                "net_position_inr": round(net_position),
            })

        if break_even_year is None:
            break_even_year = 15  # beyond 12-year window

        # ── 3. ROI metrics ────────────────────────────────────────────────────
        cum_5yr = projections[4]["cumulative_earnings_inr"] if len(projections) >= 5 else 0
        cum_10yr = projections[9]["cumulative_earnings_inr"] if len(projections) >= 10 else 0

        roi_5yr = round((cum_5yr - total_investment) / total_investment * 100) if total_investment else 0
        roi_10yr = round((cum_10yr - total_investment) / total_investment * 100) if total_investment else 0

        # ── 4. Cost breakdown for doughnut chart ─────────────────────────────
        tuition_total = request.tuition_inr * request.study_duration
        living_total = request.living_inr * request.study_duration
        scholarship_total = request.scholarship_inr * request.study_duration

        cost_breakdown = {
            "tuition_total": round(tuition_total),
            "living_total": round(living_total),
            "loan_interest": round(loan_interest_study),
            "scholarship_savings": round(scholarship_total),
        }

        # ── 5. AI qualitative advice (short prompt, flash model) ──────────────
        advice = _get_ai_advice(request, current_user, year1_salary, break_even_year, roi_5yr, roi_10yr)

        # ── 6. Budget check ───────────────────────────────────────────────────
        over_budget = (
            request.budget_inr > 0 and annual_net_cost > request.budget_inr
        )

        return {
            "total_investment_inr": round(total_investment),
            "annual_cost_inr": round(annual_net_cost),
            "year1_salary_inr": year1_salary,
            "emi_monthly_inr": round(emi_monthly),
            "break_even_year": break_even_year,
            "roi_5yr": roi_5yr,
            "roi_10yr": roi_10yr,
            "cost_breakdown": cost_breakdown,
            "projections": projections,
            "over_budget": over_budget,
            "advice": advice,
            "salary_growth_pct": int(salary_growth_pct * 100),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ROI analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _get_ai_advice(request, user, salary_inr, break_even, roi_5, roi_10) -> str:
    """Short Gemini call for qualitative advice only."""
    try:
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return ""
        client = _genai.Client(api_key=api_key)
        total_lakhs = round((request.tuition_inr + request.living_inr) * request.study_duration / 100000)
        salary_lakhs = round(salary_inr / 100000)
        prompt = (
            f"You are a concise financial advisor for Indian students studying abroad.\n"
            f"Student profile: CGPA {getattr(user,'cgpa','N/A')}, "
            f"studying {getattr(user,'field_of_study','') or 'unknown field'} "
            f"({getattr(user,'preferred_degree','') or 'Masters'}).\n"
            f"Destination: {request.country} | Career goal: {request.career_goal}\n"
            f"Total cost: ₹{total_lakhs}L over {request.study_duration} yrs | "
            f"Loan: ₹{round(request.loan_inr/100000)}L | "
            f"Expected salary: ₹{salary_lakhs}L/yr | Break-even: {break_even} yrs | "
            f"5yr ROI: {roi_5}% | 10yr ROI: {roi_10}%\n\n"
            f"Give 3-4 short bullet points of actionable advice. Cover: "
            f"(1) whether this investment is financially sound, "
            f"(2) best industries/companies to target in {request.country} for {request.career_goal}, "
            f"(3) one specific scholarship or funding tip, "
            f"(4) one risk to watch out for. "
            f"Be specific, practical, and use INR figures. Keep total under 150 words."
        )
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return resp.text or ""
    except Exception as e:
        logger.warning(f"AI advice failed: {e}")
        return ""


# ── CSV export endpoint ────────────────────────────────────────────────────────
@router.get("/export-csv")
def export_roi_csv(
    country:       str   = Query(...),
    tuition_inr:   float = Query(...),
    living_inr:    float = Query(...),
    loan_inr:      float = Query(0),
    study_duration:int   = Query(2),
    career_goal:   str   = Query("Graduate"),
    scholarship_inr:float= Query(0),
    current_user: User = Depends(get_current_user),
):
    """Returns a properly-formatted CSV file for browser download."""
    INR_TO_USD = 1 / 83
    annual_net   = tuition_inr + living_inr - scholarship_inr
    tuition_tot  = tuition_inr * study_duration
    living_tot   = living_inr  * study_duration
    loan_int     = loan_inr * 0.085 * study_duration
    total_inv    = annual_net * study_duration + loan_int

    r_m = 0.085 / 12
    emi_monthly = loan_inr * r_m / (1 - (1 + r_m) ** (-84)) if loan_inr > 0 else 0
    emi_annual  = emi_monthly * 12

    base_usd = {
        "United States":70000,"United Kingdom":52000,"Canada":58000,
        "Australia":62000,"Germany":58000,"France":46000,"Netherlands":55000,
        "Ireland":56000,"Singapore":64000,"Japan":38000,"Sweden":52000,
        "Norway":62000,"UAE":65000,"Switzerland":92000,
    }.get(country, 55000)
    year1 = round(base_usd * _career_multiplier(career_goal) * 83)

    rows = [
        ["StudyPathway ROI Analysis"],
        [],
        ["SUMMARY"],
        ["Country", country],
        ["Career Goal", career_goal],
        ["Study Duration (yrs)", study_duration],
        [],
        ["COST BREAKDOWN", "INR", "Approx USD"],
        ["Total Tuition", int(tuition_tot),  int(tuition_tot  * INR_TO_USD)],
        ["Total Living",  int(living_tot),   int(living_tot   * INR_TO_USD)],
        ["Loan Interest", int(loan_int),     int(loan_int     * INR_TO_USD)],
        ["TOTAL INVESTMENT", int(total_inv), int(total_inv    * INR_TO_USD)],
        [],
        ["ROI METRICS"],
        ["Yr-1 Expected Salary", year1, int(year1 * INR_TO_USD)],
        ["Monthly EMI", int(emi_monthly), int(emi_monthly * INR_TO_USD)],
        [],
        ["10-YEAR PROJECTION"],
        ["Year","Annual Salary (INR)","Loan EMI (INR)","Net Annual (INR)",
         "Cumulative Earnings (INR)","Net vs Investment (INR)"],
    ]

    cum = 0.0
    for yr in range(1, 11):
        sal = round(year1 * (1.08 ** (yr - 1)))
        emi = round(emi_annual) if yr <= 7 else 0
        cum += sal - emi
        rows.append([yr, sal, emi, sal - emi, int(cum), int(cum - total_inv)])

    buf = io.StringIO()
    writer = _csv.writer(buf)
    writer.writerows(rows)
    buf.seek(0)

    filename = f"StudyPathway_ROI_{country.replace(' ', '_')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
