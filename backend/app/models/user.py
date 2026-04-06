from sqlalchemy import Column, Integer, String, Boolean, Float, ARRAY, DateTime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    cgpa = Column(Float, nullable=True)
    budget = Column(Integer, nullable=True)
    target_countries = Column(ARRAY(String), nullable=True)
    phone_number = Column(String, nullable=True)
    
    # OTP fields
    otp = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
