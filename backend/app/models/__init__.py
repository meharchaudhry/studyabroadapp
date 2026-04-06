from app.core.database import Base
from app.models.user import User
from app.models.university import University
from app.models.job import Job, SavedJob, Cache

# Expose Base so alembic/env.py can import Base and see all models natively
__all__ = ["Base", "User", "University", "Job", "SavedJob", "Cache"]
