"""
AI Agent API endpoints
======================
Exposes Claude-powered features:
  POST /ai/generate-checklist   — personalised document checklist
  POST /ai/generate-timeline    — month-by-month application plan
  POST /ai/analyze-profile      — profile gap analysis
  POST /ai/chat                 — AI study coach conversation
  POST /ai/generate-sop         — Statement of Purpose outline
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.ai_agent import (
    generate_checklist,
    generate_timeline,
    analyze_profile,
    ai_coach_chat,
    generate_sop_outline,
)

router = APIRouter()


# ── Request / Response models ──────────────────────────────────────────────────

class ChecklistRequest(BaseModel):
    country: str
    profile: Optional[dict] = {}


class TimelineRequest(BaseModel):
    intake: str = "Fall"
    countries: Optional[list] = []
    profile: Optional[dict] = {}


class ProfileRequest(BaseModel):
    profile: dict


class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    profile: Optional[dict] = {}
    history: Optional[list] = []


class SopRequest(BaseModel):
    profile: Optional[dict] = {}
    university: str = ""
    program: str = ""


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/generate-checklist")
def api_generate_checklist(
    req: ChecklistRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a personalised document checklist for the given country."""
    result = generate_checklist(req.country, req.profile or {})
    return result


@router.post("/generate-timeline")
def api_generate_timeline(
    req: TimelineRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a month-by-month application timeline."""
    result = generate_timeline(req.intake, req.countries or [], req.profile or {})
    return result


@router.post("/analyze-profile")
def api_analyze_profile(
    req: ProfileRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Analyse profile strengths, gaps, and recommended actions."""
    result = analyze_profile(req.profile)
    return result


@router.post("/chat")
def api_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Send a message to the AI study coach and get a response."""
    reply = ai_coach_chat(req.message, req.profile or {}, req.history or [])
    return {"reply": reply}


@router.post("/generate-sop")
def api_generate_sop(
    req: SopRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a personalised SOP outline."""
    outline = generate_sop_outline(req.profile or {}, req.university, req.program)
    return {"outline": outline}
