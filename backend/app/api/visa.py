from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.rag import get_visa_assistant_chain, evaluate_rag_response, clear_session_memory
import json
import os

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


def load_visa_data():
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "visa_data.json"
    )
    with open(data_path, "r") as f:
        return json.load(f)


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

    return VisaChecklistResponse(
        country=matched_key,
        visa_type=matched["visa_type"],
        official_link=matched["official_link"],
        processing_time=matched["processing_time"],
        visa_fee_inr=matched["visa_fee_inr"],
        checklist=[ChecklistItem(**item) for item in matched["checklist"]]
    )


@router.get("/countries")
def get_visa_countries():
    data = load_visa_data()
    return {"countries": list(data.get("countries", {}).keys())}


@router.post("/query", response_model=VisaQueryResponse)
def visa_query(request: VisaQueryRequest) -> Any:
    """
    RAG-powered visa Q&A with hybrid search, cross-encoder re-ranking,
    and per-session conversation memory (last 6 exchanges).
    """
    try:
        chain = get_visa_assistant_chain()
        result = chain.invoke({
            "input":      request.query,   # raw query — country is passed separately
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
