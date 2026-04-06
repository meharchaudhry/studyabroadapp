from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.university import University
from app.services.recommendation import calculate_score
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

router = APIRouter()

class DecisionResponse(BaseModel):
    best_option: str
    explanation: str

@router.get("/", response_model=DecisionResponse)
def get_decision(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    
    # 1. Fetch top university logically
    query = db.query(University)
    if current_user.target_countries:
        query = query.filter(University.country.in_(current_user.target_countries))
    universities = query.all()
    
    best_uni = None
    best_score = -1
    for uni in universities:
        score = calculate_score(current_user, uni)
        if score > best_score:
            best_score = score
            best_uni = uni
            
    if not best_uni:
        return DecisionResponse(
            best_option="General Study Abroad Advice",
            explanation="We need more data to recommend a specific university."
        )
        
    # 2. Ask Gemini to synthesize a final personalized recommendation
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    prompt = f"""
    The user is looking to study abroad.
    Profile: GPA {current_user.gpa}, Budget ${current_user.budget}, Targets: {current_user.target_countries}.
    The best university match found by our algorithm is {best_uni.name} in {best_uni.country}.
    Financial info: Tuition ${best_uni.tuition}, Living Cost ${best_uni.living_cost}.
    
    Write a 3-paragraph personalized recommendation letter telling the user why {best_uni.name} is their best option, 
    touching upon their budget, academic profile, and visa/job prospects in {best_uni.country}.
    Format it enthusiastically and professionally.
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        explanation = response.content
    except Exception as e:
        explanation = f"LLM Generation Error: {e}"
        
    return DecisionResponse(
        best_option=best_uni.name,
        explanation=explanation
    )
