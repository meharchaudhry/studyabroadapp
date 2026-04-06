from typing import Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.services.rag import get_visa_assistant_chain, evaluate_rag_response
import json
import os

router = APIRouter()

class VisaQueryRequest(BaseModel):
    query: str
    country: str

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
    from fastapi import HTTPException
    data = load_visa_data()
    countries = data.get("countries", {})
    
    # Case-insensitive lookup
    matched = None
    for key in countries:
        if key.lower() == country.lower():
            matched = countries[key]
            matched_key = key
            break
    
    if not matched:
        raise HTTPException(status_code=404, detail=f"Visa information for '{country}' not found. Available: {list(countries.keys())}")
    
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
    specific_query = f"Regarding {request.country} visa for Indian students: {request.query}"
    try:
        chain = get_visa_assistant_chain()
        result = chain.invoke({"input": specific_query, "country": request.country})
        answer = result.get("answer", "No answer generated.")
        docs = result.get("context", [])
        sources = [
            SourceInfo(doc=doc.metadata.get("source", "Unknown"), chunk=doc.page_content[:120] + "...")
            for doc in docs
        ]
        metrics = evaluate_rag_response(request.query, docs, answer)
        return {"answer": answer, "sources": sources, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
