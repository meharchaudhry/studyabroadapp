from datetime import datetime
import json
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.visa_checklist import UserVisaChecklist
from app.core.database import get_db
from app.services.rag import get_visa_assistant_chain, evaluate_rag_response, clear_session_memory

router = APIRouter()


class VisaQueryRequest(BaseModel):
    query: str
    country: str
    session_id: Optional[str] = "default"  # conversation memory key


class SourceInfo(BaseModel):
    doc: str
    chunk: str


class VisaQueryResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
    metrics: dict


class ChecklistItem(BaseModel):
    id: str
    category: str
    item: str


class VisaChecklistResponse(BaseModel):
    country: str
    visa_type: str
    official_link: str
    processing_time: str
    visa_fee_inr: int
    checklist: list[ChecklistItem]
    source_doc: Optional[str] = None
    official_guidance: Optional[str] = None
    overview_summary: Optional[str] = None
    overview_points: list[str] = Field(default_factory=list)


class SaveChecklistRequest(BaseModel):
    country: str
    checklist_type: str = "official"
    title: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    items: list[dict] = Field(default_factory=list)
    checked: dict[str, bool] = Field(default_factory=dict)


class SavedChecklistResponse(BaseModel):
    country: str
    checklist_type: str
    title: Optional[str] = None
    metadata: dict
    items: list[dict]
    checked: dict[str, bool]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def load_visa_data():
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "visa_data.json"
    )
    with open(data_path, "r") as f:
        return json.load(f)


def _visa_docs_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "visa_docs",
    )


def _normalize_country_key(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _find_country_visa_doc(country: str) -> Optional[str]:
    docs_dir = _visa_docs_dir()
    if not os.path.isdir(docs_dir):
        return None

    files = [f for f in os.listdir(docs_dir) if f.lower().endswith(".md")]
    if not files:
        return None

    country_norm = _normalize_country_key(country)
    preferred = [
        f"{country.lower().replace(' ', '_')}.md",
        f"{country.lower().replace(' ', '')}.md",
    ]
    for name in preferred:
        if name in files:
            return name

    for filename in sorted(files):
        stem = os.path.splitext(filename)[0]
        stem_norm = _normalize_country_key(stem)
        if stem_norm == country_norm or stem_norm.startswith(country_norm):
            return filename

    return None


def _read_guidance_excerpt(filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    path = os.path.join(_visa_docs_dir(), filename)
    if not os.path.isfile(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    cleaned = [line for line in lines if not line.startswith("#") and not line.lower().startswith("official link:")]
    if not cleaned:
        return None

    joined = "\n".join(cleaned)
    return joined[:1600] + ("..." if len(joined) > 1600 else "")


def _sentence_split(text: str) -> list[str]:
    parts = [chunk.strip() for chunk in text.replace("\n", " ").split(".")]
    return [p + "." for p in parts if len(p) > 20]


def _get_visa_llm() -> Optional[ChatGoogleGenerativeAI]:
    api_key = settings.GOOGLE_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=api_key,
    )


def _summarize_country_guidance(country_data: dict, guidance: Optional[str]) -> tuple[str, list[str]]:
    """Create a concise, deterministic overview from checklist metadata + doc text."""
    checklist = country_data.get("checklist", []) or []
    categories = sorted({item.get("category", "Other") for item in checklist if isinstance(item, dict)})

    base = (
        f"{country_data.get('visa_type', 'Student visa')} typically requires a structured application "
        f"with identity, academic, and financial evidence. "
        f"Estimated processing time is {country_data.get('processing_time', 'varies by case')}"
    )
    if country_data.get("visa_fee_inr", 0):
        base += f", and the listed visa fee is about INR {country_data['visa_fee_inr']:,}."
    else:
        base += "."

    keyword_buckets = [
        "passport", "financial", "bank", "fund", "proof", "insurance",
        "english", "ielts", "toefl", "biometric", "medical", "tb", "interview",
    ]
    doc_points: list[str] = []
    if guidance:
        for sentence in _sentence_split(guidance):
            lo = sentence.lower()
            if any(k in lo for k in keyword_buckets):
                doc_points.append(sentence)
            if len(doc_points) >= 3:
                break

    points = [
        f"Checklist contains {len(checklist)} core items across {len(categories)} categories.",
    ]
    if categories:
        points.append(f"Main categories: {', '.join(categories[:5])}{'...' if len(categories) > 5 else ''}.")
    points.extend(doc_points)

    deduped: list[str] = []
    seen = set()
    for p in points:
        key = p.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(p.strip())

    return base, deduped[:5]


def _build_visa_overview_with_llm(country: str, country_data: dict, guidance: Optional[str]) -> Optional[dict]:
    llm = _get_visa_llm()
    if llm is None:
        return None

    checklist = country_data.get("checklist", []) or []
    checklist_text = "\n".join(
        f"- [{item.get('category', 'Other')}] {item.get('item', '')}" for item in checklist[:20] if isinstance(item, dict)
    )
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a study abroad visa analyst. Summarize the student's visa docs clearly and concisely using only the provided context. "
            "Return valid JSON only, with keys: summary (string) and points (array of 3 to 5 short bullet strings). "
            "Do not add markdown, code fences, or extra keys. Keep the tone practical and student-friendly."
        ),
        (
            "human",
            "Country: {country}\n"
            "Visa type: {visa_type}\n"
            "Processing time: {processing_time}\n"
            "Visa fee (INR): {visa_fee_inr}\n"
            "Checklist categories and items:\n{checklist_text}\n\n"
            "Source excerpt from visa docs:\n{guidance}\n\n"
            "Write the overview JSON now."
        ),
    ])

    try:
        chain = prompt | llm
        response = chain.invoke({
            "country": country,
            "visa_type": country_data.get("visa_type", "Student visa"),
            "processing_time": country_data.get("processing_time", "varies by case"),
            "visa_fee_inr": country_data.get("visa_fee_inr", 0),
            "checklist_text": checklist_text or "No checklist items available.",
            "guidance": guidance or "No source excerpt available.",
        })
        content = getattr(response, "content", "") or ""
        parsed = json.loads(content)
        summary = str(parsed.get("summary", "")).strip()
        points = parsed.get("points", [])
        if not summary:
            return None
        if not isinstance(points, list):
            points = []
        cleaned_points = [str(p).strip() for p in points if str(p).strip()]
        return {"summary": summary, "points": cleaned_points[:5]}
    except Exception:
        return None


