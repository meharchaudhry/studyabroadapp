import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.models.user import User
import google.genai as genai
from app.core.config import settings

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ROIRequest(BaseModel):
    country: str
    tuition: float
    living_cost: float
    loan_amount: float
    study_duration: int
    career_goal: str
    budget: float

def _make_llm(temperature: float = 0.3):
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        logger.error("GOOGLE_API_KEY is not set.")
        raise HTTPException(status_code=500, detail="Google API key is not configured.")
    
    genai.configure(api_key=api_key)
    
    return genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config={"temperature": temperature},
    )

@router.post("/roi")
def get_roi_analysis(
    request: ROIRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Provides a comprehensive ROI analysis for studying abroad, taking into account
    financials, career goals, and personal profile.
    """
    try:
        llm = _make_llm()

        prompt = f"""
            You are a financial advisor for a student looking to study abroad. The student has provided the following information:
            - **Destination Country:** {request.country}
            - **Annual Tuition Fees:** ${request.tuition:,.2f}
            - **Annual Living Costs:** ${request.living_cost:,.2f}
            - **Loan Amount:** ${request.loan_amount:,.2f}
            - **Duration of Study:** {request.study_duration} years
            - **Career Goal:** {request.career_goal}
            - **Annual Budget:** ${request.budget:,.2f}
            - **Student Profile:** A student with a CGPA of {current_user.cgpa}, aiming for a {current_user.preferred_degree} in {current_user.field_of_study}.

            Please provide a detailed ROI analysis that covers the following points:
            1.  **Total Investment:** Calculate the total cost of education, including tuition, living expenses, and an estimated 10% annual interest on the loan over the study duration.
            2.  **Expected Salary:** Estimate the average starting salary for a graduate in '{request.career_goal}' in {request.country}.
            3.  **Break-Even Point:** Calculate how many years it would take to pay off the total investment.
            4.  **5-Year & 10-Year ROI:** Project the return on investment over 5 and 10 years.
            5.  **Risk Assessment:** Provide a brief risk assessment (Low, Medium, High) based on the student's budget, loan amount, and the job market in the destination country.
            6.  **Personalized Advice:** Offer some personalized advice based on the student's career goals and profile. Mention specific industries or companies to target if possible.

            Structure your response as a JSON object with the following keys:
            - "total_investment"
            - "expected_salary"
            - "break_even_years"
            - "roi_5_year"
            - "roi_10_year"
            - "risk_assessment"
            - "personalized_advice"
            - "country_specific_data"
            """

        logger.info(f"Generated prompt for Gemini: {prompt}")

        response = llm.generate_content(prompt)
        logger.info(f"Received response from Gemini: {response.text}")

        return {"analysis": response.text}

    except Exception as e:
        logger.error(f"An error occurred during ROI analysis: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the ROI analysis.")

