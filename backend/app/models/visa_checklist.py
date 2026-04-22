from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, UniqueConstraint

from app.core.database import Base


class UserVisaChecklist(Base):
    __tablename__ = "user_visa_checklists"
    __table_args__ = (
        UniqueConstraint("user_id", "country", "checklist_type", name="uq_user_country_checklist_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    country = Column(String, nullable=False, index=True)
    checklist_type = Column(String, nullable=False, default="official")

    # Stored as JSON strings to stay dialect-agnostic across SQLite/Postgres.
    metadata_json = Column(Text, nullable=True)
    items_json = Column(Text, nullable=False)
    checked_json = Column(Text, nullable=False, default="{}")

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)