def _serialize_saved_checklist(row: UserVisaChecklist) -> SavedChecklistResponse:
    metadata = json.loads(row.metadata_json) if row.metadata_json else {}
    items = json.loads(row.items_json) if row.items_json else []
    checked = json.loads(row.checked_json) if row.checked_json else {}
    return SavedChecklistResponse(
        country=row.country,
        checklist_type=row.checklist_type,
        title=(metadata.get("title") if isinstance(metadata, dict) else None),
        metadata=metadata if isinstance(metadata, dict) else {},
        items=items if isinstance(items, list) else [],
        checked=checked if isinstance(checked, dict) else {},
        created_at=row.created_at.isoformat() + "Z",
        updated_at=(row.updated_at.isoformat() + "Z") if row.updated_at else None,
    )


@router.get("/checklist/{country}", response_model=VisaChecklistResponse)
def get_visa_checklist(country: str):
    data = load_visa_data()
    countries = data.get("countries", {})

    matched = None
    matched_key = None
    for key in countries:
        if key.lower() == country.lower():
            matched = countries[key]
            matched_key = key
            break

    if not matched:
        raise HTTPException(
            status_code=404,
            detail=f"Visa information for '{country}' not found. Available: {list(countries.keys())}"
        )

    source_doc = _find_country_visa_doc(matched_key)
    official_guidance = _read_guidance_excerpt(source_doc)
    llm_overview = _build_visa_overview_with_llm(matched_key, matched, official_guidance)
    if llm_overview:
        overview_summary = llm_overview["summary"]
        overview_points = llm_overview["points"]
    else:
        overview_summary, overview_points = _summarize_country_guidance(matched, official_guidance)

    return VisaChecklistResponse(
        country=matched_key,
        visa_type=matched["visa_type"],
        official_link=matched["official_link"],
        processing_time=matched["processing_time"],
        visa_fee_inr=matched["visa_fee_inr"],
        checklist=[ChecklistItem(**item) for item in matched["checklist"]],
        source_doc=source_doc,
        official_guidance=official_guidance,
        overview_summary=overview_summary,
        overview_points=overview_points,
    )


