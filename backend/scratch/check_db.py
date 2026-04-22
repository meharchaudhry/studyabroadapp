import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.university import University
from app.models.job import Job

def check_counts():
    db = SessionLocal()
    try:
        uni_count = db.query(University).count()
        job_count = db.query(Job).count()
        print(f"Universities: {uni_count}")
        print(f"Jobs: {job_count}")
    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_counts()
