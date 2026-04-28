"""
AI Agent API endpoints
======================
Exposes Gemini-powered features:
  POST /ai/generate-checklist       — personalised document checklist
  GET  /ai/checklist/{country}      — load saved checklist progress
  PUT  /ai/checklist/{country}      — save checklist progress
  POST /ai/generate-timeline        — month-by-month application plan
  POST /ai/analyze-profile          — profile gap analysis
  POST /ai/chat                     — AI study coach conversation
  POST /ai/generate-sop             — Statement of Purpose outline
"""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.visa_checklist import UserVisaChecklist
from app.services.ai_agent import (
    generate_checklist,
    generate_timeline,
    analyze_profile,
    ai_coach_chat,
    generate_sop_outline,
)
from app.services.agent_service import agent_coach_chat

router = APIRouter()


# ── Request / Response models ──────────────────────────────────────────────────

class ChecklistRequest(BaseModel):
    country: str
    profile: Optional[dict] = {}


class ChecklistSaveRequest(BaseModel):
    checklist: list
    checked: dict
    metadata: Optional[dict] = {}


class TimelineRequest(BaseModel):
    intake: str = "Fall"
    countries: Optional[list] = []
    profile: Optional[dict] = {}
    current_status: Optional[dict] = {}


class ProfileRequest(BaseModel):
    profile: dict


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    profile: Optional[dict] = {}
    history: Optional[list] = []


class SopRequest(BaseModel):
    profile: Optional[dict] = {}
    university: str = ""
    program: str = ""
    country: str = ""


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/generate-checklist")
def api_generate_checklist(
    req: ChecklistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    result = generate_checklist(req.country, req.profile or {})
    # Auto-save the freshly generated checklist to DB
    if result and result.get("checklist") and not result.get("error"):
        _upsert_checklist(
            db, current_user.id, req.country,
            items=result["checklist"],
            checked={},
            meta={
                "visa_type": result.get("visa_type", ""),
                "visa_fee_usd": result.get("visa_fee_usd", 0),
                "timeline_weeks": result.get("timeline_weeks", 8),
                "summary": result.get("summary", ""),
                "country": result.get("country", req.country),
            },
        )
    return result


@router.get("/checklist/{country}")
def api_get_checklist(
    country: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    row = db.query(UserVisaChecklist).filter(
        UserVisaChecklist.user_id == current_user.id,
        UserVisaChecklist.country == country,
    ).first()
    if not row:
        return {"saved": False}
    meta = json.loads(row.metadata_json or "{}")
    return {
        "saved": True,
        "items": json.loads(row.items_json or "[]"),
        "checked": json.loads(row.checked_json or "{}"),
        "visa_type": meta.get("visa_type", ""),
        "visa_fee_usd": meta.get("visa_fee_usd", 0),
        "timeline_weeks": meta.get("timeline_weeks", 8),
        "summary": meta.get("summary", ""),
        "country": meta.get("country", country),
    }


@router.put("/checklist/{country}")
def api_save_checklist(
    country: str,
    req: ChecklistSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    _upsert_checklist(db, current_user.id, country, req.checklist, req.checked, req.metadata or {})
    return {"saved": True}


def _upsert_checklist(db: Session, user_id: int, country: str, items: list, checked: dict, meta: dict):
    row = db.query(UserVisaChecklist).filter(
        UserVisaChecklist.user_id == user_id,
        UserVisaChecklist.country == country,
    ).first()
    now = datetime.utcnow()
    if row:
        row.items_json   = json.dumps(items)
        row.checked_json = json.dumps(checked)
        row.metadata_json = json.dumps(meta)
        row.updated_at   = now
    else:
        row = UserVisaChecklist(
            user_id=user_id,
            country=country,
            checklist_type="official",
            items_json=json.dumps(items),
            checked_json=json.dumps(checked),
            metadata_json=json.dumps(meta),
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()


@router.post("/generate-timeline")
def api_generate_timeline(
    req: TimelineRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    result = generate_timeline(req.intake, req.countries or [], req.profile or {}, req.current_status or {})
    return result


@router.post("/analyze-profile")
def api_analyze_profile(
    req: ProfileRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    result = analyze_profile(req.profile)
    return result


@router.post("/chat")
def api_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    AI Study Coach — now powered by a LangChain ReAct agent with real tools.
    Falls back to structured prompts if the agent cannot run.
    """
    result = agent_coach_chat(
        message=req.message,
        profile=req.profile or {},
        history=req.history or [],
        db=db,
    )
    return result


@router.post("/chat/simple")
def api_chat_simple(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Legacy endpoint — structured prompt only, no tool use."""
    reply = ai_coach_chat(req.message, req.profile or {}, req.history or [])
    return {"reply": reply, "tool_calls": [], "agent_used": False}


@router.post("/generate-sop")
def api_generate_sop(
    req: SopRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    from app.services.ai_agent import generate_sop_outline, resolve_university_country
    resolved = resolve_university_country(req.university, req.country)
    outline  = generate_sop_outline(req.profile or {}, req.university, req.program, resolved["country"])
    return {
        "outline":          outline,
        "resolved_country": resolved["country"],
        "country_source":   resolved["source"],   # "lookup" | "user" | "unknown"
        "country_note":     resolved.get("note", ""),
    }