@router.get("/countries")
def get_visa_countries():
    data = load_visa_data()
    visa_data_countries = set(data.get("countries", {}).keys())

    docs_dir = _visa_docs_dir()
    doc_countries = set()
    if os.path.isdir(docs_dir):
        for filename in os.listdir(docs_dir):
            if not filename.lower().endswith(".md"):
                continue
            stem = os.path.splitext(filename)[0]
            key = stem.split("_")[0].strip()
            if key:
                doc_countries.add(key.replace("-", " "))

    countries = sorted(visa_data_countries)
    return {
        "countries": countries,
        "source_docs_count": len(doc_countries),
    }


@router.get("/saved-checklist", response_model=SavedChecklistResponse)
def get_saved_checklist(
    country: str = Query(..., min_length=2),
    checklist_type: str = Query("official"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(UserVisaChecklist)
        .filter(
            UserVisaChecklist.user_id == current_user.id,
            UserVisaChecklist.country.ilike(country),
            UserVisaChecklist.checklist_type == checklist_type,
        )
        .first()
    )
    if not row:
        return SavedChecklistResponse(
            country=country,
            checklist_type=checklist_type,
            title=None,
            metadata={"exists": False},
            items=[],
            checked={},
            created_at=None,
            updated_at=None,
        )
    return _serialize_saved_checklist(row)


@router.put("/saved-checklist", response_model=SavedChecklistResponse)
def upsert_saved_checklist(
    request: SaveChecklistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    country = request.country.strip()
    checklist_type = request.checklist_type.strip().lower() or "official"

    row = (
        db.query(UserVisaChecklist)
        .filter(
            UserVisaChecklist.user_id == current_user.id,
            UserVisaChecklist.country.ilike(country),
            UserVisaChecklist.checklist_type == checklist_type,
        )
        .first()
    )

    metadata = dict(request.metadata or {})
    if request.title:
        metadata["title"] = request.title

    if row:
        row.country = country
        row.checklist_type = checklist_type
        row.metadata_json = json.dumps(metadata, ensure_ascii=False)
        row.items_json = json.dumps(request.items or [], ensure_ascii=False)
        row.checked_json = json.dumps(request.checked or {}, ensure_ascii=False)
        row.updated_at = now
    else:
        row = UserVisaChecklist(
            user_id=current_user.id,
            country=country,
            checklist_type=checklist_type,
            metadata_json=json.dumps(metadata, ensure_ascii=False),
            items_json=json.dumps(request.items or [], ensure_ascii=False),
            checked_json=json.dumps(request.checked or {}, ensure_ascii=False),
            created_at=now,
            updated_at=now,
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return _serialize_saved_checklist(row)


@router.post("/query", response_model=VisaQueryResponse)
def visa_query(request: VisaQueryRequest) -> Any:
    """
    RAG-powered visa Q&A with hybrid search, cross-encoder re-ranking,
    and per-session conversation memory (last 6 exchanges).
    """
    specific_query = f"Regarding {request.country} student visa for Indian students: {request.query}"
    try:
        chain = get_visa_assistant_chain()
        result = chain.invoke({
            "input":      specific_query,
            "country":    request.country,
            "session_id": request.session_id or "default",
        })
        answer = result.get("answer", "No answer generated.")
        docs   = result.get("context", [])
        sources = [
            SourceInfo(
                doc=doc.metadata.get("source", "Unknown"),
                chunk=doc.page_content[:120] + "..."
            )
            for doc in docs
        ]
        metrics = evaluate_rag_response(request.query, docs, answer)
        return {"answer": answer, "sources": sources, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
def clear_memory(session_id: str):
    """Clear conversation memory for a given session."""
    clear_session_memory(session_id)
    return {"message": f"Memory cleared for session '{session_id}'"}
