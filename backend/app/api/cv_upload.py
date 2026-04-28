"""
CV / Resume Upload & Extraction
================================
POST /cv/extract   — upload a PDF/DOCX, get back extracted profile fields
                     AND persist the raw resume text to user.resume_text
                     so the recommendation engine can use it.
DELETE /cv/resume  — clear saved resume text
GET  /cv/resume    — return whether a resume has been saved
"""

import base64
import io
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}
MAX_SIZE_MB = 5


# ── Text extractors ────────────────────────────────────────────────────────────

def _extract_pdf_text(data: bytes) -> str:
    try:
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        pass
    try:
        import pypdf, io
        reader = pypdf.PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {e}")


def _extract_docx_text(data: bytes) -> str:
    try:
        import docx, io
        doc = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read DOCX: {e}")


def _extract_text(data: bytes, content_type: str) -> str:
    if "pdf" in content_type:
        return _extract_pdf_text(data)
    if "word" in content_type or "docx" in content_type:
        return _extract_docx_text(data)
    return data.decode("utf-8", errors="ignore")


# ── Gemini extraction ──────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """\
You are an assistant that extracts structured information from a student's CV/resume.

Read the CV text below and extract ONLY the fields you can find with reasonable confidence.
For fields not found, use null.

Return ONLY valid JSON — no markdown, no code block, no explanation:

{
  "name": null,
  "email": null,
  "field_of_study": null,
  "preferred_degree": null,
  "cgpa": null,
  "english_test": null,
  "english_score": null,
  "toefl_score": null,
  "gre_score": null,
  "gmat_score": null,
  "work_experience_years": null,
  "career_goal": null,
  "target_countries": [],
  "skills": [],
  "education_summary": null,
  "experience_summary": null,
  "projects_summary": null,
  "budget_inr": null,
  "intake_preference": null
}

Rules:
- cgpa: extract as float on 10-point scale. If given on 4-point scale, multiply by 2.5.
- english_test: one of "IELTS" / "TOEFL" / "PTE" / "Duolingo"
- english_score: the numeric score (IELTS band, TOEFL total, etc.)
- preferred_degree: one of "Bachelors" / "Masters" / "MBA" / "PhD"
- field_of_study: the primary academic field (e.g. "Computer Science", "Data Science", "MBA")
- target_countries: list of countries mentioned as study destinations
- work_experience_years: total years as integer or float
- career_goal: a short phrase (e.g. "Software Engineer", "Data Scientist", "Product Manager")
- education_summary: 1-2 sentences summarising education history
- experience_summary: 1-2 sentences summarising work experience
- projects_summary: 1-2 sentences summarising notable projects or research

CV TEXT:
{cv_text}
"""


def _gemini_extract(cv_text: str) -> dict:
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY not configured.")

    from google import genai as _genai
    client = _genai.Client(api_key=api_key)

    prompt = EXTRACTION_PROMPT.replace("{cv_text}", cv_text[:12000])  # cap at ~12k chars

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    raw = resp.text.strip()
    # Strip markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    # Clean up nulls and empty lists
    cleaned = {}
    for k, v in data.items():
        if v is not None and v != [] and v != "":
            cleaned[k] = v

    return cleaned


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.get("/resume")
def get_resume_status(current_user: User = Depends(get_current_user)) -> Any:
    """Return whether the user has a saved resume and its filename."""
    has_resume = bool(getattr(current_user, "resume_text", None))
    return {
        "has_resume": has_resume,
        "filename": getattr(current_user, "resume_filename", None),
        "chars": len(current_user.resume_text) if has_resume else 0,
    }


@router.delete("/resume")
def delete_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Clear the user's saved resume text."""
    current_user.resume_text = None
    current_user.resume_filename = None
    db.commit()
    return {"success": True, "message": "Resume cleared. Recommendations will no longer use resume data."}


@router.post("/extract")
async def extract_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Upload a CV/resume (PDF, DOCX, or TXT).
    - Extracts structured profile fields via Gemini AI.
    - Saves the raw resume text to the user's profile for recommendation scoring.
    Returns extracted fields that can be applied to the user's profile.
    """
    content_type = file.content_type or ""
    if not any(t in content_type for t in ["pdf", "word", "docx", "text"]):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {content_type}. Upload a PDF, DOCX, or TXT file.",
        )

    data = await file.read()

    if len(data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_SIZE_MB} MB.")

    if len(data) == 0:
        raise HTTPException(status_code=422, detail="File is empty.")

    # Extract text
    try:
        cv_text = _extract_text(data, content_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text: {e}")

    if len(cv_text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Could not extract readable text from this file. Try a text-based PDF.")

    # ── Persist raw resume text to user profile ────────────────────────────────
    # This is used by the recommendation engine to provide richer subject matching
    # and by the Gemini semantic scoring to understand the student's background.
    try:
        current_user.resume_text = cv_text[:20000]   # cap at 20k chars
        current_user.resume_filename = file.filename
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Could not save resume_text to user profile: %s", e)
        # Non-fatal — continue with extraction even if save fails

    # Gemini extraction
    try:
        extracted = _gemini_extract(cv_text)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI extraction returned invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("CV extraction error: %s", e)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    return {
        "success": True,
        "filename": file.filename,
        "chars_extracted": len(cv_text),
        "resume_saved": True,
        "extracted": extracted,
    }
