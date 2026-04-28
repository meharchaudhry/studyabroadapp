from sqlalchemy import Column, Integer, String, Boolean, Float, ARRAY, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)

    # Basic profile
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)

    # ── Academic background ─────────────────────────────────────────────────────
    cgpa = Column(Float, nullable=True)               # out of 10 (Indian scale)
    field_of_study = Column(String, nullable=True)    # e.g. "Computer Science"
    preferred_degree = Column(String, nullable=True)  # "Masters" | "PhD" | "Bachelors" | "MBA"
    current_degree = Column(String, nullable=True)    # "B.Tech" | "B.Sc" | "B.Com" | "BCA" etc.
    home_university = Column(String, nullable=True)   # Current Indian college name
    graduation_year = Column(Integer, nullable=True)  # Expected graduation year

    # ── Test scores ─────────────────────────────────────────────────────────────
    english_score = Column(Float, nullable=True)      # IELTS band score (e.g. 7.5)
    english_test = Column(String, nullable=True)      # "IELTS" | "TOEFL" | "Duolingo" | "PTE"
    toefl_score = Column(Integer, nullable=True)      # TOEFL iBT (0–120)
    gre_score = Column(Integer, nullable=True)        # GRE total (260–340)
    gmat_score = Column(Integer, nullable=True)       # GMAT (200–800)
    work_experience_years = Column(Float, nullable=True)  # Years of full-time work exp

    # ── Financial & destination preferences ────────────────────────────────────
    budget = Column(Integer, nullable=True)              # Annual budget in USD (derived)
    budget_inr = Column(Integer, nullable=True)          # Annual budget in INR (user input)
    target_countries = Column(ARRAY(String), nullable=True)
    intake_preference = Column(String, nullable=True)    # "Fall" | "Spring" | "Winter"
    ranking_preference = Column(String, nullable=True)   # "Top 50"|"Top 100"|"Top 200"|"Any"
    scholarship_interest = Column(Boolean, nullable=True)
    work_abroad_interest = Column(Boolean, nullable=True)

    # ── Strategy / psychographic preferences ─────────────────────────────────
    career_goal = Column(String, nullable=True)
    preferred_environment = Column(String, nullable=True)
    study_priority = Column(String, nullable=True)
    learning_style = Column(String, nullable=True)
    living_preference = Column(String, nullable=True)

    # ── Resume / portfolio ──────────────────────────────────────────────────────
    resume_text = Column(Text, nullable=True)   # Full extracted text of uploaded résumé
    resume_filename = Column(String, nullable=True)  # Original filename for display

    # OTP fields
    otp = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)

    degrees = relationship(
        "Degree",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tests = relationship(
        "TestScore",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
