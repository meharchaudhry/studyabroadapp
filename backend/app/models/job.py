from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True) # string since it might be an adzuna ID
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    job_type = Column(String, nullable=False) # e.g., 'part-time', 'on-campus', 'graduate'
    source = Column(String, nullable=False) # 'adzuna' or 'local'
    apply_url = Column(String, nullable=True)

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)

class Cache(Base):
    """Simple Key-Value cache for rate limiting Adzuna API"""
    __tablename__ = "cache"
    
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False) # JSON string
    expires_at = Column(DateTime, nullable=False, index=True)
