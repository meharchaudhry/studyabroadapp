from sqlalchemy import Column, Integer, String, Boolean, Float, ARRAY, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Degree(Base):
    __tablename__ = "user_degrees"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    degree_level = Column(String)
    specialization = Column(String)
    cgpa = Column(Float)
    institution = Column(String, nullable=True)
    year_graduated = Column(String, nullable=True)

    user = relationship("User", back_populates="degrees")

class TestScore(Base):
    __tablename__ = "user_tests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    test_name = Column(String) # GRE, GMAT, IELTS, etc.
    score = Column(Float)
    test_date = Column(String, nullable=True)

    user = relationship("User", back_populates="tests")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    budget = Column(Integer, nullable=True)
    target_countries = Column(ARRAY(String), nullable=True)
    phone_number = Column(String, nullable=True)
    
    # Core Preferences
    work_experience_years = Column(Integer, nullable=True)
    preferred_intake = Column(String, nullable=True)

    # Relationships
    degrees = relationship("Degree", back_populates="user", cascade="all, delete-orphan")
    tests = relationship("TestScore", back_populates="user", cascade="all, delete-orphan")

    # Psychographic & Career Fields
    career_goal = Column(String, nullable=True)
    preferred_environment = Column(String, nullable=True)
    study_priority = Column(String, nullable=True)
    learning_style = Column(String, nullable=True)
    living_preference = Column(String, nullable=True)

    # OTP fields
    otp = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
