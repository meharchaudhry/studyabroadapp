from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # What kind of consultation
    consultation_type = Column(String, nullable=False)   # "visa" | "university" | "finance" | "general"
    title = Column(String, nullable=False)               # short description
    notes = Column(Text, nullable=True)                  # optional detailed notes from user

    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)      # UTC datetime chosen by user
    duration_minutes = Column(Integer, default=30)

    # Status lifecycle
    status = Column(String, default="pending")           # "pending" | "confirmed" | "cancelled" | "completed"

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
