from sqlalchemy import Column, Integer, String, Float, Boolean
from app.core.database import Base

class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False, index=True)
    ranking = Column(Integer, nullable=True)
    
    # QS Subject-specific ranking
    qs_subject_ranking = Column(Integer, nullable=True)
    subject = Column(String, nullable=True, index=True)
    
    # Financials in INR
    tuition = Column(Float, nullable=True)
    living_cost = Column(Float, nullable=True)
    
    # Rich info
    image_url = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Admission requirements for Indian students
    requirements_cgpa = Column(Float, nullable=True)   # min CGPA out of 10
    ielts = Column(Float, nullable=True)
    toefl = Column(Integer, nullable=True)
    gre_required = Column(Boolean, nullable=True)
    scholarships = Column(String, nullable=True)
    course_duration = Column(Integer, nullable=True)    # in years
