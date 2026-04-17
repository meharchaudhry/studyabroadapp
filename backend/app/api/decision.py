from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.decision_chain import run_decision_chain

router = APIRouter()

class AgentStep(BaseModel):
    id: str
    name: str
    result: str


class RecommendationItem(BaseModel):
    id: int
    name: str
    country: str
    subject: Optional[str] = None
    match_score: float
    final_score: float
    reason: str
    visa: dict
    finance: dict
    jobs: dict


class DecisionResponse(BaseModel):
    best_option: str
    explanation: str
    recommendations: List[RecommendationItem] = []
    agent_steps: List[AgentStep] = []

@router.get("/", response_model=DecisionResponse)
def get_decision(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    result = run_decision_chain(db, current_user)
    return DecisionResponse(**result)
