import os
import csv
import json
import subprocess
import sys
from datetime import datetime
from threading import Lock
from typing import List
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter()


class AutomationResponse(BaseModel):
    workflow: str
    ok: bool
    steps: List[dict]
    task_id: str | None = None
    status: str | None = None


class AutomationTaskStatus(BaseModel):
    task_id: str
    workflow: str
    status: str
    ok: bool | None = None
    started_at: str
    finished_at: str | None = None
    steps: List[dict]
    error: str | None = None


class VisaChecklistItemIn(BaseModel):
    id: str
    category: str
    item: str


class VisaCountryIn(BaseModel):
    visa_type: str = "Student Visa"
    official_link: str = ""
    processing_time: str = ""
    visa_fee_inr: int = 0
    checklist: List[VisaChecklistItemIn] = Field(default_factory=list)


class VisaDocumentIn(BaseModel):
    country: str
    filename: str | None = None
    official_link: str | None = None
    content: str


class VisaIngestRequest(BaseModel):
    countries: dict[str, VisaCountryIn] = Field(default_factory=dict)
    documents: List[VisaDocumentIn] = Field(default_factory=list)


class JobIngestRow(BaseModel):
    title: str
    company: str | None = None
    salary: str | None = None
    location: str | None = None
    job_type: str = "graduate"
    apply_link: str | None = None
    source: str | None = None
    country: str | None = None
    country_code: str | None = None


class JobsIngestRequest(BaseModel):
    jobs: List[JobIngestRow] = Field(default_factory=list)


class HousingListingIn(BaseModel):
    id: str | None = None
    title: str
    country: str
    price_inr: int
    distance_km: float | int = 0
    amenities: List[str] = Field(default_factory=list)
    image_url: str | None = None
    available_from: str | None = None
    student_friendly: bool = True


class HousingIngestRequest(BaseModel):
    listings: List[HousingListingIn] = Field(default_factory=list)


_TASKS_LOCK = Lock()
_AUTOMATION_TASKS: dict[str, dict] = {}


def _require_automation_token(x_automation_token: str | None) -> None:
    expected = settings.N8N_WEBHOOK_TOKEN
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="N8N_WEBHOOK_TOKEN is not configured on backend.",
        )
    if x_automation_token != expected:
        raise HTTPException(status_code=401, detail="Invalid automation token")


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _data_dir() -> str:
    return os.path.join(_repo_root(), "data")


def _run_step(title: str, args: List[str]) -> dict:
    proc = subprocess.run(
        args,
        cwd=_repo_root(),
        text=True,
        capture_output=True,
    )
    return {
        "title": title,
        "ok": proc.returncode == 0,
        "return_code": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
        "command": " ".join(args),
    }


