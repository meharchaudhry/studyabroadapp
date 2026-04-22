from app.core.database import Base
from app.models.user import User
from app.models.user_degree import Degree
from app.models.test_score import TestScore
from app.models.university import University
from app.models.job import Job, SavedJob, Cache
from app.models.visa_checklist import UserVisaChecklist

# Expose Base so alembic/env.py can import Base and see all models natively
__all__ = ["Base", "User", "Degree", "TestScore", "University", "Job", "SavedJob", "Cache", "UserVisaChecklist"]
