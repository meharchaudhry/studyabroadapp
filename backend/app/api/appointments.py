from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.appointment import Appointment
from app.models.user import User

router = APIRouter()

# ── Schemas ────────────────────────────────────────────────────────────────────

CONSULTATION_TYPES = {"visa", "university", "finance", "general"}
VALID_STATUSES = {"pending", "confirmed", "cancelled", "completed"}

class AppointmentCreate(BaseModel):
    consultation_type: str   # "visa" | "university" | "finance" | "general"
    title: str
    notes: Optional[str] = None
    scheduled_at: datetime   # ISO 8601 UTC
    duration_minutes: int = 30

class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    user_id: int
    consultation_type: str
    title: str
    notes: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=List[AppointmentOut])
def list_appointments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all appointments for the current user, optionally filtered by status."""
    q = db.query(Appointment).filter(Appointment.user_id == current_user.id)
    if status:
        q = q.filter(Appointment.status == status)
    return q.order_by(Appointment.scheduled_at).all()


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    body: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Book a new appointment/consultation slot."""
    if body.consultation_type not in CONSULTATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"consultation_type must be one of: {', '.join(sorted(CONSULTATION_TYPES))}"
        )
    if body.scheduled_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="scheduled_at must be in the future.")

    appt = Appointment(
        user_id=current_user.id,
        consultation_type=body.consultation_type,
        title=body.title,
        notes=body.notes,
        scheduled_at=body.scheduled_at,
        duration_minutes=body.duration_minutes,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.get("/{appt_id}", response_model=AppointmentOut)
def get_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    appt = db.query(Appointment).filter(
        Appointment.id == appt_id,
        Appointment.user_id == current_user.id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    return appt


@router.patch("/{appt_id}", response_model=AppointmentOut)
def update_appointment(
    appt_id: int,
    body: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update an existing appointment (reschedule, add notes, cancel)."""
    appt = db.query(Appointment).filter(
        Appointment.id == appt_id,
        Appointment.user_id == current_user.id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if appt.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot modify a completed appointment.")

    if body.status and body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(appt, field, value)
    appt.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(appt)
    return appt


@router.delete("/{appt_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Cancel (delete) an appointment."""
    appt = db.query(Appointment).filter(
        Appointment.id == appt_id,
        Appointment.user_id == current_user.id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    db.delete(appt)
    db.commit()