def _safe_slug(value: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "doc"


def _utc_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _create_task(workflow: str, steps: List[dict]) -> str:
    task_id = str(uuid4())
    with _TASKS_LOCK:
        _AUTOMATION_TASKS[task_id] = {
            "task_id": task_id,
            "workflow": workflow,
            "status": "running",
            "ok": None,
            "started_at": _utc_iso(),
            "finished_at": None,
            "steps": steps,
            "error": None,
        }
    return task_id


def _complete_task(task_id: str, step: dict) -> None:
    with _TASKS_LOCK:
        task = _AUTOMATION_TASKS.get(task_id)
        if not task:
            return
        task["steps"].append(step)
        task["ok"] = bool(step.get("ok", False))
        task["status"] = "completed" if task["ok"] else "failed"
        task["finished_at"] = _utc_iso()


def _fail_task(task_id: str, message: str) -> None:
    with _TASKS_LOCK:
        task = _AUTOMATION_TASKS.get(task_id)
        if not task:
            return
        task["ok"] = False
        task["status"] = "failed"
        task["error"] = message
        task["finished_at"] = _utc_iso()


def _run_visa_ingest_task(task_id: str) -> None:
    try:
        ingest_step = _run_step("Rebuild visa embeddings", [sys.executable, "scripts/ingest_visa.py"])
        _complete_task(task_id, ingest_step)
    except Exception as exc:  # pragma: no cover - defensive task guard
        _fail_task(task_id, str(exc))


@router.post("/universities/refresh", response_model=AutomationResponse)
def refresh_universities(x_automation_token: str | None = Header(default=None)):
    _require_automation_token(x_automation_token)

    steps = [
        _run_step("Fetch Kaggle rankings", [sys.executable, "scripts/fetch_kaggle_rankings.py"]),
        _run_step("Build merged university dataset", [sys.executable, "scripts/build_university_dataset.py"]),
        _run_step("Seed universities to DB", [sys.executable, "scripts/seed_universities.py"]),
    ]
    ok = all(s["ok"] for s in steps)
    return AutomationResponse(workflow="universities_refresh", ok=ok, steps=steps)


@router.post("/visa/reingest", response_model=AutomationResponse)
def reingest_visa(x_automation_token: str | None = Header(default=None)):
    _require_automation_token(x_automation_token)

    steps = [
        _run_step("Refresh visa source docs", [sys.executable, "scripts/scrape_visa.py"]),
        _run_step("Rebuild visa embeddings", [sys.executable, "scripts/ingest_visa.py"]),
    ]
    ok = all(s["ok"] for s in steps)
    return AutomationResponse(workflow="visa_reingest", ok=ok, steps=steps)


@router.post("/jobs/refresh", response_model=AutomationResponse)
def refresh_jobs(x_automation_token: str | None = Header(default=None)):
    _require_automation_token(x_automation_token)

    steps = [
        _run_step("Refresh local jobs CSV", [sys.executable, "scripts/scrape_jobs.py"]),
        _run_step("Seed jobs to DB", [sys.executable, "scripts/seed_jobs.py"]),
    ]
    ok = all(s["ok"] for s in steps)
    return AutomationResponse(workflow="jobs_refresh", ok=ok, steps=steps)


@router.post("/housing/refresh", response_model=AutomationResponse)
def refresh_housing(x_automation_token: str | None = Header(default=None)):
    _require_automation_token(x_automation_token)

    steps = [
        _run_step("Refresh housing listings JSON", [sys.executable, "scripts/generate_housing.py"]),
    ]
    ok = all(s["ok"] for s in steps)
    return AutomationResponse(workflow="housing_refresh", ok=ok, steps=steps)


@router.post("/ingest/visa", response_model=AutomationResponse)
def ingest_visa_payload(
    payload: VisaIngestRequest,
    background_tasks: BackgroundTasks,
    x_automation_token: str | None = Header(default=None),
):
    _require_automation_token(x_automation_token)

    data_dir = _data_dir()
    docs_dir = os.path.join(data_dir, "visa_docs")
    os.makedirs(docs_dir, exist_ok=True)

    written_steps: List[dict] = []

    if payload.countries:
        visa_data_path = os.path.join(data_dir, "visa_data.json")
        new_data = {
            "countries": {
                country: details.model_dump()
                for country, details in payload.countries.items()
            }
        }
        with open(visa_data_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)

        written_steps.append(
            {
                "title": "Write visa_data.json",
                "ok": True,
                "countries": len(payload.countries),
                "path": visa_data_path,
            }
        )

    if payload.documents:
        for doc in payload.documents:
            filename = doc.filename or f"{_safe_slug(doc.country)}_student_visa.md"
            if not filename.endswith(".md"):
                filename += ".md"

            header = [
                f"# {doc.country} Student Visa",
                "",
            ]
            if doc.official_link:
                header.append(f"Official Link: {doc.official_link}")
                header.append("")
            header.append(f"Last Refreshed (UTC): {datetime.utcnow().isoformat()}Z")
            header.append("")
            content = "\n".join(header) + doc.content.strip() + "\n"

            with open(os.path.join(docs_dir, filename), "w", encoding="utf-8") as f:
                f.write(content)

        written_steps.append(
            {
                "title": "Write visa markdown docs",
                "ok": True,
                "documents": len(payload.documents),
                "path": docs_dir,
            }
        )

    has_new_data = bool(payload.countries or payload.documents)
    if not has_new_data:
        steps = [
            {
                "title": "Skip visa embeddings rebuild",
                "ok": True,
                "reason": "No countries or documents provided in payload",
            }
        ]
        return AutomationResponse(
            workflow="visa_ingest_payload",
            ok=True,
            status="completed",
            steps=steps,
        )

    queued_step = {
        "title": "Rebuild visa embeddings",
        "ok": True,
        "status": "queued",
    }
    task_id = _create_task("visa_ingest_payload", written_steps + [queued_step])
    background_tasks.add_task(_run_visa_ingest_task, task_id)
    return AutomationResponse(
        workflow="visa_ingest_payload",
        ok=True,
        status="queued",
        task_id=task_id,
        steps=written_steps + [queued_step],
    )


@router.get("/tasks/{task_id}", response_model=AutomationTaskStatus)
def get_automation_task(task_id: str, x_automation_token: str | None = Header(default=None)):
    _require_automation_token(x_automation_token)

    with _TASKS_LOCK:
        task = _AUTOMATION_TASKS.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return AutomationTaskStatus(**task)


@router.post("/ingest/jobs", response_model=AutomationResponse)
def ingest_jobs_payload(
    payload: JobsIngestRequest,
    x_automation_token: str | None = Header(default=None),
):
    _require_automation_token(x_automation_token)

    data_dir = _data_dir()
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "local_jobs.csv")

    fieldnames = ["title", "company", "salary", "location", "job_type", "apply_link"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload.jobs:
            writer.writerow(
                {
                    "title": row.title,
                    "company": row.company or "",
                    "salary": row.salary or "Competitive",
                    "location": row.location or "",
                    "job_type": row.job_type or "graduate",
                    "apply_link": row.apply_link or "#",
                }
            )

    steps = [
        {
            "title": "Write local_jobs.csv",
            "ok": True,
            "rows": len(payload.jobs),
            "path": csv_path,
        },
        _run_step("Seed jobs to DB", [sys.executable, "scripts/seed_jobs.py"]),
    ]
    ok = all(s.get("ok", False) for s in steps)
    return AutomationResponse(workflow="jobs_ingest_payload", ok=ok, steps=steps)


@router.post("/ingest/housing", response_model=AutomationResponse)
def ingest_housing_payload(
    payload: HousingIngestRequest,
    x_automation_token: str | None = Header(default=None),
):
    _require_automation_token(x_automation_token)

    data_dir = _data_dir()
    os.makedirs(data_dir, exist_ok=True)
    housing_path = os.path.join(data_dir, "live_housing.json")

    listings = []
    for idx, listing in enumerate(payload.listings, start=1):
        item = listing.model_dump()
        item["id"] = item.get("id") or f"n8n_prop_{idx}"
        listings.append(item)

    with open(housing_path, "w", encoding="utf-8") as f:
        json.dump(listings, f, indent=2, ensure_ascii=False)

    steps = [
        {
            "title": "Write live_housing.json",
            "ok": True,
            "rows": len(listings),
            "path": housing_path,
        }
    ]
    return AutomationResponse(workflow="housing_ingest_payload", ok=True, steps=steps)
